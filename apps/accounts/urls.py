"""
URL configuration for accounts app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserViewSet, UserInvitationViewSet, ApiKeyViewSet,
    TeamViewSet, TeamMemberViewSet, TeamInvitationViewSet,
)
from .auth_views import CustomTokenObtainPairView, register, get_current_user, logout
from . import two_factor
from .views_frontend import (
    LoginPageView,
    RegisterPageView,
    ProfileView,
    SettingsView,
    TeamListView,
    TeamDetailView,
    UserListView,
    InvitationListView,
    TwoFactorSetupView,
)

app_name = 'accounts'

# API Router
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'invitations', UserInvitationViewSet, basename='invitation')
router.register(r'api-keys', ApiKeyViewSet, basename='apikey')
router.register(r'teams', TeamViewSet, basename='team')
router.register(r'team-members', TeamMemberViewSet, basename='team-member')
router.register(r'team-invitations', TeamInvitationViewSet, basename='team-invitation')

api_urlpatterns = [
    # JWT Authentication
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('register/', register, name='register'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', logout, name='logout'),
    path('user/', get_current_user, name='current_user'),

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

frontend_urlpatterns = [
    path('login-page/', LoginPageView.as_view(), name='login_page'),
    path('register-page/', RegisterPageView.as_view(), name='register_page'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('settings/', SettingsView.as_view(), name='settings'),
    path('teams/', TeamListView.as_view(), name='team_list'),
    path('teams/<uuid:pk>/', TeamDetailView.as_view(), name='team_detail'),
    path('users/', UserListView.as_view(), name='user_list'),
    path('invitations-list/', InvitationListView.as_view(), name='invitation_list'),
    path('2fa/setup/', TwoFactorSetupView.as_view(), name='two_factor_setup'),
]

urlpatterns = api_urlpatterns + frontend_urlpatterns
