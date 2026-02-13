"""
Admin configuration for invoicing app.
"""

from django.contrib import admin
from .models import Invoice, InvoiceItem, RecurringInvoice, LateFeePolicy, PaymentReminder


class InvoiceItemInline(admin.TabularInline):
    """Inline admin for invoice items."""
    model = InvoiceItem
    extra = 1
    fields = ['description', 'quantity', 'unit_price', 'amount', 'order']
    readonly_fields = ['amount']
    ordering = ['order']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """Admin for Invoice model."""

    list_display = [
        'invoice_number', 'client', 'status', 'issue_date', 'due_date',
        'total', 'paid_amount', 'balance_due', 'is_overdue'
    ]
    list_filter = ['status', 'issue_date', 'due_date']
    search_fields = ['invoice_number', 'client__first_name', 'client__last_name', 'client__company_name']
    readonly_fields = ['invoice_number', 'subtotal', 'tax_amount', 'total', 'created_at', 'updated_at']
    inlines = [InvoiceItemInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('invoice_number', 'client', 'contract', 'status')
        }),
        ('Dates', {
            'fields': ('issue_date', 'due_date')
        }),
        ('Financial Details', {
            'fields': (
                'subtotal', 'tax_rate', 'tax_amount', 'discount_amount',
                'total', 'paid_amount', 'currency'
            )
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_reference', 'paid_at')
        }),
        ('Notes & Terms', {
            'fields': ('notes', 'terms')
        }),
        ('Documents', {
            'fields': ('pdf_file',)
        }),
        ('Stripe Integration', {
            'fields': ('stripe_invoice_id', 'stripe_payment_intent_id')
        }),
        ('Email Tracking', {
            'fields': ('sent_at', 'viewed_at')
        }),
        ('Metadata', {
            'fields': ('metadata',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def balance_due(self, obj):
        """Display balance due."""
        return obj.balance_due
    balance_due.short_description = 'Balance Due'


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    """Admin for InvoiceItem model."""

    list_display = ['description', 'invoice', 'quantity', 'unit_price', 'amount']
    search_fields = ['description', 'invoice__invoice_number']
    readonly_fields = ['amount']

    fieldsets = (
        ('Basic Information', {
            'fields': ('invoice', 'description', 'quantity', 'unit_price', 'amount', 'order')
        }),
    )


@admin.register(RecurringInvoice)
class RecurringInvoiceAdmin(admin.ModelAdmin):
    """Admin for RecurringInvoice model."""

    list_display = [
        'name', 'client', 'frequency', 'status', 'amount',
        'next_run_date', 'total_generated', 'auto_send'
    ]
    list_filter = ['status', 'frequency', 'auto_send', 'next_run_date']
    search_fields = ['name', 'client__first_name', 'client__last_name', 'client__company_name']
    readonly_fields = ['total_generated', 'last_generated_at', 'created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'client', 'contract', 'status')
        }),
        ('Schedule', {
            'fields': ('frequency', 'start_date', 'end_date', 'next_run_date')
        }),
        ('Invoice Details', {
            'fields': ('amount', 'tax_rate', 'currency', 'items_template')
        }),
        ('Settings', {
            'fields': ('auto_send', 'payment_terms_days')
        }),
        ('Statistics', {
            'fields': ('total_generated', 'last_generated_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LateFeePolicy)
class LateFeePolicyAdmin(admin.ModelAdmin):
    """Admin for LateFeePolicy model."""

    list_display = ['name', 'fee_type', 'fee_amount', 'grace_period_days', 'apply_frequency', 'is_active']
    list_filter = ['fee_type', 'apply_frequency', 'is_active']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'is_active')
        }),
        ('Fee Configuration', {
            'fields': ('fee_type', 'fee_amount', 'max_fee_amount', 'grace_period_days', 'apply_frequency')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PaymentReminder)
class PaymentReminderAdmin(admin.ModelAdmin):
    """Admin for PaymentReminder model."""

    list_display = ['invoice', 'reminder_type', 'days_offset', 'scheduled_date', 'status', 'sent_at']
    list_filter = ['reminder_type', 'status', 'scheduled_date']
    search_fields = ['invoice__invoice_number']
    readonly_fields = ['sent_at', 'created_at']

    fieldsets = (
        ('Reminder Details', {
            'fields': ('invoice', 'reminder_type', 'days_offset', 'scheduled_date')
        }),
        ('Status', {
            'fields': ('status', 'sent_at', 'subject', 'message')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
