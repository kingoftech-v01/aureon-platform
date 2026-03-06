"""Integration URL configuration."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IntegrationViewSet

router = DefaultRouter()
router.register(r'', IntegrationViewSet, basename='integration')

app_name = 'integrations'

urlpatterns = [
    path('', include(router.urls)),
]
