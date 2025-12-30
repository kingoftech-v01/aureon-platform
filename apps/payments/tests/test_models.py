"""
Tests for payments app models.

Tests cover:
- Payment model creation and validation
- Payment properties and methods
- Refund functionality
- PaymentMethod model
"""

import pytest
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from apps.payments.models import Payment, PaymentMethod


# ============================================================================
# Payment Model Tests
# ============================================================================

@pytest.mark.django_db
class TestPaymentModel:
    """Tests for the Payment model."""

    def test_create_payment(self, invoice_sent):
        """Test creating a payment."""
        payment = Payment.objects.create(
            invoice=invoice_sent,
            amount=Decimal('1000.00'),
            currency='USD',
            payment_method=Payment.CARD,
            status=Payment.SUCCEEDED,
            payment_date=timezone.now(),
            stripe_payment_intent_id='pi_test_create',
        )

        assert payment.invoice == invoice_sent
        assert payment.amount == Decimal('1000.00')
        assert payment.status == Payment.SUCCEEDED

    def test_payment_auto_generate_transaction_id(self, invoice_sent):
        """Test transaction ID is auto-generated."""
        payment = Payment.objects.create(
            invoice=invoice_sent,
            amount=Decimal('500.00'),
            currency='USD',
            payment_method=Payment.CARD,
            status=Payment.PENDING,
            payment_date=timezone.now(),
        )

        assert payment.transaction_id is not None
        assert payment.transaction_id.startswith('TXN-')

    def test_payment_string_representation(self, payment_successful):
        """Test payment string representation."""
        expected = f"Payment {payment_successful.transaction_id} - {payment_successful.amount} {payment_successful.currency}"
        assert str(payment_successful) == expected

    def test_payment_uuid_primary_key(self, payment_successful):
        """Test payment has UUID primary key."""
        import uuid
        assert isinstance(payment_successful.id, uuid.UUID)


# ============================================================================
# Payment Status Tests
# ============================================================================

@pytest.mark.django_db
class TestPaymentStatus:
    """Tests for payment status values."""

    def test_all_status_choices_valid(self):
        """Test all status choices are valid."""
        valid_statuses = [
            Payment.PENDING,
            Payment.PROCESSING,
            Payment.SUCCEEDED,
            Payment.FAILED,
            Payment.CANCELLED,
            Payment.REFUNDED,
        ]
        for status in valid_statuses:
            assert status in dict(Payment.STATUS_CHOICES)

    def test_all_method_choices_valid(self):
        """Test all payment method choices are valid."""
        valid_methods = [
            Payment.CARD,
            Payment.BANK_TRANSFER,
            Payment.CASH,
            Payment.CHECK,
            Payment.OTHER,
        ]
        for method in valid_methods:
            assert method in dict(Payment.METHOD_CHOICES)


# ============================================================================
# Payment Properties Tests
# ============================================================================

@pytest.mark.django_db
class TestPaymentProperties:
    """Tests for payment properties."""

    def test_is_successful_true(self, payment_successful):
        """Test is_successful when payment succeeded."""
        assert payment_successful.is_successful is True

    def test_is_successful_false_pending(self, payment_pending):
        """Test is_successful when payment pending."""
        assert payment_pending.is_successful is False

    def test_is_successful_false_failed(self, payment_failed):
        """Test is_successful when payment failed."""
        assert payment_failed.is_successful is False

    def test_net_amount_no_refund(self, payment_successful):
        """Test net_amount with no refund."""
        assert payment_successful.net_amount == payment_successful.amount

    def test_net_amount_with_refund(self, payment_successful):
        """Test net_amount with partial refund."""
        refund_amount = Decimal('500.00')
        payment_successful.refunded_amount = refund_amount
        payment_successful.save()

        expected = payment_successful.amount - refund_amount
        assert payment_successful.net_amount == expected


# ============================================================================
# Payment Refund Tests
# ============================================================================

