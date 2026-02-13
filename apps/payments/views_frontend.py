"""
Frontend views for the payments app.

Provides class-based views for payment listing, payment detail,
and payment method management.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.db.models import Sum, Q

from .models import Payment, PaymentMethod


class PaymentListView(LoginRequiredMixin, ListView):
    """List all payments with filtering by status and payment method."""
    template_name = 'payments/payment_list.html'
    context_object_name = 'payments'

    def get_queryset(self):
        queryset = Payment.objects.select_related('invoice').all()
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        method = self.request.GET.get('method')
        if method:
            queryset = queryset.filter(payment_method=method)
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(transaction_id__icontains=search) |
                Q(invoice__invoice_number__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Payments'
        context['status_choices'] = Payment.STATUS_CHOICES
        context['method_choices'] = Payment.METHOD_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        context['current_method'] = self.request.GET.get('method', '')
        context['search_query'] = self.request.GET.get('q', '')
        context['total_received'] = Payment.objects.filter(
            status=Payment.SUCCEEDED
        ).aggregate(total=Sum('amount'))['total'] or 0
        context['total_refunded'] = Payment.objects.filter(
            status=Payment.REFUNDED
        ).aggregate(total=Sum('refunded_amount'))['total'] or 0
        context['pending_count'] = Payment.objects.filter(
            status=Payment.PENDING
        ).count()
        return context


class PaymentDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a single payment with invoice and refund information."""
    template_name = 'payments/payment_detail.html'
    model = Payment
    context_object_name = 'payment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Payment: {self.object.transaction_id}'
        context['invoice'] = self.object.invoice
        context['is_successful'] = self.object.is_successful
        context['net_amount'] = self.object.net_amount
        context['has_refund'] = self.object.refunded_amount > 0
        return context


class PaymentMethodListView(LoginRequiredMixin, ListView):
    """List all saved payment methods across clients."""
    template_name = 'payments/payment_method_list.html'
    context_object_name = 'payment_methods'

    def get_queryset(self):
        return PaymentMethod.objects.select_related('client').filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Payment Methods'
        context['method_type_choices'] = Payment.METHOD_CHOICES
        context['total_methods'] = PaymentMethod.objects.filter(is_active=True).count()
        return context
