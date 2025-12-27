"""
Serializers for tenant models.
"""

from rest_framework import serializers
from .models import Tenant, Domain


class DomainSerializer(serializers.ModelSerializer):
    """Serializer for Domain model."""

    class Meta:
        model = Domain
        fields = [
            'id',
            'domain',
            'is_primary',
            'ssl_enabled',
            'is_verified',
            'verified_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'verified_at', 'created_at', 'updated_at']


class TenantSerializer(serializers.ModelSerializer):
    """Serializer for Tenant model."""

    domains = DomainSerializer(many=True, read_only=True)
    is_on_trial = serializers.BooleanField(read_only=True)
    days_until_trial_ends = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tenant
        fields = [
            'id',
            'name',
            'slug',
            'schema_name',
            'tenant_type',
            'plan',
            'stripe_customer_id',
            'stripe_subscription_id',
            'contact_email',
            'contact_phone',
            'address_line1',
            'address_line2',
            'city',
            'state',
            'postal_code',
            'country',
            'logo',
            'primary_color',
            'secondary_color',
            'timezone',
            'currency',
            'language',
            'max_users',
            'max_clients',
            'max_contracts',
            'max_invoices_per_month',
            'enable_api_access',
            'enable_custom_branding',
            'enable_multi_currency',
            'enable_advanced_analytics',
            'is_active',
            'is_trial',
            'trial_ends_at',
            'is_on_trial',
            'days_until_trial_ends',
            'created_on',
            'modified_on',
            'domains',
        ]
        read_only_fields = [
            'id',
            'schema_name',
            'stripe_customer_id',
            'stripe_subscription_id',
            'is_on_trial',
            'days_until_trial_ends',
            'created_on',
            'modified_on',
        ]


class TenantCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new tenant."""

    class Meta:
        model = Tenant
        fields = [
            'name',
            'slug',
            'tenant_type',
            'contact_email',
            'contact_phone',
            'country',
            'timezone',
            'currency',
        ]

    def validate_slug(self, value):
        """Validate slug uniqueness and format."""
        if Tenant.objects.filter(slug=value).exists():
            raise serializers.ValidationError("This slug is already in use.")
        return value.lower()


class TenantUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating tenant information."""

    class Meta:
        model = Tenant
        fields = [
            'name',
            'contact_email',
            'contact_phone',
            'address_line1',
            'address_line2',
            'city',
            'state',
            'postal_code',
            'country',
            'logo',
            'primary_color',
            'secondary_color',
            'timezone',
            'currency',
            'language',
        ]


class TenantPlanUpgradeSerializer(serializers.Serializer):
    """Serializer for upgrading tenant plan."""

    plan = serializers.ChoiceField(choices=Tenant.PLAN_CHOICES)

    def validate_plan(self, value):
        """Validate plan upgrade."""
        current_plan = self.context['tenant'].plan
        plan_hierarchy = {
            Tenant.FREE: 0,
            Tenant.STARTER: 1,
            Tenant.PRO: 2,
            Tenant.BUSINESS: 3,
        }

        if plan_hierarchy.get(value, 0) < plan_hierarchy.get(current_plan, 0):
            raise serializers.ValidationError(
                "Cannot downgrade plan. Please contact support."
            )
        return value
