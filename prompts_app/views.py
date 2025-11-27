# prompts_app/views.py

from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.decorators import api_view, permission_classes
from django.db import models, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta

from .models import Category, Prompt, Favourite, PromptLike, Ad
from .serializers import CategorySerializer, PromptSerializer, AdSerializer, AdCreateSerializer  # <-- Add AdCreateSerializer


# ===================== PUBLIC APIs (Bina Login Ke) =====================

class CategoryList(generics.ListAPIView):
    queryset = Category.objects.all().order_by('order')
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PromptList(generics.ListAPIView):
    serializer_class = PromptSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Prompt.objects.select_related('category').all().order_by('-created_at')
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(title__icontains=search) |
                models.Q(prompt_text__icontains=search)
            )
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(
            queryset, many=True,
            context={'device_id': request.query_params.get('device_id'), 'request': request}
        )
        return Response(serializer.data)


class PromptDetail(generics.RetrieveAPIView):
    queryset = Prompt.objects.all()
    serializer_class = PromptSerializer
    lookup_field = 'pk'
    permission_classes = [AllowAny]

    def retrieve(self, request, *args, **kwargs):
        prompt = self.get_object()
        prompt.usage_count += 1
        prompt.save()
        serializer = self.get_serializer(
            prompt,
            context={'device_id': request.query_params.get('device_id'), 'request': request}
        )
        return Response(serializer.data)


# ===================== LIKE & FAVOURITE (Device Based) =====================

class FavouriteListCreate(generics.ListCreateAPIView):
    serializer_class = PromptSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        device_id = self.request.query_params.get('device_id')
        if not device_id:
            return Prompt.objects.none()
        return Prompt.objects.filter(favourite__device_id=device_id)

    def perform_create(self, serializer):
        device_id = self.request.data.get('device_id')
        prompt_id = self.request.data.get('prompt_id')
        Favourite.objects.get_or_create(device_id=device_id, prompt_id=prompt_id)


class FavouriteDelete(generics.DestroyAPIView):
    permission_classes = [AllowAny]

    def delete(self, request, *args, **kwargs):
        device_id = request.query_params.get('device_id')
        prompt_id = kwargs.get('pk')
        try:
            fav = Favourite.objects.get(device_id=device_id, prompt_id=prompt_id)
            fav.delete()
            return Response({"removed": True})
        except Favourite.DoesNotExist:
            return Response({"error": "Not in favourites"}, status=404)


class LikeToggle(APIView):
    permission_classes = [AllowAny]

    def post(self, request, pk):
        device_id = request.data.get('device_id')
        if not device_id:
            return Response({"error": "device_id required"}, status=400)

        prompt = get_object_or_404(Prompt, id=pk)
        like, created = PromptLike.objects.get_or_create(device_id=device_id, prompt=prompt)

        if not created:
            like.delete()
            liked = False
        else:
            liked = True

        prompt.like_count = prompt.likes.count()
        prompt.save()

        return Response({"liked": liked, "like_count": prompt.like_count})


# ===================== ADMIN ONLY APIs (JWT Required) =====================

class PromptCreateView(generics.CreateAPIView):
    queryset = Prompt.objects.all()
    serializer_class = PromptSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]


class PromptUpdateView(generics.UpdateAPIView):
    queryset = Prompt.objects.all()
    serializer_class = PromptSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    lookup_field = 'pk'


class PromptDeleteView(generics.DestroyAPIView):
    queryset = Prompt.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'


# ===================== CATEGORY ADMIN VIEWS (JWT Required) =====================

class CategoryCreateView(generics.CreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


class CategoryUpdateView(generics.UpdateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'


class CategoryDeleteView(generics.DestroyAPIView):
    queryset = Category.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'


# ===================== ADS SYSTEM - ACTIVE ADS (PUBLIC) =====================

# views.py → ActiveAdsView ko ye safe version se replace kar do

# ===================== ADS SYSTEM - ACTIVE ADS (PUBLIC) =====================

class ActiveAdsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            ads = Ad.objects.filter(is_active=True)
            active_ads = []

            for ad in ads:
                try:
                    if not ad.is_expired():
                        active_ads.append(ad)
                except:
                    continue

            banner = next((a for a in active_ads if a.ad_type == 'banner'), None)
            video = next((a for a in active_ads if a.ad_type == 'video'), None)

            return Response({
                'banner_ad': AdSerializer(banner).data if banner else None,
                'video_ad': AdSerializer(video).data if video else None,
            })

        except Exception as e:
            print("Ad Error:", e)
            return Response({
                'banner_ad': None,
                'video_ad': None
            })


# ===================== ADMIN: ACTIVATE BANNER / VIDEO AD (INSTANT LIVE) =====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def activate_banner_ad(request):
    return _activate_ad(request, 'banner')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def activate_video_ad(request):
    return _activate_ad(request, 'video')


def _activate_ad(request, ad_type):
    serializer = AdCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    with transaction.atomic():
        Ad.objects.filter(ad_type=ad_type, is_active=True).update(is_active=False)
        ad = serializer.save(
            ad_type=ad_type,
            is_active=True,
            created_at=timezone.now()
        )

    return Response({
        "success": True,
        "message": f"{ad_type.title()} Ad is now LIVE!",
        "ad": AdSerializer(ad).data
    }, status=201)