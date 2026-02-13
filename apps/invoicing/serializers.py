"""
Serializers for the invoicing app.
"""

from rest_framework import serializers
from .models import Invoice, InvoiceItem, RecurringInvoice, LateFeePolicy, PaymentReminder
from apps.clients.serializers import ClientListSerializer
from apps.contracts.serializers import ContractListSerializer


class InvoiceItemSerializer(serializers.ModelSerializer):
    """
    Serializer for invoice items.
    """
    invoice = serializers.PrimaryKeyRelatedField(
        queryset=Invoice.objects.all(),
        required=False,
    )

    class Meta:
        model = InvoiceItem
        fields = ['id', 'invoice', 'description', 'quantity', 'unit_price', 'amount', 'order']
        read_only_fields = ['id', 'amount']


class InvoiceListSerializer(serializers.ModelSerializer):
    """
    Serializer for invoice list view (minimal fields).
    """
    client_name = serializers.SerializerMethodField()
    is_overdue = serializers.ReadOnlyField()
    balance_due = serializers.ReadOnlyField()

    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'client', 'client_name', 'contract',
            'status', 'issue_date', 'due_date', 'total', 'paid_amount',
            'balance_due', 'is_overdue', 'currency', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'invoice_number', 'created_at', 'updated_at']

    def get_client_name(self, obj):
        """Get client display name."""
        return obj.client.get_display_name()


class InvoiceDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for invoice detail view.
    """
    client = ClientListSerializer(read_only=True)
    contract = ContractListSerializer(read_only=True)
    items = InvoiceItemSerializer(many=True, read_only=True)
    is_overdue = serializers.ReadOnlyField()
    balance_due = serializers.ReadOnlyField()
    is_fully_paid = serializers.ReadOnlyField()

    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = [
            'id', 'invoice_number', 'created_at', 'updated_at',
            'subtotal', 'tax_amount', 'total'
        ]


class InvoiceCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating invoices.
    """
    items = InvoiceItemSerializer(many=True, required=False)
    invoice_number = serializers.CharField(read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'client', 'contract', 'status', 'issue_date', 'due_date',
            'tax_rate', 'discount_amount', 'currency', 'notes', 'terms',
            'metadata', 'items', 'subtotal', 'tax_amount', 'total',
        ]
        read_only_fields = ['id', 'invoice_number', 'subtotal', 'tax_amount', 'total']

    def validate(self, data):
        """Validate invoice data."""
        # Validate due date is after issue date
        if data.get('due_date') and data.get('issue_date'):
            if data['due_date'] < data['issue_date']:
                raise serializers.ValidationError({
                    'due_date': 'Due date must be after issue date.'
                })

        return data

    def create(self, validated_data):
        """Create invoice with items."""
        items_data = validated_data.pop('items', [])
        invoice = Invoice.objects.create(**validated_data)

        # Create items
        for item_data in items_data:
            InvoiceItem.objects.create(invoice=invoice, **item_data)

        # Calculate totals
        invoice.calculate_totals()

        return invoice

    def update(self, instance, validated_data):
        """Update invoice and items."""
        items_data = validated_data.pop('items', None)

        # Update invoice fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update items if provided
        if items_data is not None:
            # Delete existing items not in the update
            existing_item_ids = [i.get('id') for i in items_data if i.get('id')]
            instance.items.exclude(id__in=existing_item_ids).delete()

            # Update or create items
            for item_data in items_data:
                item_id = item_data.pop('id', None)
                if item_id:
                    InvoiceItem.objects.filter(id=item_id).update(**item_data)
                else:
                    InvoiceItem.objects.create(invoice=instance, **item_data)

        # Recalculate totals
        instance.calculate_totals()

        return instance


class InvoiceStatsSerializer(serializers.Serializer):
    """
    Serializer for invoice statistics.
    """
    total_invoices = serializers.IntegerField()
    draft_invoices = serializers.IntegerField()
    sent_invoices = serializers.IntegerField()
    paid_invoices = serializers.IntegerField()
    overdue_invoices = serializers.IntegerField()
    total_invoiced = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_paid = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_outstanding = serializers.DecimalField(max_digits=12, decimal_places=2)


# --- Recurring Invoice Serializers ---

class RecurringInvoiceSerializer(serializers.ModelSerializer):
    """Serializer for recurring invoice list and detail."""
    client_name = serializers.SerializerMethodField()
    is_due = serializers.ReadOnlyField()

    class Meta:
        model = RecurringInvoice
        fields = [
            'id', 'client', 'client_name', 'contract', 'template_name',
            'frequency', 'start_date', 'end_date', 'next_run_date',
            'amount', 'currency', 'tax_rate', 'discount_amount',
            'items_template', 'auto_send', 'status', 'invoices_generated',
            'last_generated_at', 'owner', 'notes', 'metadata',
            'is_due', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'invoices_generated', 'last_generated_at', 'created_at', 'updated_at']

    def get_client_name(self, obj):
        return obj.client.get_display_name()


class RecurringInvoiceCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating recurring invoices."""

    class Meta:
        model = RecurringInvoice
        fields = [
            'id', 'client', 'contract', 'template_name', 'frequency',
            'start_date', 'end_date', 'next_run_date', 'amount',
            'currency', 'tax_rate', 'discount_amount', 'items_template',
            'auto_send', 'notes', 'metadata'
        ]
        read_only_fields = ['id']

    def validate(self, data):
        if data.get('end_date') and data.get('start_date'):
            if data['end_date'] < data['start_date']:
                raise serializers.ValidationError({
                    'end_date': 'End date must be after start date.'
                })
        return data


# --- Late Fee Policy Serializers ---

class LateFeePolicySerializer(serializers.ModelSerializer):
    """Serializer for late fee policies."""

    class Meta:
        model = LateFeePolicy
        fields = [
            'id', 'name', 'fee_type', 'fee_amount', 'grace_period_days',
            'max_fee_amount', 'is_compound', 'apply_frequency', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# --- Payment Reminder Serializers ---

class PaymentReminderSerializer(serializers.ModelSerializer):
    """Serializer for payment reminders."""
    invoice_number = serializers.SerializerMethodField()
    is_due = serializers.ReadOnlyField()

    class Meta:
        model = PaymentReminder
        fields = [
            'id', 'invoice', 'invoice_number', 'reminder_type',
            'days_offset', 'status', 'scheduled_date', 'sent_at',
            'is_due', 'created_at'
        ]
        read_only_fields = ['id', 'sent_at', 'created_at']

    def get_invoice_number(self, obj):
        return obj.invoice.invoice_number
