"""
Admin interface for tenant management.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Tenant, Domain


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    """Admin interface for Tenant model."""

    list_display = [
        'name',
        'slug',
        'tenant_type',
        'plan',
        'status_badge',
        'trial_badge',
        'created_on',
    ]

    list_filter = [
        'tenant_type',
        'plan',
        'is_active',
        'is_trial',
        'created_on',
    ]

    search_fields = [
        'name',
        'slug',
        'contact_email',
        'schema_name',
    ]

    readonly_fields = [
        'schema_name',
        'created_on',
        'modified_on',
        'trial_status_display',
    ]

    fieldsets = (
        (_('Organization Information'), {
            'fields': (
                'name',
                'slug',
                'schema_name',
                'tenant_type',
                'contact_email',
                'contact_phone',
            )
        }),
        (_('Subscription & Billing'), {
            'fields': (
                'plan',
                'stripe_customer_id',
                'stripe_subscription_id',
                'is_trial',
                'trial_ends_at',
                'trial_status_display',
            )
        }),
        (_('Address'), {
            'fields': (
                'address_line1',
                'address_line2',
                'city',
                'state',
                'postal_code',
                'country',
            ),
            'classes': ('collapse',)
        }),
        (_('Branding'), {
            'fields': (
                'logo',
                'primary_color',
                'secondary_color',
            ),
            'classes': ('collapse',)
        }),
        (_('Settings'), {
            'fields': (
                'timezone',
                'currency',
                'language',
            )
        }),
        (_('Limits & Features'), {
            'fields': (
                'max_users',
                'max_clients',
                'max_contracts',
                'max_invoices_per_month',
                'enable_api_access',
                'enable_custom_branding',
                'enable_multi_currency',
                'enable_advanced_analytics',
            )
        }),
        (_('Status'), {
            'fields': (
                'is_active',
            )
        }),
        (_('Metadata'), {
            'fields': (
                'metadata',
                'created_on',
                'modified_on',
            ),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        """Display colored badge for tenant status."""
        if obj.is_active:
            color = 'green'
            text = 'Active'
        else:
            color = 'red'
            text = 'Inactive'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, text
        )
    status_badge.short_description = _('Status')

    def trial_badge(self, obj):
        """Display trial status badge."""
        if not obj.is_trial:
            return format_html('<span style="color: gray;">-</span>')

        if obj.is_on_trial:
            days_left = obj.days_until_trial_ends
            color = 'orange' if days_left < 7 else 'blue'
            return format_html(
                '<span style="color: {}; font-weight: bold;">Trial ({} days)</span>',
                color, days_left
            )
        else:
            return format_html('<span style="color: red; font-weight: bold;">Expired</span>')
    trial_badge.short_description = _('Trial')

    def trial_status_display(self, obj):
        """Display detailed trial status."""
        if not obj.is_trial:
            return "Not on trial"
        if obj.is_on_trial:
            return f"Trial active - {obj.days_until_trial_ends} days remaining"
        return "Trial expired"
    trial_status_display.short_description = _('Trial Status')

    actions = ['activate_tenants', 'deactivate_tenants', 'upgrade_to_starter']

    def activate_tenants(self, request, queryset):
        """Activate selected tenants."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} tenant(s) activated successfully.')
    activate_tenants.short_description = _('Activate selected tenants')

    def deactivate_tenants(self, request, queryset):
        """Deactivate selected tenants."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} tenant(s) deactivated successfully.')
    deactivate_tenants.short_description = _('Deactivate selected tenants')

    def upgrade_to_starter(self, request, queryset):
        """Upgrade selected tenants to Starter plan."""
        for tenant in queryset:
            tenant.upgrade_plan(Tenant.STARTER)
        self.message_user(request, f'{queryset.count()} tenant(s) upgraded to Starter plan.')
    upgrade_to_starter.short_description = _('Upgrade to Starter Plan')


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    """Admin interface for Domain model."""

    list_display = [
        'domain',
        'tenant',
        'primary_badge',
        'verified_badge',
        'ssl_badge',
        'created_at',
    ]

    list_filter = [
        'is_primary',
        'is_verified',
        'ssl_enabled',
        'created_at',
    ]

    search_fields = [
        'domain',
        'tenant__name',
        'tenant__slug',
    ]

    readonly_fields = [
        'created_at',
        'updated_at',
        'verified_at',
    ]

    fieldsets = (
        (_('Domain Information'), {
            'fields': (
                'domain',
                'tenant',
                'is_primary',
            )
        }),
        (_('Security & Verification'), {
            'fields': (
                'ssl_enabled',
                'is_verified',
                'verified_at',
            )
        }),
        (_('Timestamps'), {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    def primary_badge(self, obj):
        """Display badge for primary domain."""
        if obj.is_primary:
            return format_html('<span style="color: blue; font-weight: bold;">Primary</span>')
        return '-'
    primary_badge.short_description = _('Primary')

    def verified_badge(self, obj):
        """Display badge for verification status."""
        if obj.is_verified:
            return format_html('<span style="color: green;">✓ Verified</span>')
        return format_html('<span style="color: orange;">⚠ Unverified</span>')
    verified_badge.short_description = _('Verified')

    def ssl_badge(self, obj):
        """Display badge for SSL status."""
        if obj.ssl_enabled:
            return format_html('<span style="color: green;">🔒 SSL</span>')
        return format_html('<span style="color: red;">⚠ No SSL</span>')
    ssl_badge.short_description = _('SSL')

    actions = ['verify_domains', 'enable_ssl']

    def verify_domains(self, request, queryset):
        """Mark selected domains as verified."""
        from django.utils import timezone
        updated = queryset.update(is_verified=True, verified_at=timezone.now())
        self.message_user(request, f'{updated} domain(s) verified successfully.')
    verify_domains.short_description = _('Verify selected domains')

    def enable_ssl(self, request, queryset):
        """Enable SSL for selected domains."""
        updated = queryset.update(ssl_enabled=True)
        self.message_user(request, f'SSL enabled for {updated} domain(s).')
    enable_ssl.short_description = _('Enable SSL')
