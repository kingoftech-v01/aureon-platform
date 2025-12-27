"""API views for analytics endpoints."""

from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from .models import RevenueMetric, ClientMetric, ActivityLog
from .services import RevenueMetricsCalculator, ClientMetricsCalculator, DashboardDataService


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_summary(request):
    """
    Get dashboard summary data.

    GET /api/analytics/dashboard/
    """
    try:
        data = DashboardDataService.get_dashboard_summary()
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def revenue_metrics(request):
    """
    Get revenue metrics.

    GET /api/analytics/revenue/
    Query params:
        - months: Number of months to retrieve (default: 12)
    """
    try:
        months = int(request.query_params.get('months', 12))

        metrics = []
        now = timezone.now()

        for i in range(months, 0, -1):
            month_date = now - timedelta(days=30 * i)
            year = month_date.year
            month = month_date.month

            metric = RevenueMetric.objects.filter(year=year, month=month).first()

            if metric:
                metrics.append({
                    'period': metric.period_name,
                    'year': metric.year,
                    'month': metric.month,
                    'total_revenue': float(metric.total_revenue),
                    'recurring_revenue': float(metric.recurring_revenue),
                    'one_time_revenue': float(metric.one_time_revenue),
                    'invoices_sent': metric.invoices_sent,
                    'invoices_paid': metric.invoices_paid,
                    'payments_received': metric.payments_received,
                    'active_clients': metric.active_clients,
                    'new_clients': metric.new_clients,
                    'churned_clients': metric.churned_clients,
                })

        return Response(metrics, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_metrics(request):
    """
    Get client metrics.

    GET /api/analytics/clients/
    Query params:
        - sort: Sort field (lifetime_value, outstanding_balance, etc.)
        - limit: Number of results (default: 10)
    """
    try:
        sort_field = request.query_params.get('sort', '-lifetime_value')
        limit = int(request.query_params.get('limit', 10))

        client_metrics = ClientMetric.objects.order_by(sort_field)[:limit]

        data = []
        for cm in client_metrics:
            data.append({
                'client_id': str(cm.client.id),
                'client_name': cm.client.full_name,
                'client_email': cm.client.email,
                'lifetime_value': float(cm.lifetime_value),
                'outstanding_balance': float(cm.outstanding_balance),
                'total_invoices': cm.total_invoices,
                'paid_invoices': cm.paid_invoices,
                'overdue_invoices': cm.overdue_invoices,
                'active_contracts': cm.active_contracts,
                'payment_reliability_score': float(cm.payment_reliability_score),
                'days_since_last_payment': cm.days_since_last_payment,
            })

        return Response(data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def activity_feed(request):
    """
    Get recent activity feed.

    GET /api/analytics/activity/
    Query params:
        - limit: Number of activities (default: 20)
    """
    try:
        limit = int(request.query_params.get('limit', 20))

        activities = ActivityLog.objects.order_by('-created_at')[:limit]

        data = []
        for activity in activities:
            data.append({
                'id': str(activity.id),
                'type': activity.activity_type,
                'type_display': activity.get_activity_type_display(),
                'description': activity.description,
                'user': activity.user.email if activity.user else 'System',
                'timestamp': activity.created_at.isoformat(),
                'metadata': activity.metadata,
            })

        return Response(data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recalculate_metrics(request):
    """
    Trigger recalculation of metrics.

    POST /api/analytics/recalculate/
    Body:
        - year: Year to recalculate (optional)
        - month: Month to recalculate (optional)
    """
    try:
        year = request.data.get('year', timezone.now().year)
        month = request.data.get('month', timezone.now().month)

        metric = RevenueMetricsCalculator.calculate_month_metrics(year, month)

        return Response({
            'message': f'Metrics recalculated for {year}-{month}',
            'total_revenue': float(metric.total_revenue),
            'mrr': float(metric.recurring_revenue)
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
