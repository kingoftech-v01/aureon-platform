"""
Admin configuration for contracts app.
"""

from django.contrib import admin
from .models import Contract, ContractMilestone


class ContractMilestoneInline(admin.TabularInline):
    """Inline admin for contract milestones."""
    model = ContractMilestone
    extra = 1
    fields = ['title', 'due_date', 'amount', 'status', 'order']
    ordering = ['order', 'due_date']


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    """Admin for Contract model."""

    list_display = [
        'contract_number', 'client', 'title', 'contract_type',
        'value', 'status', 'start_date', 'end_date', 'is_signed'
    ]
    list_filter = ['status', 'contract_type', 'signed_by_client', 'signed_by_company']
    search_fields = ['contract_number', 'title', 'client__first_name', 'client__last_name', 'client__company_name']
    readonly_fields = ['contract_number', 'created_at', 'updated_at']
    inlines = [ContractMilestoneInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('contract_number', 'client', 'title', 'description', 'contract_type', 'status')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date')
        }),
        ('Financial Details', {
            'fields': ('value', 'currency', 'hourly_rate', 'estimated_hours', 'payment_terms', 'invoice_schedule')
        }),
        ('Terms & Conditions', {
            'fields': ('terms_and_conditions',)
        }),
        ('Signature', {
            'fields': (
                'signed_by_client', 'signed_by_company', 'signed_at',
                'signature_client', 'signature_company', 'docusign_envelope_id'
            )
        }),
        ('Documents', {
            'fields': ('contract_file',)
        }),
        ('Assignment & Progress', {
            'fields': ('owner', 'completion_percentage')
        }),
        ('Financial Tracking', {
            'fields': ('invoiced_amount', 'paid_amount')
        }),
        ('Notes', {
            'fields': ('notes', 'metadata')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ContractMilestone)
class ContractMilestoneAdmin(admin.ModelAdmin):
    """Admin for ContractMilestone model."""

    list_display = ['title', 'contract', 'due_date', 'amount', 'status', 'completed_at']
    list_filter = ['status', 'invoice_generated']
    search_fields = ['title', 'contract__contract_number', 'contract__title']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('contract', 'title', 'description', 'due_date', 'amount', 'status', 'order')
        }),
        ('Completion', {
            'fields': ('completed_at', 'completed_by')
        }),
        ('Invoice', {
            'fields': ('invoice_generated',)
        }),
        ('Deliverables', {
            'fields': ('deliverables', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
