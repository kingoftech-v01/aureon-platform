"""
Tests for tenants app models.

Tests cover:
- Tenant model creation and validation
- Tenant properties and methods
- Tenant plan upgrades
- Domain model
"""

import pytest
from datetime import timedelta
from django.utils import timezone
from apps.tenants.models import Tenant, Domain


# ============================================================================
# Tenant Model Tests
# ============================================================================

@pytest.mark.django_db
class TestTenantModel:
    """Tests for the Tenant model."""

    def test_create_tenant(self):
        """Test creating a tenant."""
        tenant = Tenant(
            name='New Organization',
            slug='new-org',
            tenant_type=Tenant.AGENCY,
            contact_email='contact@neworg.com',
        )
        tenant.save()

        assert tenant.name == 'New Organization'
        assert tenant.slug == 'new-org'
        assert tenant.schema_name == 'new-org'

    def test_tenant_auto_set_schema_name(self):
        """Test schema_name is auto-set from slug."""
        tenant = Tenant(
            name='Auto Schema',
            slug='auto-schema',
            contact_email='auto@schema.com',
        )
        tenant.save()

        assert tenant.schema_name == 'auto-schema'

    def test_tenant_string_representation(self, tenant):
        """Test tenant string representation."""
        expected = f"{tenant.name} ({tenant.tenant_type})"
        assert str(tenant) == expected


# ============================================================================
# Tenant Type Tests
# ============================================================================

@pytest.mark.django_db
class TestTenantTypes:
    """Tests for tenant type values."""

    def test_all_tenant_types_valid(self):
        """Test all tenant types are valid."""
        valid_types = [
            Tenant.FREELANCER,
            Tenant.AGENCY,
            Tenant.STARTUP,
            Tenant.ENTERPRISE,
        ]
        for tenant_type in valid_types:
            assert tenant_type in dict(Tenant.TENANT_TYPE_CHOICES)

    def test_all_plan_choices_valid(self):
        """Test all plan choices are valid."""
        valid_plans = [
            Tenant.FREE,
            Tenant.STARTER,
            Tenant.PRO,
            Tenant.BUSINESS,
        ]
        for plan in valid_plans:
            assert plan in dict(Tenant.PLAN_CHOICES)


# ============================================================================
# Tenant Trial Tests
# ============================================================================

@pytest.mark.django_db
class TestTenantTrial:
    """Tests for tenant trial functionality."""

    def test_is_on_trial_active(self, tenant_with_trial):
        """Test is_on_trial when trial is active."""
        assert tenant_with_trial.is_on_trial is True

    def test_is_on_trial_expired(self, tenant_with_trial):
        """Test is_on_trial when trial has expired."""
        tenant_with_trial.trial_ends_at = timezone.now() - timedelta(days=1)
        tenant_with_trial.save()

        assert tenant_with_trial.is_on_trial is False

    def test_is_on_trial_not_trial(self, tenant):
        """Test is_on_trial when not a trial account."""
        assert tenant.is_trial is False
        assert tenant.is_on_trial is False

    def test_days_until_trial_ends(self, tenant_with_trial):
        """Test days_until_trial_ends calculation."""
        days = tenant_with_trial.days_until_trial_ends
        assert days > 0 and days <= 14

    def test_days_until_trial_ends_expired(self, tenant_with_trial):
        """Test days_until_trial_ends when expired."""
        tenant_with_trial.trial_ends_at = timezone.now() - timedelta(days=1)
        tenant_with_trial.save()

        assert tenant_with_trial.days_until_trial_ends == 0

    def test_days_until_trial_ends_not_trial(self, tenant):
        """Test days_until_trial_ends for non-trial tenant."""
        assert tenant.days_until_trial_ends == 0


# ============================================================================
# Tenant Limits Tests
# ============================================================================

@pytest.mark.django_db
class TestTenantLimits:
    """Tests for tenant usage limits."""

    def test_can_add_user_within_limit(self, tenant):
        """Test can_add_user when within limit."""
        # Tenant starts with no users in test
        assert tenant.can_add_user() is True

    def test_can_add_user_at_limit(self, tenant, admin_user):
        """Test can_add_user when at limit."""
        tenant.max_users = 1
        tenant.save()

        # admin_user is already associated with tenant
        assert tenant.can_add_user() is False

    def test_can_add_client(self, tenant):
        """Test can_add_client method."""
        # Currently returns True as placeholder
        assert tenant.can_add_client() is True

    def test_default_limits(self, tenant):
        """Test default limit values."""
        assert tenant.max_users > 0
        assert tenant.max_clients > 0
        assert tenant.max_contracts > 0
        assert tenant.max_invoices_per_month > 0


