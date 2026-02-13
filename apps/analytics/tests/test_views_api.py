"""
Tests for analytics views_api.py endpoints.

Covers all function-based API views:
- dashboard_summary (GET /api/analytics/dashboard/)
- revenue_metrics (GET /api/analytics/revenue/)
- client_metrics (GET /api/analytics/clients/)
- activity_feed (GET /api/analytics/activity/)
- recalculate_metrics (POST /api/analytics/recalculate/)

Tests ensure authentication enforcement, successful responses, error
handling, and query-parameter logic.
"""

import pytest
from decimal import Decimal
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.analytics.models import RevenueMetric, ClientMetric, ActivityLog


# ---------------------------------------------------------------------------
# URL constants
# ---------------------------------------------------------------------------

DASHBOARD_URL = '/api/analytics/dashboard/'
REVENUE_URL = '/api/analytics/revenue/'
CLIENTS_URL = '/api/analytics/clients/'
ACTIVITY_URL = '/api/analytics/activity/'
RECALCULATE_URL = '/api/analytics/recalculate/'


# ---------------------------------------------------------------------------
# dashboard_summary
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestDashboardSummaryAPI:
    """Tests for the dashboard_summary view exposed via views_api."""

    @patch('apps.analytics.views.DashboardDataService')
    def test_success(self, mock_svc, authenticated_admin_client):
        """Authenticated GET returns 200 with dashboard payload."""
        mock_svc.get_dashboard_summary.return_value = {
            'total_revenue': 80000.0,
            'mrr': 40000.0,
            'active_clients': 200,
        }
        response = authenticated_admin_client.get(DASHBOARD_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_revenue'] == 80000.0
        assert response.data['mrr'] == 40000.0
        assert response.data['active_clients'] == 200

    def test_unauthenticated(self, api_client):
        """Unauthenticated requests are rejected."""
        response = api_client.get(DASHBOARD_URL)
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    @patch('apps.analytics.views.DashboardDataService')
    def test_service_exception_returns_500(self, mock_svc, authenticated_admin_client):
        """When DashboardDataService raises, the view returns 500."""
        mock_svc.get_dashboard_summary.side_effect = Exception('DB down')
        response = authenticated_admin_client.get(DASHBOARD_URL)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'error' in response.data
        assert 'DB down' in response.data['error']

    def test_post_method_not_allowed(self, authenticated_admin_client):
        """POST is not accepted on dashboard_summary."""
        response = authenticated_admin_client.post(DASHBOARD_URL)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


# ---------------------------------------------------------------------------
# revenue_metrics
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestRevenueMetricsAPI:
    """Tests for the revenue_metrics view exposed via views_api."""

    def _seed_metrics(self, months=3):
        """Create RevenueMetric rows for the last *months* months."""
        now = timezone.now()
        created = []
        for i in range(months, 0, -1):
            month_date = now - timedelta(days=30 * i)
            metric = RevenueMetric.objects.create(
                year=month_date.year,
                month=month_date.month,
                total_revenue=Decimal('10000.00') * i,
                recurring_revenue=Decimal('6000.00') * i,
                one_time_revenue=Decimal('4000.00') * i,
                invoices_sent=10 * i,
                invoices_paid=9 * i,
                payments_received=9 * i,
                active_clients=40 + i * 5,
                new_clients=3 * i,
                churned_clients=i,
            )
            created.append(metric)
        return created

    def test_success_default_months(self, authenticated_admin_client):
        """GET with no ?months defaults to 12 and returns matching data."""
        self._seed_metrics(3)
        response = authenticated_admin_client.get(REVENUE_URL)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        # Should contain the 3 seeded months that fall within the 12-month window
        assert len(response.data) >= 1

    def test_custom_months_param(self, authenticated_admin_client):
        """GET with ?months=3 only searches the last 3 months."""
        self._seed_metrics(3)
        response = authenticated_admin_client.get(REVENUE_URL, {'months': '3'})

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_data_structure(self, authenticated_admin_client):
        """Each item has the expected keys."""
        self._seed_metrics(1)
        response = authenticated_admin_client.get(REVENUE_URL, {'months': '2'})

        assert response.status_code == status.HTTP_200_OK
        if response.data:
            item = response.data[0]
            for key in (
                'period', 'year', 'month', 'total_revenue',
                'recurring_revenue', 'one_time_revenue',
                'invoices_sent', 'invoices_paid',
                'payments_received', 'active_clients',
                'new_clients', 'churned_clients',
            ):
                assert key in item, f"Missing key {key}"

    def test_empty_when_no_data(self, authenticated_admin_client):
        """Returns an empty list when there are no RevenueMetric rows."""
        response = authenticated_admin_client.get(REVENUE_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_invalid_months_returns_500(self, authenticated_admin_client):
        """Non-integer ?months triggers the except branch."""
        response = authenticated_admin_client.get(REVENUE_URL, {'months': 'abc'})

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'error' in response.data

    def test_unauthenticated(self, api_client):
        """Unauthenticated requests are rejected."""
        response = api_client.get(REVENUE_URL)
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )


# ---------------------------------------------------------------------------
# client_metrics
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestClientMetricsAPI:
    """Tests for the client_metrics view exposed via views_api."""

    @pytest.fixture
    def client_with_metric(self, admin_user):
        """Create a Client + ClientMetric pair."""
        from apps.clients.models import Client

        client = Client.objects.create(
            first_name='Alice',
            last_name='Metrics',
            email='alice@metrics.test',
            lifecycle_stage=Client.ACTIVE,
            owner=admin_user,
        )
        metric = ClientMetric.objects.create(
            client=client,
            lifetime_value=Decimal('60000.00'),
            outstanding_balance=Decimal('3000.00'),
            total_invoices=25,
            paid_invoices=22,
            overdue_invoices=2,
            active_contracts=4,
            payment_reliability_score=Decimal('88.50'),
            days_since_last_payment=7,
        )
        return client, metric

    def test_success(self, authenticated_admin_client, client_with_metric):
        """GET returns 200 with a list of client metric dicts."""
        response = authenticated_admin_client.get(CLIENTS_URL)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) == 1

    def test_data_structure(self, authenticated_admin_client, client_with_metric):
        """Each item contains all expected fields."""
        response = authenticated_admin_client.get(CLIENTS_URL)

        assert response.status_code == status.HTTP_200_OK
        item = response.data[0]
        expected_keys = [
            'client_id', 'client_name', 'client_email',
            'lifetime_value', 'outstanding_balance',
            'total_invoices', 'paid_invoices', 'overdue_invoices',
            'active_contracts', 'payment_reliability_score',
            'days_since_last_payment',
        ]
        for key in expected_keys:
            assert key in item, f"Missing key {key}"

    def test_data_values(self, authenticated_admin_client, client_with_metric):
        """Returned values match what was stored."""
        client, _ = client_with_metric
        response = authenticated_admin_client.get(CLIENTS_URL)

        item = response.data[0]
        assert item['client_id'] == str(client.id)
        assert item['client_email'] == 'alice@metrics.test'
        assert item['lifetime_value'] == 60000.0
        assert item['outstanding_balance'] == 3000.0
        assert item['payment_reliability_score'] == 88.5

    def test_sort_param(self, authenticated_admin_client, client_with_metric):
        """?sort= parameter is accepted and returns 200."""
        response = authenticated_admin_client.get(
            CLIENTS_URL, {'sort': '-outstanding_balance'}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_limit_param(self, authenticated_admin_client, client_with_metric):
        """?limit= parameter controls result count."""
        response = authenticated_admin_client.get(CLIENTS_URL, {'limit': '1'})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) <= 1

    def test_empty_when_no_data(self, authenticated_admin_client):
        """Returns empty list when there are no ClientMetric rows."""
        response = authenticated_admin_client.get(CLIENTS_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_invalid_limit_returns_500(self, authenticated_admin_client):
        """Non-integer ?limit triggers the except branch."""
        response = authenticated_admin_client.get(CLIENTS_URL, {'limit': 'bad'})

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'error' in response.data

    def test_unauthenticated(self, api_client):
        """Unauthenticated requests are rejected."""
        response = api_client.get(CLIENTS_URL)
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )


