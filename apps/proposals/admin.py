"""
Admin configuration for proposals app.
"""

from django.contrib import admin
from .models import Proposal, ProposalSection, ProposalPricingOption, ProposalActivity


class ProposalSectionInline(admin.TabularInline):
    """Inline admin for proposal sections."""
    model = ProposalSection
    extra = 1
    fields = ['title', 'section_type', 'order', 'content']
    ordering = ['order']


class ProposalPricingOptionInline(admin.TabularInline):
    """Inline admin for proposal pricing options."""
    model = ProposalPricingOption
    extra = 1
    fields = ['name', 'price', 'is_recommended', 'order', 'description']
    ordering = ['order']


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    """Admin for Proposal model."""

    list_display = [
        'proposal_number', 'client', 'title', 'status',
        'total_value', 'currency', 'valid_until', 'is_expired',
        'owner', 'created_at'
    ]
    list_filter = ['status', 'currency', 'created_at']
    search_fields = [
        'proposal_number', 'title', 'description',
        'client__first_name', 'client__last_name', 'client__company_name'
    ]
    readonly_fields = ['proposal_number', 'created_at', 'updated_at']
    inlines = [ProposalSectionInline, ProposalPricingOptionInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('proposal_number', 'client', 'title', 'description', 'status')
        }),
        ('Financial Details', {
            'fields': ('total_value', 'currency', 'valid_until')
        }),
        ('Assignment', {
            'fields': ('owner',)
        }),
        ('Contract Link', {
            'fields': ('contract',)
        }),
        ('Tracking Dates', {
            'fields': ('sent_at', 'viewed_at', 'accepted_at', 'declined_at')
        }),
        ('Client Response', {
            'fields': ('client_message', 'signature')
        }),
        ('Documents', {
            'fields': ('pdf_file',)
        }),
        ('Metadata', {
            'fields': ('metadata',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def is_expired(self, obj):
        """Display is_expired property."""
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = 'Expired'


@admin.register(ProposalSection)
class ProposalSectionAdmin(admin.ModelAdmin):
    """Admin for ProposalSection model."""

    list_display = ['title', 'proposal', 'section_type', 'order', 'created_at']
    list_filter = ['section_type']
    search_fields = ['title', 'content', 'proposal__proposal_number']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('proposal', 'title', 'section_type', 'order')
        }),
        ('Content', {
            'fields': ('content',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProposalPricingOption)
class ProposalPricingOptionAdmin(admin.ModelAdmin):
    """Admin for ProposalPricingOption model."""

    list_display = ['name', 'proposal', 'price', 'is_recommended', 'order', 'created_at']
    list_filter = ['is_recommended']
    search_fields = ['name', 'description', 'proposal__proposal_number']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('proposal', 'name', 'description', 'price', 'is_recommended', 'order')
        }),
        ('Features', {
            'fields': ('features',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProposalActivity)
class ProposalActivityAdmin(admin.ModelAdmin):
    """Admin for ProposalActivity model."""

    list_display = ['proposal', 'activity_type', 'user', 'ip_address', 'created_at']
    list_filter = ['activity_type', 'created_at']
    search_fields = ['proposal__proposal_number', 'description']
    readonly_fields = ['created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('proposal', 'activity_type', 'description')
        }),
        ('User Details', {
            'fields': ('user', 'ip_address')
        }),
        ('Metadata', {
            'fields': ('metadata',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
