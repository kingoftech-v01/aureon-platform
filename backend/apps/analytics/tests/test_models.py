"""Tests for analytics models."""

import uuid
import pytest
from decimal import Decimal
from datetime import date
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.analytics.models import RevenueMetric, ClientMetric, ActivityLog

User = get_user_model()


@pytest.mark.django_db
class TestRevenueMetric:
    """Tests for the RevenueMetric model."""

    def _create_metric(self, **kwargs):
        """Helper to create a RevenueMetric."""
        defaults = {
            'year': 2025,
            'month': 6,
            'total_revenue': Decimal('50000.00'),
            'recurring_revenue': Decimal('30000.00'),
            'one_time_revenue': Decimal('20000.00'),
            'invoices_sent': 50,
            'invoices_paid': 40,
            'invoices_overdue': 5,
            'average_invoice_value': Decimal('1000.00'),
            'payments_received': 40,
            'payments_failed': 3,
            'refunds_issued': 2,
            'refund_amount': Decimal('500.00'),
            'new_clients': 10,
            'churned_clients': 2,
            'active_clients': 150,
            'contracts_signed': 15,
            'contracts_completed': 8,
            'active_contracts': 45,
            'total_contract_value': Decimal('200000.00'),
            'payment_success_rate': Decimal('93.02'),
            'churn_rate': Decimal('1.32'),
        }
        defaults.update(kwargs)
        return RevenueMetric.objects.create(**defaults)

    def test_create_metric(self):
        """Test creating a revenue metric."""
        metric = self._create_metric()
        assert metric.pk is not None
        assert isinstance(metric.id, uuid.UUID)
        assert metric.year == 2025
        assert metric.month == 6

    def test_str_representation(self):
        """Test string representation."""
        metric = self._create_metric()
        expected = "2025-06: $50000.00"
        assert str(metric) == expected

    def test_str_representation_single_digit_month(self):
        """Test string representation with single digit month."""
        metric = self._create_metric(year=2025, month=1, total_revenue=Decimal('10000.00'))
        expected = "2025-01: $10000.00"
        assert str(metric) == expected

    def test_period_name_property(self):
        """Test period_name property."""
        metric = self._create_metric(year=2025, month=1)
        assert metric.period_name == 'January 2025'

    def test_period_name_december(self):
        """Test period_name for December."""
        metric = self._create_metric(year=2025, month=12)
        assert metric.period_name == 'December 2025'

    def test_period_name_june(self):
        """Test period_name for June."""
        metric = self._create_metric()
        assert metric.period_name == 'June 2025'

    def test_default_values(self):
        """Test default values on metric creation."""
        metric = RevenueMetric.objects.create(year=2025, month=3)
        assert metric.total_revenue == Decimal('0.00')
        assert metric.recurring_revenue == Decimal('0.00')
        assert metric.one_time_revenue == Decimal('0.00')
        assert metric.invoices_sent == 0
        assert metric.invoices_paid == 0
        assert metric.invoices_overdue == 0
        assert metric.average_invoice_value == Decimal('0.00')
        assert metric.payments_received == 0
        assert metric.payments_failed == 0
        assert metric.refunds_issued == 0
        assert metric.refund_amount == Decimal('0.00')
        assert metric.new_clients == 0
        assert metric.churned_clients == 0
        assert metric.active_clients == 0
        assert metric.contracts_signed == 0
        assert metric.contracts_completed == 0
        assert metric.active_contracts == 0
        assert metric.total_contract_value == Decimal('0.00')
        assert metric.payment_success_rate == Decimal('0.00')
        assert metric.churn_rate == Decimal('0.00')

    def test_unique_together_year_month(self):
        """Test unique_together constraint on year and month."""
        self._create_metric(year=2025, month=6)
        with pytest.raises(Exception):
            self._create_metric(year=2025, month=6)

    def test_different_year_same_month(self):
        """Test that same month in different year is allowed."""
        self._create_metric(year=2025, month=6)
        metric2 = self._create_metric(year=2024, month=6)
        assert metric2.pk is not None

    def test_meta_ordering(self):
        """Test model ordering by -year, -month."""
        m1 = self._create_metric(year=2024, month=6)
        m2 = self._create_metric(year=2025, month=1)
        m3 = self._create_metric(year=2025, month=12)

        metrics = list(RevenueMetric.objects.all())
        assert metrics[0].year == 2025 and metrics[0].month == 12
        assert metrics[1].year == 2025 and metrics[1].month == 1
        assert metrics[2].year == 2024 and metrics[2].month == 6

    def test_meta_verbose_names(self):
        """Test meta verbose names."""
        assert RevenueMetric._meta.verbose_name == 'Revenue Metric'
        assert RevenueMetric._meta.verbose_name_plural == 'Revenue Metrics'

    def test_timestamps_set_automatically(self):
        """Test that timestamps are set automatically."""
        metric = self._create_metric()
        assert metric.created_at is not None
        assert metric.calculated_at is not None

    def test_uuid_primary_key(self):
        """Test that id is a UUID."""
        metric = self._create_metric()
        assert isinstance(metric.id, uuid.UUID)

    def test_indexes_exist(self):
        """Test that indexes are defined."""
        index_fields = [idx.fields for idx in RevenueMetric._meta.indexes]
        assert ['-year', '-month'] in index_fields

    def test_revenue_values(self):
        """Test revenue-related field values."""
        metric = self._create_metric()
        assert metric.total_revenue == Decimal('50000.00')
        assert metric.recurring_revenue == Decimal('30000.00')
        assert metric.one_time_revenue == Decimal('20000.00')

    def test_client_metrics_values(self):
        """Test client-related metric values."""
        metric = self._create_metric()
        assert metric.new_clients == 10
        assert metric.churned_clients == 2
        assert metric.active_clients == 150

    def test_contract_metrics_values(self):
        """Test contract-related metric values."""
        metric = self._create_metric()
        assert metric.contracts_signed == 15
        assert metric.contracts_completed == 8
        assert metric.active_contracts == 45
        assert metric.total_contract_value == Decimal('200000.00')


