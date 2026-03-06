"""Django admin configuration for tenants app."""

from django.contrib import admin
from django.utils.html import format_html
from .models import Tenant, Domain


class DomainInline(admin.TabularInline):
    """Inline admin for domains within a tenant."""

    model = Domain
    extra = 0
    readonly_fields = ['id', 'created_at']
    fields = ['domain', 'is_primary', 'is_verified', 'created_at']


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    """Admin interface for Tenant model."""

    list_display = [
        'name',
        'slug',
        'owner',
        'plan_badge',
        'is_active',
        'max_users',
        'max_clients',
        'created_at',
    ]

    list_filter = [
        'plan',
        'is_active',
        'created_at',
    ]

    search_fields = [
        'name',
        'slug',
        'owner__email',
        'owner__first_name',
        'owner__last_name',
    ]

    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Tenant Information', {
            'fields': (
                'id',
                'name',
                'slug',
                'owner',
                'plan',
                'is_active',
                'trial_ends_at',
            )
        }),
        ('Usage Limits', {
            'fields': (
                'max_users',
                'max_clients',
                'max_contracts_per_month',
                'max_invoices_per_month',
                'storage_limit_gb',
            )
        }),
        ('Branding', {
            'fields': (
                'logo',
                'primary_color',
                'accent_color',
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )

    inlines = [DomainInline]

    def plan_badge(self, obj):
        """Display plan with colored badge."""
        colors = {
            'free': '#6B7280',
            'starter': '#3B82F6',
            'professional': '#10B981',
            'enterprise': '#F59E0B',
        }
        color = colors.get(obj.plan, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_plan_display()
        )
    plan_badge.short_description = 'Plan'


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    """Admin interface for Domain model."""

    list_display = [
        'domain',
        'tenant',
        'is_primary',
        'is_verified',
        'created_at',
    ]

    list_filter = [
        'is_primary',
        'is_verified',
        'created_at',
    ]

    search_fields = [
        'domain',
        'tenant__name',
        'tenant__slug',
    ]

    readonly_fields = ['id', 'created_at']
