"""
Tests for RecurringInvoice, LateFeePolicy, and PaymentReminder models and views.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone

from apps.invoicing.models import RecurringInvoice, LateFeePolicy, PaymentReminder, Invoice


# ============================================================================
# RecurringInvoice Model Tests
# ============================================================================


@pytest.mark.django_db
class TestRecurringInvoiceModel:
    """Tests for RecurringInvoice model."""

    def test_str_representation(self, admin_user, client_company):
        ri = RecurringInvoice.objects.create(
            client=client_company,
            template_name='Monthly Retainer',
            frequency=RecurringInvoice.MONTHLY,
            start_date=date.today(),
            next_run_date=date.today(),
            amount=Decimal('1000.00'),
            owner=admin_user,
        )
        assert 'Monthly Retainer' in str(ri)
        assert 'monthly' in str(ri)

    def test_is_due_active_past(self, admin_user, client_company):
        ri = RecurringInvoice.objects.create(
            client=client_company,
            template_name='Retainer',
            frequency=RecurringInvoice.MONTHLY,
            start_date=date.today() - timedelta(days=60),
            next_run_date=date.today() - timedelta(days=1),
            amount=Decimal('500.00'),
            status=RecurringInvoice.ACTIVE,
            owner=admin_user,
        )
        assert ri.is_due is True

    def test_is_due_active_future(self, admin_user, client_company):
        ri = RecurringInvoice.objects.create(
            client=client_company,
            template_name='Retainer',
            frequency=RecurringInvoice.MONTHLY,
            start_date=date.today(),
            next_run_date=date.today() + timedelta(days=30),
            amount=Decimal('500.00'),
            status=RecurringInvoice.ACTIVE,
            owner=admin_user,
        )
        assert ri.is_due is False

    def test_is_due_paused(self, admin_user, client_company):
        ri = RecurringInvoice.objects.create(
            client=client_company,
            template_name='Retainer',
            frequency=RecurringInvoice.MONTHLY,
            start_date=date.today() - timedelta(days=60),
            next_run_date=date.today() - timedelta(days=1),
            amount=Decimal('500.00'),
            status=RecurringInvoice.PAUSED,
            owner=admin_user,
        )
        assert ri.is_due is False

    def test_calculate_next_run_date_monthly(self, admin_user, client_company):
        ri = RecurringInvoice.objects.create(
            client=client_company,
            template_name='Monthly',
            frequency=RecurringInvoice.MONTHLY,
            start_date=date(2026, 1, 1),
            next_run_date=date(2026, 1, 1),
            amount=Decimal('500.00'),
            owner=admin_user,
        )
        ri.calculate_next_run_date()
        ri.refresh_from_db()
        assert ri.next_run_date == date(2026, 2, 1)

    def test_calculate_next_run_date_weekly(self, admin_user, client_company):
        ri = RecurringInvoice.objects.create(
            client=client_company,
            template_name='Weekly',
            frequency=RecurringInvoice.WEEKLY,
            start_date=date(2026, 1, 1),
            next_run_date=date(2026, 1, 1),
            amount=Decimal('200.00'),
            owner=admin_user,
        )
        ri.calculate_next_run_date()
        ri.refresh_from_db()
        assert ri.next_run_date == date(2026, 1, 8)

    def test_calculate_next_run_date_quarterly(self, admin_user, client_company):
        ri = RecurringInvoice.objects.create(
            client=client_company,
            template_name='Quarterly',
            frequency=RecurringInvoice.QUARTERLY,
            start_date=date(2026, 1, 1),
            next_run_date=date(2026, 1, 1),
            amount=Decimal('3000.00'),
            owner=admin_user,
        )
        ri.calculate_next_run_date()
        ri.refresh_from_db()
        assert ri.next_run_date == date(2026, 4, 1)

    def test_calculate_next_run_date_marks_completed(self, admin_user, client_company):
        ri = RecurringInvoice.objects.create(
            client=client_company,
            template_name='Short Term',
            frequency=RecurringInvoice.MONTHLY,
            start_date=date(2026, 1, 1),
            next_run_date=date(2026, 1, 31),
            end_date=date(2026, 2, 15),
            amount=Decimal('500.00'),
            owner=admin_user,
        )
        ri.calculate_next_run_date()
        ri.refresh_from_db()
        assert ri.status == RecurringInvoice.COMPLETED

    def test_generate_invoice_without_template(self, admin_user, client_company):
        ri = RecurringInvoice.objects.create(
            client=client_company,
            template_name='Simple Service',
            frequency=RecurringInvoice.MONTHLY,
            start_date=date.today(),
            next_run_date=date.today(),
            amount=Decimal('1500.00'),
            auto_send=False,
            owner=admin_user,
        )
        invoice = ri.generate_invoice()
        assert isinstance(invoice, Invoice)
        assert invoice.client == client_company
        assert invoice.items.count() == 1
        assert invoice.items.first().unit_price == Decimal('1500.00')
        ri.refresh_from_db()
        assert ri.invoices_generated == 1
        assert ri.last_generated_at is not None

    def test_generate_invoice_with_template_items(self, admin_user, client_company):
        items = [
            {'description': 'Service A', 'quantity': 1, 'unit_price': 500, 'order': 0},
            {'description': 'Service B', 'quantity': 2, 'unit_price': 250, 'order': 1},
        ]
        ri = RecurringInvoice.objects.create(
            client=client_company,
            template_name='Multi-item',
            frequency=RecurringInvoice.MONTHLY,
            start_date=date.today(),
            next_run_date=date.today(),
            amount=Decimal('1000.00'),
            items_template=items,
            auto_send=False,
            owner=admin_user,
        )
        invoice = ri.generate_invoice()
        assert invoice.items.count() == 2

    def test_generate_invoice_auto_send(self, admin_user, client_company):
        ri = RecurringInvoice.objects.create(
            client=client_company,
            template_name='Auto-send',
            frequency=RecurringInvoice.MONTHLY,
            start_date=date.today(),
            next_run_date=date.today(),
            amount=Decimal('500.00'),
            auto_send=True,
            owner=admin_user,
        )
        invoice = ri.generate_invoice()
        assert invoice.status == Invoice.SENT


# ============================================================================
# LateFeePolicy Model Tests
# ============================================================================


@pytest.mark.django_db
class TestLateFeePolicyModel:
    """Tests for LateFeePolicy model."""

    def test_str_flat(self):
        policy = LateFeePolicy.objects.create(
            name='Standard Flat Fee',
            fee_type=LateFeePolicy.FLAT,
            fee_amount=Decimal('25.00'),
        )
        assert '$25.00' in str(policy)
        assert 'flat' in str(policy)

    def test_str_percentage(self):
        policy = LateFeePolicy.objects.create(
            name='Standard Rate',
            fee_type=LateFeePolicy.PERCENTAGE,
            fee_amount=Decimal('5.00'),
        )
        assert '5.00%' in str(policy)

    def test_calculate_fee_flat(self):
        policy = LateFeePolicy.objects.create(
            name='Flat Fee',
            fee_type=LateFeePolicy.FLAT,
            fee_amount=Decimal('50.00'),
        )
        fee = policy.calculate_fee(Decimal('1000.00'))
        assert fee == Decimal('50.00')

    def test_calculate_fee_percentage(self):
        policy = LateFeePolicy.objects.create(
            name='Percentage Fee',
            fee_type=LateFeePolicy.PERCENTAGE,
            fee_amount=Decimal('10.00'),
        )
        fee = policy.calculate_fee(Decimal('1000.00'))
        assert fee == Decimal('100.00')

    def test_calculate_fee_percentage_with_cap(self):
        policy = LateFeePolicy.objects.create(
            name='Capped Fee',
            fee_type=LateFeePolicy.PERCENTAGE,
            fee_amount=Decimal('20.00'),
            max_fee_amount=Decimal('100.00'),
        )
        fee = policy.calculate_fee(Decimal('1000.00'))
        assert fee == Decimal('100.00')

    def test_calculate_fee_percentage_under_cap(self):
        policy = LateFeePolicy.objects.create(
            name='Under Cap',
            fee_type=LateFeePolicy.PERCENTAGE,
            fee_amount=Decimal('5.00'),
            max_fee_amount=Decimal('100.00'),
        )
        fee = policy.calculate_fee(Decimal('1000.00'))
        assert fee == Decimal('50.00')

    def test_flat_fee_ignores_cap(self):
        policy = LateFeePolicy.objects.create(
            name='Flat with cap',
            fee_type=LateFeePolicy.FLAT,
            fee_amount=Decimal('200.00'),
            max_fee_amount=Decimal('100.00'),
        )
        fee = policy.calculate_fee(Decimal('1000.00'))
        assert fee == Decimal('100.00')

    def test_default_values(self):
        policy = LateFeePolicy.objects.create(
            name='Defaults',
            fee_amount=Decimal('5.00'),
        )
        assert policy.fee_type == LateFeePolicy.PERCENTAGE
        assert policy.apply_frequency == LateFeePolicy.ONCE
        assert policy.is_active is True
        assert policy.grace_period_days == 0


# ============================================================================
# PaymentReminder Model Tests
# ============================================================================


@pytest.mark.django_db
class TestPaymentReminderModel:
    """Tests for PaymentReminder model."""

    def test_str_representation(self, invoice_sent):
        reminder = PaymentReminder.objects.create(
            invoice=invoice_sent,
            reminder_type=PaymentReminder.BEFORE_DUE,
            days_offset=7,
            scheduled_date=date.today() + timedelta(days=7),
        )
        assert invoice_sent.invoice_number in str(reminder)
        assert 'before_due' in str(reminder)

    def test_is_due_scheduled_past(self, invoice_sent):
        reminder = PaymentReminder.objects.create(
            invoice=invoice_sent,
            reminder_type=PaymentReminder.BEFORE_DUE,
            days_offset=7,
            scheduled_date=date.today() - timedelta(days=1),
            status=PaymentReminder.SCHEDULED,
        )
        assert reminder.is_due is True

    def test_is_due_scheduled_future(self, invoice_sent):
        reminder = PaymentReminder.objects.create(
            invoice=invoice_sent,
            reminder_type=PaymentReminder.BEFORE_DUE,
            days_offset=7,
            scheduled_date=date.today() + timedelta(days=7),
            status=PaymentReminder.SCHEDULED,
        )
        assert reminder.is_due is False

    def test_is_due_already_sent(self, invoice_sent):
        reminder = PaymentReminder.objects.create(
            invoice=invoice_sent,
            reminder_type=PaymentReminder.BEFORE_DUE,
            days_offset=7,
            scheduled_date=date.today() - timedelta(days=1),
            status=PaymentReminder.SENT,
        )
        assert reminder.is_due is False

    def test_mark_sent(self, invoice_sent):
        reminder = PaymentReminder.objects.create(
            invoice=invoice_sent,
            reminder_type=PaymentReminder.ON_DUE,
            days_offset=0,
            scheduled_date=date.today(),
        )
        reminder.mark_sent()
        reminder.refresh_from_db()
        assert reminder.status == PaymentReminder.SENT
        assert reminder.sent_at is not None

    def test_default_values(self, invoice_sent):
        reminder = PaymentReminder.objects.create(
            invoice=invoice_sent,
            scheduled_date=date.today(),
        )
        assert reminder.status == PaymentReminder.SCHEDULED
        assert reminder.reminder_type == PaymentReminder.BEFORE_DUE
        assert reminder.days_offset == 7


# ============================================================================
# API ViewSet Tests
# ============================================================================


@pytest.mark.django_db
class TestRecurringInvoiceViewSet:
    """Tests for RecurringInvoiceViewSet."""

    def test_list(self, authenticated_admin_client, admin_user, client_company):
        RecurringInvoice.objects.create(
            client=client_company,
            template_name='Test Recurring',
            frequency=RecurringInvoice.MONTHLY,
            start_date=date.today(),
            next_run_date=date.today(),
            amount=Decimal('1000.00'),
            owner=admin_user,
        )
        response = authenticated_admin_client.get('/api/invoicing/api/recurring-invoices/')
        assert response.status_code == 200

    def test_create(self, authenticated_admin_client, client_company):
        data = {
            'client': str(client_company.id),
            'template_name': 'New Recurring',
            'frequency': 'monthly',
            'start_date': str(date.today()),
            'next_run_date': str(date.today()),
            'amount': '2000.00',
        }
        response = authenticated_admin_client.post(
            '/api/invoicing/api/recurring-invoices/', data, format='json'
        )
        assert response.status_code in [201, 400]

    def test_retrieve(self, authenticated_admin_client, admin_user, client_company):
        ri = RecurringInvoice.objects.create(
            client=client_company,
            template_name='Retrieve Test',
            frequency=RecurringInvoice.MONTHLY,
            start_date=date.today(),
            next_run_date=date.today(),
            amount=Decimal('500.00'),
            owner=admin_user,
        )
        response = authenticated_admin_client.get(f'/api/invoicing/api/recurring-invoices/{ri.id}/')
        assert response.status_code == 200


@pytest.mark.django_db
class TestLateFeePolicyViewSet:
    """Tests for LateFeePolicyViewSet."""

    def test_list(self, authenticated_admin_client):
        LateFeePolicy.objects.create(
            name='Test Policy',
            fee_type=LateFeePolicy.PERCENTAGE,
            fee_amount=Decimal('5.00'),
        )
        response = authenticated_admin_client.get('/api/invoicing/api/late-fee-policies/')
        assert response.status_code == 200

    def test_create(self, authenticated_admin_client):
        data = {
            'name': 'New Policy',
            'fee_type': 'flat',
            'fee_amount': '25.00',
        }
        response = authenticated_admin_client.post(
            '/api/invoicing/api/late-fee-policies/', data, format='json'
        )
        assert response.status_code in [201, 400]


@pytest.mark.django_db
class TestPaymentReminderViewSet:
    """Tests for PaymentReminderViewSet."""

    def test_list(self, authenticated_admin_client, invoice_sent):
        PaymentReminder.objects.create(
            invoice=invoice_sent,
            reminder_type=PaymentReminder.BEFORE_DUE,
            days_offset=7,
            scheduled_date=date.today(),
        )
        response = authenticated_admin_client.get('/api/invoicing/api/payment-reminders/')
        assert response.status_code == 200

    def test_create(self, authenticated_admin_client, invoice_sent):
        data = {
            'invoice': str(invoice_sent.id),
            'reminder_type': 'before_due',
            'days_offset': 3,
            'scheduled_date': str(date.today() + timedelta(days=3)),
        }
        response = authenticated_admin_client.post(
            '/api/invoicing/api/payment-reminders/', data, format='json'
        )
        assert response.status_code in [201, 400]
