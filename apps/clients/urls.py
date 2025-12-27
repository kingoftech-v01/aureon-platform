"""
URL configuration for clients app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'clients'

# Import viewsets
from .views import ClientViewSet, ClientNoteViewSet, ClientDocumentViewSet

# API Router
router = DefaultRouter()
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'notes', ClientNoteViewSet, basename='client-note')
router.register(r'documents', ClientDocumentViewSet, basename='client-document')

urlpatterns = [
    path('api/', include(router.urls)),
]
