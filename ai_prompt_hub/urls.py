# ai_prompt_hub/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings

# JWT Views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# 🔥 TEMPORARY MIGRATION ENDPOINT (will remove after use)
from django.core.management import call_command
from django.http import JsonResponse

def run_migrations(request):
    try:
        call_command('migrate')
        return JsonResponse({"status": "migrations applied successfully"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API
    path('api/', include('prompts_app.urls')),
    
    # JWT Login Endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # 🔥 Temporary migration URL
    path('run-migrations/', run_migrations),
]

# Serve media files in development
