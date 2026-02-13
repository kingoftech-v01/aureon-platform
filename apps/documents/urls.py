"""Document URL configuration."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet
from .views_frontend import (
    DocumentListView,
    DocumentDetailView,
    DocumentUploadView,
)

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')

app_name = 'documents'

api_urlpatterns = [
    path('api/', include(router.urls)),
]

frontend_urlpatterns = [
    path('', DocumentListView.as_view(), name='document_list'),
    path('upload/', DocumentUploadView.as_view(), name='document_upload'),
    path('<uuid:pk>/', DocumentDetailView.as_view(), name='document_detail'),
]

urlpatterns = api_urlpatterns + frontend_urlpatterns
