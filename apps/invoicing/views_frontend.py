"""
Frontend views for the invoicing app.

Provides class-based views for invoice listing, detail, creation, editing,
recurring invoice management, late fee policies, and payment reminders.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, CreateView
from django.db.models import Sum, Q

from .models import Invoice, InvoiceItem, RecurringInvoice, LateFeePolicy, PaymentReminder


class InvoiceListView(LoginRequiredMixin, ListView):
    """List all invoices with filtering by status and search."""
    template_name = 'invoicing/invoice_list.html'
    context_object_name = 'invoices'

    def get_queryset(self):
        queryset = Invoice.objects.select_related('client', 'contract').all()
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(invoice_number__icontains=search) |
                Q(client__company_name__icontains=search) |
                Q(client__first_name__icontains=search) |
                Q(client__last_name__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Invoices'
        context['status_choices'] = Invoice.STATUS_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('q', '')
        context['total_invoices'] = Invoice.objects.count()
        context['total_outstanding'] = Invoice.objects.filter(
            status__in=[Invoice.SENT, Invoice.VIEWED, Invoice.PARTIALLY_PAID, Invoice.OVERDUE]
        ).aggregate(total=Sum('total'))['total'] or 0
        context['overdue_count'] = Invoice.objects.filter(status=Invoice.OVERDUE).count()
        return context


class InvoiceDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a single invoice with line items and payment history."""
    template_name = 'invoicing/invoice_detail.html'
    model = Invoice
    context_object_name = 'invoice'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['payments'] = self.object.payments.all()
        context['reminders'] = self.object.payment_reminders.all()
        context['page_title'] = f'Invoice: {self.object.invoice_number}'
        context['balance_due'] = self.object.balance_due
        context['is_overdue'] = self.object.is_overdue
        context['is_fully_paid'] = self.object.is_fully_paid
        return context


class InvoiceCreateView(LoginRequiredMixin, CreateView):
    """Create a new invoice."""
    template_name = 'invoicing/invoice_create.html'
    model = Invoice
    fields = [
        'client', 'contract', 'issue_date', 'due_date', 'tax_rate',
        'discount_amount', 'currency', 'notes', 'terms',
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Create Invoice'
        from apps.clients.models import Client
        context['clients'] = Client.objects.filter(is_active=True)
        from apps.contracts.models import Contract
        context['contracts'] = Contract.objects.filter(status=Contract.ACTIVE)
        return context


class InvoiceEditView(LoginRequiredMixin, TemplateView):
    """Edit an existing invoice."""
    template_name = 'invoicing/invoice_edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invoice = Invoice.objects.select_related('client', 'contract').get(pk=self.kwargs['pk'])
        context['invoice'] = invoice
        context['items'] = invoice.items.all()
        context['page_title'] = f'Edit Invoice: {invoice.invoice_number}'
        context['status_choices'] = Invoice.STATUS_CHOICES
        from apps.clients.models import Client
        context['clients'] = Client.objects.filter(is_active=True)
        from apps.contracts.models import Contract
        context['contracts'] = Contract.objects.filter(status=Contract.ACTIVE)
        return context


class RecurringInvoiceListView(LoginRequiredMixin, ListView):
    """List all recurring invoices."""
    template_name = 'invoicing/recurring_invoice_list.html'
    context_object_name = 'recurring_invoices'

    def get_queryset(self):
        return RecurringInvoice.objects.select_related('client', 'contract', 'owner').all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Recurring Invoices'
        context['status_choices'] = RecurringInvoice.STATUS_CHOICES
        context['frequency_choices'] = RecurringInvoice.FREQUENCY_CHOICES
        context['active_count'] = RecurringInvoice.objects.filter(
            status=RecurringInvoice.ACTIVE
        ).count()
        return context


class RecurringInvoiceDetailView(LoginRequiredMixin, DetailView):
    """Detail view of a recurring invoice."""
    template_name = 'invoicing/recurring_invoice_detail.html'
    model = RecurringInvoice
    context_object_name = 'recurring_invoice'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Recurring Invoice: {self.object.template_name}'
        context['is_due'] = self.object.is_due
        context['invoices_generated'] = self.object.invoices_generated
        context['next_run_date'] = self.object.next_run_date
        context['items_template'] = self.object.items_template
        return context


class LateFeePolicyListView(LoginRequiredMixin, ListView):
    """List all late fee policies."""
    template_name = 'invoicing/late_fee_policy_list.html'
    context_object_name = 'policies'

    def get_queryset(self):
        return LateFeePolicy.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Late Fee Policies'
        context['fee_type_choices'] = LateFeePolicy.FEE_TYPE_CHOICES
        context['frequency_choices'] = LateFeePolicy.APPLY_FREQUENCY_CHOICES
        context['active_count'] = LateFeePolicy.objects.filter(is_active=True).count()
        return context


class PaymentReminderListView(LoginRequiredMixin, ListView):
    """List all payment reminders."""
    template_name = 'invoicing/payment_reminder_list.html'
    context_object_name = 'reminders'

    def get_queryset(self):
        return PaymentReminder.objects.select_related('invoice').all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Payment Reminders'
        context['status_choices'] = PaymentReminder.STATUS_CHOICES
        context['reminder_type_choices'] = PaymentReminder.REMINDER_TYPE_CHOICES
        context['scheduled_count'] = PaymentReminder.objects.filter(
            status=PaymentReminder.SCHEDULED
        ).count()
        context['sent_count'] = PaymentReminder.objects.filter(
            status=PaymentReminder.SENT
        ).count()
        return context
