import os
from pathlib import Path
from decouple import config
from datetime import timedelta
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-please-change-me')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'rest_framework_simplejwt',
    'django_filters',
    'corsheaders',
    'prompts_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ai_prompt_hub.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ai_prompt_hub.wsgi.application'


# ============================
# DATABASE
# ============================

if config("DATABASE_URL", default=None):
    DATABASES = {
        'default': dj_database_url.config(
            default=config("DATABASE_URL"),
            conn_max_age=600
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / "db.sqlite3",
        }
    }


# ============================
# CACHE — views.py ke liye zaroori
# ============================

REDIS_URL = config('REDIS_URL', default=None)

if REDIS_URL:
    # Production: Render/Railway pe Redis add karo, REDIS_URL env var set karo
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        }
    }
else:
    # Local development: in-memory cache (server restart pe clear ho jata hai)
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "ai-prompt-hub-cache",
        }
    }


# ============================
# AUTH
# ============================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ============================
# REST FRAMEWORK
# ============================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
}


# ============================
# CORS
# ============================

CORS_ALLOW_ALL_ORIGINS = True


# ============================
# LOCALISATION
# ============================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True


# ============================
# STATIC FILES
# ============================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'


# ============================
# CLOUDFLARE R2 — .env se lo, hardcode mat karo
# ============================
# R2 ek S3-compatible object storage hai. Media (image/video) seedha
# browser se R2 mein presigned URL ke through upload hota hai — Django
# sirf presigned URL generate karta hai, file bytes Django se nahi guzarte.

R2_ACCOUNT_ID        = config('R2_ACCOUNT_ID')
R2_ACCESS_KEY_ID     = config('R2_ACCESS_KEY_ID')
R2_SECRET_ACCESS_KEY = config('R2_SECRET_ACCESS_KEY')
R2_BUCKET_NAME       = config('R2_BUCKET_NAME')
R2_ENDPOINT_URL      = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

# Public URL jisse uploaded files browser mein serve honge.
# Ya to R2.dev wala default domain use karo, ya apna custom domain
# (Cloudflare dashboard -> R2 -> bucket -> Settings -> Custom Domain / Public Access)
# Example: "https://pub-xxxxxxxx.r2.dev"  ya  "https://media.yourdomain.com"
R2_PUBLIC_URL = config('R2_PUBLIC_URL').rstrip('/')

# Kitni der tak presigned upload URL valid rahega (seconds)
R2_PRESIGN_EXPIRY = 300

# Max upload size jo backend allow karega (bytes) — video ke liye zyada rakha
R2_MAX_UPLOAD_SIZE_BYTES = 200 * 1024 * 1024  # 200 MB

# ============================
# MISC
# ============================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'