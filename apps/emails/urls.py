"""
URL configuration for emails app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EmailAccountViewSet,
    EmailMessageViewSet,
    EmailAttachmentViewSet,
    EmailTemplateViewSet,
)
from .views_frontend import (
    EmailInboxView,
    EmailDetailView,
    EmailComposeView,
    EmailAccountSettingsView,
    EmailTemplateListView,
)

app_name = 'emails'

router = DefaultRouter()
router.register(r'email-accounts', EmailAccountViewSet, basename='email-account')
router.register(r'emails', EmailMessageViewSet, basename='email')
router.register(r'email-attachments', EmailAttachmentViewSet, basename='email-attachment')
router.register(r'email-templates', EmailTemplateViewSet, basename='email-template')

api_urlpatterns = [
    path('api/', include(router.urls)),
]

frontend_urlpatterns = [
    path('', EmailInboxView.as_view(), name='inbox'),
    path('compose/', EmailComposeView.as_view(), name='compose'),
    path('accounts/', EmailAccountSettingsView.as_view(), name='account_settings'),
    path('templates/', EmailTemplateListView.as_view(), name='template_list'),
    path('<uuid:pk>/', EmailDetailView.as_view(), name='email_detail'),
]

urlpatterns = api_urlpatterns + frontend_urlpatterns
