"""
URL configuration for clients app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_health import ClientHealthScoreView

app_name = 'clients'

# Import viewsets
from .views import ClientViewSet, ClientNoteViewSet, ClientDocumentViewSet

# API Router
router = DefaultRouter()
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'notes', ClientNoteViewSet, basename='client-note')
router.register(r'documents', ClientDocumentViewSet, basename='client-document')

urlpatterns = [
    path('', include(router.urls)),
    path('health/', ClientHealthScoreView.as_view(), name='client-health-scores'),
    path('<uuid:client_id>/health/', ClientHealthScoreView.as_view(), name='client-health-score'),
]
