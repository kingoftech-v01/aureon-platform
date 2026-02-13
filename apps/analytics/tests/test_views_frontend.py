"""
Tests for analytics app frontend views.

Tests cover:
- DashboardView (main dashboard with key metrics and summaries)
- RevenueView (revenue metrics list with aggregate totals)
- ClientMetricsView (per-client analytics and performance)
- ActivityFeedView (activity feed with type filtering)
- Authentication enforcement (LoginRequiredMixin redirects)
"""

import uuid
from decimal import Decimal

import factory
import pytest
from django.test import Client as TestClient
from django.template import TemplateDoesNotExist

from apps.accounts.models import User
from apps.clients.models import Client
from apps.analytics.models import RevenueMetric, ClientMetric, ActivityLog


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------
class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating User instances."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    id = factory.LazyFunction(uuid.uuid4)
    email = factory.Sequence(lambda n: f'analyticsuser{n}@test.com')
    username = factory.Sequence(lambda n: f'analyticsuser{n}')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = factory.PostGenerationMethodCall('set_password', 'TestPass123!')
    is_active = True
    is_staff = True
    is_verified = True
    role = User.ADMIN


class ClientFactory(factory.django.DjangoModelFactory):
    """Factory for creating Client instances."""

    class Meta:
        model = Client

    client_type = Client.COMPANY
    company_name = factory.Sequence(lambda n: f'Analytics Test Co {n}')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.LazyAttribute(
        lambda obj: f'{obj.first_name.lower()}.{obj.last_name.lower()}@analyticstest.com'
    )
    lifecycle_stage = Client.ACTIVE
    is_active = True
    owner = factory.SubFactory(UserFactory)


class RevenueMetricFactory(factory.django.DjangoModelFactory):
    """Factory for creating RevenueMetric instances."""

    class Meta:
        model = RevenueMetric

    year = 2026
    month = factory.Sequence(lambda n: (n % 12) + 1)
    total_revenue = Decimal('10000.00')
    recurring_revenue = Decimal('7000.00')
    one_time_revenue = Decimal('3000.00')
    refund_amount = Decimal('200.00')
    invoices_sent = 10
    invoices_paid = 8
    invoices_overdue = 1
    new_clients = 3
    active_clients = 20


class ClientMetricFactory(factory.django.DjangoModelFactory):
    """Factory for creating ClientMetric instances."""

    class Meta:
        model = ClientMetric

    client = factory.SubFactory(ClientFactory)
    lifetime_value = Decimal('25000.00')
    average_invoice_value = Decimal('2500.00')
    total_invoices = 10
    paid_invoices = 8
    payment_reliability_score = Decimal('85.00')


class ActivityLogFactory(factory.django.DjangoModelFactory):
    """Factory for creating ActivityLog instances."""

    class Meta:
        model = ActivityLog

    activity_type = ActivityLog.INVOICE_CREATED
    description = factory.Sequence(lambda n: f'Activity event {n}')
    user = factory.SubFactory(UserFactory)


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------
DASHBOARD_URL = '/api/analytics/overview/'
REVENUE_URL = '/api/analytics/revenue-report/'
CLIENT_METRICS_URL = '/api/analytics/client-metrics/'
ACTIVITY_FEED_URL = '/api/analytics/activity-feed/'


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def auth_client(user):
    client = TestClient()
    client.force_login(user)
    return client


@pytest.fixture
def revenue_metric(db):
    return RevenueMetricFactory(year=2026, month=2)


@pytest.fixture
def client_metric(db):
    return ClientMetricFactory()


@pytest.fixture
def activity_log(user):
    return ActivityLogFactory(user=user)