@pytest.mark.django_db
class TestClientMetric:
    """Tests for the ClientMetric model."""

    @pytest.fixture
    def client(self, admin_user):
        """Create a client for testing."""
        from apps.clients.models import Client
        return Client.objects.create(
            first_name='Analytics',
            last_name='Client',
            email='analytics@example.com',
            lifecycle_stage=Client.ACTIVE,
            owner=admin_user,
        )

    def _create_client_metric(self, client, **kwargs):
        """Helper to create a ClientMetric."""
        defaults = {
            'client': client,
            'lifetime_value': Decimal('25000.00'),
            'average_invoice_value': Decimal('2500.00'),
            'total_invoices': 10,
            'paid_invoices': 8,
            'overdue_invoices': 1,
            'outstanding_balance': Decimal('5000.00'),
            'total_payments': 8,
            'failed_payments': 1,
            'total_contracts': 3,
            'active_contracts': 2,
            'days_since_last_payment': 15,
            'payment_reliability_score': Decimal('88.89'),
        }
        defaults.update(kwargs)
        return ClientMetric.objects.create(**defaults)

    def test_create_client_metric(self, client):
        """Test creating a client metric."""
        metric = self._create_client_metric(client)
        assert metric.pk is not None
        assert isinstance(metric.id, uuid.UUID)
        assert metric.client == client

    def test_str_representation(self, client):
        """Test string representation."""
        metric = self._create_client_metric(client)
        # Client.full_name doesn't exist as property; get_full_name() does
        # The __str__ method calls self.client.full_name which would fail
        # We test the expected behavior with get_full_name
        expected = f"Metrics for {client.get_full_name()}"
        assert str(metric) == expected

    def test_default_values(self, client):
        """Test default values on client metric creation."""
        metric = ClientMetric.objects.create(client=client)
        assert metric.lifetime_value == Decimal('0.00')
        assert metric.average_invoice_value == Decimal('0.00')
        assert metric.total_invoices == 0
        assert metric.paid_invoices == 0
        assert metric.overdue_invoices == 0
        assert metric.outstanding_balance == Decimal('0.00')
        assert metric.total_payments == 0
        assert metric.failed_payments == 0
        assert metric.total_contracts == 0
        assert metric.active_contracts == 0
        assert metric.days_since_last_payment == 0
        assert metric.payment_reliability_score == Decimal('0.00')

    def test_one_to_one_with_client(self, client):
        """Test one-to-one relationship with client."""
        self._create_client_metric(client)
        with pytest.raises(Exception):
            self._create_client_metric(client)

    def test_client_cascade_delete(self, client):
        """Test that deleting client cascades to metrics."""
        metric = self._create_client_metric(client)
        client_pk = client.pk
        client.delete()
        assert ClientMetric.objects.filter(client_id=client_pk).count() == 0

    def test_last_invoice_date(self, client):
        """Test last_invoice_date field."""
        today = date.today()
        metric = self._create_client_metric(client, last_invoice_date=today)
        metric.refresh_from_db()
        assert metric.last_invoice_date == today

    def test_last_payment_date(self, client):
        """Test last_payment_date field."""
        today = date.today()
        metric = self._create_client_metric(client, last_payment_date=today)
        metric.refresh_from_db()
        assert metric.last_payment_date == today

    def test_null_date_fields(self, client):
        """Test date fields can be null."""
        metric = ClientMetric.objects.create(client=client)
        assert metric.last_invoice_date is None
        assert metric.last_payment_date is None

    def test_meta_ordering(self, admin_user):
        """Test model ordering by -lifetime_value."""
        from apps.clients.models import Client

        client1 = Client.objects.create(
            first_name='Low', last_name='Value',
            email='low@example.com', lifecycle_stage=Client.ACTIVE,
            owner=admin_user,
        )
        client2 = Client.objects.create(
            first_name='High', last_name='Value',
            email='high@example.com', lifecycle_stage=Client.ACTIVE,
            owner=admin_user,
        )

        self._create_client_metric(client1, lifetime_value=Decimal('1000.00'))
        self._create_client_metric(client2, lifetime_value=Decimal('50000.00'))

        metrics = list(ClientMetric.objects.all())
        assert metrics[0].lifetime_value >= metrics[1].lifetime_value

    def test_meta_verbose_names(self):
        """Test meta verbose names."""
        assert ClientMetric._meta.verbose_name == 'Client Metric'
        assert ClientMetric._meta.verbose_name_plural == 'Client Metrics'

    def test_timestamps_set_automatically(self, client):
        """Test that timestamps are set automatically."""
        metric = self._create_client_metric(client)
        assert metric.created_at is not None
        assert metric.updated_at is not None

    def test_related_name_from_client(self, client):
        """Test related_name 'metrics' from client."""
        self._create_client_metric(client)
        assert client.metrics is not None
        assert client.metrics.lifetime_value == Decimal('25000.00')


