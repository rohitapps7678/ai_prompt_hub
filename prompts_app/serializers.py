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
    """
    PERFECTLY FIXED: Frontend sirf 8 fields bhejta hai, baaki sabko default values
    Create + Update dono perfect kaam karega. Save hone ke baad refresh par values rahenge!
    """
    # Frontend se aane wale fields (HTML form se)
    banner_android = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    banner_ios = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    interstitial_android = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    interstitial_ios = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    rewarded_android = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    rewarded_ios = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    app_open_android = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    app_open_ios = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    
    # is_active checkbox
    is_active = serializers.BooleanField(default=False)
    
    # Baaki model fields (jo frontend nahi bhejta) - auto handle
    id = serializers.UUIDField(read_only=True)
    app_id_android = serializers.CharField(max_length=100, required=False, default="ca-app-pub-3940256099942544~3347511713")
    app_id_ios = serializers.CharField(max_length=100, required=False, default="ca-app-pub-3940256099942544~3347511713")
    rewarded_interstitial_android = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    rewarded_interstitial_ios = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    native_android = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    native_ios = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True, default="Updated from AI Prompt Admin Panel")
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = AdmobConfig
        fields = [
            'id', 'is_active', 'banner_android', 'banner_ios', 'interstitial_android', 'interstitial_ios',
            'rewarded_android', 'rewarded_ios', 'app_open_android', 'app_open_ios',
            'rewarded_interstitial_android', 'rewarded_interstitial_ios',
            'native_android', 'native_ios', 'app_id_android', 'app_id_ios', 'notes', 'updated_at'
        ]
        read_only_fields = ['id', 'updated_at']

    def create(self, validated_data):
        """Create ke time sab fields perfect save honge"""
        return AdmobConfig.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """Update ke time sirf jo fields aaye wohi update honge, baaki same rahenge"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def to_representation(self, instance):
        """Response mein clean data bhejo - empty strings ko "" hi rakho"""
        data = super().to_representation(instance)
        # Frontend ke liye clean fields
        frontend_fields = [
            'banner_android', 'banner_ios', 'interstitial_android', 'interstitial_ios',
            'rewarded_android', 'rewarded_ios', 'app_open_android', 'app_open_ios'
        ]
        for field in frontend_fields:
            if field in data and data[field] is None:
                data[field] = ""
        return data