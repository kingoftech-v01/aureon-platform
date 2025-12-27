"""
URL configuration for integrations app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'integrations'

router = DefaultRouter()
# TODO: Add viewsets when implemented

urlpatterns = [
    path('api/', include(router.urls)),
]
