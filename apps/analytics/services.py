"""Analytics calculation services."""

import logging
from decimal import Decimal
from datetime import datetime, timedelta
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from .models import RevenueMetric, ClientMetric, ActivityLog

logger = logging.getLogger(__name__)


class RevenueMetricsCalculator:
    """Calculator for monthly revenue metrics."""

    @staticmethod
    def calculate_month_metrics(year, month):
        """
        Calculate revenue metrics for a specific month.

        Args:
            year: Year (e.g., 2025)
            month: Month (1-12)

        Returns:
            RevenueMetric: Calculated metrics
        """
        from apps.invoicing.models import Invoice
        from apps.payments.models import Payment
        from apps.contracts.models import Contract
        from apps.clients.models import Client

        # Date range for the month
        from datetime import date
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        # Get or create metric record
        metric, created = RevenueMetric.objects.get_or_create(
            year=year,
            month=month
        )

        # Invoice Metrics
        invoices = Invoice.objects.filter(
            issue_date__gte=start_date,
            issue_date__lt=end_date
        )

        metric.invoices_sent = invoices.filter(status__in=[Invoice.SENT, Invoice.VIEWED, Invoice.PAID]).count()
        metric.invoices_paid = invoices.filter(status=Invoice.PAID).count()
        metric.invoices_overdue = Invoice.objects.filter(
            due_date__lt=timezone.now().date(),
            status__in=[Invoice.SENT, Invoice.VIEWED]
        ).count()

        avg_value = invoices.aggregate(avg=Avg('total'))['avg']
        metric.average_invoice_value = avg_value or Decimal('0.00')

        # Payment Metrics
        payments = Payment.objects.filter(
            payment_date__gte=start_date,
            payment_date__lt=end_date
        )

        successful_payments = payments.filter(status=Payment.SUCCEEDED)
        metric.payments_received = successful_payments.count()
        metric.payments_failed = payments.filter(status=Payment.FAILED).count()

        # Calculate total revenue from successful payments
        revenue = successful_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        metric.total_revenue = revenue

        # Refunds
        refunded = payments.filter(status=Payment.REFUNDED)
        metric.refunds_issued = refunded.count()
        metric.refund_amount = refunded.aggregate(total=Sum('refunded_amount'))['total'] or Decimal('0.00')

        # Contract Metrics
        contracts = Contract.objects.filter(
            created_at__gte=start_date,
            created_at__lt=end_date
        )

        metric.contracts_signed = contracts.filter(
            signature_date__isnull=False
        ).count()

        metric.contracts_completed = Contract.objects.filter(
            status=Contract.COMPLETED,
            updated_at__gte=start_date,
            updated_at__lt=end_date
        ).count()

        metric.active_contracts = Contract.objects.filter(
            status=Contract.ACTIVE
        ).count()

        total_contract_value = contracts.aggregate(total=Sum('total_value'))['total']
        metric.total_contract_value = total_contract_value or Decimal('0.00')

        # Client Metrics
        metric.new_clients = Client.objects.filter(
            created_at__gte=start_date,
            created_at__lt=end_date
        ).count()

        metric.churned_clients = Client.objects.filter(
            lifecycle_stage=Client.CHURNED,
            updated_at__gte=start_date,
            updated_at__lt=end_date
        ).count()

        metric.active_clients = Client.objects.filter(
            lifecycle_stage=Client.ACTIVE
        ).count()

        # Recurring Revenue (from retainer contracts)
        recurring_revenue = Contract.objects.filter(
            contract_type=Contract.RETAINER,
            status=Contract.ACTIVE
        ).aggregate(total=Sum('monthly_rate'))['total']
        metric.recurring_revenue = recurring_revenue or Decimal('0.00')

        # One-time revenue
        metric.one_time_revenue = metric.total_revenue - metric.recurring_revenue

        # Calculated Metrics
        total_payments = metric.payments_received + metric.payments_failed
        if total_payments > 0:
            metric.payment_success_rate = (Decimal(metric.payments_received) / Decimal(total_payments)) * 100
        else:
            metric.payment_success_rate = Decimal('0.00')

        total_clients = metric.active_clients + metric.churned_clients
        if total_clients > 0:
            metric.churn_rate = (Decimal(metric.churned_clients) / Decimal(total_clients)) * 100
        else:
            metric.churn_rate = Decimal('0.00')

        metric.save()

        logger.info(f"Calculated metrics for {year}-{month}: ${metric.total_revenue}")

        return metric


