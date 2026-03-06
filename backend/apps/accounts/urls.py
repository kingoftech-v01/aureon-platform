"""
URL configuration for accounts app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import UserViewSet, UserInvitationViewSet, ApiKeyViewSet
from .auth_views import CustomTokenObtainPairView, register, get_current_user, logout
from . import two_factor

app_name = 'accounts'

# API Router
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'invitations', UserInvitationViewSet, basename='invitation')
router.register(r'api-keys', ApiKeyViewSet, basename='apikey')

urlpatterns = [
    # JWT Authentication
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('register/', register, name='register'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', logout, name='logout'),
    path('user/', get_current_user, name='current_user'),
    path('me/', get_current_user, name='current_user_me'),

    # Two-Factor Authentication
    path('2fa/enable/', two_factor.enable_2fa, name='2fa_enable'),
    path('2fa/verify-setup/', two_factor.verify_2fa_setup, name='2fa_verify_setup'),
    path('2fa/disable/', two_factor.disable_2fa, name='2fa_disable'),
    path('2fa/verify/', two_factor.verify_2fa_token, name='2fa_verify'),
    path('2fa/backup-code/', two_factor.use_backup_code, name='2fa_backup_code'),
    path('2fa/regenerate-backup-codes/', two_factor.regenerate_backup_codes, name='2fa_regenerate_codes'),
    path('2fa/status/', two_factor.get_2fa_status, name='2fa_status'),

    # User Management API
    path('api/', include(router.urls)),
]
