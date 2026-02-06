"""
Tests for tenants app serializers.
"""

import pytest
from datetime import timedelta
from django.utils import timezone
from apps.tenants.models import Tenant, Domain
from apps.tenants.serializers import (
    DomainSerializer,
    TenantSerializer,
    TenantCreateSerializer,
    TenantUpdateSerializer,
    TenantPlanUpgradeSerializer,
)


# ============================================================================
# DomainSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestDomainSerializer:
    """Tests for DomainSerializer."""

    def test_serializes_expected_fields(self, domain):
        """Verify all expected fields are serialized."""
        serializer = DomainSerializer(domain)
        data = serializer.data
        expected_fields = [
            'id', 'domain', 'is_primary', 'ssl_enabled',
            'is_verified', 'verified_at', 'created_at', 'updated_at',
        ]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"

    def test_read_only_fields(self):
        """Verify read_only_fields are set."""
        meta = DomainSerializer.Meta
        assert 'id' in meta.read_only_fields
        assert 'verified_at' in meta.read_only_fields
        assert 'created_at' in meta.read_only_fields
        assert 'updated_at' in meta.read_only_fields

    def test_domain_data_values(self, domain):
        """Test that serialized values match the model."""
        serializer = DomainSerializer(domain)
        data = serializer.data
        assert data['domain'] == 'test-org.aureon.local'
        assert data['is_primary'] is True
        assert data['ssl_enabled'] is True
        assert data['is_verified'] is True


# ============================================================================
# TenantSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestTenantSerializer:
    """Tests for TenantSerializer."""

    def test_serializes_expected_fields(self, tenant, domain):
        """Verify all expected fields are serialized."""
        serializer = TenantSerializer(tenant)
        data = serializer.data
        assert 'id' in data
        assert 'name' in data
        assert 'slug' in data
        assert 'schema_name' in data
        assert 'tenant_type' in data
        assert 'plan' in data
        assert 'is_on_trial' in data
        assert 'days_until_trial_ends' in data
        assert 'domains' in data
        assert 'created_on' in data
        assert 'modified_on' in data

    def test_tenant_data_values(self, tenant):
        """Test serialized values match model."""
        serializer = TenantSerializer(tenant)
        data = serializer.data
        assert data['name'] == 'Test Organization'
        assert data['slug'] == 'test-org'
        assert data['tenant_type'] == Tenant.AGENCY
        assert data['plan'] == Tenant.PRO
        assert data['is_active'] is True

    def test_is_on_trial_false(self, tenant):
        """Test is_on_trial is False for non-trial tenant."""
        serializer = TenantSerializer(tenant)
        assert serializer.data['is_on_trial'] is False

    def test_is_on_trial_true(self, tenant_with_trial):
        """Test is_on_trial is True for trial tenant."""
        serializer = TenantSerializer(tenant_with_trial)
        assert serializer.data['is_on_trial'] is True

    def test_days_until_trial_ends_no_trial(self, tenant):
        """Test days_until_trial_ends is 0 for non-trial tenant."""
        serializer = TenantSerializer(tenant)
        assert serializer.data['days_until_trial_ends'] == 0

    def test_days_until_trial_ends_with_trial(self, tenant_with_trial):
        """Test days_until_trial_ends returns positive number for trial tenant."""
        serializer = TenantSerializer(tenant_with_trial)
        assert serializer.data['days_until_trial_ends'] > 0

    def test_domains_nested(self, tenant, domain):
        """Test domains are nested within tenant serialization."""
        serializer = TenantSerializer(tenant)
        data = serializer.data
        assert len(data['domains']) == 1
        assert data['domains'][0]['domain'] == 'test-org.aureon.local'

    def test_read_only_fields(self):
        """Verify read_only_fields are configured."""
        meta = TenantSerializer.Meta
        assert 'id' in meta.read_only_fields
        assert 'schema_name' in meta.read_only_fields
        assert 'stripe_customer_id' in meta.read_only_fields
        assert 'stripe_subscription_id' in meta.read_only_fields
        assert 'is_on_trial' in meta.read_only_fields
        assert 'days_until_trial_ends' in meta.read_only_fields
        assert 'created_on' in meta.read_only_fields
        assert 'modified_on' in meta.read_only_fields


# ============================================================================
# TenantCreateSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestTenantCreateSerializer:
    """Tests for TenantCreateSerializer."""

    def test_valid_data(self):
        """Test serializer with valid data."""
        data = {
            'name': 'New Tenant',
            'slug': 'new-tenant',
            'tenant_type': Tenant.FREELANCER,
            'contact_email': 'new@tenant.com',
            'contact_phone': '+1234567890',
            'country': 'United States',
            'timezone': 'UTC',
            'currency': 'USD',
        }
        serializer = TenantCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_slug_uniqueness_validation(self, tenant):
        """Test that duplicate slug is rejected."""
        data = {
            'name': 'Duplicate Slug Tenant',
            'slug': 'test-org',  # Same as existing tenant
            'tenant_type': Tenant.FREELANCER,
            'contact_email': 'duplicate@tenant.com',
        }
        serializer = TenantCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'slug' in serializer.errors

    def test_slug_is_lowercased(self):
        """Test that slug is lowercased during validation."""
        data = {
            'name': 'Uppercase Slug',
            'slug': 'UPPER-CASE-SLUG',
            'tenant_type': Tenant.FREELANCER,
            'contact_email': 'upper@tenant.com',
        }
        serializer = TenantCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['slug'] == 'upper-case-slug'

    def test_missing_required_fields(self):
        """Test validation fails without required fields."""
        data = {}
        serializer = TenantCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'name' in serializer.errors
        assert 'slug' in serializer.errors
        assert 'contact_email' in serializer.errors

    def test_fields_list(self):
        """Test the fields list is correct."""
        expected = [
            'name', 'slug', 'tenant_type', 'contact_email',
            'contact_phone', 'country', 'timezone', 'currency',
        ]
        assert TenantCreateSerializer.Meta.fields == expected


