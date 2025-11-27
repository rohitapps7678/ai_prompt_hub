# prompts_app/models.py

from django.db import models
import uuid


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    icon = models.CharField(max_length=100, blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Prompt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    prompt_text = models.TextField()

    # CLOUDINARY IMAGE URL - Sirf string URL save hoga
    image_url = models.URLField(max_length=500, blank=True, null=True, default=None)

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='prompts')
    tags = models.CharField(max_length=300, blank=True)
    is_premium = models.BooleanField(default=False)
    usage_count = models.BigIntegerField(default=0)
    like_count = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Favourite(models.Model):
    device_id = models.CharField(max_length=255)
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('device_id', 'prompt')


class PromptLike(models.Model):
    device_id = models.CharField(max_length=255)
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('device_id', 'prompt')

# prompts_app/models.py (add this model)

class Ad(models.Model):
    AD_TYPE_CHOICES = [
        ('banner', 'Banner Ad'),
        ('video', 'Video Ad'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100, help_text="Internal name")
    ad_type = models.CharField(max_length=10, choices=AD_TYPE_CHOICES)
    
    # For Banner
    image_url = models.URLField(blank=True, null=True)
    
    # For Video (YouTube embed link ya direct MP4)
    video_url = models.URLField(blank=True, null=True, help_text="YouTube: https://youtube.com/watch?v=xxx ya direct MP4 link")
    
    redirect_url = models.URLField(max_length=500, help_text="Jahan click karne pe jayega")
    
    is_active = models.BooleanField(default=True)
    show_after_seconds = models.PositiveIntegerField(default=0, help_text="Kitne seconds baad dubara dikhega (0 = har baar)")
    duration_days = models.PositiveIntegerField(default=7, help_text="Kitne din tak ye ad dikhega")
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(days=self.duration_days)
    
    def __str__(self):
        return f"{self.title} ({self.ad_type})"