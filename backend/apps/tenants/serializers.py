"""
Serializers for the tenants app.
"""

from rest_framework import serializers
from .models import Tenant, Domain


class DomainSerializer(serializers.ModelSerializer):
    """
    Serializer for Domain model.
    """

    class Meta:
        model = Domain
        fields = [
            'id', 'tenant', 'domain', 'is_primary',
            'is_verified', 'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'is_verified']


class TenantSerializer(serializers.ModelSerializer):
    """
    Serializer for Tenant model.
    """
    domains = DomainSerializer(many=True, read_only=True)
    owner_email = serializers.SerializerMethodField()
    is_on_trial = serializers.ReadOnlyField()
    is_trial_expired = serializers.ReadOnlyField()

    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slug', 'owner', 'owner_email', 'plan',
            'is_active', 'trial_ends_at', 'max_users', 'max_clients',
            'max_contracts_per_month', 'max_invoices_per_month',
            'storage_limit_gb', 'logo', 'primary_color', 'accent_color',
            'created_at', 'updated_at', 'domains',
            'is_on_trial', 'is_trial_expired',
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

    def get_owner_email(self, obj):
        """Get owner email address."""
        if obj.owner:
            return obj.owner.email
        return None
