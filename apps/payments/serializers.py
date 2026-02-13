"""
Serializers for the payments app.
"""

from rest_framework import serializers
from .models import Payment, PaymentMethod
from apps.invoicing.serializers import InvoiceListSerializer


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for payments.
    """
    invoice_number = serializers.SerializerMethodField()
    client_name = serializers.SerializerMethodField()
    is_successful = serializers.ReadOnlyField()
    net_amount = serializers.ReadOnlyField()

    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = [
            'id', 'transaction_id', 'created_at', 'updated_at',
            'stripe_payment_intent_id', 'stripe_charge_id'
        ]

    def get_invoice_number(self, obj):
        """Get invoice number."""
        if obj.invoice:
            return obj.invoice.invoice_number
        return None

    def get_client_name(self, obj):
        """Get client name."""
        if obj.invoice and obj.invoice.client:
            return obj.invoice.client.get_display_name()
        return None


class PaymentMethodSerializer(serializers.ModelSerializer):
    """
    Serializer for payment methods.
    """

    class Meta:
        model = PaymentMethod
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class PaymentStatsSerializer(serializers.Serializer):
    """
    Serializer for payment statistics.
    """
    total_payments = serializers.IntegerField()
    successful_payments = serializers.IntegerField()
    failed_payments = serializers.IntegerField()
    refunded_payments = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_refunded = serializers.DecimalField(max_digits=12, decimal_places=2)
