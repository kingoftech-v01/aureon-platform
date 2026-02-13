"""
Tests for RecurringInvoice, LateFeePolicy, and PaymentReminder models and views.

Tests cover:
- RecurringInvoice model: __str__, generate_invoice(), calculate_next_run_date(), status transitions
- LateFeePolicy model: __str__, calculate_fee() for FLAT and PERCENTAGE types, max_fee_amount cap
- PaymentReminder model: __str__, mark_sent()
- RecurringInvoiceViewSet: list, create, retrieve, pause, resume, generate_now actions
- LateFeePolicyViewSet: CRUD
- PaymentReminderViewSet: list, create, send_now, cancel actions
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch
from django.utils import timezone
from rest_framework import status

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

    def test_is_due_active_today(self, admin_user, client_company):
        """Test is_due returns True when next_run_date is today."""
        ri = RecurringInvoice.objects.create(
            client=client_company,
            template_name='Today Retainer',
            frequency=RecurringInvoice.MONTHLY,
            start_date=date.today() - timedelta(days=30),
            next_run_date=date.today(),
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

    def test_is_due_cancelled(self, admin_user, client_company):
        """Test is_due returns False when status is cancelled."""
        ri = RecurringInvoice.objects.create(
            client=client_company,
            template_name='Cancelled Retainer',
            frequency=RecurringInvoice.MONTHLY,
            start_date=date.today() - timedelta(days=60),
            next_run_date=date.today() - timedelta(days=1),
            amount=Decimal('500.00'),
            status=RecurringInvoice.CANCELLED,
            owner=admin_user,
        )
        assert ri.is_due is False

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

    def test_calculate_next_run_date_biweekly(self, admin_user, client_company):
        """Test calculate_next_run_date for biweekly frequency."""
        ri = RecurringInvoice.objects.create(
            client=client_company,
            template_name='Biweekly',
            frequency=RecurringInvoice.BIWEEKLY,
            start_date=date(2026, 1, 1),
            next_run_date=date(2026, 1, 1),
            amount=Decimal('300.00'),
            owner=admin_user,
        )
        ri.calculate_next_run_date()
        ri.refresh_from_db()
        assert ri.next_run_date == date(2026, 1, 15)

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

    def test_calculate_next_run_date_annually(self, admin_user, client_company):
        """Test calculate_next_run_date for annual frequency."""
        ri = RecurringInvoice.objects.create(
            client=client_company,
            template_name='Annual',
            frequency=RecurringInvoice.ANNUALLY,
            start_date=date(2026, 3, 1),
            next_run_date=date(2026, 3, 1),
            amount=Decimal('12000.00'),
            owner=admin_user,
        )
        ri.calculate_next_run_date()
        ri.refresh_from_db()
        assert ri.next_run_date == date(2027, 3, 1)

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

    def test_calculate_next_run_date_stays_active_when_under_end_date(
        self, admin_user, client_company
    ):
        """Test status stays active when next_run_date is before end_date."""
        ri = RecurringInvoice.objects.create(
            client=client_company,
            template_name='Long Term',
            frequency=RecurringInvoice.MONTHLY,
            start_date=date(2026, 1, 1),
            next_run_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            amount=Decimal('500.00'),
            owner=admin_user,
        )
        ri.calculate_next_run_date()
        ri.refresh_from_db()
        assert ri.status == RecurringInvoice.ACTIVE
        assert ri.next_run_date == date(2026, 2, 1)

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
        assert invoice.items.first().description == 'Simple Service'
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
        descs = list(invoice.items.order_by('order').values_list('description', flat=True))
        assert descs == ['Service A', 'Service B']

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

    def test_generate_invoice_no_auto_send(self, admin_user, client_company):
        """Test generate_invoice leaves status as draft when auto_send is False."""
        ri = RecurringInvoice.objects.create(
            client=client_company,
            template_name='No Auto-send',
            frequency=RecurringInvoice.MONTHLY,
            start_date=date.today(),
            next_run_date=date.today(),
            amount=Decimal('500.00'),
            auto_send=False,
            owner=admin_user,
        )
        invoice = ri.generate_invoice()
        assert invoice.status == Invoice.DRAFT

    def test_generate_invoice_uses_tax_rate_and_discount(self, admin_user, client_company):
        """Test generate_invoice passes tax_rate and discount to the invoice."""
        ri = RecurringInvoice.objects.create(
            client=client_company,
            template_name='Tax Retainer',
            frequency=RecurringInvoice.MONTHLY,
            start_date=date.today(),
            next_run_date=date.today(),
            amount=Decimal('1000.00'),
            tax_rate=Decimal('10.00'),
            discount_amount=Decimal('50.00'),
            auto_send=False,
            owner=admin_user,
        )
        invoice = ri.generate_invoice()
        assert invoice.tax_rate == Decimal('10.00')
        assert invoice.discount_amount == Decimal('50.00')

    def test_generate_invoice_with_contract(self, admin_user, client_company, contract_fixed):
        """Test generate_invoice links to a contract when set."""
        ri = RecurringInvoice.objects.create(
            client=client_company,
            contract=contract_fixed,
            template_name='Contract Retainer',
            frequency=RecurringInvoice.MONTHLY,
            start_date=date.today(),
            next_run_date=date.today(),
            amount=Decimal('1000.00'),
            auto_send=False,
            owner=admin_user,
        )
        invoice = ri.generate_invoice()
        assert invoice.contract == contract_fixed

    def test_generate_invoice_advances_next_run_date(self, admin_user, client_company):
        """Test generate_invoice calls calculate_next_run_date."""
        original_date = date(2026, 2, 1)
        ri = RecurringInvoice.objects.create(
            client=client_company,
            template_name='Advance Test',
            frequency=RecurringInvoice.MONTHLY,
            start_date=date(2026, 1, 1),
            next_run_date=original_date,
            amount=Decimal('500.00'),
            auto_send=False,
            owner=admin_user,
        )
        ri.generate_invoice()
        ri.refresh_from_db()
        assert ri.next_run_date == date(2026, 3, 1)


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

    def test_calculate_fee_flat_same_for_any_total(self):
        """Test flat fee is the same regardless of invoice total."""
        policy = LateFeePolicy.objects.create(
            name='Flat Fee Any',
            fee_type=LateFeePolicy.FLAT,
            fee_amount=Decimal('50.00'),
        )
        fee_small = policy.calculate_fee(Decimal('100.00'))
        fee_large = policy.calculate_fee(Decimal('50000.00'))
        assert fee_small == fee_large == Decimal('50.00')

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

    def test_calculate_fee_percentage_no_cap(self):
        """Test percentage fee without max_fee_amount has no limit."""
        policy = LateFeePolicy.objects.create(
            name='No Cap',
            fee_type=LateFeePolicy.PERCENTAGE,
            fee_amount=Decimal('2.00'),
            max_fee_amount=None,
        )
        fee = policy.calculate_fee(Decimal('100000.00'))
        assert fee == Decimal('2000.00')

    def test_flat_fee_with_max_cap_applied(self):
        """Test flat fee is capped by max_fee_amount when it exceeds cap."""
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
        assert policy.is_compound is False


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
        assert 'scheduled' in str(reminder)

    def test_is_due_scheduled_past(self, invoice_sent):
        reminder = PaymentReminder.objects.create(
            invoice=invoice_sent,
            reminder_type=PaymentReminder.BEFORE_DUE,
            days_offset=7,
            scheduled_date=date.today() - timedelta(days=1),
            status=PaymentReminder.SCHEDULED,
        )
        assert reminder.is_due is True

    def test_is_due_scheduled_today(self, invoice_sent):
        """Test is_due returns True when scheduled_date is today."""
        reminder = PaymentReminder.objects.create(
            invoice=invoice_sent,
            reminder_type=PaymentReminder.ON_DUE,
            days_offset=0,
            scheduled_date=date.today(),
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

    def test_is_due_cancelled(self, invoice_sent):
        """Test is_due returns False when reminder is cancelled."""
        reminder = PaymentReminder.objects.create(
            invoice=invoice_sent,
            reminder_type=PaymentReminder.AFTER_DUE,
            days_offset=3,
            scheduled_date=date.today() - timedelta(days=1),
            status=PaymentReminder.CANCELLED,
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
# RecurringInvoiceViewSet Tests
# ============================================================================


@pytest.mark.django_db
class TestRecurringInvoiceViewSet:
    """Tests for RecurringInvoiceViewSet."""

    def test_list(self, authenticated_admin_client, admin_user, client_company):
        """Test listing recurring invoices returns 200."""
        RecurringInvoice.objects.create(
            client=client_company,
            template_name='Test Recurring',
            frequency=RecurringInvoice.MONTHLY,
            start_date=date.today(),
            next_run_date=date.today(),
            amount=Decimal('1000.00'),
            owner=admin_user,
        )
        response = authenticated_admin_client.get('/api/api/recurring-invoices/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_unauthenticated(self, api_client):
        """Test unauthenticated access is denied."""
        response = api_client.get('/api/api/recurring-invoices/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create(self, authenticated_admin_client, client_company):
        """Test creating a recurring invoice."""
        data = {
            'client': str(client_company.id),
            'template_name': 'New Recurring',
            'frequency': 'monthly',
            'start_date': str(date.today()),
            'next_run_date': str(date.today()),
            'amount': '2000.00',
        }
        response = authenticated_admin_client.post(
            '/api/api/recurring-invoices/', data, format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['template_name'] == 'New Recurring'

    def test_create_sets_owner(self, authenticated_admin_client, client_company, admin_user):
        """Test that perform_create sets owner to the current user."""
        data = {
            'client': str(client_company.id),
            'template_name': 'Owner Test',
            'frequency': 'monthly',
            'start_date': str(date.today()),
            'next_run_date': str(date.today()),
            'amount': '1000.00',
        }
        response = authenticated_admin_client.post(
            '/api/api/recurring-invoices/', data, format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        ri = RecurringInvoice.objects.get(id=response.data['id'])
        assert ri.owner == admin_user

    def test_retrieve(self, authenticated_admin_client, admin_user, client_company):
        """Test retrieving a single recurring invoice."""
        ri = RecurringInvoice.objects.create(
            client=client_company,
            template_name='Retrieve Test',
            frequency=RecurringInvoice.MONTHLY,
            start_date=date.today(),
            next_run_date=date.today(),
            amount=Decimal('500.00'),
            owner=admin_user,
        )
        response = authenticated_admin_client.get(f'/api/api/recurring-invoices/{ri.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['template_name'] == 'Retrieve Test'

    def test_update(self, authenticated_admin_client, admin_user, client_company):
        """Test updating a recurring invoice."""
        ri = RecurringInvoice.objects.create(
            client=client_company,
            template_name='Before Update',
            frequency=RecurringInvoice.MONTHLY,
            start_date=date.today(),
            next_run_date=date.today(),
            amount=Decimal('500.00'),
            owner=admin_user,
        )
        response = authenticated_admin_client.patch(
            f'/api/api/recurring-invoices/{ri.id}/',
            {'template_name': 'After Update'},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['template_name'] == 'After Update'

    def test_delete(self, authenticated_admin_client, admin_user, client_company):
        """Test deleting a recurring invoice."""
        ri = RecurringInvoice.objects.create(
            client=client_company,
            template_name='Delete Test',
            frequency=RecurringInvoice.MONTHLY,
            start_date=date.today(),
            next_run_date=date.today(),
            amount=Decimal('500.00'),
            owner=admin_user,
        )
        response = authenticated_admin_client.delete(
            f'/api/api/recurring-invoices/{ri.id}/'
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not RecurringInvoice.objects.filter(id=ri.id).exists()

    def test_pause_active(self, authenticated_admin_client, admin_user, client_company):
        """Test pausing an active recurring invoice."""
        ri = RecurringInvoice.objects.create(
            client=client_company,
            template_name='Pause Test',
            frequency=RecurringInvoice.MONTHLY,
            start_date=date.today(),
            next_run_date=date.today(),
            amount=Decimal('500.00'),
            status=RecurringInvoice.ACTIVE,
            owner=admin_user,
        )
        response = authenticated_admin_client.post(
            f'/api/api/recurring-invoices/{ri.id}/pause/'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == RecurringInvoice.PAUSED

    def test_pause_non_active_fails(self, authenticated_admin_client, admin_user, client_company):
        """Test pausing a non-active recurring invoice returns 400."""
        ri = RecurringInvoice.objects.create(
            client=client_company,
            template_name='Pause Fail Test',
            frequency=RecurringInvoice.MONTHLY,
            start_date=date.today(),
            next_run_date=date.today(),
            amount=Decimal('500.00'),
            status=RecurringInvoice.PAUSED,
            owner=admin_user,
        )
        response = authenticated_admin_client.post(
            f'/api/api/recurring-invoices/{ri.id}/pause/'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Only active' in response.data['detail']

    def test_resume_paused(self, authenticated_admin_client, admin_user, client_company):
        """Test resuming a paused recurring invoice."""
        ri = RecurringInvoice.objects.create(
            client=client_company,
            template_name='Resume Test',
            frequency=RecurringInvoice.MONTHLY,
            start_date=date.today(),
            next_run_date=date.today(),
            amount=Decimal('500.00'),
            status=RecurringInvoice.PAUSED,
            owner=admin_user,
        )
        response = authenticated_admin_client.post(
            f'/api/api/recurring-invoices/{ri.id}/resume/'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == RecurringInvoice.ACTIVE

    def test_resume_non_paused_fails(self, authenticated_admin_client, admin_user, client_company):
        """Test resuming a non-paused recurring invoice returns 400."""
        ri = RecurringInvoice.objects.create(
            client=client_company,
            template_name='Resume Fail Test',
            frequency=RecurringInvoice.MONTHLY,
            start_date=date.today(),
            next_run_date=date.today(),
            amount=Decimal('500.00'),
            status=RecurringInvoice.ACTIVE,
            owner=admin_user,
        )
        response = authenticated_admin_client.post(
            f'/api/api/recurring-invoices/{ri.id}/resume/'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Only paused' in response.data['detail']

    def test_generate_now(self, authenticated_admin_client, admin_user, client_company):
        """Test generate_now creates an invoice immediately."""
        ri = RecurringInvoice.objects.create(
            client=client_company,
            template_name='Generate Now',
            frequency=RecurringInvoice.MONTHLY,
            start_date=date.today(),
            next_run_date=date.today(),
            amount=Decimal('1000.00'),
            auto_send=False,
            owner=admin_user,
        )
        response = authenticated_admin_client.post(
            f'/api/api/recurring-invoices/{ri.id}/generate_now/'
        )
        assert response.status_code == status.HTTP_200_OK
        assert 'invoice_id' in response.data
        assert 'invoice_number' in response.data
        assert response.data['invoice_number'].startswith('INV-')

    @patch(
        'apps.invoicing.models.RecurringInvoice.generate_invoice',
        side_effect=Exception('generation failed'),
    )
    def test_generate_now_error_returns_500(
        self, mock_gen, authenticated_admin_client, admin_user, client_company
    ):
        """Test generate_now returns 500 when generate_invoice raises."""
        ri = RecurringInvoice.objects.create(
            client=client_company,
            template_name='Error Test',
            frequency=RecurringInvoice.MONTHLY,
            start_date=date.today(),
            next_run_date=date.today(),
            amount=Decimal('1000.00'),
            owner=admin_user,
        )
        response = authenticated_admin_client.post(
            f'/api/api/recurring-invoices/{ri.id}/generate_now/'
        )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'Failed to generate invoice' in response.data['detail']

    def test_non_staff_filtered_access(
        self, authenticated_contributor_client, admin_user, client_company
    ):
        """Test non-staff users have filtered access."""
        RecurringInvoice.objects.create(
            client=client_company,
            template_name='Filtered',
            frequency=RecurringInvoice.MONTHLY,
            start_date=date.today(),
            next_run_date=date.today(),
            amount=Decimal('500.00'),
            owner=admin_user,
        )
        response = authenticated_contributor_client.get('/api/api/recurring-invoices/')
        assert response.status_code == status.HTTP_200_OK

    def test_filter_by_status(self, authenticated_admin_client, admin_user, client_company):
        """Test filtering recurring invoices by status."""
        RecurringInvoice.objects.create(
            client=client_company,
            template_name='Active RI',
            frequency=RecurringInvoice.MONTHLY,
            start_date=date.today(),
            next_run_date=date.today(),
            amount=Decimal('500.00'),
            status=RecurringInvoice.ACTIVE,
            owner=admin_user,
        )
        response = authenticated_admin_client.get(
            '/api/api/recurring-invoices/?status=active'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_filter_by_frequency(self, authenticated_admin_client, admin_user, client_company):
        """Test filtering recurring invoices by frequency."""
        RecurringInvoice.objects.create(
            client=client_company,
            template_name='Weekly RI',
            frequency=RecurringInvoice.WEEKLY,
            start_date=date.today(),
            next_run_date=date.today(),
            amount=Decimal('200.00'),
            owner=admin_user,
        )
        response = authenticated_admin_client.get(
            '/api/api/recurring-invoices/?frequency=weekly'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_search_by_template_name(self, authenticated_admin_client, admin_user, client_company):
        """Test searching recurring invoices by template_name."""
        RecurringInvoice.objects.create(
            client=client_company,
            template_name='UniqueSearchName',
            frequency=RecurringInvoice.MONTHLY,
            start_date=date.today(),
            next_run_date=date.today(),
            amount=Decimal('500.00'),
            owner=admin_user,
        )
        response = authenticated_admin_client.get(
            '/api/api/recurring-invoices/?search=UniqueSearchName'
        )
        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# LateFeePolicyViewSet Tests
# ============================================================================


@pytest.mark.django_db
class TestLateFeePolicyViewSet:
    """Tests for LateFeePolicyViewSet."""

    def test_list(self, authenticated_admin_client):
        """Test listing late fee policies."""
        LateFeePolicy.objects.create(
            name='Test Policy',
            fee_type=LateFeePolicy.PERCENTAGE,
            fee_amount=Decimal('5.00'),
        )
        response = authenticated_admin_client.get('/api/api/late-fee-policies/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_unauthenticated(self, api_client):
        """Test unauthenticated access is denied."""
        response = api_client.get('/api/api/late-fee-policies/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create(self, authenticated_admin_client):
        """Test creating a late fee policy."""
        data = {
            'name': 'New Policy',
            'fee_type': 'flat',
            'fee_amount': '25.00',
            'grace_period_days': 5,
            'apply_frequency': 'once',
            'is_active': True,
        }
        response = authenticated_admin_client.post(
            '/api/api/late-fee-policies/', data, format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Policy'

    def test_retrieve(self, authenticated_admin_client):
        """Test retrieving a single late fee policy."""
        policy = LateFeePolicy.objects.create(
            name='Retrieve Policy',
            fee_type=LateFeePolicy.FLAT,
            fee_amount=Decimal('30.00'),
        )
        response = authenticated_admin_client.get(
            f'/api/api/late-fee-policies/{policy.id}/'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Retrieve Policy'

    def test_update(self, authenticated_admin_client):
        """Test updating a late fee policy."""
        policy = LateFeePolicy.objects.create(
            name='Before Update',
            fee_type=LateFeePolicy.FLAT,
            fee_amount=Decimal('30.00'),
        )
        response = authenticated_admin_client.patch(
            f'/api/api/late-fee-policies/{policy.id}/',
            {'name': 'After Update', 'fee_amount': '75.00'},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'After Update'
        assert response.data['fee_amount'] == '75.00'

    def test_delete(self, authenticated_admin_client):
        """Test deleting a late fee policy."""
        policy = LateFeePolicy.objects.create(
            name='Delete Policy',
            fee_type=LateFeePolicy.FLAT,
            fee_amount=Decimal('30.00'),
        )
        response = authenticated_admin_client.delete(
            f'/api/api/late-fee-policies/{policy.id}/'
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not LateFeePolicy.objects.filter(id=policy.id).exists()

    def test_filter_by_fee_type(self, authenticated_admin_client):
        """Test filtering policies by fee_type."""
        LateFeePolicy.objects.create(
            name='Flat',
            fee_type=LateFeePolicy.FLAT,
            fee_amount=Decimal('25.00'),
        )
        LateFeePolicy.objects.create(
            name='Pct',
            fee_type=LateFeePolicy.PERCENTAGE,
            fee_amount=Decimal('5.00'),
        )
        response = authenticated_admin_client.get(
            '/api/api/late-fee-policies/?fee_type=flat'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_filter_by_is_active(self, authenticated_admin_client):
        """Test filtering policies by is_active."""
        LateFeePolicy.objects.create(
            name='Active',
            fee_amount=Decimal('5.00'),
            is_active=True,
        )
        LateFeePolicy.objects.create(
            name='Inactive',
            fee_amount=Decimal('5.00'),
            is_active=False,
        )
        response = authenticated_admin_client.get(
            '/api/api/late-fee-policies/?is_active=true'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_search_by_name(self, authenticated_admin_client):
        """Test searching policies by name."""
        LateFeePolicy.objects.create(
            name='UniqueLateFee',
            fee_amount=Decimal('5.00'),
        )
        response = authenticated_admin_client.get(
            '/api/api/late-fee-policies/?search=UniqueLateFee'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_filter_by_apply_frequency(self, authenticated_admin_client):
        """Test filtering policies by apply_frequency."""
        LateFeePolicy.objects.create(
            name='Monthly Apply',
            fee_amount=Decimal('5.00'),
            apply_frequency=LateFeePolicy.MONTHLY,
        )
        response = authenticated_admin_client.get(
            '/api/api/late-fee-policies/?apply_frequency=monthly'
        )
        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# PaymentReminderViewSet Tests
# ============================================================================


@pytest.mark.django_db
class TestPaymentReminderViewSet:
    """Tests for PaymentReminderViewSet."""

    def test_list(self, authenticated_admin_client, invoice_sent):
        """Test listing payment reminders."""
        PaymentReminder.objects.create(
            invoice=invoice_sent,
            reminder_type=PaymentReminder.BEFORE_DUE,
            days_offset=7,
            scheduled_date=date.today(),
        )
        response = authenticated_admin_client.get('/api/api/payment-reminders/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_unauthenticated(self, api_client):
        """Test unauthenticated access is denied."""
        response = api_client.get('/api/api/payment-reminders/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create(self, authenticated_admin_client, invoice_sent):
        """Test creating a payment reminder."""
        data = {
            'invoice': str(invoice_sent.id),
            'reminder_type': 'before_due',
            'days_offset': 3,
            'scheduled_date': str(date.today() + timedelta(days=3)),
        }
        response = authenticated_admin_client.post(
            '/api/api/payment-reminders/', data, format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['reminder_type'] == PaymentReminder.BEFORE_DUE

    def test_retrieve(self, authenticated_admin_client, invoice_sent):
        """Test retrieving a single payment reminder."""
        reminder = PaymentReminder.objects.create(
            invoice=invoice_sent,
            reminder_type=PaymentReminder.BEFORE_DUE,
            days_offset=7,
            scheduled_date=date.today(),
        )
        response = authenticated_admin_client.get(
            f'/api/api/payment-reminders/{reminder.id}/'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_send_now_scheduled(self, authenticated_admin_client, invoice_sent):
        """Test send_now action marks a scheduled reminder as sent."""
        reminder = PaymentReminder.objects.create(
            invoice=invoice_sent,
            reminder_type=PaymentReminder.BEFORE_DUE,
            days_offset=7,
            scheduled_date=date.today(),
            status=PaymentReminder.SCHEDULED,
        )
        response = authenticated_admin_client.post(
            f'/api/api/payment-reminders/{reminder.id}/send_now/'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == PaymentReminder.SENT
        assert response.data['sent_at'] is not None

    def test_send_now_already_sent_fails(self, authenticated_admin_client, invoice_sent):
        """Test send_now on already-sent reminder returns 400."""
        reminder = PaymentReminder.objects.create(
            invoice=invoice_sent,
            reminder_type=PaymentReminder.BEFORE_DUE,
            days_offset=7,
            scheduled_date=date.today() - timedelta(days=1),
            status=PaymentReminder.SENT,
            sent_at=timezone.now() - timedelta(days=1),
        )
        response = authenticated_admin_client.post(
            f'/api/api/payment-reminders/{reminder.id}/send_now/'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Only scheduled' in response.data['detail']

    def test_cancel_scheduled(self, authenticated_admin_client, invoice_sent):
        """Test cancel action cancels a scheduled reminder."""
        reminder = PaymentReminder.objects.create(
            invoice=invoice_sent,
            reminder_type=PaymentReminder.BEFORE_DUE,
            days_offset=7,
            scheduled_date=date.today() + timedelta(days=5),
            status=PaymentReminder.SCHEDULED,
        )
        response = authenticated_admin_client.post(
            f'/api/api/payment-reminders/{reminder.id}/cancel/'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == PaymentReminder.CANCELLED

    def test_cancel_already_sent_fails(self, authenticated_admin_client, invoice_sent):
        """Test cancel on already-sent reminder returns 400."""
        reminder = PaymentReminder.objects.create(
            invoice=invoice_sent,
            reminder_type=PaymentReminder.BEFORE_DUE,
            days_offset=7,
            scheduled_date=date.today() - timedelta(days=1),
            status=PaymentReminder.SENT,
            sent_at=timezone.now() - timedelta(days=1),
        )
        response = authenticated_admin_client.post(
            f'/api/api/payment-reminders/{reminder.id}/cancel/'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Only scheduled' in response.data['detail']

    def test_cancel_already_cancelled_fails(self, authenticated_admin_client, invoice_sent):
        """Test cancel on already-cancelled reminder returns 400."""
        reminder = PaymentReminder.objects.create(
            invoice=invoice_sent,
            reminder_type=PaymentReminder.AFTER_DUE,
            days_offset=3,
            scheduled_date=date.today(),
            status=PaymentReminder.CANCELLED,
        )
        response = authenticated_admin_client.post(
            f'/api/api/payment-reminders/{reminder.id}/cancel/'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_filter_by_invoice(self, authenticated_admin_client, invoice_sent):
        """Test filtering reminders by invoice."""
        PaymentReminder.objects.create(
            invoice=invoice_sent,
            reminder_type=PaymentReminder.BEFORE_DUE,
            days_offset=7,
            scheduled_date=date.today(),
        )
        response = authenticated_admin_client.get(
            f'/api/api/payment-reminders/?invoice={invoice_sent.id}'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_filter_by_status(self, authenticated_admin_client, invoice_sent):
        """Test filtering reminders by status."""
        PaymentReminder.objects.create(
            invoice=invoice_sent,
            scheduled_date=date.today(),
            status=PaymentReminder.SCHEDULED,
        )
        response = authenticated_admin_client.get(
            '/api/api/payment-reminders/?status=scheduled'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_filter_by_reminder_type(self, authenticated_admin_client, invoice_sent):
        """Test filtering reminders by reminder_type."""
        PaymentReminder.objects.create(
            invoice=invoice_sent,
            reminder_type=PaymentReminder.AFTER_DUE,
            days_offset=5,
            scheduled_date=date.today(),
        )
        response = authenticated_admin_client.get(
            '/api/api/payment-reminders/?reminder_type=after_due'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_non_staff_filtered_access(
        self, authenticated_contributor_client, invoice_sent
    ):
        """Test non-staff users have filtered access to payment reminders."""
        PaymentReminder.objects.create(
            invoice=invoice_sent,
            scheduled_date=date.today(),
        )
        response = authenticated_contributor_client.get('/api/api/payment-reminders/')
        assert response.status_code == status.HTTP_200_OK
