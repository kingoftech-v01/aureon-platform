"""Subscription URL configuration."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SubscriptionPlanViewSet, SubscriptionViewSet
from .views_frontend import (
    SubscriptionPlanListView,
    SubscriptionDetailView,
    SubscriptionManageView,
)

router = DefaultRouter()
router.register(r'plans', SubscriptionPlanViewSet, basename='subscription-plan')
router.register(r'', SubscriptionViewSet, basename='subscription')

app_name = 'subscriptions'

api_urlpatterns = [
    path('', include(router.urls)),
]

frontend_urlpatterns = [
    path('plans/', SubscriptionPlanListView.as_view(), name='plan_list'),
    path('<uuid:pk>/', SubscriptionDetailView.as_view(), name='subscription_detail'),
    path('manage/', SubscriptionManageView.as_view(), name='subscription_manage'),
]

urlpatterns = api_urlpatterns + frontend_urlpatterns
