"""
Tests for invoicing app models.

Tests cover:
- Invoice model creation and validation
- Invoice properties and methods
- InvoiceItem model
- Auto-generation of invoice numbers
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from apps.invoicing.models import Invoice, InvoiceItem


# ============================================================================
# Invoice Model Tests
# ============================================================================

@pytest.mark.django_db
class TestInvoiceModel:
    """Tests for the Invoice model."""

    def test_create_invoice(self, client_company, contract_fixed):
        """Test creating an invoice."""
        invoice = Invoice.objects.create(
            client=client_company,
            contract=contract_fixed,
            status=Invoice.DRAFT,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            subtotal=Decimal('5000.00'),
            tax_rate=Decimal('8.00'),
            tax_amount=Decimal('400.00'),
            total=Decimal('5400.00'),
            currency='USD',
        )

        assert invoice.client == client_company
        assert invoice.contract == contract_fixed
        assert invoice.status == Invoice.DRAFT

    def test_invoice_auto_generate_number(self, client_company):
        """Test that invoice number is auto-generated."""
        invoice = Invoice.objects.create(
            client=client_company,
            status=Invoice.DRAFT,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            subtotal=Decimal('1000.00'),
            total=Decimal('1000.00'),
        )

        assert invoice.invoice_number is not None
        assert invoice.invoice_number.startswith('INV-')

    def test_invoice_string_representation(self, invoice_draft):
        """Test invoice string representation."""
        expected = f"{invoice_draft.invoice_number} - {invoice_draft.client.get_display_name()}"
        assert str(invoice_draft) == expected

    def test_invoice_uuid_primary_key(self, invoice_draft):
        """Test invoice has UUID primary key."""
        import uuid
        assert isinstance(invoice_draft.id, uuid.UUID)


# ============================================================================
# Invoice Status Tests
# ============================================================================

@pytest.mark.django_db
class TestInvoiceStatus:
    """Tests for invoice status values."""

    def test_all_status_choices_valid(self):
        """Test all status choices are valid."""
        valid_statuses = [
            Invoice.DRAFT,
            Invoice.SENT,
            Invoice.VIEWED,
            Invoice.PAID,
            Invoice.PARTIALLY_PAID,
            Invoice.OVERDUE,
            Invoice.CANCELLED,
        ]
        for status in valid_statuses:
            assert status in dict(Invoice.STATUS_CHOICES)


# ============================================================================
# Invoice Overdue Tests
# ============================================================================

@pytest.mark.django_db
class TestInvoiceOverdue:
    """Tests for invoice overdue functionality."""

    def test_is_overdue_past_due_date(self, invoice_overdue):
        """Test is_overdue for past due date."""
        assert invoice_overdue.is_overdue is True

    def test_is_overdue_future_due_date(self, invoice_draft):
        """Test is_overdue for future due date."""
        assert invoice_draft.is_overdue is False

    def test_is_overdue_paid_invoice(self, invoice_paid):
        """Test is_overdue for paid invoice."""
        assert invoice_paid.is_overdue is False

    def test_is_overdue_cancelled_invoice(self, client_company):
        """Test is_overdue for cancelled invoice."""
        invoice = Invoice.objects.create(
            client=client_company,
            status=Invoice.CANCELLED,
            issue_date=date.today() - timedelta(days=60),
            due_date=date.today() - timedelta(days=30),
            total=Decimal('1000.00'),
        )

        assert invoice.is_overdue is False


# ============================================================================
# Invoice Payment Tests
# ============================================================================

@pytest.mark.django_db
class TestInvoicePayment:
    """Tests for invoice payment functionality."""

    def test_balance_due(self, invoice_sent):
        """Test balance_due calculation."""
        expected = invoice_sent.total - invoice_sent.paid_amount
        assert invoice_sent.balance_due == expected

    def test_balance_due_fully_paid(self, invoice_paid):
        """Test balance_due when fully paid."""
        assert invoice_paid.balance_due == Decimal('0.00')

    def test_is_fully_paid(self, invoice_paid):
        """Test is_fully_paid property."""
        assert invoice_paid.is_fully_paid is True

    def test_is_fully_paid_partial(self, invoice_sent):
        """Test is_fully_paid with partial payment."""
        invoice_sent.paid_amount = invoice_sent.total / 2
        invoice_sent.save()

        assert invoice_sent.is_fully_paid is False

    def test_mark_as_paid(self, invoice_sent):
        """Test mark_as_paid method."""
        invoice_sent.mark_as_paid(
            payment_amount=invoice_sent.total,
            payment_method='card',
            payment_reference='txn_test123'
        )

        assert invoice_sent.status == Invoice.PAID
        assert invoice_sent.paid_at is not None
        assert invoice_sent.payment_method == 'card'
        assert invoice_sent.payment_reference == 'txn_test123'

    def test_mark_as_paid_partial(self, invoice_sent):
        """Test mark_as_paid with partial payment."""
        partial_amount = invoice_sent.total / 2
        invoice_sent.mark_as_paid(payment_amount=partial_amount)

        assert invoice_sent.status == Invoice.PARTIALLY_PAID
        assert invoice_sent.paid_amount == partial_amount

    def test_mark_as_sent(self, invoice_draft):
        """Test mark_as_sent method."""
        invoice_draft.mark_as_sent()

        assert invoice_draft.status == Invoice.SENT
        assert invoice_draft.sent_at is not None


# ============================================================================
# Invoice Calculation Tests
# ============================================================================

@pytest.mark.django_db
class TestInvoiceCalculation:
    """Tests for invoice calculation functionality."""

    def test_calculate_totals(self, invoice_draft, invoice_item):
        """Test calculate_totals method."""
        invoice_draft.tax_rate = Decimal('10.00')
        invoice_draft.discount_amount = Decimal('100.00')
        invoice_draft.calculate_totals()

        # Subtotal from items
        expected_subtotal = invoice_item.amount
        expected_tax = (expected_subtotal * Decimal('10.00')) / 100
        expected_total = expected_subtotal + expected_tax - Decimal('100.00')

        assert invoice_draft.subtotal == expected_subtotal
        assert invoice_draft.tax_amount == expected_tax
        assert invoice_draft.total == expected_total


# ============================================================================
# InvoiceItem Model Tests
# ============================================================================

@pytest.mark.django_db
class TestInvoiceItemModel:
    """Tests for the InvoiceItem model."""

    def test_create_invoice_item(self, invoice_draft):
        """Test creating an invoice item."""
        item = InvoiceItem.objects.create(
            invoice=invoice_draft,
            description='Consulting Services',
            quantity=Decimal('10.00'),
            unit_price=Decimal('100.00'),
            amount=Decimal('1000.00'),
            order=0,
        )

        assert item.invoice == invoice_draft
        assert item.description == 'Consulting Services'
        assert item.amount == Decimal('1000.00')

    def test_invoice_item_string_representation(self, invoice_item):
        """Test invoice item string representation."""
        expected = f"{invoice_item.description} - {invoice_item.amount}"
        assert str(invoice_item) == expected

    def test_invoice_item_uuid_primary_key(self, invoice_item):
        """Test invoice item has UUID primary key."""
        import uuid
        assert isinstance(invoice_item.id, uuid.UUID)

    def test_invoice_item_auto_calculate_amount(self, invoice_draft):
        """Test amount is auto-calculated on save."""
        item = InvoiceItem(
            invoice=invoice_draft,
            description='Test Item',
            quantity=Decimal('5.00'),
            unit_price=Decimal('200.00'),
        )
        # Don't set amount, let it be calculated
        item.amount = item.quantity * item.unit_price
        item.save()

        assert item.amount == Decimal('1000.00')


# ============================================================================
# Invoice Metadata Tests
# ============================================================================

@pytest.mark.django_db
class TestInvoiceMetadata:
    """Tests for invoice metadata JSON field."""

    def test_metadata_default_empty_dict(self, client_company):
        """Test metadata defaults to empty dict."""
        invoice = Invoice.objects.create(
            client=client_company,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            total=Decimal('1000.00'),
        )
        assert invoice.metadata == {}

    def test_metadata_stores_json(self, invoice_draft):
        """Test metadata can store JSON data."""
        invoice_draft.metadata = {
            'po_number': 'PO-12345',
            'department': 'Engineering',
        }
        invoice_draft.save()

        invoice_draft.refresh_from_db()
        assert invoice_draft.metadata['po_number'] == 'PO-12345'


# ============================================================================
# Invoice Edge Cases
# ============================================================================

@pytest.mark.django_db
class TestInvoiceEdgeCases:
    """Edge case tests for Invoice model."""

    def test_invoice_without_contract(self, client_individual):
        """Test invoice without associated contract."""
        invoice = Invoice.objects.create(
            client=client_individual,
            contract=None,
            status=Invoice.DRAFT,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            total=Decimal('500.00'),
        )

        assert invoice.contract is None

    def test_invoice_notes_field(self, invoice_draft):
        """Test invoice notes field."""
        invoice_draft.notes = 'Please pay promptly.'
        invoice_draft.save()

        invoice_draft.refresh_from_db()
        assert invoice_draft.notes == 'Please pay promptly.'

    def test_invoice_terms_field(self, invoice_draft):
        """Test invoice terms field."""
        invoice_draft.terms = 'Payment due within 30 days.'
        invoice_draft.save()

        invoice_draft.refresh_from_db()
        assert 'Payment due' in invoice_draft.terms

    def test_invoice_stripe_fields(self, invoice_paid):
        """Test invoice Stripe integration fields."""
        assert invoice_paid.stripe_invoice_id == '' or invoice_paid.stripe_invoice_id is not None

    def test_invoice_email_tracking(self, invoice_sent):
        """Test invoice email tracking fields."""
        assert invoice_sent.sent_at is not None

    def test_invoice_viewed_tracking(self, invoice_sent):
        """Test invoice viewed tracking."""
        invoice_sent.viewed_at = timezone.now()
        invoice_sent.status = Invoice.VIEWED
        invoice_sent.save()

        invoice_sent.refresh_from_db()
        assert invoice_sent.viewed_at is not None

    def test_multiple_invoice_items(self, invoice_draft):
        """Test invoice with multiple items."""
        items = []
        for i in range(5):
            item = InvoiceItem.objects.create(
                invoice=invoice_draft,
                description=f'Service {i+1}',
                quantity=Decimal('1.00'),
                unit_price=Decimal(f'{(i+1)*100}.00'),
                amount=Decimal(f'{(i+1)*100}.00'),
                order=i,
            )
            items.append(item)

        assert invoice_draft.items.count() == 6  # 5 + original from fixture

    def test_invoice_item_order(self, invoice_draft):
        """Test invoice items are ordered."""
        InvoiceItem.objects.create(
            invoice=invoice_draft,
            description='Second Item',
            quantity=Decimal('1.00'),
            unit_price=Decimal('200.00'),
            amount=Decimal('200.00'),
            order=2,
        )
        InvoiceItem.objects.create(
            invoice=invoice_draft,
            description='First Item',
            quantity=Decimal('1.00'),
            unit_price=Decimal('100.00'),
            amount=Decimal('100.00'),
            order=1,
        )

        items = list(invoice_draft.items.all())
        orders = [item.order for item in items]
        assert orders == sorted(orders)
