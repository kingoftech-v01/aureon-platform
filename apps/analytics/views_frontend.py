"""
Frontend views for the analytics app.

Provides class-based views for the main dashboard, revenue metrics,
client metrics, and activity feed.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView
from django.db.models import Sum, Count, Q
from django.utils import timezone

from .models import RevenueMetric, ClientMetric, ActivityLog


class DashboardView(LoginRequiredMixin, TemplateView):
    """Main analytics dashboard showing key metrics and summaries."""
    template_name = 'analytics/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Dashboard'

        now = timezone.now()
        current_year = now.year
        current_month = now.month

        # Current month revenue metric
        current_metric = RevenueMetric.objects.filter(
            year=current_year, month=current_month
        ).first()
        context['current_metric'] = current_metric

        # Recent metrics for chart data (last 12 months)
        context['recent_metrics'] = RevenueMetric.objects.order_by(
            '-year', '-month'
        )[:12]

        # Summary counts
        from apps.clients.models import Client
        from apps.contracts.models import Contract
        from apps.invoicing.models import Invoice

        context['active_clients'] = Client.objects.filter(
            is_active=True, lifecycle_stage=Client.ACTIVE
        ).count()
        context['active_contracts'] = Contract.objects.filter(
            status=Contract.ACTIVE
        ).count()
        context['pending_invoices'] = Invoice.objects.filter(
            status__in=[Invoice.SENT, Invoice.VIEWED]
        ).count()
        context['overdue_invoices'] = Invoice.objects.filter(
            status=Invoice.OVERDUE
        ).count()
        context['total_outstanding'] = Invoice.objects.filter(
            status__in=[Invoice.SENT, Invoice.VIEWED, Invoice.PARTIALLY_PAID, Invoice.OVERDUE]
        ).aggregate(total=Sum('total'))['total'] or 0

        # Recent activity
        context['recent_activity'] = ActivityLog.objects.select_related('user')[:10]

        return context


class RevenueView(LoginRequiredMixin, ListView):
    """Revenue metrics and trends over time."""
    template_name = 'analytics/revenue.html'
    context_object_name = 'metrics'

    def get_queryset(self):
        return RevenueMetric.objects.order_by('-year', '-month')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Revenue Analytics'

        # Calculate totals across all periods
        totals = RevenueMetric.objects.aggregate(
            total_revenue=Sum('total_revenue'),
            total_recurring=Sum('recurring_revenue'),
            total_one_time=Sum('one_time_revenue'),
            total_refunds=Sum('refund_amount'),
        )
        context['total_revenue'] = totals['total_revenue'] or 0
        context['total_recurring'] = totals['total_recurring'] or 0
        context['total_one_time'] = totals['total_one_time'] or 0
        context['total_refunds'] = totals['total_refunds'] or 0
        return context


class ClientMetricsView(LoginRequiredMixin, ListView):
    """Per-client analytics and performance metrics."""
    template_name = 'analytics/client_metrics.html'
    context_object_name = 'client_metrics'

    def get_queryset(self):
        return ClientMetric.objects.select_related('client').all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Client Metrics'
        context['total_clients'] = ClientMetric.objects.count()
        context['total_lifetime_value'] = ClientMetric.objects.aggregate(
            total=Sum('lifetime_value')
        )['total'] or 0
        context['avg_reliability_score'] = ClientMetric.objects.aggregate(
            avg=Sum('payment_reliability_score')
        )['avg'] or 0
        return context


class ActivityFeedView(LoginRequiredMixin, ListView):
    """Activity feed showing recent actions and events across the system."""
    template_name = 'analytics/activity_feed.html'
    context_object_name = 'activities'

    def get_queryset(self):
        queryset = ActivityLog.objects.select_related('user').all()
        activity_type = self.request.GET.get('type')
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Activity Feed'
        context['activity_type_choices'] = ActivityLog.ACTIVITY_TYPE_CHOICES
        context['current_type'] = self.request.GET.get('type', '')
        context['total_activities'] = ActivityLog.objects.count()
        return context
