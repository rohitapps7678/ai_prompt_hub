# ai_prompt_hub/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings

# JWT Views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API
    path('api/', include('prompts_app.urls')),
    
    # JWT Login Endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# Serve media files in developmen