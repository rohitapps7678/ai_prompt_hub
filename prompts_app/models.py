# prompts_app/models.py

from django.db import models
import uuid
from django.utils import timezone
from datetime import timedelta


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


class Ad(models.Model):
    AD_TYPE_CHOICES = [
        ('banner', 'Banner Ad'),
        ('video', 'Video Ad'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100, help_text="Internal name")
    ad_type = models.CharField(max_length=10, choices=AD_TYPE_CHOICES)
    image_url = models.URLField(blank=True, null=True)
    video_url = models.URLField(blank=True, null=True, help_text="YouTube: https://youtube.com/watch?v=xxx ya direct MP4 link")
    redirect_url = models.URLField(max_length=500, help_text="Jahan click karne pe jayega")
    is_active = models.BooleanField(default=True)
    show_after_seconds = models.PositiveIntegerField(default=0)
    duration_days = models.PositiveIntegerField(default=7)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(days=self.duration_days)
    
    def __str__(self):
        return f"{self.title} ({self.ad_type})"


# ── NAYA MODEL ADMOB CONFIGURATION KE LIYE ────────────────────────────────
class AdmobConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Normally sirf ek active record hoga
    is_active = models.BooleanField(default=True)
    
    # AdMob App ID (sirf info ke liye, app mein manifest se hi use hoga)
    app_id_android = models.CharField(max_length=100, blank=True, default="ca-app-pub-xxxxxxxxxxxxxxxx~yyyyyyyyyy")
    app_id_ios     = models.CharField(max_length=100, blank=True, default="ca-app-pub-xxxxxxxxxxxxxxxx~yyyyyyyyyy")
    
    # Important Ad Unit IDs
    banner_android             = models.CharField(max_length=100, blank=True)
    banner_ios                 = models.CharField(max_length=100, blank=True)
    interstitial_android       = models.CharField(max_length=100, blank=True)
    interstitial_ios           = models.CharField(max_length=100, blank=True)
    rewarded_android           = models.CharField(max_length=100, blank=True)
    rewarded_ios               = models.CharField(max_length=100, blank=True)
    rewarded_interstitial_android = models.CharField(max_length=100, blank=True)
    rewarded_interstitial_ios  = models.CharField(max_length=100, blank=True)
    app_open_android           = models.CharField(max_length=100, blank=True)
    app_open_ios               = models.CharField(max_length=100, blank=True)
    
    # Optional: Native ads bhi rakh sakte ho future mein
    native_android             = models.CharField(max_length=100, blank=True)
    native_ios                 = models.CharField(max_length=100, blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, help_text="Kis date ko kisne change kiya tha")

    class Meta:
        verbose_name = "AdMob Configuration"
        verbose_name_plural = "AdMob Configuration"

    def __str__(self):
        return "AdMob Configuration (active)" if self.is_active else "AdMob Configuration (inactive)"