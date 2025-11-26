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
    image = models.ImageField(upload_to='prompts/', blank=True, null=True)  # NAYA
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='prompts')
    tags = models.CharField(max_length=300, blank=True)
    is_premium = models.BooleanField(default=False)
    usage_count = models.BigIntegerField(default=0)
    like_count = models.BigIntegerField(default=0)  # NAYA
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


# NAYA LIKE MODEL
class PromptLike(models.Model):
    device_id = models.CharField(max_length=255)
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('device_id', 'prompt')  # Ek device = Ek like