# ============================================================================
# Tenant Plan Upgrade Tests
# ============================================================================

@pytest.mark.django_db
class TestTenantPlanUpgrade:
    """Tests for tenant plan upgrade functionality."""

    def test_upgrade_to_starter(self):
        """Test upgrading to starter plan."""
        tenant = Tenant(
            name='Upgrade Test',
            slug='upgrade-test',
            contact_email='upgrade@test.com',
            plan=Tenant.FREE,
        )
        tenant.save()

        tenant.upgrade_plan(Tenant.STARTER)

        assert tenant.plan == Tenant.STARTER
        assert tenant.max_users == 3
        assert tenant.max_clients == 50
        assert tenant.enable_custom_branding is True

    def test_upgrade_to_pro(self):
        """Test upgrading to pro plan."""
        tenant = Tenant(
            name='Pro Upgrade',
            slug='pro-upgrade',
            contact_email='pro@test.com',
            plan=Tenant.FREE,
        )
        tenant.save()

        tenant.upgrade_plan(Tenant.PRO)

        assert tenant.plan == Tenant.PRO
        assert tenant.max_users == 10
        assert tenant.enable_api_access is True
        assert tenant.enable_multi_currency is True
        assert tenant.enable_advanced_analytics is True

    def test_upgrade_to_business(self):
        """Test upgrading to business plan."""
        tenant = Tenant(
            name='Business Upgrade',
            slug='business-upgrade',
            contact_email='business@test.com',
            plan=Tenant.FREE,
        )
        tenant.save()

        tenant.upgrade_plan(Tenant.BUSINESS)

        assert tenant.plan == Tenant.BUSINESS
        assert tenant.max_users == 50
        assert tenant.max_clients == 1000
        assert tenant.max_contracts == 500


# ============================================================================
# Tenant Feature Flags Tests
# ============================================================================

@pytest.mark.django_db
class TestTenantFeatureFlags:
    """Tests for tenant feature flags."""

    def test_feature_flags_defaults(self, tenant_with_trial):
        """Test feature flags defaults for free plan."""
        assert tenant_with_trial.enable_api_access is False
        assert tenant_with_trial.enable_custom_branding is False
        assert tenant_with_trial.enable_multi_currency is False
        assert tenant_with_trial.enable_advanced_analytics is False

    def test_feature_flags_pro_plan(self, tenant):
        """Test feature flags for pro plan."""
        tenant.upgrade_plan(Tenant.PRO)

        assert tenant.enable_api_access is True
        assert tenant.enable_custom_branding is True
        assert tenant.enable_multi_currency is True
        assert tenant.enable_advanced_analytics is True


# ============================================================================
# Tenant Branding Tests
# ============================================================================

@pytest.mark.django_db
class TestTenantBranding:
    """Tests for tenant branding fields."""

    def test_default_colors(self, tenant):
        """Test default brand colors."""
        assert tenant.primary_color == '#1E40AF'
        assert tenant.secondary_color == '#10B981'

    def test_custom_colors(self):
        """Test custom brand colors."""
        tenant = Tenant(
            name='Branded Tenant',
            slug='branded',
            contact_email='branded@test.com',
            primary_color='#FF0000',
            secondary_color='#00FF00',
        )
        tenant.save()

        assert tenant.primary_color == '#FF0000'
        assert tenant.secondary_color == '#00FF00'


# ============================================================================
# Tenant Settings Tests
# ============================================================================

@pytest.mark.django_db
class TestTenantSettings:
    """Tests for tenant settings fields."""

    def test_default_settings(self, tenant):
        """Test default settings."""
        assert tenant.timezone == 'America/New_York' or tenant.timezone == 'UTC'
        assert tenant.currency == 'USD'
        assert tenant.language == 'en'

    def test_custom_settings(self):
        """Test custom settings."""
        tenant = Tenant(
            name='EU Tenant',
            slug='eu-tenant',
            contact_email='eu@test.com',
            timezone='Europe/London',
            currency='EUR',
            language='de',
        )
        tenant.save()

        assert tenant.timezone == 'Europe/London'
        assert tenant.currency == 'EUR'
        assert tenant.language == 'de'