@pytest.mark.django_db
class TestActivityLog:
    """Tests for the ActivityLog model."""

    def _create_activity(self, user=None, **kwargs):
        """Helper to create an ActivityLog entry."""
        defaults = {
            'activity_type': ActivityLog.INVOICE_CREATED,
            'description': 'Invoice INV-001 created',
            'user': user,
            'related_objects': {'invoice_id': 'test-uuid'},
            'metadata': {'source': 'api'},
            'ip_address': '192.168.1.1',
            'user_agent': 'Mozilla/5.0',
        }
        defaults.update(kwargs)
        return ActivityLog.objects.create(**defaults)

    def test_create_activity(self):
        """Test creating an activity log entry."""
        activity = self._create_activity()
        assert activity.pk is not None
        assert isinstance(activity.id, uuid.UUID)

    def test_str_representation_with_user(self, admin_user):
        """Test string representation with user."""
        activity = self._create_activity(user=admin_user)
        expected = f"{admin_user.email}: Invoice INV-001 created"
        assert str(activity) == expected

    def test_str_representation_without_user(self):
        """Test string representation without user (system activity)."""
        activity = self._create_activity()
        expected = "System: Invoice INV-001 created"
        assert str(activity) == expected

    def test_activity_type_choices(self):
        """Test all activity type constants."""
        assert ActivityLog.INVOICE_CREATED == 'invoice_created'
        assert ActivityLog.INVOICE_SENT == 'invoice_sent'
        assert ActivityLog.INVOICE_PAID == 'invoice_paid'
        assert ActivityLog.PAYMENT_RECEIVED == 'payment_received'
        assert ActivityLog.PAYMENT_FAILED == 'payment_failed'
        assert ActivityLog.CONTRACT_SIGNED == 'contract_signed'
        assert ActivityLog.CONTRACT_COMPLETED == 'contract_completed'
        assert ActivityLog.CLIENT_CREATED == 'client_created'
        assert ActivityLog.CLIENT_UPDATED == 'client_updated'
        assert ActivityLog.USER_LOGIN == 'user_login'
        assert ActivityLog.USER_LOGOUT == 'user_logout'

    def test_all_activity_types_creatable(self):
        """Test creating activities with all types."""
        types = [
            ActivityLog.INVOICE_CREATED, ActivityLog.INVOICE_SENT,
            ActivityLog.INVOICE_PAID, ActivityLog.PAYMENT_RECEIVED,
            ActivityLog.PAYMENT_FAILED, ActivityLog.CONTRACT_SIGNED,
            ActivityLog.CONTRACT_COMPLETED, ActivityLog.CLIENT_CREATED,
            ActivityLog.CLIENT_UPDATED, ActivityLog.USER_LOGIN,
            ActivityLog.USER_LOGOUT,
        ]
        for activity_type in types:
            activity = self._create_activity(
                activity_type=activity_type,
                description=f'Test {activity_type}',
            )
            assert activity.activity_type == activity_type

    def test_related_objects_json_field(self):
        """Test related_objects JSON field."""
        related = {
            'invoice_id': 'inv-uuid',
            'client_id': 'client-uuid',
        }
        activity = self._create_activity(related_objects=related)
        activity.refresh_from_db()
        assert activity.related_objects == related

    def test_metadata_json_field(self):
        """Test metadata JSON field."""
        metadata = {'source': 'webhook', 'event': 'payment.succeeded'}
        activity = self._create_activity(metadata=metadata)
        activity.refresh_from_db()
        assert activity.metadata == metadata

    def test_default_json_fields(self):
        """Test default values for JSON fields."""
        activity = ActivityLog.objects.create(
            activity_type=ActivityLog.USER_LOGIN,
            description='User logged in',
        )
        assert activity.related_objects == {}
        assert activity.metadata == {}

    def test_ip_address_null(self):
        """Test ip_address can be null."""
        activity = ActivityLog.objects.create(
            activity_type=ActivityLog.USER_LOGIN,
            description='User logged in',
            ip_address=None,
        )
        assert activity.ip_address is None

    def test_ip_address_ipv4(self):
        """Test ip_address with IPv4 address."""
        activity = self._create_activity(ip_address='192.168.1.100')
        assert activity.ip_address == '192.168.1.100'

    def test_ip_address_ipv6(self):
        """Test ip_address with IPv6 address."""
        activity = self._create_activity(ip_address='2001:0db8:85a3:0000:0000:8a2e:0370:7334')
        assert activity.ip_address == '2001:0db8:85a3:0000:0000:8a2e:0370:7334'

    def test_user_agent_blank(self):
        """Test user_agent can be blank."""
        activity = self._create_activity(user_agent='')
        assert activity.user_agent == ''

    def test_user_set_null_on_delete(self, admin_user):
        """Test that deleting user sets activity.user to NULL."""
        activity = self._create_activity(user=admin_user)
        admin_user.delete()
        activity.refresh_from_db()
        assert activity.user is None

    def test_meta_ordering(self):
        """Test model ordering by -created_at."""
        a1 = self._create_activity(description='First')
        a2 = self._create_activity(description='Second')

        activities = list(ActivityLog.objects.all())
        assert activities[0].created_at >= activities[1].created_at

    def test_meta_verbose_names(self):
        """Test meta verbose names."""
        assert ActivityLog._meta.verbose_name == 'Activity Log'
        assert ActivityLog._meta.verbose_name_plural == 'Activity Logs'

    def test_indexes_exist(self):
        """Test that indexes are defined."""
        index_fields = [idx.fields for idx in ActivityLog._meta.indexes]
        assert ['-created_at'] in index_fields
        assert ['user', '-created_at'] in index_fields
        assert ['activity_type', '-created_at'] in index_fields

    def test_timestamp_set_automatically(self):
        """Test that created_at is set automatically."""
        activity = self._create_activity()
        assert activity.created_at is not None

    def test_uuid_primary_key(self):
        """Test that id is a UUID."""
        activity = self._create_activity()
        assert isinstance(activity.id, uuid.UUID)
