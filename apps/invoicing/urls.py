"""
URL configuration for invoicing app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    InvoiceViewSet, InvoiceItemViewSet,
    RecurringInvoiceViewSet, LateFeePolicyViewSet, PaymentReminderViewSet,
)
from .views_frontend import (
    InvoiceListView,
    InvoiceDetailView,
    InvoiceCreateView,
    InvoiceEditView,
    RecurringInvoiceListView,
    RecurringInvoiceDetailView,
    LateFeePolicyListView,
    PaymentReminderListView,
)

app_name = 'invoicing'

router = DefaultRouter()
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'items', InvoiceItemViewSet, basename='invoice-item')
router.register(r'recurring-invoices', RecurringInvoiceViewSet, basename='recurring-invoice')
router.register(r'late-fee-policies', LateFeePolicyViewSet, basename='late-fee-policy')
router.register(r'payment-reminders', PaymentReminderViewSet, basename='payment-reminder')

api_urlpatterns = [
    path('api/', include(router.urls)),
]

frontend_urlpatterns = [
    path('', InvoiceListView.as_view(), name='invoice_list'),
    path('create/', InvoiceCreateView.as_view(), name='invoice_create'),
    path('<uuid:pk>/', InvoiceDetailView.as_view(), name='invoice_detail'),
    path('<uuid:pk>/edit/', InvoiceEditView.as_view(), name='invoice_edit'),
    path('recurring/', RecurringInvoiceListView.as_view(), name='recurring_list'),
    path('recurring/<uuid:pk>/', RecurringInvoiceDetailView.as_view(), name='recurring_detail'),
    path('late-fees/', LateFeePolicyListView.as_view(), name='late_fee_list'),
    path('reminders/', PaymentReminderListView.as_view(), name='reminder_list'),
]

urlpatterns = api_urlpatterns + frontend_urlpatterns
