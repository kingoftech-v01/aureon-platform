"""
Analytics Celery tasks for Aureon SaaS Platform.

These tasks handle analytics and reporting operations.
"""
from celery import shared_task
from datetime import timedelta
from django.utils import timezone
import logging
from apps.analytics.services import DashboardDataService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2)
def generate_daily_analytics(self):
    """Generate daily analytics summary. Runs at 3 AM."""
    try:
        from apps.analytics.services import RevenueMetricsCalculator, ClientMetricsCalculator
        from apps.clients.models import Client

        logger.info("Generating daily analytics...")
        today = timezone.now()

        # Calculate revenue metrics for current month
        metric = RevenueMetricsCalculator.calculate_month_metrics(today.year, today.month)

        # Update client metrics for active clients
        active_clients = Client.objects.filter(lifecycle_stage='active')
        client_count = 0
        for client in active_clients:
            try:
                ClientMetricsCalculator.calculate_client_metrics(client)
                client_count += 1
            except Exception as e:
                logger.warning(f"Could not calculate metrics for client {client.id}: {e}")

        logger.info(f"Daily analytics: revenue=${metric.total_revenue}, {client_count} client metrics updated")
        return {
            'status': 'success',
            'date': today.date().isoformat(),
            'revenue': str(metric.total_revenue),
            'clients_updated': client_count
        }
    except Exception as exc:
        logger.error(f"Daily analytics generation failed: {exc}")
        raise self.retry(exc=exc, countdown=300)


@shared_task(bind=True, max_retries=2)
def generate_weekly_reports(self):
    """Generate weekly reports. Runs Monday at 5 AM."""
    try:
        from apps.analytics.services import RevenueMetricsCalculator

        logger.info("Generating weekly reports...")
        today = timezone.now()

        # Calculate metrics for the past 4 weeks
        metrics = []
        for weeks_ago in range(4):
            date = today - timedelta(weeks=weeks_ago)
            metric = RevenueMetricsCalculator.calculate_month_metrics(date.year, date.month)
            metrics.append(metric)

        # Get dashboard summary
        summary = DashboardDataService.get_dashboard_summary()

        logger.info(f"Weekly report generated: {len(metrics)} months calculated")
        return {
            'status': 'success',
            'week': today.isocalendar()[1],
            'total_revenue': str(sum(m.total_revenue for m in metrics)),
            'active_clients': summary.get('active_clients', 0)
        }
    except Exception as exc:
        logger.error(f"Weekly report generation failed: {exc}")
        raise self.retry(exc=exc, countdown=300)


@shared_task(bind=True, max_retries=2)
def calculate_revenue_metrics(self):
    """Calculate revenue metrics. Runs every 4 hours."""
    try:
        from apps.analytics.services import RevenueMetricsCalculator

        logger.info("Calculating revenue metrics...")
        today = timezone.now()

        # Calculate current month
        metric = RevenueMetricsCalculator.calculate_month_metrics(today.year, today.month)

        # Also recalculate previous month if we're in the first week
        if today.day <= 7:
            prev_month = today.month - 1 if today.month > 1 else 12
            prev_year = today.year if today.month > 1 else today.year - 1
            RevenueMetricsCalculator.calculate_month_metrics(prev_year, prev_month)

        logger.info(f"Revenue metrics calculated: ${metric.total_revenue}")
        return {
            'status': 'success',
            'timestamp': timezone.now().isoformat(),
            'revenue': str(metric.total_revenue)
        }
    except Exception as exc:
        logger.error(f"Revenue metrics calculation failed: {exc}")
        raise self.retry(exc=exc, countdown=120)
