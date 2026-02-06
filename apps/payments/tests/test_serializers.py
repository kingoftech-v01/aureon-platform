"""
Tests for payments app serializers.
"""

import pytest
from decimal import Decimal
from unittest.mock import patch

from apps.payments.models import Payment, PaymentMethod
from apps.payments.serializers import (
    PaymentSerializer,
    PaymentMethodSerializer,
    PaymentStatsSerializer,
)


# ============================================================================
# PaymentSerializer Tests
# ============================================================================


class TestPaymentSerializer:
    """Tests for PaymentSerializer."""

    @pytest.mark.django_db
    def test_serializes_all_fields(self, payment_successful):
        """Test that all expected fields are present."""
        serializer = PaymentSerializer(payment_successful)
        data = serializer.data

        assert 'id' in data
        assert 'invoice' in data
        assert 'amount' in data
        assert 'currency' in data
        assert 'payment_method' in data
        assert 'status' in data
        assert 'transaction_id' in data
        assert 'payment_date' in data
        assert 'invoice_number' in data
        assert 'client_name' in data
        assert 'is_successful' in data
        assert 'net_amount' in data

    @pytest.mark.django_db
    def test_invoice_number_field(self, payment_successful):
        """Test that invoice_number is correctly resolved."""
        serializer = PaymentSerializer(payment_successful)
        data = serializer.data

        assert data['invoice_number'] == payment_successful.invoice.invoice_number

    @pytest.mark.django_db
    def test_client_name_field(self, payment_successful):
        """Test that client_name is correctly resolved."""
        serializer = PaymentSerializer(payment_successful)
        data = serializer.data

        expected_name = payment_successful.invoice.client.get_display_name()
        assert data['client_name'] == expected_name

    @pytest.mark.django_db
    def test_is_successful_true(self, payment_successful):
        """Test is_successful for a successful payment."""
        serializer = PaymentSerializer(payment_successful)
        data = serializer.data

        assert data['is_successful'] is True

    @pytest.mark.django_db
    def test_is_successful_false_pending(self, payment_pending):
        """Test is_successful for a pending payment."""
        serializer = PaymentSerializer(payment_pending)
        data = serializer.data

        assert data['is_successful'] is False

    @pytest.mark.django_db
    def test_is_successful_false_failed(self, payment_failed):
        """Test is_successful for a failed payment."""
        serializer = PaymentSerializer(payment_failed)
        data = serializer.data

        assert data['is_successful'] is False

    @pytest.mark.django_db
    def test_net_amount_no_refund(self, payment_successful):
        """Test net_amount when no refund has been made."""
        serializer = PaymentSerializer(payment_successful)
        data = serializer.data

        assert Decimal(data['net_amount']) == payment_successful.amount

    @pytest.mark.django_db
    def test_net_amount_with_refund(self, payment_successful):
        """Test net_amount after a partial refund."""
        payment_successful.refunded_amount = Decimal('500.00')
        payment_successful.save()

        serializer = PaymentSerializer(payment_successful)
        data = serializer.data

        expected = payment_successful.amount - Decimal('500.00')
        assert Decimal(data['net_amount']) == expected

    @pytest.mark.django_db
    def test_net_amount_full_refund(self, payment_successful):
        """Test net_amount after full refund."""
        payment_successful.refunded_amount = payment_successful.amount
        payment_successful.status = Payment.REFUNDED
        payment_successful.save()

        serializer = PaymentSerializer(payment_successful)
        data = serializer.data

        assert Decimal(data['net_amount']) == Decimal('0.00')

    @pytest.mark.django_db
    def test_read_only_fields(self):
        """Test that read-only fields are declared."""
        read_only = PaymentSerializer.Meta.read_only_fields
        assert 'id' in read_only
        assert 'transaction_id' in read_only
        assert 'created_at' in read_only
        assert 'updated_at' in read_only
        assert 'stripe_payment_intent_id' in read_only
        assert 'stripe_charge_id' in read_only

    @pytest.mark.django_db
    def test_serializes_stripe_fields(self, payment_successful):
        """Test that stripe fields are serialized."""
        serializer = PaymentSerializer(payment_successful)
        data = serializer.data

        assert data['stripe_payment_intent_id'] == 'pi_test_successful'
        assert data['stripe_charge_id'] == 'ch_test_successful'

    @pytest.mark.django_db
    def test_serializes_card_details(self, payment_successful):
        """Test that card details are serialized."""
        serializer = PaymentSerializer(payment_successful)
        data = serializer.data

        assert data['card_last4'] == '4242'
        assert data['card_brand'] == 'visa'

    @pytest.mark.django_db
    def test_serializes_failure_info(self, payment_failed):
        """Test that failure details are serialized."""
        serializer = PaymentSerializer(payment_failed)
        data = serializer.data

        assert data['failure_code'] == 'card_declined'
        assert data['failure_message'] == 'Your card was declined.'

    @pytest.mark.django_db
    def test_serializes_receipt_info(self, payment_successful):
        """Test that receipt info is serialized."""
        serializer = PaymentSerializer(payment_successful)
        data = serializer.data

        assert data['receipt_url'] == 'https://stripe.com/receipts/test'
        assert data['receipt_sent'] is True

    @pytest.mark.django_db
    def test_client_name_company_type(self, payment_successful):
        """Test client_name for company-type client."""
        serializer = PaymentSerializer(payment_successful)
        data = serializer.data

        # invoice_paid -> client_company -> company_name='Test Company Inc.'
        assert data['client_name'] == 'Test Company Inc.'

    @pytest.mark.django_db
    def test_client_name_individual_type(self, payment_failed):
        """Test client_name for individual-type client."""
        serializer = PaymentSerializer(payment_failed)
        data = serializer.data

        # invoice_overdue -> client_individual -> Jane Smith
        expected = payment_failed.invoice.client.get_display_name()
        assert data['client_name'] == expected