@pytest.mark.django_db
class TestPaymentRefund:
    """Tests for payment refund functionality."""

    def test_process_refund_full(self, payment_successful):
        """Test processing a full refund."""
        refund_amount = payment_successful.amount
        payment_successful.process_refund(refund_amount, 'Customer request')

        assert payment_successful.status == Payment.REFUNDED
        assert payment_successful.refunded_amount == refund_amount
        assert payment_successful.refunded_at is not None
        assert payment_successful.refund_reason == 'Customer request'

    def test_process_refund_partial(self, payment_successful):
        """Test processing a partial refund."""
        partial_refund = payment_successful.amount / 2
        payment_successful.process_refund(partial_refund, 'Partial refund')

        assert payment_successful.refunded_amount == partial_refund
        # Status should not be REFUNDED for partial refund
        assert payment_successful.status == Payment.SUCCEEDED

    def test_process_refund_non_successful_fails(self, payment_pending):
        """Test refund fails for non-successful payment."""
        with pytest.raises(ValueError) as exc_info:
            payment_pending.process_refund(Decimal('100.00'))

        assert 'Only successful payments can be refunded' in str(exc_info.value)

    def test_process_refund_exceeds_amount_fails(self, payment_successful):
        """Test refund fails when exceeding available amount."""
        excess_amount = payment_successful.amount + Decimal('100.00')

        with pytest.raises(ValueError) as exc_info:
            payment_successful.process_refund(excess_amount)

        assert 'exceeds available amount' in str(exc_info.value)

    def test_multiple_partial_refunds(self, payment_successful):
        """Test multiple partial refunds."""
        first_refund = payment_successful.amount / 3
        second_refund = payment_successful.amount / 3

        payment_successful.process_refund(first_refund)
        assert payment_successful.refunded_amount == first_refund

        payment_successful.process_refund(second_refund)
        expected_total = first_refund + second_refund
        assert payment_successful.refunded_amount == expected_total


# ============================================================================
# Payment Stripe Integration Tests
# ============================================================================

@pytest.mark.django_db
class TestPaymentStripeIntegration:
    """Tests for payment Stripe integration fields."""

    def test_stripe_payment_intent_id(self, payment_successful):
        """Test Stripe payment intent ID field."""
        assert payment_successful.stripe_payment_intent_id is not None

    def test_stripe_charge_id(self, payment_successful):
        """Test Stripe charge ID field."""
        assert payment_successful.stripe_charge_id is not None

    def test_stripe_customer_id(self, invoice_sent):
        """Test Stripe customer ID field."""
        payment = Payment.objects.create(
            invoice=invoice_sent,
            amount=Decimal('100.00'),
            payment_method=Payment.CARD,
            status=Payment.SUCCEEDED,
            payment_date=timezone.now(),
            stripe_customer_id='cus_test123',
        )

        assert payment.stripe_customer_id == 'cus_test123'


# ============================================================================
# Payment Card Details Tests
# ============================================================================

@pytest.mark.django_db
class TestPaymentCardDetails:
    """Tests for payment card details fields."""

    def test_card_last4(self, payment_successful):
        """Test card last 4 digits field."""
        assert payment_successful.card_last4 == '4242'

    def test_card_brand(self, payment_successful):
        """Test card brand field."""
        assert payment_successful.card_brand == 'visa'


# ============================================================================
# Payment Failure Tests
# ============================================================================

@pytest.mark.django_db
class TestPaymentFailure:
    """Tests for payment failure fields."""

    def test_failure_code(self, payment_failed):
        """Test failure code field."""
        assert payment_failed.failure_code == 'card_declined'

    def test_failure_message(self, payment_failed):
        """Test failure message field."""
        assert 'declined' in payment_failed.failure_message


# ============================================================================
# PaymentMethod Model Tests
# ============================================================================

@pytest.mark.django_db
class TestPaymentMethodModel:
    """Tests for the PaymentMethod model."""

    def test_create_payment_method(self, client_company):
        """Test creating a payment method."""
        pm = PaymentMethod.objects.create(
            client=client_company,
            type=Payment.CARD,
            is_default=True,
            card_last4='1234',
            card_brand='mastercard',
            card_exp_month=6,
            card_exp_year=2026,
            stripe_payment_method_id='pm_test_new',
        )

        assert pm.client == client_company
        assert pm.type == Payment.CARD
        assert pm.is_default is True

    def test_payment_method_string_representation_card(self, payment_method_card):
        """Test payment method string representation for card."""
        expected = f"{payment_method_card.card_brand} .... {payment_method_card.card_last4}"
        assert str(payment_method_card) == expected

    def test_payment_method_string_representation_other(self, client_company):
        """Test payment method string representation for non-card."""
        pm = PaymentMethod.objects.create(
            client=client_company,
            type=Payment.BANK_TRANSFER,
            stripe_payment_method_id='pm_bank_test',
        )

        assert 'Bank Transfer' in str(pm)

    def test_payment_method_uuid_primary_key(self, payment_method_card):
        """Test payment method has UUID primary key."""
        import uuid
        assert isinstance(payment_method_card.id, uuid.UUID)

    def test_only_one_default_per_client(self, client_company):
        """Test only one payment method can be default per client."""
        pm1 = PaymentMethod.objects.create(
            client=client_company,
            type=Payment.CARD,
            is_default=True,
            card_last4='1111',
            stripe_payment_method_id='pm_first',
        )

        pm2 = PaymentMethod.objects.create(
            client=client_company,
            type=Payment.CARD,
            is_default=True,
            card_last4='2222',
            stripe_payment_method_id='pm_second',
        )

        pm1.refresh_from_db()
        assert pm1.is_default is False
        assert pm2.is_default is True


# ============================================================================
# Payment Metadata Tests
# ============================================================================

@pytest.mark.django_db
class TestPaymentMetadata:
    """Tests for payment metadata JSON field."""

    def test_metadata_default_empty_dict(self, invoice_sent):
        """Test metadata defaults to empty dict."""
        payment = Payment.objects.create(
            invoice=invoice_sent,
            amount=Decimal('100.00'),
            payment_method=Payment.CARD,
            status=Payment.PENDING,
            payment_date=timezone.now(),
        )

        assert payment.metadata == {}

    def test_metadata_stores_json(self, payment_successful):
        """Test metadata can store JSON data."""
        payment_successful.metadata = {
            'order_id': 'ORD-12345',
            'customer_note': 'Expedited processing',
        }
        payment_successful.save()

        payment_successful.refresh_from_db()
        assert payment_successful.metadata['order_id'] == 'ORD-12345'


# ============================================================================
# Payment Edge Cases
# ============================================================================

@pytest.mark.django_db
class TestPaymentEdgeCases:
    """Edge case tests for Payment model."""

    def test_payment_receipt_fields(self, payment_successful):
        """Test payment receipt fields."""
        assert payment_successful.receipt_url is not None
        assert payment_successful.receipt_sent is True

    def test_payment_notes_field(self, invoice_sent):
        """Test payment notes field."""
        payment = Payment.objects.create(
            invoice=invoice_sent,
            amount=Decimal('100.00'),
            payment_method=Payment.CARD,
            status=Payment.SUCCEEDED,
            payment_date=timezone.now(),
            notes='Payment processed via phone.',
        )

        assert 'phone' in payment.notes

    def test_payment_different_currencies(self, invoice_sent):
        """Test payment with different currencies."""
        payment = Payment.objects.create(
            invoice=invoice_sent,
            amount=Decimal('100.00'),
            currency='EUR',
            payment_method=Payment.CARD,
            status=Payment.SUCCEEDED,
            payment_date=timezone.now(),
        )

        assert payment.currency == 'EUR'

    def test_payment_timestamps(self, payment_successful):
        """Test payment has created_at and updated_at."""
        assert payment_successful.created_at is not None
        assert payment_successful.updated_at is not None