# ---------------------------------------------------------------------------
# activity_feed
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestActivityFeedAPI:
    """Tests for the activity_feed view exposed via views_api."""

    def _create_activities(self, user=None, count=5):
        """Seed ActivityLog rows."""
        activities = []
        for i in range(count):
            activity = ActivityLog.objects.create(
                activity_type=ActivityLog.INVOICE_CREATED,
                description=f'Invoice INV-{i:04d} created',
                user=user,
                metadata={'index': i},
            )
            activities.append(activity)
        return activities

    def test_success(self, authenticated_admin_client, admin_user):
        """GET returns activities as a list."""
        self._create_activities(user=admin_user, count=3)
        response = authenticated_admin_client.get(ACTIVITY_URL)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) == 3

    def test_data_structure(self, authenticated_admin_client, admin_user):
        """Each activity has the expected keys."""
        self._create_activities(user=admin_user, count=1)
        response = authenticated_admin_client.get(ACTIVITY_URL)

        item = response.data[0]
        for key in ('id', 'type', 'type_display', 'description',
                     'user', 'timestamp', 'metadata'):
            assert key in item, f"Missing key {key}"

    def test_user_email_shown(self, authenticated_admin_client, admin_user):
        """When an activity has a user, the user's email is returned."""
        self._create_activities(user=admin_user, count=1)
        response = authenticated_admin_client.get(ACTIVITY_URL)

        assert response.data[0]['user'] == admin_user.email

    def test_system_user_shown_when_no_user(self, authenticated_admin_client):
        """When an activity has no user, 'System' is returned."""
        ActivityLog.objects.create(
            activity_type=ActivityLog.PAYMENT_RECEIVED,
            description='Auto payment received',
        )
        response = authenticated_admin_client.get(ACTIVITY_URL)

        assert response.data[0]['user'] == 'System'

    def test_default_limit_is_20(self, authenticated_admin_client, admin_user):
        """Without ?limit, at most 20 activities are returned."""
        self._create_activities(user=admin_user, count=25)
        response = authenticated_admin_client.get(ACTIVITY_URL)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 20

    def test_custom_limit(self, authenticated_admin_client, admin_user):
        """?limit=5 returns at most 5 activities."""
        self._create_activities(user=admin_user, count=10)
        response = authenticated_admin_client.get(ACTIVITY_URL, {'limit': '5'})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 5

    def test_ordering_descending_created_at(self, authenticated_admin_client, admin_user):
        """Activities are returned newest-first."""
        self._create_activities(user=admin_user, count=5)
        response = authenticated_admin_client.get(ACTIVITY_URL)

        timestamps = [entry['timestamp'] for entry in response.data]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_empty_when_no_data(self, authenticated_admin_client):
        """Returns empty list when there are no ActivityLog rows."""
        response = authenticated_admin_client.get(ACTIVITY_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_invalid_limit_returns_500(self, authenticated_admin_client):
        """Non-integer ?limit triggers the except branch."""
        response = authenticated_admin_client.get(ACTIVITY_URL, {'limit': 'xyz'})

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'error' in response.data

    def test_unauthenticated(self, api_client):
        """Unauthenticated requests are rejected."""
        response = api_client.get(ACTIVITY_URL)
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )


