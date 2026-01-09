# prompts_app/serializers.py - COMPLETE FIXED VERSION

from rest_framework import serializers
from .models import Category, Prompt, PromptLike, Ad, AdmobConfig


class CategorySerializer(serializers.ModelSerializer):
    prompts_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'order', 'prompts_count']

    def get_prompts_count(self, obj):
        return obj.prompts.count()


class PromptSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        write_only=True
    )
    category_data = CategorySerializer(source='category', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)

    image_url = serializers.URLField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=500
    )

    like_count = serializers.IntegerField(source='likes.count', read_only=True)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Prompt
        fields = [
            'id', 'title', 'prompt_text', 'image_url',
            'category', 'category_data', 'category_slug',
            'tags', 'is_premium', 'usage_count',
            'like_count', 'is_liked', 'created_at'
        ]

    def get_is_liked(self, obj):
        device_id = self.context.get('device_id')
        if device_id:
            return obj.likes.filter(device_id=device_id).exists()
        return False


class AdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ad
        fields = ['id', 'title', 'ad_type', 'image_url', 'video_url', 'redirect_url', 'show_after_seconds']


class AdCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ad
        fields = ['title', 'ad_type', 'image_url', 'video_url', 'redirect_url', 'show_after_seconds', 'duration_days']

    def validate(self, data):
        ad_type = data.get('ad_type')
        if ad_type == 'banner' and not data.get('image_url'):
            raise serializers.ValidationError("image_url is required for banner ads")
        if ad_type == 'video' and not data.get('video_url'):
            raise serializers.ValidationError("video_url is required for video ads")
        return data


# 🔥 FIXED ADMOB CONFIG SERIALIZER - YEH HI PROBLEM THI 🔥
class AdmobConfigSerializer(serializers.ModelSerializer):
    # Explicitly define only the fields you actually want to accept from frontend
    banner_android             = serializers.CharField(required=False, allow_blank=True, default="")
    banner_ios                 = serializers.CharField(required=False, allow_blank=True, default="")
    interstitial_android       = serializers.CharField(required=False, allow_blank=True, default="")
    interstitial_ios           = serializers.CharField(required=False, allow_blank=True, default="")
    rewarded_android           = serializers.CharField(required=False, allow_blank=True, default="")
    rewarded_ios               = serializers.CharField(required=False, allow_blank=True, default="")
    app_open_android           = serializers.CharField(required=False, allow_blank=True, default="")
    app_open_ios               = serializers.CharField(required=False, allow_blank=True, default="")
    is_active                  = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = AdmobConfig
        fields = [
            'id',
            'is_active',
            'banner_android', 'banner_ios',
            'interstitial_android', 'interstitial_ios',
            'rewarded_android', 'rewarded_ios',
            'app_open_android', 'app_open_ios',
            'app_id_android', 'app_id_ios',           # ← still include in response
            'rewarded_interstitial_android', 'rewarded_interstitial_ios',
            'native_android', 'native_ios',
            'notes', 'updated_at'
        ]
        read_only_fields = ['id', 'updated_at', 'notes']  # optional

    # Optional: give defaults for fields frontend doesn't send
    def get_default_values(self):
        return {
            'app_id_android': 'ca-app-pub-3940256099942544~3347511713',  # test app id
            'app_id_ios': 'ca-app-pub-3940256099942544~3347511713',
            'rewarded_interstitial_android': '',
            'rewarded_interstitial_ios': '',
            'native_android': '',
            'native_ios': '',
            'notes': 'Updated from admin panel',
        }

    def create(self, validated_data):
        defaults = self.get_default_values()
        defaults.update(validated_data)
        return AdmobConfig.objects.create(**defaults)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance