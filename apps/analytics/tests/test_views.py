"""Tests for analytics API views."""

import uuid
import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock
from datetime import date, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.analytics.models import RevenueMetric, ClientMetric, ActivityLog

User = get_user_model()


@pytest.mark.django_db
class TestDashboardSummaryView:
    """Tests for dashboard_summary view."""

    def test_dashboard_summary_authenticated(self, authenticated_admin_client):
        """Test authenticated access to dashboard summary."""
        with patch('apps.analytics.views.DashboardDataService') as mock_service:
            mock_service.get_dashboard_summary.return_value = {
                'total_revenue': 50000.0,
                'mrr': 30000.0,
                'active_clients': 150,
            }
            response = authenticated_admin_client.get('/api/analytics/dashboard/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_revenue'] == 50000.0

    def test_dashboard_summary_unauthenticated(self, api_client):
        """Test unauthenticated access to dashboard summary is forbidden."""
        response = api_client.get('/api/analytics/dashboard/')
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_dashboard_summary_error(self, authenticated_admin_client):
        """Test dashboard summary with service error."""
        with patch('apps.analytics.views.DashboardDataService') as mock_service:
            mock_service.get_dashboard_summary.side_effect = Exception('Database error')
            response = authenticated_admin_client.get('/api/analytics/dashboard/')

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'error' in response.data


@pytest.mark.django_db
class TestRevenueMetricsView:
    """Tests for revenue_metrics view."""

    def _create_metrics(self):
        """Create test revenue metrics for the past few months."""
        metrics = []
        now = timezone.now()
        for i in range(3, 0, -1):
            month_date = now - timedelta(days=30 * i)
            metric = RevenueMetric.objects.create(
                year=month_date.year,
                month=month_date.month,
                total_revenue=Decimal('10000.00') * i,
                recurring_revenue=Decimal('5000.00') * i,
                one_time_revenue=Decimal('5000.00') * i,
                invoices_sent=10 * i,
                invoices_paid=8 * i,
                payments_received=8 * i,
                active_clients=50 + i * 10,
                new_clients=5 * i,
                churned_clients=i,
            )
            metrics.append(metric)
        return metrics

    def test_revenue_metrics_authenticated(self, authenticated_admin_client):
        """Test authenticated access to revenue metrics."""
        self._create_metrics()
        response = authenticated_admin_client.get('/api/analytics/revenue/')

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_revenue_metrics_default_months(self, authenticated_admin_client):
        """Test default months parameter (12)."""
        self._create_metrics()
        response = authenticated_admin_client.get('/api/analytics/revenue/')

        assert response.status_code == status.HTTP_200_OK

    def test_revenue_metrics_custom_months(self, authenticated_admin_client):
        """Test custom months parameter."""
        self._create_metrics()
        response = authenticated_admin_client.get('/api/analytics/revenue/?months=3')

        assert response.status_code == status.HTTP_200_OK

    def test_revenue_metrics_unauthenticated(self, api_client):
        """Test unauthenticated access is forbidden."""
        response = api_client.get('/api/analytics/revenue/')
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_revenue_metrics_with_existing_data(self, authenticated_admin_client):
        """Test revenue metrics returns correct data structure."""
        now = timezone.now()
        month_date = now - timedelta(days=30)
        RevenueMetric.objects.create(
            year=month_date.year,
            month=month_date.month,
            total_revenue=Decimal('25000.00'),
            recurring_revenue=Decimal('15000.00'),
            one_time_revenue=Decimal('10000.00'),
            invoices_sent=20,
            invoices_paid=15,
            payments_received=15,
            active_clients=100,
            new_clients=8,
            churned_clients=2,
        )
        response = authenticated_admin_client.get('/api/analytics/revenue/?months=2')

        assert response.status_code == status.HTTP_200_OK
        if len(response.data) > 0:
            metric = response.data[0]
            assert 'period' in metric
            assert 'year' in metric
            assert 'month' in metric
            assert 'total_revenue' in metric
            assert 'recurring_revenue' in metric
            assert 'one_time_revenue' in metric
            assert 'invoices_sent' in metric
            assert 'invoices_paid' in metric
            assert 'payments_received' in metric
            assert 'active_clients' in metric
            assert 'new_clients' in metric
            assert 'churned_clients' in metric

    def test_revenue_metrics_no_data(self, authenticated_admin_client):
        """Test revenue metrics when no data exists."""
        response = authenticated_admin_client.get('/api/analytics/revenue/')

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) == 0

    def test_revenue_metrics_error(self, authenticated_admin_client):
        """Test revenue metrics with invalid months parameter."""
        response = authenticated_admin_client.get('/api/analytics/revenue/?months=invalid')

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'error' in response.data


