"""Subscription URL configuration."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SubscriptionPlanViewSet, SubscriptionViewSet

router = DefaultRouter()
router.register(r'plans', SubscriptionPlanViewSet, basename='subscription-plan')
router.register(r'', SubscriptionViewSet, basename='subscription')

app_name = 'subscriptions'

urlpatterns = [
    path('', include(router.urls)),
]