# ============================================================================
# TenantUpdateSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestTenantUpdateSerializer:
    """Tests for TenantUpdateSerializer."""

    def test_valid_update_data(self, tenant):
        """Test valid update data."""
        data = {
            'name': 'Updated Organization',
            'contact_email': 'updated@org.com',
            'city': 'New City',
        }
        serializer = TenantUpdateSerializer(tenant, data=data, partial=True)
        assert serializer.is_valid(), serializer.errors

    def test_partial_update(self, tenant):
        """Test partial update of tenant."""
        data = {'name': 'Partially Updated'}
        serializer = TenantUpdateSerializer(tenant, data=data, partial=True)
        assert serializer.is_valid(), serializer.errors
        updated = serializer.save()
        assert updated.name == 'Partially Updated'
        # Other fields unchanged
        assert updated.contact_email == 'admin@testorg.com'

    def test_fields_list(self):
        """Test the update serializer fields list."""
        expected = [
            'name', 'contact_email', 'contact_phone',
            'address_line1', 'address_line2', 'city', 'state',
            'postal_code', 'country', 'logo', 'primary_color',
            'secondary_color', 'timezone', 'currency', 'language',
        ]
        assert TenantUpdateSerializer.Meta.fields == expected

    def test_cannot_update_slug(self, tenant):
        """Test that slug is not included in update fields."""
        assert 'slug' not in TenantUpdateSerializer.Meta.fields

    def test_cannot_update_plan(self, tenant):
        """Test that plan is not included in update fields (use upgrade_plan instead)."""
        assert 'plan' not in TenantUpdateSerializer.Meta.fields


# ============================================================================
# TenantPlanUpgradeSerializer Tests
# ============================================================================

@pytest.mark.django_db
class TestTenantPlanUpgradeSerializer:
    """Tests for TenantPlanUpgradeSerializer."""

    def test_valid_upgrade(self, tenant):
        """Test valid plan upgrade from PRO to BUSINESS."""
        data = {'plan': Tenant.BUSINESS}
        serializer = TenantPlanUpgradeSerializer(
            data=data, context={'tenant': tenant}
        )
        assert serializer.is_valid(), serializer.errors

    def test_same_plan_is_valid(self, tenant):
        """Test upgrading to same plan level is allowed (not a downgrade)."""
        data = {'plan': Tenant.PRO}
        serializer = TenantPlanUpgradeSerializer(
            data=data, context={'tenant': tenant}
        )
        assert serializer.is_valid(), serializer.errors

    def test_downgrade_is_rejected(self, tenant):
        """Test that downgrading plan is rejected."""
        # tenant is on PRO, try to go to STARTER
        data = {'plan': Tenant.STARTER}
        serializer = TenantPlanUpgradeSerializer(
            data=data, context={'tenant': tenant}
        )
        assert not serializer.is_valid()
        assert 'plan' in serializer.errors

    def test_downgrade_to_free_is_rejected(self, tenant):
        """Test that downgrading to free from PRO is rejected."""
        data = {'plan': Tenant.FREE}
        serializer = TenantPlanUpgradeSerializer(
            data=data, context={'tenant': tenant}
        )
        assert not serializer.is_valid()
        assert 'plan' in serializer.errors

    def test_upgrade_from_free_to_starter(self):
        """Test upgrading from FREE to STARTER."""
        from apps.tenants.models import Tenant as TenantModel
        mock_tenant = TenantModel(plan=Tenant.FREE)
        data = {'plan': Tenant.STARTER}
        serializer = TenantPlanUpgradeSerializer(
            data=data, context={'tenant': mock_tenant}
        )
        assert serializer.is_valid(), serializer.errors

    def test_upgrade_from_free_to_business(self):
        """Test upgrading from FREE to BUSINESS."""
        from apps.tenants.models import Tenant as TenantModel
        mock_tenant = TenantModel(plan=Tenant.FREE)
        data = {'plan': Tenant.BUSINESS}
        serializer = TenantPlanUpgradeSerializer(
            data=data, context={'tenant': mock_tenant}
        )
        assert serializer.is_valid(), serializer.errors

    def test_invalid_plan_choice(self, tenant):
        """Test that invalid plan choice is rejected."""
        data = {'plan': 'invalid_plan'}
        serializer = TenantPlanUpgradeSerializer(
            data=data, context={'tenant': tenant}
        )
        assert not serializer.is_valid()
        assert 'plan' in serializer.errors

    def test_missing_plan(self, tenant):
        """Test that missing plan is rejected."""
        data = {}
        serializer = TenantPlanUpgradeSerializer(
            data=data, context={'tenant': tenant}
        )
        assert not serializer.is_valid()
        assert 'plan' in serializer.errors
