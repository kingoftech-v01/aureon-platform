"""
Frontend views for the expenses app.

Provides class-based views for expense listing, detail, creation,
category management, and expense reporting.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, CreateView
from django.db.models import Sum, Q

from .models import Expense, ExpenseCategory


class ExpenseListView(LoginRequiredMixin, ListView):
    """List all expenses with filtering by status, category, and date range."""
    template_name = 'expenses/expense_list.html'
    context_object_name = 'expenses'

    def get_queryset(self):
        queryset = Expense.objects.select_related(
            'category', 'client', 'contract', 'submitted_by', 'approved_by'
        ).all()
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        is_billable = self.request.GET.get('billable')
        if is_billable == 'true':
            queryset = queryset.filter(is_billable=True)
        elif is_billable == 'false':
            queryset = queryset.filter(is_billable=False)
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(description__icontains=search) |
                Q(vendor__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Expenses'
        context['status_choices'] = Expense.STATUS_CHOICES
        context['payment_method_choices'] = Expense.PAYMENT_METHOD_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        context['current_category'] = self.request.GET.get('category', '')
        context['current_billable'] = self.request.GET.get('billable', '')
        context['search_query'] = self.request.GET.get('q', '')
        context['categories'] = ExpenseCategory.objects.filter(is_active=True)
        context['total_expenses'] = Expense.objects.aggregate(
            total=Sum('amount')
        )['total'] or 0
        context['pending_count'] = Expense.objects.filter(
            status=Expense.PENDING
        ).count()
        context['billable_total'] = Expense.objects.filter(
            is_billable=True, is_invoiced=False
        ).aggregate(total=Sum('amount'))['total'] or 0
        return context


class ExpenseDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a single expense with receipt and approval information."""
    template_name = 'expenses/expense_detail.html'
    model = Expense
    context_object_name = 'expense'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Expense: {self.object.description}'
        context['category'] = self.object.category
        context['client'] = self.object.client
        context['contract'] = self.object.contract
        context['invoice'] = self.object.invoice
        context['submitted_by'] = self.object.submitted_by
        context['approved_by'] = self.object.approved_by
        context['is_pending'] = self.object.is_pending
        context['has_receipt'] = bool(self.object.receipt_file)
        return context


class ExpenseCreateView(LoginRequiredMixin, CreateView):
    """Create a new expense."""
    template_name = 'expenses/expense_create.html'
    model = Expense
    fields = [
        'description', 'amount', 'currency', 'category', 'expense_date',
        'client', 'contract', 'is_billable', 'receipt_file',
        'receipt_number', 'vendor', 'payment_method', 'notes', 'tags',
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Add Expense'
        context['categories'] = ExpenseCategory.objects.filter(is_active=True)
        context['payment_method_choices'] = Expense.PAYMENT_METHOD_CHOICES
        from apps.clients.models import Client
        context['clients'] = Client.objects.filter(is_active=True)
        from apps.contracts.models import Contract
        context['contracts'] = Contract.objects.filter(status=Contract.ACTIVE)
        return context


class ExpenseCategoryListView(LoginRequiredMixin, ListView):
    """List all expense categories."""
    template_name = 'expenses/expense_category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return ExpenseCategory.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Expense Categories'
        context['active_count'] = ExpenseCategory.objects.filter(is_active=True).count()
        context['total_count'] = ExpenseCategory.objects.count()
        return context


class ExpenseReportView(LoginRequiredMixin, TemplateView):
    """Expense report view with aggregations and summaries."""
    template_name = 'expenses/expense_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Expense Report'

        # Date range filtering
        from django.utils import timezone
        from datetime import timedelta

        date_range = self.request.GET.get('range', '30')
        try:
            days = int(date_range)
        except ValueError:
            days = 30
        start_date = timezone.now().date() - timedelta(days=days)

        expenses_in_range = Expense.objects.filter(expense_date__gte=start_date)

        context['date_range'] = date_range
        context['start_date'] = start_date

        # Totals
        context['total_amount'] = expenses_in_range.aggregate(
            total=Sum('amount')
        )['total'] or 0
        context['billable_amount'] = expenses_in_range.filter(
            is_billable=True
        ).aggregate(total=Sum('amount'))['total'] or 0
        context['non_billable_amount'] = expenses_in_range.filter(
            is_billable=False
        ).aggregate(total=Sum('amount'))['total'] or 0

        # By category
        context['expenses_by_category'] = expenses_in_range.values(
            'category__name'
        ).annotate(total=Sum('amount')).order_by('-total')

        # By status
        context['expenses_by_status'] = expenses_in_range.values(
            'status'
        ).annotate(total=Sum('amount')).order_by('-total')

        # By payment method
        context['expenses_by_method'] = expenses_in_range.values(
            'payment_method'
        ).annotate(total=Sum('amount')).order_by('-total')

        return context