@pytest.mark.django_db
class TestClientMetricsView:
    """Tests for client_metrics view."""

    @pytest.fixture
    def client_with_metric(self, admin_user):
        """Create a client with associated metrics."""
        from apps.clients.models import Client

        client = Client.objects.create(
            first_name='Metric',
            last_name='Client',
            email='metric@example.com',
            lifecycle_stage=Client.ACTIVE,
            owner=admin_user,
        )
        metric = ClientMetric.objects.create(
            client=client,
            lifetime_value=Decimal('50000.00'),
            outstanding_balance=Decimal('5000.00'),
            total_invoices=20,
            paid_invoices=18,
            overdue_invoices=1,
            active_contracts=3,
            payment_reliability_score=Decimal('90.00'),
            days_since_last_payment=10,
        )
        return client, metric

    def test_client_metrics_authenticated(self, authenticated_admin_client, client_with_metric):
        """Test authenticated access to client metrics."""
        response = authenticated_admin_client.get('/api/analytics/clients/')

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) == 1

    def test_client_metrics_data_structure(self, authenticated_admin_client, client_with_metric):
        """Test returned data structure."""
        client, _ = client_with_metric
        response = authenticated_admin_client.get('/api/analytics/clients/')

        assert response.status_code == status.HTTP_200_OK
        data = response.data[0]
        assert 'client_id' in data
        assert 'client_name' in data
        assert 'client_email' in data
        assert 'lifetime_value' in data
        assert 'outstanding_balance' in data
        assert 'total_invoices' in data
        assert 'paid_invoices' in data
        assert 'overdue_invoices' in data
        assert 'active_contracts' in data
        assert 'payment_reliability_score' in data
        assert 'days_since_last_payment' in data

    def test_client_metrics_default_sort(self, authenticated_admin_client, client_with_metric):
        """Test default sort by -lifetime_value."""
        response = authenticated_admin_client.get('/api/analytics/clients/')
        assert response.status_code == status.HTTP_200_OK

    def test_client_metrics_custom_sort(self, authenticated_admin_client, client_with_metric):
        """Test custom sort parameter."""
        response = authenticated_admin_client.get('/api/analytics/clients/?sort=-outstanding_balance')
        assert response.status_code == status.HTTP_200_OK

    def test_client_metrics_custom_limit(self, authenticated_admin_client, client_with_metric):
        """Test custom limit parameter."""
        response = authenticated_admin_client.get('/api/analytics/clients/?limit=5')
        assert response.status_code == status.HTTP_200_OK

    def test_client_metrics_unauthenticated(self, api_client):
        """Test unauthenticated access is forbidden."""
        response = api_client.get('/api/analytics/clients/')
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_client_metrics_no_data(self, authenticated_admin_client):
        """Test client metrics when no data exists."""
        response = authenticated_admin_client.get('/api/analytics/clients/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_client_metrics_error(self, authenticated_admin_client):
        """Test client metrics with invalid limit parameter."""
        response = authenticated_admin_client.get('/api/analytics/clients/?limit=invalid')

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'error' in response.data


@pytest.mark.django_db
class TestActivityFeedView:
    """Tests for activity_feed view."""

    def _create_activities(self, user=None, count=5):
        """Create test activity logs."""
        activities = []
        for i in range(count):
            activity = ActivityLog.objects.create(
                activity_type=ActivityLog.INVOICE_CREATED,
                description=f'Invoice INV-{i:03d} created',
                user=user,
                metadata={'source': 'test'},
            )
            activities.append(activity)
        return activities

    def test_activity_feed_authenticated(self, authenticated_admin_client, admin_user):
        """Test authenticated access to activity feed."""
        self._create_activities(user=admin_user)
        response = authenticated_admin_client.get('/api/analytics/activity/')

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) == 5

    def test_activity_feed_data_structure(self, authenticated_admin_client, admin_user):
        """Test returned data structure."""
        self._create_activities(user=admin_user, count=1)
        response = authenticated_admin_client.get('/api/analytics/activity/')

        assert response.status_code == status.HTTP_200_OK
        data = response.data[0]
        assert 'id' in data
        assert 'type' in data
        assert 'type_display' in data
        assert 'description' in data
        assert 'user' in data
        assert 'timestamp' in data
        assert 'metadata' in data

    def test_activity_feed_default_limit(self, authenticated_admin_client, admin_user):
        """Test default limit of 20."""
        self._create_activities(user=admin_user, count=25)
        response = authenticated_admin_client.get('/api/analytics/activity/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 20

    def test_activity_feed_custom_limit(self, authenticated_admin_client, admin_user):
        """Test custom limit parameter."""
        self._create_activities(user=admin_user, count=10)
        response = authenticated_admin_client.get('/api/analytics/activity/?limit=3')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

    def test_activity_feed_system_user(self, authenticated_admin_client):
        """Test activity feed with system activities (no user)."""
        ActivityLog.objects.create(
            activity_type=ActivityLog.PAYMENT_RECEIVED,
            description='System payment received',
        )
        response = authenticated_admin_client.get('/api/analytics/activity/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data[0]['user'] == 'System'

    def test_activity_feed_unauthenticated(self, api_client):
        """Test unauthenticated access is forbidden."""
        response = api_client.get('/api/analytics/activity/')
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_activity_feed_empty(self, authenticated_admin_client):
        """Test activity feed with no activities."""
        response = authenticated_admin_client.get('/api/analytics/activity/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_activity_feed_error(self, authenticated_admin_client):
        """Test activity feed with invalid limit."""
        response = authenticated_admin_client.get('/api/analytics/activity/?limit=invalid')

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'error' in response.data

    def test_activity_feed_ordered_by_created_at_desc(self, authenticated_admin_client, admin_user):
        """Test that activities are ordered by most recent first."""
        self._create_activities(user=admin_user, count=3)
        response = authenticated_admin_client.get('/api/analytics/activity/')

        assert response.status_code == status.HTTP_200_OK
        timestamps = [entry['timestamp'] for entry in response.data]
        assert timestamps == sorted(timestamps, reverse=True)


@pytest.mark.django_db
class TestRecalculateMetricsView:
    """Tests for recalculate_metrics view."""

    @patch('apps.analytics.views.RevenueMetricsCalculator')
    def test_recalculate_metrics_authenticated(self, mock_calculator, authenticated_admin_client):
        """Test authenticated access to recalculate metrics."""
        mock_metric = MagicMock()
        mock_metric.total_revenue = Decimal('50000.00')
        mock_metric.recurring_revenue = Decimal('30000.00')
        mock_calculator.calculate_month_metrics.return_value = mock_metric

        response = authenticated_admin_client.post(
            '/api/analytics/recalculate/',
            {'year': 2025, 'month': 6},
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data
        assert response.data['total_revenue'] == 50000.0
        assert response.data['mrr'] == 30000.0

    @patch('apps.analytics.views.RevenueMetricsCalculator')
    def test_recalculate_metrics_default_params(self, mock_calculator, authenticated_admin_client):
        """Test recalculate with default (current) month and year."""
        mock_metric = MagicMock()
        mock_metric.total_revenue = Decimal('10000.00')
        mock_metric.recurring_revenue = Decimal('5000.00')
        mock_calculator.calculate_month_metrics.return_value = mock_metric

        response = authenticated_admin_client.post(
            '/api/analytics/recalculate/',
            {},
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        now = timezone.now()
        mock_calculator.calculate_month_metrics.assert_called_once_with(now.year, now.month)

    def test_recalculate_metrics_unauthenticated(self, api_client):
        """Test unauthenticated access is forbidden."""
        response = api_client.post('/api/analytics/recalculate/')
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    @patch('apps.analytics.views.RevenueMetricsCalculator')
    def test_recalculate_metrics_error(self, mock_calculator, authenticated_admin_client):
        """Test recalculate with calculation error."""
        mock_calculator.calculate_month_metrics.side_effect = Exception('Calculation failed')

        response = authenticated_admin_client.post(
            '/api/analytics/recalculate/',
            {'year': 2025, 'month': 6},
            format='json',
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    @patch('apps.analytics.views.RevenueMetricsCalculator')
    def test_recalculate_get_method_not_allowed(self, mock_calculator, authenticated_admin_client):
        """Test that GET method is not allowed."""
        response = authenticated_admin_client.get('/api/analytics/recalculate/')

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
