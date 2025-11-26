# prompts_app/serializers.py

from rest_framework import serializers
from .models import Category, Prompt, PromptLike
from django.conf import settings


class CategorySerializer(serializers.ModelSerializer):
    prompts_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon', 'order', 'prompts_count']

    def get_prompts_count(self, obj):
        return obj.prompts.count()


class PromptSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        write_only=True
    )
    category_data = CategorySerializer(source='category', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)

    image = serializers.ImageField(required=False, write_only=True)
    image_url = serializers.SerializerMethodField()

    like_count = serializers.IntegerField(source='likes.count', read_only=True)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Prompt
        fields = [
            'id', 'title', 'prompt_text', 'image', 'image_url',
            'category', 'category_data', 'category_slug', 'tags', 'is_premium',
            'usage_count', 'like_count', 'is_liked', 'created_at'
        ]

    # FIXED: Full absolute image URL hamesha milega
    def get_image_url(self, obj):
        if not obj.image:
            return None

        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.image.url)  # .url use karo, name nahi!

        # Agar request nahi hai (fallback) – settings mein BASE_URL hona chahiye
        base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
        return f"{base_url}{obj.image.url}"

    # Device-based like check
    def get_is_liked(self, obj):
        device_id = self.context.get('device_id')
        if device_id:
            return obj.likes.filter(device_id=device_id).exists()
        return False