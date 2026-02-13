"""
URL configuration for payments app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, PaymentMethodViewSet
from .views_frontend import (
    PaymentListView,
    PaymentDetailView,
    PaymentMethodListView,
)

app_name = 'payments'

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'payment-methods', PaymentMethodViewSet, basename='payment-method')

api_urlpatterns = [
    path('api/', include(router.urls)),
]

frontend_urlpatterns = [
    path('', PaymentListView.as_view(), name='payment_list'),
    path('methods/', PaymentMethodListView.as_view(), name='payment_method_list'),
    path('<uuid:pk>/', PaymentDetailView.as_view(), name='payment_detail'),
]

urlpatterns = api_urlpatterns + frontend_urlpatterns
