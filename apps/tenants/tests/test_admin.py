"""
Tests for tenants app admin configuration.
"""

import pytest
from datetime import timedelta
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from django.utils import timezone
from apps.tenants.models import Tenant, Domain
from apps.tenants.admin import TenantAdmin, DomainAdmin


@pytest.mark.django_db
class TestTenantAdmin:
    """Tests for TenantAdmin."""

    def setup_method(self):
        """Set up admin site and admin class."""
        self.site = AdminSite()
        self.admin = TenantAdmin(Tenant, self.site)
        self.request_factory = RequestFactory()

    def test_tenant_admin_is_registered(self):
        """Test Tenant model is registered in admin."""
        from django.contrib import admin
        assert Tenant in admin.site._registry

    def test_list_display(self):
        """Test list_display fields."""
        expected = [
            'name', 'slug', 'tenant_type', 'plan',
            'status_badge', 'trial_badge', 'created_on',
        ]
        assert self.admin.list_display == expected

    def test_list_filter(self):
        """Test list_filter fields."""
        expected = ['tenant_type', 'plan', 'is_active', 'is_trial', 'created_on']
        assert self.admin.list_filter == expected

    def test_search_fields(self):
        """Test search_fields."""
        assert 'name' in self.admin.search_fields
        assert 'slug' in self.admin.search_fields
        assert 'contact_email' in self.admin.search_fields
        assert 'schema_name' in self.admin.search_fields

    def test_readonly_fields(self):
        """Test readonly_fields."""
        assert 'schema_name' in self.admin.readonly_fields
        assert 'created_on' in self.admin.readonly_fields
        assert 'modified_on' in self.admin.readonly_fields
        assert 'trial_status_display' in self.admin.readonly_fields

    def test_status_badge_active(self, tenant):
        """Test status_badge for active tenant."""
        result = self.admin.status_badge(tenant)
        assert 'green' in result
        assert 'Active' in result

    def test_status_badge_inactive(self, tenant):
        """Test status_badge for inactive tenant."""
        tenant.is_active = False
        result = self.admin.status_badge(tenant)
        assert 'red' in result
        assert 'Inactive' in result

    def test_status_badge_short_description(self):
        """Test status_badge has short_description."""
        assert self.admin.status_badge.short_description is not None

    def test_trial_badge_no_trial(self, tenant):
        """Test trial_badge for non-trial tenant."""
        result = self.admin.trial_badge(tenant)
        assert 'gray' in result

    def test_trial_badge_active_trial(self, tenant_with_trial):
        """Test trial_badge for tenant on active trial."""
        result = self.admin.trial_badge(tenant_with_trial)
        assert 'Trial' in result
        # Should show days
        assert 'days' in result

    def test_trial_badge_active_trial_less_than_7_days(self, tenant_with_trial):
        """Test trial_badge shows orange color when trial expires in less than 7 days."""
        tenant_with_trial.trial_ends_at = timezone.now() + timedelta(days=3)
        tenant_with_trial.save()
        result = self.admin.trial_badge(tenant_with_trial)
        assert 'orange' in result

    def test_trial_badge_active_trial_more_than_7_days(self, tenant_with_trial):
        """Test trial_badge shows blue color when trial has more than 7 days."""
        tenant_with_trial.trial_ends_at = timezone.now() + timedelta(days=10)
        tenant_with_trial.save()
        result = self.admin.trial_badge(tenant_with_trial)
        assert 'blue' in result

    def test_trial_badge_expired(self, tenant_with_trial):
        """Test trial_badge for expired trial."""
        tenant_with_trial.trial_ends_at = timezone.now() - timedelta(days=1)
        tenant_with_trial.save()
        result = self.admin.trial_badge(tenant_with_trial)
        assert 'Expired' in result
        assert 'red' in result

    def test_trial_badge_short_description(self):
        """Test trial_badge has short_description."""
        assert self.admin.trial_badge.short_description is not None

    def test_trial_status_display_no_trial(self, tenant):
        """Test trial_status_display for non-trial tenant."""
        result = self.admin.trial_status_display(tenant)
        assert 'Not on trial' in result

    def test_trial_status_display_active_trial(self, tenant_with_trial):
        """Test trial_status_display for active trial."""
        result = self.admin.trial_status_display(tenant_with_trial)
        assert 'Trial active' in result
        assert 'days remaining' in result

    def test_trial_status_display_expired(self, tenant_with_trial):
        """Test trial_status_display for expired trial."""
        tenant_with_trial.trial_ends_at = timezone.now() - timedelta(days=1)
        tenant_with_trial.save()
        result = self.admin.trial_status_display(tenant_with_trial)
        assert 'Trial expired' in result

    def test_activate_tenants_action(self, admin_user):
        """Test activate_tenants admin action."""
        inactive_tenant = Tenant(
            name='Inactive Tenant',
            slug='inactive-tenant',
            schema_name='inactive_tenant',
            contact_email='inactive@test.com',
            is_active=False,
        )
        inactive_tenant.save()
        request = self.request_factory.get('/admin/')
        request.user = admin_user
        queryset = Tenant.objects.filter(pk=inactive_tenant.pk)
        self.admin.activate_tenants(request, queryset)
        inactive_tenant.refresh_from_db()
        assert inactive_tenant.is_active is True

    def test_deactivate_tenants_action(self, admin_user, tenant):
        """Test deactivate_tenants admin action."""
        request = self.request_factory.get('/admin/')
        request.user = admin_user
        queryset = Tenant.objects.filter(pk=tenant.pk)
        self.admin.deactivate_tenants(request, queryset)
        tenant.refresh_from_db()
        assert tenant.is_active is False

    def test_upgrade_to_starter_action(self, admin_user):
        """Test upgrade_to_starter admin action."""
        free_tenant = Tenant(
            name='Free Tenant',
            slug='free-tenant',
            schema_name='free_tenant',
            contact_email='free@test.com',
            plan=Tenant.FREE,
        )
        free_tenant.save()
        request = self.request_factory.get('/admin/')
        request.user = admin_user
        queryset = Tenant.objects.filter(pk=free_tenant.pk)
        self.admin.upgrade_to_starter(request, queryset)
        free_tenant.refresh_from_db()
        assert free_tenant.plan == Tenant.STARTER

    def test_actions_list(self):
        """Test that all actions are registered."""
        assert 'activate_tenants' in self.admin.actions
        assert 'deactivate_tenants' in self.admin.actions
        assert 'upgrade_to_starter' in self.admin.actions

    def test_fieldsets_present(self):
        """Test fieldsets are defined."""
        assert self.admin.fieldsets is not None
        assert len(self.admin.fieldsets) > 0


