# prompts_app/views.py - OPTIMIZED VERSION

from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework import status   # ← ADD THIS LINE
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.decorators import api_view, permission_classes
from django.db import models, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta

# FIX #1: Django cache framework
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.core.cache import cache

from .models import Category, Prompt, Favourite, PromptLike, Ad, AdmobConfig
from .serializers import (
    CategorySerializer,
    PromptSerializer,
    AdSerializer,
    AdCreateSerializer,
    AdmobConfigSerializer,
)

User = get_user_model()

CACHE_TTL = 60 * 5  # 5 minutes


# ===================== PUBLIC APIs =====================

class CategoryList(generics.ListAPIView):
    # FIX #2: prefetch_related so prompts_count doesn't N+1
    queryset = Category.objects.prefetch_related('prompts').order_by('order')
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        # FIX #3: Cache category list — it barely changes
        cache_key = 'category_list'
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        real_categories = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(real_categories, many=True)
        real_data = serializer.data

        total_prompts = Prompt.objects.count()

        all_category = {
            "id": "all",
            "name": "All",
            "slug": "all",
            "order": -999,
            "prompts_count": total_prompts,
        }

        final_data = [all_category] + list(real_data)
        cache.set(cache_key, final_data, CACHE_TTL)
        return Response(final_data)


class PromptList(generics.ListAPIView):
    serializer_class = PromptSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        # FIX #4: select_related avoids extra JOIN per prompt
        queryset = (
            Prompt.objects
            .select_related('category')
            .prefetch_related('likes')
            .order_by('-created_at')
        )

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(title__icontains=search) |
                models.Q(prompt_text__icontains=search)
            )

        category = self.request.query_params.get('category')
        if category not in ['all', '', None]:
            queryset = queryset.filter(category__slug=category)

        return queryset

    def list(self, request, *args, **kwargs):
        device_id = request.query_params.get('device_id', '')
        category  = request.query_params.get('category', 'all') or 'all'
        search    = request.query_params.get('search', '')

        # FIX #5: Cache per-category (but NOT per-device, so is_liked handled below)
        cache_key = f'prompts_{category}_{search}'
        cached_data = cache.get(cache_key)

        if cached_data is None:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(
                queryset, many=True,
                context={'device_id': device_id},
            )
            cached_data = serializer.data
            # Don't cache search results (too varied); cache category pages
            if not search:
                cache.set(cache_key, cached_data, CACHE_TTL)

        # FIX #6: Inject is_liked per-device after cache fetch (fast set lookup)
        if device_id and cached_data:
            liked_ids = set(
                PromptLike.objects
                .filter(device_id=device_id)
                .values_list('prompt_id', flat=True)
            )
            # Mutate a copy so cached object stays clean
            import copy
            cached_data = copy.deepcopy(cached_data)
            for p in cached_data:
                p['is_liked'] = str(p['id']) in {str(i) for i in liked_ids}

        return Response(cached_data)


class PromptDetail(generics.RetrieveAPIView):
    queryset = Prompt.objects.select_related('category').prefetch_related('likes')
    serializer_class = PromptSerializer
    lookup_field = 'pk'
    permission_classes = [AllowAny]

    def retrieve(self, request, *args, **kwargs):
        prompt = self.get_object()
        # FIX #7: Use F() expression — no race condition on usage_count
        Prompt.objects.filter(pk=prompt.pk).update(
            usage_count=models.F('usage_count') + 1
        )
        serializer = self.get_serializer(
            prompt,
            context={'device_id': request.query_params.get('device_id')},
        )
        return Response(serializer.data)


# ===================== LIKE & FAVOURITE =====================

class FavouriteListCreate(generics.ListCreateAPIView):
    serializer_class = PromptSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        device_id = self.request.query_params.get('device_id')
        if not device_id:
            return Prompt.objects.none()
        return Prompt.objects.filter(
            favourite__device_id=device_id
        ).select_related('category')

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
        like, created = PromptLike.objects.get_or_create(
            device_id=device_id, prompt=prompt
        )

        if not created:
            like.delete()
            liked = False
        else:
            liked = True

        like_count = prompt.likes.count()
        # FIX #8: Save only like_count field, not full object
        Prompt.objects.filter(pk=prompt.pk).update(like_count=like_count)

        # Invalidate cache so next list call reflects new count
        cache.delete(f'prompts_{prompt.category.slug}_')
        cache.delete('prompts_all_')

        return Response({"liked": liked, "like_count": like_count})


# ===================== ADMIN ONLY APIs =====================

class PromptCreateView(generics.CreateAPIView):
    queryset = Prompt.objects.all()
    serializer_class = PromptSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def perform_create(self, serializer):
        instance = serializer.save()
        # Bust cache for affected category
        cache.delete(f'prompts_{instance.category.slug}_')
        cache.delete('prompts_all_')
        cache.delete('category_list')


class PromptUpdateView(generics.UpdateAPIView):
    queryset = Prompt.objects.all()
    serializer_class = PromptSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    lookup_field = 'pk'

    def perform_update(self, serializer):
        instance = serializer.save()
        cache.delete(f'prompts_{instance.category.slug}_')
        cache.delete('prompts_all_')


class PromptDeleteView(generics.DestroyAPIView):
    queryset = Prompt.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

    def perform_destroy(self, instance):
        cache.delete(f'prompts_{instance.category.slug}_')
        cache.delete('prompts_all_')
        cache.delete('category_list')
        instance.delete()


