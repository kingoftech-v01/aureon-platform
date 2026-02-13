"""Document URL configuration."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')

app_name = 'documents'

urlpatterns = [
    path('api/', include(router.urls)),
]