@pytest.mark.django_db
class TestDomainAdmin:
    """Tests for DomainAdmin."""

    def setup_method(self):
        """Set up admin site and admin class."""
        self.site = AdminSite()
        self.admin = DomainAdmin(Domain, self.site)
        self.request_factory = RequestFactory()

    def test_domain_admin_is_registered(self):
        """Test Domain model is registered in admin."""
        from django.contrib import admin
        assert Domain in admin.site._registry

    def test_list_display(self):
        """Test list_display fields."""
        expected = [
            'domain', 'tenant', 'primary_badge', 'verified_badge',
            'ssl_badge', 'created_at',
        ]
        assert self.admin.list_display == expected

    def test_list_filter(self):
        """Test list_filter fields."""
        assert 'is_primary' in self.admin.list_filter
        assert 'is_verified' in self.admin.list_filter
        assert 'ssl_enabled' in self.admin.list_filter
        assert 'created_at' in self.admin.list_filter

    def test_search_fields(self):
        """Test search_fields."""
        assert 'domain' in self.admin.search_fields
        assert 'tenant__name' in self.admin.search_fields
        assert 'tenant__slug' in self.admin.search_fields

    def test_readonly_fields(self):
        """Test readonly_fields."""
        assert 'created_at' in self.admin.readonly_fields
        assert 'updated_at' in self.admin.readonly_fields
        assert 'verified_at' in self.admin.readonly_fields

    def test_primary_badge_primary(self, domain):
        """Test primary_badge for primary domain."""
        result = self.admin.primary_badge(domain)
        assert 'Primary' in result
        assert 'blue' in result

    def test_primary_badge_non_primary(self, tenant):
        """Test primary_badge for non-primary domain."""
        secondary = Domain.objects.create(
            tenant=tenant,
            domain='secondary.aureon.local',
            is_primary=False,
        )
        result = self.admin.primary_badge(secondary)
        assert result == '-'

    def test_verified_badge_verified(self, domain):
        """Test verified_badge for verified domain."""
        result = self.admin.verified_badge(domain)
        assert 'green' in result
        assert 'Verified' in result

    def test_verified_badge_unverified(self, tenant):
        """Test verified_badge for unverified domain."""
        unverified = Domain.objects.create(
            tenant=tenant,
            domain='unverified.aureon.local',
            is_primary=False,
            is_verified=False,
        )
        result = self.admin.verified_badge(unverified)
        assert 'orange' in result
        assert 'Unverified' in result

    def test_ssl_badge_enabled(self, domain):
        """Test ssl_badge for SSL enabled domain."""
        result = self.admin.ssl_badge(domain)
        assert 'green' in result
        assert 'SSL' in result

    def test_ssl_badge_disabled(self, tenant):
        """Test ssl_badge for SSL disabled domain."""
        no_ssl = Domain.objects.create(
            tenant=tenant,
            domain='nossl.aureon.local',
            is_primary=False,
            ssl_enabled=False,
        )
        result = self.admin.ssl_badge(no_ssl)
        assert 'red' in result
        assert 'No SSL' in result

    def test_verify_domains_action(self, admin_user, tenant):
        """Test verify_domains admin action."""
        unverified = Domain.objects.create(
            tenant=tenant,
            domain='toverify.aureon.local',
            is_primary=False,
            is_verified=False,
        )
        request = self.request_factory.get('/admin/')
        request.user = admin_user
        queryset = Domain.objects.filter(pk=unverified.pk)
        self.admin.verify_domains(request, queryset)
        unverified.refresh_from_db()
        assert unverified.is_verified is True
        assert unverified.verified_at is not None

    def test_enable_ssl_action(self, admin_user, tenant):
        """Test enable_ssl admin action."""
        no_ssl = Domain.objects.create(
            tenant=tenant,
            domain='enablessl.aureon.local',
            is_primary=False,
            ssl_enabled=False,
        )
        request = self.request_factory.get('/admin/')
        request.user = admin_user
        queryset = Domain.objects.filter(pk=no_ssl.pk)
        self.admin.enable_ssl(request, queryset)
        no_ssl.refresh_from_db()
        assert no_ssl.ssl_enabled is True

    def test_actions_list(self):
        """Test all actions are registered."""
        assert 'verify_domains' in self.admin.actions
        assert 'enable_ssl' in self.admin.actions

    def test_fieldsets_present(self):
        """Test fieldsets are defined."""
        assert self.admin.fieldsets is not None
        assert len(self.admin.fieldsets) > 0

    def test_badge_short_descriptions(self):
        """Test all badge methods have short_description."""
        assert self.admin.primary_badge.short_description is not None
        assert self.admin.verified_badge.short_description is not None
        assert self.admin.ssl_badge.short_description is not None
