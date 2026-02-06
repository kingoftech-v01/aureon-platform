"""
Tests for invoicing app signals.
"""

import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock

from apps.invoicing.models import Invoice, InvoiceItem


# ============================================================================
# InvoiceItem Signal Tests
# ============================================================================


class TestInvoiceItemSignals:
    """Tests for invoice item signals (post_save, post_delete)."""

    @pytest.mark.django_db
    def test_recalculate_totals_on_item_save(self, invoice_draft):
        """Test that invoice totals are recalculated when an item is saved."""
        initial_subtotal = invoice_draft.subtotal

        item = InvoiceItem.objects.create(
            invoice=invoice_draft,
            description='New Service',
            quantity=Decimal('2.00'),
            unit_price=Decimal('1000.00'),
            amount=Decimal('2000.00'),
            order=1,
        )

        invoice_draft.refresh_from_db()
        # After signal fires, subtotal should be recalculated from items
        assert invoice_draft.subtotal == Decimal('2000.00')

    @pytest.mark.django_db
    def test_recalculate_totals_on_item_update(self, invoice_draft, invoice_item):
        """Test that invoice totals are recalculated when an item is updated."""
        # Update item
        invoice_item.unit_price = Decimal('7500.00')
        invoice_item.save()

        invoice_draft.refresh_from_db()
        # Should recalculate: 1 * 7500 = 7500 subtotal
        assert invoice_draft.subtotal == Decimal('7500.00')

    @pytest.mark.django_db
    def test_recalculate_totals_on_item_delete(self, invoice_draft, invoice_item):
        """Test that invoice totals are recalculated when an item is deleted."""
        invoice_item.delete()

        invoice_draft.refresh_from_db()
        # No items left, subtotal should be 0
        assert invoice_draft.subtotal == Decimal('0')

    @pytest.mark.django_db
    def test_recalculate_includes_tax(self, invoice_draft):
        """Test that signal-triggered recalculation includes tax."""
        # invoice_draft has tax_rate=8%
        item = InvoiceItem.objects.create(
            invoice=invoice_draft,
            description='Taxable Service',
            quantity=Decimal('1.00'),
            unit_price=Decimal('1000.00'),
            amount=Decimal('1000.00'),
            order=0,
        )

        invoice_draft.refresh_from_db()
        expected_tax = Decimal('1000.00') * Decimal('8.00') / 100
        assert invoice_draft.tax_amount == expected_tax
        assert invoice_draft.total == Decimal('1000.00') + expected_tax

    @pytest.mark.django_db
    def test_multiple_items_calculation(self, invoice_draft):
        """Test recalculation with multiple items."""
        InvoiceItem.objects.create(
            invoice=invoice_draft,
            description='Service A',
            quantity=Decimal('1.00'),
            unit_price=Decimal('1000.00'),
            amount=Decimal('1000.00'),
            order=0,
        )
        InvoiceItem.objects.create(
            invoice=invoice_draft,
            description='Service B',
            quantity=Decimal('2.00'),
            unit_price=Decimal('500.00'),
            amount=Decimal('1000.00'),
            order=1,
        )

        invoice_draft.refresh_from_db()
        assert invoice_draft.subtotal == Decimal('2000.00')

    @pytest.mark.django_db
    def test_delete_one_of_multiple_items(self, invoice_draft):
        """Test deleting one item when multiple exist."""
        item1 = InvoiceItem.objects.create(
            invoice=invoice_draft,
            description='Service A',
            quantity=Decimal('1.00'),
            unit_price=Decimal('1000.00'),
            amount=Decimal('1000.00'),
            order=0,
        )
        item2 = InvoiceItem.objects.create(
            invoice=invoice_draft,
            description='Service B',
            quantity=Decimal('1.00'),
            unit_price=Decimal('2000.00'),
            amount=Decimal('2000.00'),
            order=1,
        )

        item1.delete()

        invoice_draft.refresh_from_db()
        assert invoice_draft.subtotal == Decimal('2000.00')