class ClientMetricsCalculator:
    """Calculator for per-client metrics."""

    @staticmethod
    def calculate_client_metrics(client):
        """
        Calculate metrics for a specific client.

        Args:
            client: Client instance

        Returns:
            ClientMetric: Calculated metrics
        """
        from apps.invoicing.models import Invoice
        from apps.payments.models import Payment
        from apps.contracts.models import Contract

        # Get or create metric record
        metric, created = ClientMetric.objects.get_or_create(client=client)

        # Invoice Metrics
        invoices = Invoice.objects.filter(client=client)
        metric.total_invoices = invoices.count()
        metric.paid_invoices = invoices.filter(status=Invoice.PAID).count()
        metric.overdue_invoices = invoices.filter(
            due_date__lt=timezone.now().date(),
            status__in=[Invoice.SENT, Invoice.VIEWED]
        ).count()

        # Average invoice value
        avg_value = invoices.aggregate(avg=Avg('total'))['avg']
        metric.average_invoice_value = avg_value or Decimal('0.00')

        # Outstanding balance
        outstanding = invoices.filter(
            status__in=[Invoice.SENT, Invoice.VIEWED, Invoice.PARTIALLY_PAID]
        ).aggregate(total=Sum('balance_due'))['total']
        metric.outstanding_balance = outstanding or Decimal('0.00')

        # Last invoice date
        last_invoice = invoices.order_by('-issue_date').first()
        if last_invoice:
            metric.last_invoice_date = last_invoice.issue_date

        # Payment Metrics
        payments = Payment.objects.filter(client=client)
        metric.total_payments = payments.filter(status=Payment.SUCCEEDED).count()
        metric.failed_payments = payments.filter(status=Payment.FAILED).count()

        # Lifetime value (total successful payments)
        ltv = payments.filter(status=Payment.SUCCEEDED).aggregate(total=Sum('amount'))['total']
        metric.lifetime_value = ltv or Decimal('0.00')

        # Last payment date
        last_payment = payments.filter(status=Payment.SUCCEEDED).order_by('-payment_date').first()
        if last_payment:
            metric.last_payment_date = last_payment.payment_date
            metric.days_since_last_payment = (timezone.now().date() - last_payment.payment_date).days
        else:
            metric.days_since_last_payment = 0

        # Contract Metrics
        contracts = Contract.objects.filter(client=client)
        metric.total_contracts = contracts.count()
        metric.active_contracts = contracts.filter(status=Contract.ACTIVE).count()

        # Payment Reliability Score (0-100)
        total_payments_attempted = metric.total_payments + metric.failed_payments
        if total_payments_attempted > 0:
            success_rate = (Decimal(metric.total_payments) / Decimal(total_payments_attempted)) * 100
            # Bonus points for having no overdue invoices
            overdue_penalty = min(metric.overdue_invoices * 5, 20)
            metric.payment_reliability_score = max(Decimal('0.00'), success_rate - Decimal(overdue_penalty))
        else:
            metric.payment_reliability_score = Decimal('100.00')  # No history = perfect score initially

        metric.save()

        logger.info(f"Calculated metrics for client {client.full_name}: LTV ${metric.lifetime_value}")

        return metric


class ActivityLogger:
    """Service for logging user and system activities."""

    @staticmethod
    def log_activity(activity_type, description, user=None, related_objects=None, metadata=None, request=None):
        """
        Log an activity.

        Args:
            activity_type: Type of activity (from ActivityLog.ACTIVITY_TYPE_CHOICES)
            description: Human-readable description
            user: User who performed the activity (optional)
            related_objects: Dict of related object IDs (optional)
            metadata: Additional metadata (optional)
            request: HTTP request object for IP/user agent (optional)

        Returns:
            ActivityLog: Created activity log
        """
        ip_address = None
        user_agent = ''

        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')

            user_agent = request.META.get('HTTP_USER_AGENT', '')

        activity = ActivityLog.objects.create(
            activity_type=activity_type,
            description=description,
            user=user,
            related_objects=related_objects or {},
            metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent
        )

        logger.info(f"Activity logged: {description}")

        return activity


class DashboardDataService:
    """Service for generating dashboard data."""

    @staticmethod
    def get_dashboard_summary():
        """
        Get summary data for main dashboard.

        Returns:
            dict: Dashboard summary data
        """
        from apps.invoicing.models import Invoice
        from apps.payments.models import Payment
        from apps.contracts.models import Contract
        from apps.clients.models import Client

        # Current month revenue
        current_month = timezone.now().month
        current_year = timezone.now().year

        current_metric = RevenueMetric.objects.filter(
            year=current_year,
            month=current_month
        ).first()

        # Get last 6 months of revenue
        revenue_trend = []
        for i in range(6, 0, -1):
            month_date = timezone.now() - timedelta(days=30 * i)
            metric = RevenueMetric.objects.filter(
                year=month_date.year,
                month=month_date.month
            ).first()

            revenue_trend.append({
                'month': month_date.strftime('%b %Y'),
                'revenue': float(metric.total_revenue) if metric else 0
            })

        # Quick stats
        stats = {
            'total_revenue': float(current_metric.total_revenue) if current_metric else 0,
            'mrr': float(current_metric.recurring_revenue) if current_metric else 0,
            'active_clients': current_metric.active_clients if current_metric else 0,
            'active_contracts': current_metric.active_contracts if current_metric else 0,
            'pending_invoices': Invoice.objects.filter(
                status__in=[Invoice.SENT, Invoice.VIEWED]
            ).count(),
            'overdue_invoices': Invoice.objects.filter(
                due_date__lt=timezone.now().date(),
                status__in=[Invoice.SENT, Invoice.VIEWED]
            ).count(),
            'revenue_trend': revenue_trend
        }

        # Top clients by revenue
        top_clients = ClientMetric.objects.order_by('-lifetime_value')[:5]
        stats['top_clients'] = [
            {
                'name': cm.client.full_name,
                'revenue': float(cm.lifetime_value),
                'outstanding': float(cm.outstanding_balance)
            }
            for cm in top_clients
        ]

        # Recent activity
        recent_activities = ActivityLog.objects.order_by('-created_at')[:10]
        stats['recent_activities'] = [
            {
                'type': activity.get_activity_type_display(),
                'description': activity.description,
                'timestamp': activity.created_at.isoformat()
            }
            for activity in recent_activities
        ]

        return stats