# ===================== CATEGORY ADMIN VIEWS =====================

class CategoryCreateView(generics.CreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()
        cache.delete('category_list')


class CategoryUpdateView(generics.UpdateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def perform_update(self, serializer):
        serializer.save()
        cache.delete('category_list')


class CategoryDeleteView(generics.DestroyAPIView):
    queryset = Category.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def perform_destroy(self, instance):
        cache.delete('category_list')
        instance.delete()


# ===================== ADS =====================

class ActiveAdsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            ads = Ad.objects.filter(is_active=True)
            active_ads = [ad for ad in ads if not ad.is_expired()]
            banner = next((a for a in active_ads if a.ad_type == 'banner'), None)
            video  = next((a for a in active_ads if a.ad_type == 'video'), None)
            return Response({
                'banner_ad': AdSerializer(banner).data if banner else None,
                'video_ad':  AdSerializer(video).data  if video  else None,
            })
        except Exception as e:
            return Response({'banner_ad': None, 'video_ad': None})


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
        ad = serializer.save(ad_type=ad_type, is_active=True, created_at=timezone.now())

    return Response({
        "success": True,
        "message": f"{ad_type.title()} Ad is now LIVE!",
        "ad": AdSerializer(ad).data,
    }, status=201)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deactivate_ad(request):
    ad_type = request.data.get('ad_type')
    if ad_type not in ['banner', 'video']:
        return Response({"error": "ad_type must be 'banner' or 'video'"}, status=400)

    with transaction.atomic():
        count = Ad.objects.filter(ad_type=ad_type, is_active=True).update(is_active=False)

    msg = f"{ad_type.title()} ad deactivated" if count else f"No active {ad_type} ad found"
    return Response({"success": True, "message": msg})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_admin_credentials(request):
    if not request.user.is_superuser:
        return Response({"error": "Only superuser can change admin credentials"}, status=403)

    username = request.data.get('username')
    password = request.data.get('password')

    if not username or len(username) < 4:
        return Response({"error": "Username must be at least 4 characters"}, status=400)
    if not password or len(password) < 6:
        return Response({"error": "Password must be at least 6 characters"}, status=400)

    try:
        user = request.user
        user.username = username
        user.set_password(password)
        user.save()
        return Response({"success": True, "message": "Admin credentials updated! Please login again."})
    except Exception:
        return Response({"error": "Failed to update credentials"}, status=500)


# ===================== ADMOB CONFIG =====================

class AdmobConfigPublicView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        config = AdmobConfig.objects.filter(is_active=True).first()
        if config:
            return Response(AdmobConfigSerializer(config).data)

        return Response({
            "banner_android":             "ca-app-pub-3940256099942544/6300978111",
            "banner_ios":                 "ca-app-pub-3940256099942544/2934735716",
            "interstitial_android":       "ca-app-pub-3940256099942544/1033173712",
            "interstitial_ios":           "ca-app-pub-3940256099942544/4411468910",
            "rewarded_android":           "ca-app-pub-3940256099942544/5224354917",
            "rewarded_ios":               "ca-app-pub-3940256099942544/1712485313",
            "app_open_android":           "ca-app-pub-3940256099942544/3419835294",
            "app_open_ios":               "ca-app-pub-3940256099942544/5662855255",
            "rewarded_interstitial_android": "ca-app-pub-3940256099942544/5351527112",
            "rewarded_interstitial_ios":  "ca-app-pub-3940256099942544/6978759865",
            "native_android": "",
            "native_ios": "",
        })


class AdmobConfigAdminView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        config = (
            AdmobConfig.objects.filter(is_active=True).first()
            or AdmobConfig.objects.order_by('-updated_at').first()
        )
        if config:
            return Response(AdmobConfigSerializer(config).data)

        return Response({
            "banner_android": "", "banner_ios": "",
            "interstitial_android": "", "interstitial_ios": "",
            "rewarded_android": "", "rewarded_ios": "",
            "app_open_android": "", "app_open_ios": "",
            "is_active": False,
            "app_id_android": "", "app_id_ios": "",
            "rewarded_interstitial_android": "", "rewarded_interstitial_ios": "",
            "native_android": "", "native_ios": "",
            "notes": "",
        })

    @transaction.atomic
    def post(self, request):
        data = request.data.copy()
        defaults = {
            "app_id_android": "",
            "app_id_ios": "",
            "rewarded_interstitial_android": "",
            "rewarded_interstitial_ios": "",
            "native_android": "",
            "native_ios": "",
            "notes": "Updated from admin panel on " + timezone.now().strftime("%Y-%m-%d %H:%M"),
        }
        for key, value in defaults.items():
            data.setdefault(key, value)

        want_active = bool(data.get("is_active"))
        if want_active:
            AdmobConfig.objects.filter(is_active=True).update(is_active=False)

        existing = AdmobConfig.objects.first()
        if existing:
            serializer = AdmobConfigSerializer(existing, data=data, partial=True)
        else:
            serializer = AdmobConfigSerializer(data=data)

        if serializer.is_valid():
            saved = serializer.save()
            saved.is_active = want_active
            saved.save(update_fields=["is_active"])
            return Response({
                "success": True,
                "message": "AdMob settings saved successfully!",
                "data": AdmobConfigSerializer(saved).data,
            })

        return Response({"success": False, "errors": serializer.errors}, status=400)