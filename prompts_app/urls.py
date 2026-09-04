# prompts_app/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Public APIs
    path('categories/', views.CategoryList.as_view(), name='category-list'),
    path('prompts/', views.PromptList.as_view(), name='prompt-list'),
    path('prompts/<uuid:pk>/', views.PromptDetail.as_view(), name='prompt-detail'),
    path('social-links/', views.SocialLinkPublicList.as_view(), name='social-links-public'),

    # Device-based Features
    path('favourites/', views.FavouriteListCreate.as_view(), name='favourite-list'),
    path('favourites/<uuid:pk>/', views.FavouriteDelete.as_view(), name='favourite-delete'),
    path('like/<uuid:pk>/', views.LikeToggle.as_view(), name='like-toggle'),

    # Admin Only - Prompts
    path('admin/prompts/create/', views.PromptCreateView.as_view(), name='prompt-create'),
    path('admin/prompts/<uuid:pk>/update/', views.PromptUpdateView.as_view(), name='prompt-update'),
    path('admin/prompts/<uuid:pk>/delete/', views.PromptDeleteView.as_view(), name='prompt-delete'),
    path('ads/active/', views.ActiveAdsView.as_view(), name='active-ads'),
    path('admob-config/', views.AdmobConfigPublicView.as_view(), name='admob-config-public'),
    path('admob-config/admin/', views.AdmobConfigAdminView.as_view(), name='admob-config-admin'),

    path('admin/ads/activate-banner/', views.activate_banner_ad),
    path('admin/ads/activate-video/', views.activate_video_ad),
    path('admin/ads/deactivate/', views.deactivate_ad, name='deactivate-ad'),
    path('admin/change-credentials/', views.change_admin_credentials, name='change-credentials'),

    # Admin Only - Categories
    path('admin/categories/create/', views.CategoryCreateView.as_view(), name='category-create'),
    path('admin/categories/<uuid:id>/update/', views.CategoryUpdateView.as_view(), name='category-update'),
    path('admin/categories/<uuid:id>/delete/', views.CategoryDeleteView.as_view(), name='category-delete'),

    # Admin Only - Social Links ("Follow Us" channels)
    path('admin/social-links/', views.SocialLinkAdminList.as_view(), name='social-link-admin-list'),
    path('admin/social-links/<uuid:pk>/', views.SocialLinkAdminDetail.as_view(), name='social-link-admin-detail'),

    # Cloudflare R2 media upload (image + video) — replaces Cloudinary flow
    path('admin/media/presign/', views.MediaPresignView.as_view(), name='media-presign'),
    path('admin/media/delete/', views.MediaDeleteView.as_view(), name='media-delete'),
]