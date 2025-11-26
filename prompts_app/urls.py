# prompts_app/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Public APIs
    path('categories/', views.CategoryList.as_view(), name='category-list'),
    path('prompts/', views.PromptList.as_view(), name='prompt-list'),
    path('prompts/<uuid:pk>/', views.PromptDetail.as_view(), name='prompt-detail'),

    # Device-based Features
    path('favourites/', views.FavouriteListCreate.as_view(), name='favourite-list'),
    path('favourites/<uuid:pk>/', views.FavouriteDelete.as_view(), name='favourite-delete'),
    path('like/<uuid:pk>/', views.LikeToggle.as_view(), name='like-toggle'),

    # Admin Only - Prompts
    path('admin/prompts/create/', views.PromptCreateView.as_view(), name='prompt-create'),
    path('admin/prompts/<uuid:pk>/update/', views.PromptUpdateView.as_view(), name='prompt-update'),
    path('admin/prompts/<uuid:pk>/delete/', views.PromptDeleteView.as_view(), name='prompt-delete'),

    # Admin Only - Categories
    path('admin/categories/create/', views.CategoryCreateView.as_view(), name='category-create'),
    path('admin/categories/<uuid:id>/update/', views.CategoryUpdateView.as_view(), name='category-update'),
    path('admin/categories/<uuid:id>/delete/', views.CategoryDeleteView.as_view(), name='category-delete'),
]