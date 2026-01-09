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
from django.contrib.auth import get_user_model
from datetime import timedelta

from .models import Category, Prompt, Favourite, PromptLike, Ad, AdmobConfig
from .serializers import (
    CategorySerializer,
    PromptSerializer,
    AdSerializer,
    AdCreateSerializer,
    AdmobConfigSerializer
)

User = get_user_model()


# ===================== PUBLIC APIs (Bina Login Ke) =====================

class CategoryList(generics.ListAPIView):
    queryset = Category.objects.all().order_by('order')
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        real_categories = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(real_categories, many=True)
        real_data = serializer.data

        total_prompts = Prompt.objects.count()

        all_category = {
            "id": "all",
            "name": "All",
            "slug": "all",
            "order": -999,
            "prompts_count": total_prompts
        }

        final_data = [all_category] + real_data
        return Response(final_data)


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
        if category not in ['all', '', None]:
            queryset = queryset.filter(category__slug=category)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(
            queryset, many=True,
            context={'device_id': request.query_params.get('device_id')}
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
            context={'device_id': request.query_params.get('device_id')}
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


# ===================== CATEGORY ADMIN VIEWS =====================

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

class ActiveAdsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            ads = Ad.objects.filter(is_active=True)
            active_ads = [ad for ad in ads if not ad.is_expired()]

            banner = next((a for a in active_ads if a.ad_type == 'banner'), None)
            video = next((a for a in active_ads if a.ad_type == 'video'), None)

            return Response({
                'banner_ad': AdSerializer(banner).data if banner else None,
                'video_ad': AdSerializer(video).data if video else None,
            })
        except Exception as e:
            print("Ad Error:", e)
            return Response({'banner_ad': None, 'video_ad': None})


# ===================== ADMIN: ACTIVATE / DEACTIVATE ADS =====================

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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deactivate_ad(request):
    ad_type = request.data.get('ad_type')

    if ad_type not in ['banner', 'video']:
        return Response({"error": "ad_type must be 'banner' or 'video'"}, status=400)

    with transaction.atomic():
        count = Ad.objects.filter(ad_type=ad_type, is_active=True).update(is_active=False)

    if count > 0:
        return Response({"success": True, "message": f"{ad_type.title()} ad deactivated"})
    return Response({"success": True, "message": f"No active {ad_type} ad found"})


# ===================== ADMIN: CHANGE CREDENTIALS =====================

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
        return Response({
            "success": True,
            "message": "Admin credentials updated! Please login again."
        })
    except Exception:
        return Response({"error": "Failed to update credentials"}, status=500)


class AdmobConfigView(APIView):
    """
    Flutter ऐप इस endpoint से AdMob के सारे ad unit IDs ले सकता है।
    Admin पैनल में AdmobConfig मॉडल एडिट करके IDs बदल सकते हो।
    """
    permission_classes = [AllowAny]

    def get(self, request):
        # सबसे पहले एक्टिव कॉन्फ़िगरेशन ढूंढो
        config = AdmobConfig.objects.filter(is_active=True).first()

        if config:
            # अगर एक्टिव कॉन्फ़िगरेशन मिल गया तो उसे serialize करके भेज दो
            serializer = AdmobConfigSerializer(config)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # अगर कोई एक्टिव कॉन्फ़िगरेशन नहीं मिला तो Google के ऑफिशियल टेस्ट IDs भेजो
        # (ये IDs प्रोडक्शन में भी काम करते हैं, लेकिन असली revenue नहीं देते)
        test_config = {
            "banner_android": "ca-app-pub-3940256099942544/6300978111",
            "banner_ios": "ca-app-pub-3940256099942544/2934735716",
            "interstitial_android": "ca-app-pub-3940256099942544/1033173712",
            "interstitial_ios": "ca-app-pub-3940256099942544/4411468910",
            "rewarded_android": "ca-app-pub-3940256099942544/5224354917",
            "rewarded_ios": "ca-app-pub-3940256099942544/1712485313",
            "app_open_android": "ca-app-pub-3940256099942544/3419835294",
            "app_open_ios": "ca-app-pub-3940256099942544/5662855255",
            "rewarded_interstitial_android": "ca-app-pub-3940256099942544/5351527112",
            "rewarded_interstitial_ios": "ca-app-pub-3940256099942544/6978759865",
            "native_android": "",
            "native_ios": "",
            # अगर आप और IDs इस्तेमाल करना चाहते हो तो यहाँ जोड़ सकते हो
        }

        return Response(test_config, status=status.HTTP_200_OK)

# prompts_app/views.py

# ... पहले के सारे imports और views ...

# 1. Public GET endpoint (Flutter app के लिए - कोई authentication नहीं)
class AdmobConfigPublicView(APIView):
    """
    Flutter ऐप के लिए: AdMob IDs public तरीके से लोड करने के लिए
    """
    permission_classes = [AllowAny]

    def get(self, request):
        config = AdmobConfig.objects.filter(is_active=True).first()

        if config:
            serializer = AdmobConfigSerializer(config)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Fallback test IDs
        test_config = {
            "banner_android": "ca-app-pub-3940256099942544/6300978111",
            "banner_ios": "ca-app-pub-3940256099942544/2934735716",
            "interstitial_android": "ca-app-pub-3940256099942544/1033173712",
            "interstitial_ios": "ca-app-pub-3940256099942544/4411468910",
            "rewarded_android": "ca-app-pub-3940256099942544/5224354917",
            "rewarded_ios": "ca-app-pub-3940256099942544/1712485313",
            "app_open_android": "ca-app-pub-3940256099942544/3419835294",
            "app_open_ios": "ca-app-pub-3940256099942544/5662855255",
            # ... बाकी IDs अगर जरूरी हों
        }
        return Response(test_config, status=status.HTTP_200_OK)


class AdmobConfigAdminView(APIView):
    """
    Admin panel (settings.html) के लिए:
    - GET  → active config दिखाता है (fallback: last saved)
    - POST → config create/update करता है + is_active को सही तरीके से संभालता है
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        1️⃣ पहले active config ढूंढे
        2️⃣ अगर active नहीं मिला → last updated config दिखाए
        3️⃣ अगर DB empty है → empty defaults
        """

        config = AdmobConfig.objects.filter(is_active=True).first()

        # 🔥 FALLBACK: अगर active config नहीं मिला
        if not config:
            config = AdmobConfig.objects.order_by('-updated_at').first()

        if config:
            return Response(AdmobConfigSerializer(config).data, status=200)

        # 🔹 DB पूरी तरह खाली हो तो
        return Response({
            "banner_android": "",
            "banner_ios": "",
            "interstitial_android": "",
            "interstitial_ios": "",
            "rewarded_android": "",
            "rewarded_ios": "",
            "app_open_android": "",
            "app_open_ios": "",
            "is_active": False,

            # serializer safe fields
            "app_id_android": "",
            "app_id_ios": "",
            "rewarded_interstitial_android": "",
            "rewarded_interstitial_ios": "",
            "native_android": "",
            "native_ios": "",
            "notes": ""
        }, status=200)

    @transaction.atomic
    def post(self, request):
        """
        Save / Update config
        - boolean is_active safe handling
        - old active auto disable
        """

        data = request.data.copy()

        # 🔹 serializer ko satisfy karne ke liye defaults
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

        # ✅ BOOLEAN FIX (YEH HI MAIN BUG THA)
        want_active = bool(data.get("is_active"))

        # 🔥 agar active banana hai → purane sab inactive
        if want_active:
            AdmobConfig.objects.filter(is_active=True).update(is_active=False)

        # 🔹 ek hi record maintain karenge
        existing = AdmobConfig.objects.first()

        if existing:
            serializer = AdmobConfigSerializer(existing, data=data, partial=True)
        else:
            serializer = AdmobConfigSerializer(data=data)

        if serializer.is_valid():
            saved = serializer.save()

            # 🔹 is_active explicitly set
            saved.is_active = want_active
            saved.save(update_fields=["is_active"])

            return Response({
                "success": True,
                "message": "AdMob settings saved successfully!",
                "data": AdmobConfigSerializer(saved).data
            }, status=200)

        return Response({
            "success": False,
            "errors": serializer.errors,
            "received_data": dict(data)
        }, status=400)
