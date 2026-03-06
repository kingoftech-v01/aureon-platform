"""
Tests for payments app signals.
"""

import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.utils import timezone

from apps.payments.models import Payment
from apps.invoicing.models import Invoice


# ============================================================================
# Payment Signal Tests
# ============================================================================


class TestPaymentSignals:
    """Tests for payment post_save signals."""

    @pytest.mark.django_db
    def test_invoice_updated_on_payment_success_not_created(self, payment_pending):
        """Test that invoice is marked as paid when payment status changes to succeeded (update, not create)."""
        invoice = payment_pending.invoice
        original_paid_amount = invoice.paid_amount

        # Simulate payment succeeding (update, not create)
        payment_pending.status = Payment.SUCCEEDED
        payment_pending.save()

        invoice.refresh_from_db()
        # Invoice paid_amount should be updated
        assert invoice.paid_amount > original_paid_amount

    @pytest.mark.django_db
    def test_invoice_not_updated_on_payment_create(self, invoice_sent):
        """Test that signal does not fire for created=True even with succeeded status."""
        original_paid = invoice_sent.paid_amount

        # Create a new succeeded payment (created=True should skip the signal logic)
        payment = Payment.objects.create(
            invoice=invoice_sent,
            amount=Decimal('100.00'),
            currency='USD',
            payment_method=Payment.CARD,
            status=Payment.SUCCEEDED,
            payment_date=timezone.now(),
            stripe_payment_intent_id='pi_test_new_created',
        )

        invoice_sent.refresh_from_db()
        # The signal only triggers for not-created payments, so no update
        assert invoice_sent.paid_amount == original_paid

    @pytest.mark.django_db
    def test_invoice_not_updated_on_failed_payment(self, payment_pending):
        """Test that invoice is NOT updated when payment fails."""
        invoice = payment_pending.invoice
        original_paid_amount = invoice.paid_amount

        payment_pending.status = Payment.FAILED
        payment_pending.save()

        invoice.refresh_from_db()
        assert invoice.paid_amount == original_paid_amount

    @pytest.mark.django_db
    def test_invoice_not_updated_on_pending_save(self, payment_pending):
        """Test that saving a pending payment does not update the invoice."""
        invoice = payment_pending.invoice
        original_paid_amount = invoice.paid_amount

        payment_pending.notes = 'Updated notes'
        payment_pending.save()

        invoice.refresh_from_db()
        assert invoice.paid_amount == original_paid_amount

    @pytest.mark.django_db
    def test_signal_passes_payment_details_to_invoice(self, payment_pending):
        """Test that signal passes correct payment details to mark_as_paid."""
        payment_pending.status = Payment.SUCCEEDED
        payment_pending.save()

        invoice = payment_pending.invoice
        invoice.refresh_from_db()

        # The signal calls mark_as_paid with:
        # payment_amount=instance.amount
        # payment_method=instance.payment_method
        # payment_reference=instance.transaction_id
        assert invoice.payment_reference == payment_pending.transaction_id
        assert invoice.payment_method == payment_pending.payment_method

    @pytest.mark.django_db
    def test_invoice_marked_paid_when_full_amount(self, invoice_sent):
        """Test invoice status changes to PAID when full amount is paid."""
        payment = Payment.objects.create(
            invoice=invoice_sent,
            amount=invoice_sent.total,
            currency='USD',
            payment_method=Payment.CARD,
            status=Payment.PENDING,
            payment_date=timezone.now(),
            stripe_payment_intent_id='pi_test_full_payment',
        )

        # Update to succeeded (not created)
        payment.status = Payment.SUCCEEDED
        payment.save()

        invoice_sent.refresh_from_db()
        assert invoice_sent.status == Invoice.PAID

    @pytest.mark.django_db
    def test_invoice_partially_paid_when_partial_amount(self, invoice_sent):
        """Test invoice status changes to PARTIALLY_PAID for partial payment."""
        partial_amount = invoice_sent.total / 2

        payment = Payment.objects.create(
            invoice=invoice_sent,
            amount=partial_amount,
            currency='USD',
            payment_method=Payment.CARD,
            status=Payment.PENDING,
            payment_date=timezone.now(),
            stripe_payment_intent_id='pi_test_partial_payment',
        )

        payment.status = Payment.SUCCEEDED
        payment.save()

        invoice_sent.refresh_from_db()
        assert invoice_sent.status == Invoice.PARTIALLY_PAID
