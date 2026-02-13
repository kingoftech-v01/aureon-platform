"""
Admin configuration for expenses app.
"""

from django.contrib import admin
from .models import ExpenseCategory, Expense


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    """Admin for ExpenseCategory model."""

    list_display = ['name', 'color', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'description', 'color', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    """Admin for Expense model."""

    list_display = [
        'description', 'amount', 'currency', 'category', 'expense_date',
        'client', 'is_billable', 'is_invoiced', 'status', 'submitted_by',
        'payment_method', 'created_at',
    ]
    list_filter = [
        'status', 'category', 'is_billable', 'is_invoiced',
        'payment_method', 'expense_date',
    ]
    search_fields = [
        'description', 'vendor', 'receipt_number',
        'submitted_by__email', 'client__first_name',
        'client__last_name', 'client__company_name',
    ]
    readonly_fields = [
        'id', 'submitted_by', 'approved_by', 'approved_at',
        'created_at', 'updated_at',
    ]

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id', 'description', 'amount', 'currency', 'category',
                'expense_date', 'vendor',
            )
        }),
        ('Relationships', {
            'fields': ('client', 'contract', 'invoice')
        }),
        ('Billing', {
            'fields': ('is_billable', 'is_invoiced', 'payment_method')
        }),
        ('Receipt', {
            'fields': ('receipt_file', 'receipt_number')
        }),
        ('Status & Approval', {
            'fields': ('status', 'submitted_by', 'approved_by', 'approved_at')
        }),
        ('Notes & Metadata', {
            'fields': ('notes', 'tags', 'metadata')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