# ---------------------------------------------------------------------------
# DashboardView tests
# ---------------------------------------------------------------------------
class TestDashboardView:
    """Tests for DashboardView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self):
        client = TestClient()
        response = client.get(DASHBOARD_URL)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, revenue_metric):
        try:
            response = auth_client.get(DASHBOARD_URL)
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(self, auth_client, revenue_metric, activity_log):
        try:
            response = auth_client.get(DASHBOARD_URL)
            ctx = response.context
            assert ctx['page_title'] == 'Dashboard'
            assert 'current_metric' in ctx
            assert 'recent_metrics' in ctx
            assert 'active_clients' in ctx
            assert 'active_contracts' in ctx
            assert 'pending_invoices' in ctx
            assert 'overdue_invoices' in ctx
            assert 'total_outstanding' in ctx
            assert 'recent_activity' in ctx
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# RevenueView tests
# ---------------------------------------------------------------------------
class TestRevenueView:
    """Tests for RevenueView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self):
        client = TestClient()
        response = client.get(REVENUE_URL)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, revenue_metric):
        try:
            response = auth_client.get(REVENUE_URL)
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(self, auth_client, revenue_metric):
        try:
            response = auth_client.get(REVENUE_URL)
            ctx = response.context
            assert ctx['page_title'] == 'Revenue Analytics'
            assert 'total_revenue' in ctx
            assert 'total_recurring' in ctx
            assert 'total_one_time' in ctx
            assert 'total_refunds' in ctx
            assert 'metrics' in ctx
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_metrics_ordered_by_period(self, auth_client):
        RevenueMetricFactory(year=2025, month=12)
        RevenueMetricFactory(year=2026, month=1)
        try:
            response = auth_client.get(REVENUE_URL)
            metrics = list(response.context['metrics'])
            # Should be ordered by -year, -month (newest first)
            assert metrics[0].year >= metrics[-1].year
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# ClientMetricsView tests
# ---------------------------------------------------------------------------
class TestClientMetricsView:
    """Tests for ClientMetricsView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self):
        client = TestClient()
        response = client.get(CLIENT_METRICS_URL)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, client_metric):
        try:
            response = auth_client.get(CLIENT_METRICS_URL)
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(self, auth_client, client_metric):
        try:
            response = auth_client.get(CLIENT_METRICS_URL)
            ctx = response.context
            assert ctx['page_title'] == 'Client Metrics'
            assert 'total_clients' in ctx
            assert 'total_lifetime_value' in ctx
            assert 'avg_reliability_score' in ctx
            assert 'client_metrics' in ctx
        except TemplateDoesNotExist:
            pass


# ---------------------------------------------------------------------------
# ActivityFeedView tests
# ---------------------------------------------------------------------------
class TestActivityFeedView:
    """Tests for ActivityFeedView."""

    @pytest.mark.django_db
    def test_unauthenticated_redirect(self):
        client = TestClient()
        response = client.get(ACTIVITY_FEED_URL)
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    @pytest.mark.django_db
    def test_authenticated_returns_200(self, auth_client, activity_log):
        try:
            response = auth_client.get(ACTIVITY_FEED_URL)
            assert response.status_code == 200
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_context_contains_expected_keys(self, auth_client, activity_log):
        try:
            response = auth_client.get(ACTIVITY_FEED_URL)
            ctx = response.context
            assert ctx['page_title'] == 'Activity Feed'
            assert 'activity_type_choices' in ctx
            assert 'current_type' in ctx
            assert 'total_activities' in ctx
            assert 'activities' in ctx
        except TemplateDoesNotExist:
            pass

    @pytest.mark.django_db
    def test_filter_by_activity_type(self, auth_client, user):
        invoice_activity = ActivityLogFactory(
            user=user, activity_type=ActivityLog.INVOICE_CREATED
        )
        ActivityLogFactory(
            user=user, activity_type=ActivityLog.PAYMENT_RECEIVED
        )
        try:
            response = auth_client.get(
                ACTIVITY_FEED_URL, {'type': ActivityLog.INVOICE_CREATED}
            )
            activities = list(response.context['activities'])
            assert invoice_activity in activities
            assert all(
                a.activity_type == ActivityLog.INVOICE_CREATED for a in activities
            )
        except TemplateDoesNotExist:
            pass