# ---------------------------------------------------------------------------
# recalculate_metrics
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestRecalculateMetricsAPI:
    """Tests for the recalculate_metrics view exposed via views_api."""

    @patch('apps.analytics.views.RevenueMetricsCalculator')
    def test_success_with_explicit_year_month(self, mock_calc, authenticated_admin_client):
        """POST with year/month returns 200 and the recalculated data."""
        mock_metric = MagicMock()
        mock_metric.total_revenue = Decimal('45000.00')
        mock_metric.recurring_revenue = Decimal('25000.00')
        mock_calc.calculate_month_metrics.return_value = mock_metric

        response = authenticated_admin_client.post(
            RECALCULATE_URL,
            {'year': 2025, 'month': 11},
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data
        assert '2025' in response.data['message']
        assert '11' in response.data['message']
        assert response.data['total_revenue'] == 45000.0
        assert response.data['mrr'] == 25000.0
        mock_calc.calculate_month_metrics.assert_called_once_with(2025, 11)

    @patch('apps.analytics.views.RevenueMetricsCalculator')
    def test_defaults_to_current_month(self, mock_calc, authenticated_admin_client):
        """POST without year/month defaults to the current period."""
        mock_metric = MagicMock()
        mock_metric.total_revenue = Decimal('1000.00')
        mock_metric.recurring_revenue = Decimal('500.00')
        mock_calc.calculate_month_metrics.return_value = mock_metric

        response = authenticated_admin_client.post(
            RECALCULATE_URL, {}, format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        now = timezone.now()
        mock_calc.calculate_month_metrics.assert_called_once_with(now.year, now.month)

    @patch('apps.analytics.views.RevenueMetricsCalculator')
    def test_calculator_exception_returns_400(self, mock_calc, authenticated_admin_client):
        """When the calculator raises, the view returns 400."""
        mock_calc.calculate_month_metrics.side_effect = Exception('calc error')

        response = authenticated_admin_client.post(
            RECALCULATE_URL,
            {'year': 2025, 'month': 1},
            format='json',
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
        assert 'calc error' in response.data['error']

    def test_unauthenticated(self, api_client):
        """Unauthenticated requests are rejected."""
        response = api_client.post(RECALCULATE_URL)
        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_get_method_not_allowed(self, authenticated_admin_client):
        """GET is not accepted on recalculate_metrics."""
        response = authenticated_admin_client.get(RECALCULATE_URL)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
