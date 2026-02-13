"""Notification URL configuration."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, NotificationTemplateViewSet
from .views_frontend import (
    NotificationListView,
    NotificationSettingsView,
    NotificationTemplateListView,
)

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'notification-templates', NotificationTemplateViewSet, basename='notification-template')

app_name = 'notifications'

api_urlpatterns = [
    path('api/', include(router.urls)),
]

frontend_urlpatterns = [
    path('', NotificationListView.as_view(), name='notification_list'),
    path('settings/', NotificationSettingsView.as_view(), name='notification_settings'),
    path('templates/', NotificationTemplateListView.as_view(), name='template_list'),
]

urlpatterns = api_urlpatterns + frontend_urlpatterns
