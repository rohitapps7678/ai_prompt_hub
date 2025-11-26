# prompts_app/serializers.py

from rest_framework import serializers
from .models import Category, Prompt, PromptLike


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

    # YE SIRF EK BAAR HONA CHAHIYE → URLField (write + read)
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