from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Prompt, Favourite, PromptLike

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Prompt)
class PromptAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'like_count', 'usage_count', 'image_preview', 'created_at']
    list_filter = ['category', 'is_premium']
    search_fields = ['title', 'prompt_text']
    readonly_fields = ['like_count', 'usage_count', 'image_preview']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: cover; border-radius:8px;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = "Preview"