# ============================================================================
# Tenant Metadata Tests
# ============================================================================

@pytest.mark.django_db
class TestTenantMetadata:
    """Tests for tenant metadata JSON field."""

    def test_metadata_default_empty_dict(self):
        """Test metadata defaults to empty dict."""
        tenant = Tenant(
            name='Meta Test',
            slug='meta-test',
            contact_email='meta@test.com',
        )
        tenant.save()

        assert tenant.metadata == {}

    def test_metadata_stores_json(self, tenant):
        """Test metadata can store JSON data."""
        tenant.metadata = {
            'industry': 'Technology',
            'size': 'enterprise',
            'custom': {'key': 'value'},
        }
        tenant.save()

        tenant.refresh_from_db()
        assert tenant.metadata['industry'] == 'Technology'


# ============================================================================
# Domain Model Tests
# ============================================================================

@pytest.mark.django_db
class TestDomainModel:
    """Tests for the Domain model."""

    def test_create_domain(self, tenant):
        """Test creating a domain."""
        domain = Domain.objects.create(
            tenant=tenant,
            domain='new-domain.example.com',
            is_primary=False,
        )

        assert domain.tenant == tenant
        assert domain.domain == 'new-domain.example.com'

    def test_domain_string_representation(self, domain):
        """Test domain string representation."""
        expected = f"{domain.domain} (Primary)"
        assert str(domain) == expected

    def test_only_one_primary_domain_per_tenant(self, tenant):
        """Test only one primary domain per tenant."""
        d1 = Domain.objects.create(
            tenant=tenant,
            domain='first.example.com',
            is_primary=True,
        )

        d2 = Domain.objects.create(
            tenant=tenant,
            domain='second.example.com',
            is_primary=True,
        )

        d1.refresh_from_db()
        assert d1.is_primary is False
        assert d2.is_primary is True

    def test_domain_ssl_enabled_default(self, tenant):
        """Test SSL enabled by default."""
        domain = Domain.objects.create(
            tenant=tenant,
            domain='ssl.example.com',
        )

        assert domain.ssl_enabled is True

    def test_domain_verification(self, tenant):
        """Test domain verification."""
        domain = Domain.objects.create(
            tenant=tenant,
            domain='verify.example.com',
            is_verified=False,
        )

        assert domain.is_verified is False
        assert domain.verified_at is None

        domain.is_verified = True
        domain.verified_at = timezone.now()
        domain.save()

        domain.refresh_from_db()
        assert domain.is_verified is True
        assert domain.verified_at is not None


# ============================================================================
# Tenant Edge Cases
# ============================================================================

@pytest.mark.django_db
class TestTenantEdgeCases:
    """Edge case tests for Tenant model."""

    def test_tenant_with_stripe_integration(self, tenant):
        """Test tenant with Stripe integration fields."""
        tenant.stripe_customer_id = 'cus_test123'
        tenant.stripe_subscription_id = 'sub_test456'
        tenant.save()

        tenant.refresh_from_db()
        assert tenant.stripe_customer_id == 'cus_test123'
        assert tenant.stripe_subscription_id == 'sub_test456'

    def test_tenant_address_fields(self, tenant):
        """Test tenant address fields."""
        assert tenant.address_line1 is not None
        assert tenant.city is not None
        assert tenant.country is not None

    def test_tenant_deactivation(self, tenant):
        """Test tenant deactivation."""
        tenant.is_active = False
        tenant.save()

        tenant.refresh_from_db()
        assert tenant.is_active is False

    def test_tenant_timestamps(self, tenant):
        """Test tenant has created_on and modified_on."""
        assert tenant.created_on is not None
        assert tenant.modified_on is not None

    def test_tenant_slug_validation(self):
        """Test tenant slug validation."""
        # Valid slug
        tenant = Tenant(
            name='Valid Slug',
            slug='valid-slug-123',
            contact_email='valid@test.com',
        )
        tenant.save()

        assert tenant.slug == 'valid-slug-123'
