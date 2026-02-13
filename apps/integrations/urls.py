"""Integration URL configuration."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IntegrationViewSet
from .views_frontend import (
    IntegrationListView,
    IntegrationDetailView,
    IntegrationConnectView,
)

router = DefaultRouter()
router.register(r'', IntegrationViewSet, basename='integration')

app_name = 'integrations'

api_urlpatterns = [
    path('', include(router.urls)),
]

frontend_urlpatterns = [
    path('list/', IntegrationListView.as_view(), name='integration_list'),
    path('<uuid:pk>/', IntegrationDetailView.as_view(), name='integration_detail'),
    path('connect/', IntegrationConnectView.as_view(), name='integration_connect'),
]

urlpatterns = api_urlpatterns + frontend_urlpatterns
