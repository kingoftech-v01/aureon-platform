"""
URL configuration for tenants app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TenantViewSet

app_name = 'tenants'

# API Router
router = DefaultRouter()
router.register(r'tenants', TenantViewSet, basename='tenant')

urlpatterns = [
    path('', include(router.urls)),
]
