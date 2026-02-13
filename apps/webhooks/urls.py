"""
URL configuration for webhooks app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views_frontend import (
    WebhookEventListView,
    WebhookEventDetailView,
    WebhookEndpointListView,
)

app_name = 'webhooks'

router = DefaultRouter()
# ViewSets will be added here when needed

api_urlpatterns = [
    # Stripe webhook endpoint
    path('stripe/', views.stripe_webhook, name='stripe_webhook'),

    # Generic webhook endpoint
    path('receive/<uuid:endpoint_id>/', views.generic_webhook, name='generic_webhook'),

    # Health check
    path('health/', views.webhook_health, name='webhook_health'),

    # API routes
    path('api/', include(router.urls)),
]

frontend_urlpatterns = [
    path('events/', WebhookEventListView.as_view(), name='event_list'),
    path('events/<uuid:pk>/', WebhookEventDetailView.as_view(), name='event_detail'),
    path('endpoints/', WebhookEndpointListView.as_view(), name='endpoint_list'),
]

urlpatterns = api_urlpatterns + frontend_urlpatterns