# ============================================================================
# PaymentMethodSerializer Tests
# ============================================================================


class TestPaymentMethodSerializer:
    """Tests for PaymentMethodSerializer."""

    @pytest.mark.django_db
    def test_serializes_all_fields(self, payment_method_card):
        """Test that all expected fields are present."""
        serializer = PaymentMethodSerializer(payment_method_card)
        data = serializer.data

        assert 'id' in data
        assert 'client' in data
        assert 'type' in data
        assert 'is_default' in data
        assert 'card_last4' in data
        assert 'card_brand' in data
        assert 'card_exp_month' in data
        assert 'card_exp_year' in data
        assert 'stripe_payment_method_id' in data
        assert 'is_active' in data
        assert 'created_at' in data
        assert 'updated_at' in data

    @pytest.mark.django_db
    def test_serialized_values_match(self, payment_method_card):
        """Test that serialized values match the model instance."""
        serializer = PaymentMethodSerializer(payment_method_card)
        data = serializer.data

        assert data['type'] == Payment.CARD
        assert data['is_default'] is True
        assert data['card_last4'] == '4242'
        assert data['card_brand'] == 'visa'
        assert data['card_exp_month'] == 12
        assert data['card_exp_year'] == 2025
        assert data['stripe_payment_method_id'] == 'pm_test_card'
        assert data['is_active'] is True

    @pytest.mark.django_db
    def test_read_only_fields(self):
        """Test that read-only fields are declared."""
        read_only = PaymentMethodSerializer.Meta.read_only_fields
        assert 'id' in read_only
        assert 'created_at' in read_only
        assert 'updated_at' in read_only

    @pytest.mark.django_db
    def test_valid_data_deserialization(self, client_company):
        """Test deserialization with valid data."""
        data = {
            'client': str(client_company.id),
            'type': Payment.CARD,
            'is_default': False,
            'card_last4': '9876',
            'card_brand': 'amex',
            'card_exp_month': 3,
            'card_exp_year': 2028,
            'stripe_payment_method_id': 'pm_new_card_test',
            'is_active': True,
        }
        serializer = PaymentMethodSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    @pytest.mark.django_db
    def test_missing_required_client(self):
        """Test that client is required."""
        data = {
            'type': Payment.CARD,
            'stripe_payment_method_id': 'pm_no_client',
        }
        serializer = PaymentMethodSerializer(data=data)
        assert not serializer.is_valid()
        assert 'client' in serializer.errors

    @pytest.mark.django_db
    def test_missing_required_stripe_id(self, client_company):
        """Test that stripe_payment_method_id is required."""
        data = {
            'client': str(client_company.id),
            'type': Payment.CARD,
        }
        serializer = PaymentMethodSerializer(data=data)
        assert not serializer.is_valid()
        assert 'stripe_payment_method_id' in serializer.errors

    @pytest.mark.django_db
    def test_bank_transfer_type(self, client_company):
        """Test serialization of bank transfer payment method."""
        data = {
            'client': str(client_company.id),
            'type': Payment.BANK_TRANSFER,
            'stripe_payment_method_id': 'pm_bank_test',
            'is_default': False,
            'is_active': True,
        }
        serializer = PaymentMethodSerializer(data=data)
        assert serializer.is_valid(), serializer.errors


# ============================================================================
# PaymentStatsSerializer Tests
# ============================================================================


class TestPaymentStatsSerializer:
    """Tests for PaymentStatsSerializer."""

    def test_serializes_stats_data(self):
        """Test serialization of statistics data."""
        stats = {
            'total_payments': 50,
            'successful_payments': 40,
            'failed_payments': 5,
            'refunded_payments': 5,
            'total_amount': Decimal('100000.00'),
            'total_refunded': Decimal('5000.00'),
        }
        serializer = PaymentStatsSerializer(stats)
        data = serializer.data

        assert data['total_payments'] == 50
        assert data['successful_payments'] == 40
        assert data['failed_payments'] == 5
        assert data['refunded_payments'] == 5
        assert Decimal(data['total_amount']) == Decimal('100000.00')
        assert Decimal(data['total_refunded']) == Decimal('5000.00')

    def test_serializes_zero_stats(self):
        """Test serialization with all zeros."""
        stats = {
            'total_payments': 0,
            'successful_payments': 0,
            'failed_payments': 0,
            'refunded_payments': 0,
            'total_amount': Decimal('0.00'),
            'total_refunded': Decimal('0.00'),
        }
        serializer = PaymentStatsSerializer(stats)
        data = serializer.data

        assert data['total_payments'] == 0
        assert Decimal(data['total_amount']) == Decimal('0.00')

    def test_valid_data_deserialization(self):
        """Test that valid stats data passes validation."""
        data = {
            'total_payments': 10,
            'successful_payments': 8,
            'failed_payments': 1,
            'refunded_payments': 1,
            'total_amount': '50000.00',
            'total_refunded': '2500.00',
        }
        serializer = PaymentStatsSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_missing_required_field(self):
        """Test that missing required fields cause validation errors."""
        data = {
            'total_payments': 10,
            # Missing other required fields
        }
        serializer = PaymentStatsSerializer(data=data)
        assert not serializer.is_valid()
        assert 'successful_payments' in serializer.errors

    def test_all_fields_present(self):
        """Test that all expected fields are defined on the serializer."""
        serializer = PaymentStatsSerializer()
        field_names = set(serializer.fields.keys())
        expected = {
            'total_payments', 'successful_payments', 'failed_payments',
            'refunded_payments', 'total_amount', 'total_refunded',
        }
        assert expected == field_names
