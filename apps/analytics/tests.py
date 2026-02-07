"""
Comprehensive unit tests for analytics app.

Tests metric calculations (RevenueMetricsCalculator, ClientMetricsCalculator, etc.).
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.utils import timezone

from .models import RevenueMetric, ClientMetric, ActivityLog
from .services import (
    RevenueMetricsCalculator,
    ClientMetricsCalculator,
    ActivityLogger,
    DashboardDataService
)


@pytest.mark.django_db
class RevenueMetricsCalculatorTests(TestCase):
    """Test RevenueMetricsCalculator service."""

    def setUp(self):
        """Set up test data."""
        from apps.tenants.models import Tenant
        from apps.clients.models import Client
        from apps.invoicing.models import Invoice
        from apps.payments.models import Payment
        from apps.contracts.models import Contract

        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            slug='test-tenant'
        )

        self.client = Client.objects.create(
            tenant=self.tenant,
            email='client@example.com',
            first_name='Test',
            last_name='Client',
            lifecycle_stage=Client.ACTIVE
        )

        # Set up test date
        self.test_year = 2025
        self.test_month = 1
        self.start_date = date(2025, 1, 1)
        self.end_date = date(2025, 2, 1)

    def test_calculate_month_metrics_empty(self):
        """Test calculating metrics for a month with no data."""
        metric = RevenueMetricsCalculator.calculate_month_metrics(
            year=self.test_year,
            month=self.test_month
        )

        self.assertIsNotNone(metric)
        self.assertEqual(metric.year, self.test_year)
        self.assertEqual(metric.month, self.test_month)
        self.assertEqual(metric.total_revenue, Decimal('0.00'))
        self.assertEqual(metric.invoices_sent, 0)
        self.assertEqual(metric.payments_received, 0)

    def test_calculate_invoice_metrics(self):
        """Test calculating invoice-related metrics."""
        from apps.invoicing.models import Invoice

        # Create invoices for the test month
        for i in range(5):
            Invoice.objects.create(
                tenant=self.tenant,
                client=self.client,
                invoice_number=f'INV-{i:03d}',
                issue_date=self.start_date + timedelta(days=i),
                due_date=self.start_date + timedelta(days=30),
                subtotal=Decimal('100.00'),
                tax=Decimal('10.00'),
                total=Decimal('110.00'),
                currency='USD',
                status=Invoice.SENT if i < 3 else Invoice.PAID
            )

        metric = RevenueMetricsCalculator.calculate_month_metrics(
            year=self.test_year,
            month=self.test_month
        )

        self.assertEqual(metric.invoices_sent, 5)
        self.assertEqual(metric.invoices_paid, 2)
        self.assertEqual(metric.average_invoice_value, Decimal('110.00'))

    def test_calculate_payment_metrics(self):
        """Test calculating payment-related metrics."""
        from apps.payments.models import Payment

        # Create successful payments
        for i in range(3):
            Payment.objects.create(
                client=self.client,
                amount=Decimal('100.00'),
                currency='USD',
                status=Payment.SUCCESS,
                payment_method=Payment.CARD,
                payment_date=self.start_date + timedelta(days=i)
            )

        # Create failed payment
        Payment.objects.create(
            client=self.client,
            amount=Decimal('50.00'),
            currency='USD',
            status=Payment.FAILED,
            payment_method=Payment.CARD,
            payment_date=self.start_date + timedelta(days=5)
        )

        metric = RevenueMetricsCalculator.calculate_month_metrics(
            year=self.test_year,
            month=self.test_month
        )

        self.assertEqual(metric.payments_received, 3)
        self.assertEqual(metric.payments_failed, 1)
        self.assertEqual(metric.total_revenue, Decimal('300.00'))
        self.assertEqual(metric.payment_success_rate, Decimal('75.00'))

    def test_calculate_refund_metrics(self):
        """Test calculating refund metrics."""
        from apps.payments.models import Payment

        # Create refunded payment
        Payment.objects.create(
            client=self.client,
            amount=Decimal('200.00'),
            currency='USD',
            status=Payment.REFUNDED,
            payment_method=Payment.CARD,
            payment_date=self.start_date,
            refunded_amount=Decimal('100.00')
        )

        metric = RevenueMetricsCalculator.calculate_month_metrics(
            year=self.test_year,
            month=self.test_month
        )

        self.assertEqual(metric.refunds_issued, 1)
        self.assertEqual(metric.refund_amount, Decimal('100.00'))

    def test_calculate_contract_metrics(self):
        """Test calculating contract-related metrics."""
        from apps.contracts.models import Contract

        # Create contracts
        for i in range(3):
            contract = Contract.objects.create(
                tenant=self.tenant,
                client=self.client,
                title=f'Contract {i}',
                contract_type=Contract.PROJECT,
                status=Contract.ACTIVE,
                start_date=self.start_date,
                total_value=Decimal('1000.00'),
                currency='USD'
            )
            # Set signature date
            contract.signature_date = self.start_date + timedelta(days=i)
            contract.save()

        metric = RevenueMetricsCalculator.calculate_month_metrics(
            year=self.test_year,
            month=self.test_month
        )

        self.assertEqual(metric.contracts_signed, 3)
        self.assertEqual(metric.active_contracts, 3)
        self.assertEqual(metric.total_contract_value, Decimal('3000.00'))

    def test_calculate_recurring_revenue_metrics(self):
        """Test calculating recurring revenue from retainer contracts."""
        from apps.contracts.models import Contract

        # Create retainer contracts
        for i in range(2):
            Contract.objects.create(
                tenant=self.tenant,
                client=self.client,
                title=f'Retainer {i}',
                contract_type=Contract.RETAINER,
                status=Contract.ACTIVE,
                start_date=self.start_date,
                total_value=Decimal('5000.00'),
                monthly_rate=Decimal('500.00'),
                currency='USD'
            )

        metric = RevenueMetricsCalculator.calculate_month_metrics(
            year=self.test_year,
            month=self.test_month
        )

        self.assertEqual(metric.recurring_revenue, Decimal('1000.00'))

    def test_calculate_client_metrics(self):
        """Test calculating client-related metrics."""
        from apps.clients.models import Client

        # Create new clients
        for i in range(3):
            Client.objects.create(
                tenant=self.tenant,
                email=f'new{i}@example.com',
                first_name='New',
                last_name=f'Client {i}',
                lifecycle_stage=Client.ACTIVE
            )

        # Create churned client
        churned = Client.objects.create(
            tenant=self.tenant,
            email='churned@example.com',
            first_name='Churned',
            last_name='Client',
            lifecycle_stage=Client.CHURNED
        )

        metric = RevenueMetricsCalculator.calculate_month_metrics(
            year=self.test_year,
            month=self.test_month
        )

        self.assertEqual(metric.new_clients, 3)
        # active_clients includes all ACTIVE clients (including the one from setUp)
        self.assertGreaterEqual(metric.active_clients, 3)

    def test_calculate_churn_rate(self):
        """Test churn rate calculation."""
        from apps.clients.models import Client

        # Create active clients
        for i in range(10):
            Client.objects.create(
                tenant=self.tenant,
                email=f'active{i}@example.com',
                first_name='Active',
                last_name=f'Client {i}',
                lifecycle_stage=Client.ACTIVE
            )

        # Create churned clients
        for i in range(2):
            Client.objects.create(
                tenant=self.tenant,
                email=f'churned{i}@example.com',
                first_name='Churned',
                last_name=f'Client {i}',
                lifecycle_stage=Client.CHURNED
            )

        metric = RevenueMetricsCalculator.calculate_month_metrics(
            year=self.test_year,
            month=self.test_month
        )

        # Churn rate calculation includes the client from setUp
        self.assertGreater(metric.churn_rate, Decimal('0.00'))

    def test_metric_updates_existing_record(self):
        """Test that calculating metrics updates existing record."""
        # First calculation
        metric1 = RevenueMetricsCalculator.calculate_month_metrics(
            year=self.test_year,
            month=self.test_month
        )
        metric1_id = metric1.id

        # Add new data
        from apps.payments.models import Payment
        Payment.objects.create(
            client=self.client,
            amount=Decimal('500.00'),
            currency='USD',
            status=Payment.SUCCESS,
            payment_method=Payment.CARD,
            payment_date=self.start_date
        )

        # Second calculation
        metric2 = RevenueMetricsCalculator.calculate_month_metrics(
            year=self.test_year,
            month=self.test_month
        )

        # Should update same record
        self.assertEqual(metric1_id, metric2.id)
        self.assertEqual(metric2.total_revenue, Decimal('500.00'))


@pytest.mark.django_db
class ClientMetricsCalculatorTests(TestCase):
    """Test ClientMetricsCalculator service."""

    def setUp(self):
        """Set up test data."""
        from apps.tenants.models import Tenant
        from apps.clients.models import Client

        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            slug='test-tenant'
        )

        self.client = Client.objects.create(
            tenant=self.tenant,
            email='client@example.com',
            first_name='Test',
            last_name='Client'
        )

    def test_calculate_client_metrics_empty(self):
        """Test calculating metrics for client with no data."""
        metric = ClientMetricsCalculator.calculate_client_metrics(self.client)

        self.assertIsNotNone(metric)
        self.assertEqual(metric.client, self.client)
        self.assertEqual(metric.lifetime_value, Decimal('0.00'))
        self.assertEqual(metric.total_invoices, 0)
        self.assertEqual(metric.total_payments, 0)

    def test_calculate_invoice_metrics(self):
        """Test calculating invoice metrics for client."""
        from apps.invoicing.models import Invoice

        # Create invoices
        for i in range(5):
            Invoice.objects.create(
                tenant=self.tenant,
                client=self.client,
                invoice_number=f'INV-{i:03d}',
                issue_date=date.today() - timedelta(days=30),
                due_date=date.today() - timedelta(days=i),
                total=Decimal('200.00'),
                balance_due=Decimal('100.00') if i < 2 else Decimal('0.00'),
                currency='USD',
                status=Invoice.PAID if i >= 2 else Invoice.SENT
            )

        metric = ClientMetricsCalculator.calculate_client_metrics(self.client)

        self.assertEqual(metric.total_invoices, 5)
        self.assertEqual(metric.paid_invoices, 3)
        self.assertEqual(metric.average_invoice_value, Decimal('200.00'))
        self.assertEqual(metric.outstanding_balance, Decimal('200.00'))

    def test_calculate_overdue_invoices(self):
        """Test calculating overdue invoices."""
        from apps.invoicing.models import Invoice

        # Create overdue invoice
        Invoice.objects.create(
            tenant=self.tenant,
            client=self.client,
            invoice_number='INV-OVERDUE',
            issue_date=date.today() - timedelta(days=60),
            due_date=date.today() - timedelta(days=30),
            total=Decimal('500.00'),
            currency='USD',
            status=Invoice.SENT
        )

        metric = ClientMetricsCalculator.calculate_client_metrics(self.client)

        self.assertEqual(metric.overdue_invoices, 1)

    def test_calculate_payment_metrics(self):
        """Test calculating payment metrics for client."""
        from apps.payments.models import Payment

        # Create successful payments
        for i in range(4):
            Payment.objects.create(
                client=self.client,
                amount=Decimal('250.00'),
                currency='USD',
                status=Payment.SUCCESS,
                payment_method=Payment.CARD,
                payment_date=date.today() - timedelta(days=i)
            )

        # Create failed payment
        Payment.objects.create(
            client=self.client,
            amount=Decimal('100.00'),
            currency='USD',
            status=Payment.FAILED,
            payment_method=Payment.CARD,
            payment_date=date.today()
        )

        metric = ClientMetricsCalculator.calculate_client_metrics(self.client)

        self.assertEqual(metric.total_payments, 4)
        self.assertEqual(metric.failed_payments, 1)
        self.assertEqual(metric.lifetime_value, Decimal('1000.00'))

    def test_calculate_last_payment_date(self):
        """Test calculating last payment date."""
        from apps.payments.models import Payment

        last_payment_date = date.today() - timedelta(days=5)

        Payment.objects.create(
            client=self.client,
            amount=Decimal('100.00'),
            currency='USD',
            status=Payment.SUCCESS,
            payment_method=Payment.CARD,
            payment_date=last_payment_date
        )

        metric = ClientMetricsCalculator.calculate_client_metrics(self.client)

        self.assertEqual(metric.last_payment_date, last_payment_date)
        self.assertEqual(metric.days_since_last_payment, 5)

    def test_calculate_contract_metrics(self):
        """Test calculating contract metrics for client."""
        from apps.contracts.models import Contract

        # Create active contracts
        for i in range(3):
            Contract.objects.create(
                tenant=self.tenant,
                client=self.client,
                title=f'Contract {i}',
                contract_type=Contract.PROJECT,
                status=Contract.ACTIVE,
                start_date=date.today(),
                total_value=Decimal('5000.00'),
                currency='USD'
            )

        # Create completed contract
        Contract.objects.create(
            tenant=self.tenant,
            client=self.client,
            title='Completed Contract',
            contract_type=Contract.PROJECT,
            status=Contract.COMPLETED,
            start_date=date.today() - timedelta(days=90),
            total_value=Decimal('3000.00'),
            currency='USD'
        )

        metric = ClientMetricsCalculator.calculate_client_metrics(self.client)

        self.assertEqual(metric.total_contracts, 4)
        self.assertEqual(metric.active_contracts, 3)

    def test_payment_reliability_score_perfect(self):
        """Test payment reliability score with perfect payment history."""
        from apps.payments.models import Payment

        # Create all successful payments
        for i in range(10):
            Payment.objects.create(
                client=self.client,
                amount=Decimal('100.00'),
                currency='USD',
                status=Payment.SUCCESS,
                payment_method=Payment.CARD,
                payment_date=date.today()
            )

        metric = ClientMetricsCalculator.calculate_client_metrics(self.client)

        self.assertEqual(metric.payment_reliability_score, Decimal('100.00'))

    def test_payment_reliability_score_with_failures(self):
        """Test payment reliability score with some failed payments."""
        from apps.payments.models import Payment

        # Create mix of successful and failed payments
        for i in range(8):
            Payment.objects.create(
                client=self.client,
                amount=Decimal('100.00'),
                currency='USD',
                status=Payment.SUCCESS,
                payment_method=Payment.CARD,
                payment_date=date.today()
            )

        for i in range(2):
            Payment.objects.create(
                client=self.client,
                amount=Decimal('100.00'),
                currency='USD',
                status=Payment.FAILED,
                payment_method=Payment.CARD,
                payment_date=date.today()
            )

        metric = ClientMetricsCalculator.calculate_client_metrics(self.client)

        # 80% success rate
        self.assertEqual(metric.payment_reliability_score, Decimal('80.00'))

    def test_payment_reliability_score_with_overdue_penalty(self):
        """Test payment reliability score with overdue invoice penalty."""
        from apps.payments.models import Payment
        from apps.invoicing.models import Invoice

        # Create successful payments
        for i in range(10):
            Payment.objects.create(
                client=self.client,
                amount=Decimal('100.00'),
                currency='USD',
                status=Payment.SUCCESS,
                payment_method=Payment.CARD,
                payment_date=date.today()
            )

        # Create overdue invoices (penalty of 5 points each)
        for i in range(3):
            Invoice.objects.create(
                tenant=self.tenant,
                client=self.client,
                invoice_number=f'INV-OVERDUE-{i}',
                issue_date=date.today() - timedelta(days=60),
                due_date=date.today() - timedelta(days=30),
                total=Decimal('500.00'),
                currency='USD',
                status=Invoice.SENT
            )

        metric = ClientMetricsCalculator.calculate_client_metrics(self.client)

        # 100% payment success - 15 points penalty = 85
        self.assertEqual(metric.payment_reliability_score, Decimal('85.00'))

    def test_metric_updates_existing_record(self):
        """Test that calculating metrics updates existing record."""
        # First calculation
        metric1 = ClientMetricsCalculator.calculate_client_metrics(self.client)
        metric1_id = metric1.id

        # Second calculation
        metric2 = ClientMetricsCalculator.calculate_client_metrics(self.client)

        # Should update same record
        self.assertEqual(metric1_id, metric2.id)


class ActivityLoggerTests(TestCase):
    """Test ActivityLogger service."""

    def setUp(self):
        """Set up test data."""
        from apps.accounts.models import User

        self.user = User.objects.create_user(
            username='test',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_log_activity_basic(self):
        """Test logging basic activity."""
        activity = ActivityLogger.log_activity(
            activity_type=ActivityLog.INVOICE_CREATED,
            description='Invoice INV-001 created',
            user=self.user
        )

        self.assertIsNotNone(activity)
        self.assertEqual(activity.activity_type, ActivityLog.INVOICE_CREATED)
        self.assertEqual(activity.description, 'Invoice INV-001 created')
        self.assertEqual(activity.user, self.user)

    def test_log_activity_with_related_objects(self):
        """Test logging activity with related objects."""
        related_objects = {
            'invoice_id': 'inv_123',
            'client_id': 'client_456'
        }

        activity = ActivityLogger.log_activity(
            activity_type=ActivityLog.INVOICE_SENT,
            description='Invoice sent to client',
            user=self.user,
            related_objects=related_objects
        )

        self.assertEqual(activity.related_objects, related_objects)

    def test_log_activity_with_metadata(self):
        """Test logging activity with metadata."""
        metadata = {
            'amount': '500.00',
            'currency': 'USD',
            'payment_method': 'card'
        }

        activity = ActivityLogger.log_activity(
            activity_type=ActivityLog.PAYMENT_RECEIVED,
            description='Payment received',
            user=self.user,
            metadata=metadata
        )

        self.assertEqual(activity.metadata, metadata)

    def test_log_activity_with_request_info(self):
        """Test logging activity with HTTP request information."""
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0'

        activity = ActivityLogger.log_activity(
            activity_type=ActivityLog.USER_LOGIN,
            description='User logged in',
            user=self.user,
            request=request
        )

        self.assertEqual(activity.ip_address, '192.168.1.1')
        self.assertEqual(activity.user_agent, 'Mozilla/5.0')

    def test_log_activity_without_user(self):
        """Test logging system activity without user."""
        activity = ActivityLogger.log_activity(
            activity_type=ActivityLog.INVOICE_PAID,
            description='Invoice automatically marked as paid'
        )

        self.assertIsNone(activity.user)
        self.assertEqual(activity.description, 'Invoice automatically marked as paid')


@pytest.mark.django_db
class DashboardDataServiceTests(TestCase):
    """Test DashboardDataService functionality."""

    def setUp(self):
        """Set up test data."""
        from apps.tenants.models import Tenant
        from apps.clients.models import Client

        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            slug='test-tenant'
        )

        self.client = Client.objects.create(
            tenant=self.tenant,
            email='client@example.com',
            first_name='Test',
            last_name='Client',
            lifecycle_stage=Client.ACTIVE
        )

    def test_get_dashboard_summary_empty(self):
        """Test getting dashboard summary with no data."""
        summary = DashboardDataService.get_dashboard_summary()

        self.assertIsNotNone(summary)
        self.assertIn('total_revenue', summary)
        self.assertIn('mrr', summary)
        self.assertIn('active_clients', summary)
        self.assertIn('revenue_trend', summary)
        self.assertIn('top_clients', summary)
        self.assertIn('recent_activities', summary)

    def test_get_dashboard_summary_with_data(self):
        """Test getting dashboard summary with actual data."""
        from apps.payments.models import Payment
        from apps.invoicing.models import Invoice

        # Create current month metric
        current_month = timezone.now().month
        current_year = timezone.now().year

        metric = RevenueMetric.objects.create(
            year=current_year,
            month=current_month,
            total_revenue=Decimal('5000.00'),
            recurring_revenue=Decimal('2000.00'),
            active_clients=10,
            active_contracts=15
        )

        # Create invoices
        Invoice.objects.create(
            tenant=self.tenant,
            client=self.client,
            invoice_number='INV-001',
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            total=Decimal('500.00'),
            currency='USD',
            status=Invoice.SENT
        )

        summary = DashboardDataService.get_dashboard_summary()

        self.assertEqual(summary['total_revenue'], 5000.00)
        self.assertEqual(summary['mrr'], 2000.00)
        self.assertEqual(summary['active_clients'], 10)
        self.assertEqual(summary['pending_invoices'], 1)

    def test_get_dashboard_revenue_trend(self):
        """Test revenue trend data in dashboard."""
        # Create metrics for last 6 months
        current_date = timezone.now()
        for i in range(6, 0, -1):
            month_date = current_date - timedelta(days=30 * i)
            RevenueMetric.objects.create(
                year=month_date.year,
                month=month_date.month,
                total_revenue=Decimal(f'{i * 1000}.00')
            )

        summary = DashboardDataService.get_dashboard_summary()

        self.assertEqual(len(summary['revenue_trend']), 6)
        # Verify revenue values
        for item in summary['revenue_trend']:
            self.assertIn('month', item)
            self.assertIn('revenue', item)

    def test_get_dashboard_top_clients(self):
        """Test top clients data in dashboard."""
        from apps.clients.models import Client

        # Create clients with metrics
        for i in range(7):
            client = Client.objects.create(
                tenant=self.tenant,
                email=f'client{i}@example.com',
                first_name=f'Client',
                last_name=f'{i}'
            )
            ClientMetric.objects.create(
                client=client,
                lifetime_value=Decimal(f'{(i + 1) * 1000}.00'),
                outstanding_balance=Decimal(f'{(i + 1) * 100}.00')
            )

        summary = DashboardDataService.get_dashboard_summary()

        # Should return top 5 clients
        self.assertEqual(len(summary['top_clients']), 5)
        # Verify first client has highest revenue
        self.assertGreaterEqual(
            summary['top_clients'][0]['revenue'],
            summary['top_clients'][1]['revenue']
        )

    def test_get_dashboard_recent_activities(self):
        """Test recent activities in dashboard."""
        from apps.accounts.models import User

        user = User.objects.create_user(
            username='test',
            email='test@example.com',
            password='testpass123'
        )

        # Create activities
        for i in range(15):
            ActivityLog.objects.create(
                activity_type=ActivityLog.INVOICE_CREATED,
                description=f'Invoice {i} created',
                user=user
            )

        summary = DashboardDataService.get_dashboard_summary()

        # Should return 10 most recent activities
        self.assertEqual(len(summary['recent_activities']), 10)


class RevenueMetricModelTests(TestCase):
    """Test RevenueMetric model."""

    def test_revenue_metric_creation(self):
        """Test creating revenue metric."""
        metric = RevenueMetric.objects.create(
            year=2025,
            month=1,
            total_revenue=Decimal('10000.00'),
            recurring_revenue=Decimal('5000.00')
        )

        self.assertEqual(metric.year, 2025)
        self.assertEqual(metric.month, 1)
        self.assertEqual(metric.total_revenue, Decimal('10000.00'))

    def test_period_name_property(self):
        """Test period_name property."""
        metric = RevenueMetric.objects.create(
            year=2025,
            month=6
        )

        self.assertEqual(metric.period_name, 'June 2025')

    def test_unique_together_constraint(self):
        """Test unique_together constraint on year/month."""
        RevenueMetric.objects.create(year=2025, month=1)

        with self.assertRaises(Exception):
            RevenueMetric.objects.create(year=2025, month=1)


class ClientMetricModelTests(TestCase):
    """Test ClientMetric model."""

    def setUp(self):
        """Set up test data."""
        from apps.tenants.models import Tenant
        from apps.clients.models import Client

        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            slug='test-tenant'
        )

        self.client = Client.objects.create(
            tenant=self.tenant,
            email='client@example.com',
            first_name='Test',
            last_name='Client'
        )

    def test_client_metric_creation(self):
        """Test creating client metric."""
        metric = ClientMetric.objects.create(
            client=self.client,
            lifetime_value=Decimal('15000.00'),
            total_invoices=20,
            paid_invoices=18
        )

        self.assertEqual(metric.client, self.client)
        self.assertEqual(metric.lifetime_value, Decimal('15000.00'))

    def test_one_to_one_relationship(self):
        """Test one-to-one relationship with client."""
        ClientMetric.objects.create(client=self.client)

        with self.assertRaises(Exception):
            ClientMetric.objects.create(client=self.client)
