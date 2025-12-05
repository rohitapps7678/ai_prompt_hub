# ai_prompt_hub/urls.py

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

# JWT Auth Views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# TEMP MIGRATION SUPPORT (OPTIONAL)
from django.core.management import call_command
from django.contrib.auth.models import User


# ======================
# HEALTH ENDPOINT (PING)
# ======================
def health(request):
    return JsonResponse({"status": "ok"})


# =====================
# RUN MIGRATIONS (TEMP)
# =====================
def run_migrations(request):
    try:
        # Create migrations
        call_command('makemigrations')
        # Apply migrations
        call_command('migrate')

        return JsonResponse({
            "status": "makemigrations + migrate applied successfully"
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ================================
# CREATE ADMIN USER (TEMP UTILITY)
# ================================
def create_admin(request):
    try:
        if User.objects.filter(username="rohit").exists():
            return JsonResponse({"status": "admin already exists"})

        User.objects.create_superuser(
            username="rohit",
            password="rohit7678@",
            email="admin@example.com"
        )
        return JsonResponse({"status": "admin user created"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# =============
# URL PATTERNS
# =============
urlpatterns = [
    path('admin/', admin.site.urls),

    # Public & Admin APIs
    path('api/', include('prompts_app.urls')),

    # JWT Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Health check (Ping for Render)
    path('health/', health),

    # TEMP Tools (Remove in production)
    path('run-migrations/', run_migrations),
    path('create-admin/', create_admin),
]
