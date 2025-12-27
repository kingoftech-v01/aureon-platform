"""
Admin configuration for payments app.
"""

from django.contrib import admin
from .models import Payment, PaymentMethod


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin for Payment model."""

    list_display = [
        'transaction_id', 'invoice', 'amount', 'currency',
        'payment_method', 'status', 'payment_date'
    ]
    list_filter = ['status', 'payment_method', 'payment_date']
    search_fields = ['transaction_id', 'invoice__invoice_number', 'stripe_payment_intent_id']
    readonly_fields = ['transaction_id', 'created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('transaction_id', 'invoice', 'amount', 'currency', 'payment_method', 'status')
        }),
        ('Payment Date', {
            'fields': ('payment_date',)
        }),
        ('Stripe Integration', {
            'fields': ('stripe_payment_intent_id', 'stripe_charge_id', 'stripe_customer_id')
        }),
        ('Card Details', {
            'fields': ('card_last4', 'card_brand')
        }),
        ('Refund Information', {
            'fields': ('refunded_amount', 'refund_reason', 'refunded_at')
        }),
        ('Failure Information', {
            'fields': ('failure_code', 'failure_message')
        }),
        ('Receipt', {
            'fields': ('receipt_url', 'receipt_sent')
        }),
        ('Notes', {
            'fields': ('notes', 'metadata')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    """Admin for PaymentMethod model."""

    list_display = ['client', 'type', 'card_brand', 'card_last4', 'is_default', 'is_active']
    list_filter = ['type', 'is_default', 'is_active']
    search_fields = ['client__first_name', 'client__last_name', 'stripe_payment_method_id']

    fieldsets = (
        ('Basic Information', {
            'fields': ('client', 'type', 'is_default', 'is_active')
        }),
        ('Card Details', {
            'fields': ('card_last4', 'card_brand', 'card_exp_month', 'card_exp_year')
        }),
        ('Stripe Integration', {
            'fields': ('stripe_payment_method_id',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
