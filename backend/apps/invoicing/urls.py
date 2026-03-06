"""
URL configuration for invoicing app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InvoiceViewSet, InvoiceItemViewSet

app_name = 'invoicing'

router = DefaultRouter()
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'items', InvoiceItemViewSet, basename='invoice-item')

urlpatterns = [
    path('', include(router.urls)),
]
