# prompts_app/views.py

from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db import models
from django.shortcuts import get_object_or_404

from .models import Category, Prompt, Favourite, PromptLike
from .serializers import CategorySerializer, PromptSerializer


# ===================== PUBLIC APIs (Bina Login Ke) =====================

class CategoryList(generics.ListAPIView):
    queryset = Category.objects.all().order_by('order')
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

    # Fix: Direct list return (no pagination issue)
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PromptList(generics.ListAPIView):
    serializer_class = PromptSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Prompt.objects.select_related('category').all().order_by('-created_at')
        device_id = self.request.query_params.get('device_id')

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
        serializer = serializer = self.get_serializer(
    queryset, many=True,
    context={
        'device_id': request.query_params.get('device_id'),
        'request': request
    }
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
        serializer = serializer = self.get_serializer(
    prompt,
    context={
        'device_id': request.query_params.get('device_id'),
        'request': request
    }
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
    lookup_field = 'id'  # UUID field


class CategoryDeleteView(generics.DestroyAPIView):
    queryset = Category.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'