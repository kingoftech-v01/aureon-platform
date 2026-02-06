"""
Tests for tenants app views.
"""

import pytest
from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from apps.tenants.models import Tenant, Domain


# ============================================================================
# TenantViewSet Tests
# ============================================================================

@pytest.mark.django_db
class TestTenantViewSetList:
    """Tests for TenantViewSet list action."""

    def test_list_tenants_as_superuser(self, authenticated_superuser_client, tenant):
        """Test superuser can list all tenants."""
        response = authenticated_superuser_client.get('/api/tenants/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_tenants_unauthenticated(self, api_client):
        """Test unauthenticated users cannot list tenants."""
        response = api_client.get('/api/tenants/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_tenants_as_regular_user_sees_own_tenant(
        self, authenticated_admin_client, tenant, admin_user
    ):
        """Test regular user sees only their own tenant."""
        response = authenticated_admin_client.get('/api/tenants/')
        assert response.status_code == status.HTTP_200_OK
        # admin_user has tenant_id set, should only see their tenant
        results = response.data.get('results', response.data)
        if isinstance(results, list):
            tenant_ids = [str(t['id']) for t in results]
            assert str(tenant.id) in tenant_ids


@pytest.mark.django_db
class TestTenantViewSetRetrieve:
    """Tests for TenantViewSet retrieve action."""

    def test_retrieve_tenant(self, authenticated_superuser_client, tenant):
        """Test retrieving a tenant by ID."""
        response = authenticated_superuser_client.get(f'/api/tenants/{tenant.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Test Organization'
        assert response.data['slug'] == 'test-org'

    def test_retrieve_nonexistent_tenant(self, authenticated_superuser_client):
        """Test retrieving a non-existent tenant returns 404."""
        import uuid
        fake_id = uuid.uuid4()
        response = authenticated_superuser_client.get(f'/api/tenants/{fake_id}/')
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestTenantViewSetCreate:
    """Tests for TenantViewSet create action."""

    def test_create_tenant(self, authenticated_superuser_client):
        """Test creating a new tenant with default trial period."""
        data = {
            'name': 'Created Tenant',
            'slug': 'created-tenant',
            'tenant_type': Tenant.FREELANCER,
            'contact_email': 'created@tenant.com',
        }
        response = authenticated_superuser_client.post('/api/tenants/', data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Created Tenant'
        assert response.data['plan'] == Tenant.FREE
        assert response.data['is_trial'] is True

        # Verify domain was created
        tenant_obj = Tenant.objects.get(slug='created-tenant')
        domains = Domain.objects.filter(tenant=tenant_obj)
        assert domains.count() == 1
        assert domains.first().is_primary is True
        assert 'created-tenant' in domains.first().domain

    def test_create_tenant_with_duplicate_slug(self, authenticated_superuser_client, tenant):
        """Test creating tenant with duplicate slug fails."""
        data = {
            'name': 'Duplicate Slug',
            'slug': 'test-org',
            'contact_email': 'dup@test.com',
        }
        response = authenticated_superuser_client.post('/api/tenants/', data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_tenant_missing_required_fields(self, authenticated_superuser_client):
        """Test creating tenant without required fields fails."""
        data = {}
        response = authenticated_superuser_client.post('/api/tenants/', data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestTenantViewSetUpdate:
    """Tests for TenantViewSet update actions."""

    def test_partial_update_tenant(self, authenticated_superuser_client, tenant):
        """Test partial update of tenant."""
        data = {'name': 'Updated Org Name'}
        response = authenticated_superuser_client.patch(
            f'/api/tenants/{tenant.id}/', data
        )
        assert response.status_code == status.HTTP_200_OK
        tenant.refresh_from_db()
        assert tenant.name == 'Updated Org Name'

    def test_update_tenant_contact_info(self, authenticated_superuser_client, tenant):
        """Test updating tenant contact information."""
        data = {
            'name': tenant.name,
            'contact_email': 'newemail@org.com',
            'contact_phone': '+9876543210',
        }
        response = authenticated_superuser_client.patch(
            f'/api/tenants/{tenant.id}/', data
        )
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestTenantViewSetUpgradePlan:
    """Tests for TenantViewSet upgrade_plan action."""

    def test_upgrade_plan(self, authenticated_superuser_client, tenant):
        """Test upgrading tenant plan."""
        data = {'plan': Tenant.BUSINESS}
        response = authenticated_superuser_client.post(
            f'/api/tenants/{tenant.id}/upgrade_plan/', data
        )
        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data
        tenant.refresh_from_db()
        assert tenant.plan == Tenant.BUSINESS

    def test_upgrade_plan_downgrade_rejected(self, authenticated_superuser_client, tenant):
        """Test downgrade is rejected."""
        data = {'plan': Tenant.STARTER}
        response = authenticated_superuser_client.post(
            f'/api/tenants/{tenant.id}/upgrade_plan/', data
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_upgrade_plan_invalid_plan(self, authenticated_superuser_client, tenant):
        """Test upgrade with invalid plan value."""
        data = {'plan': 'nonexistent'}
        response = authenticated_superuser_client.post(
            f'/api/tenants/{tenant.id}/upgrade_plan/', data
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestTenantViewSetUsageStats:
    """Tests for TenantViewSet usage_stats action."""

    def test_usage_stats(self, authenticated_superuser_client, tenant):
        """Test getting usage stats for a tenant."""
        response = authenticated_superuser_client.get(
            f'/api/tenants/{tenant.id}/usage_stats/'
        )
        assert response.status_code == status.HTTP_200_OK
        assert 'users' in response.data
        assert 'clients' in response.data
        assert 'contracts' in response.data
        assert 'invoices_this_month' in response.data
        assert 'current' in response.data['users']
        assert 'limit' in response.data['users']

    def test_usage_stats_unauthenticated(self, api_client, tenant):
        """Test unauthenticated user cannot access usage stats."""
        response = api_client.get(f'/api/tenants/{tenant.id}/usage_stats/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestTenantViewSetActivate:
    """Tests for TenantViewSet activate action."""

    def test_activate_tenant(self, authenticated_superuser_client, tenant):
        """Test activating a tenant."""
        tenant.is_active = False
        tenant.save()
        response = authenticated_superuser_client.post(
            f'/api/tenants/{tenant.id}/activate/'
        )
        assert response.status_code == status.HTTP_200_OK
        assert 'activated' in response.data['message']
        tenant.refresh_from_db()
        assert tenant.is_active is True

    def test_activate_already_active_tenant(self, authenticated_superuser_client, tenant):
        """Test activating an already active tenant still succeeds."""
        assert tenant.is_active is True
        response = authenticated_superuser_client.post(
            f'/api/tenants/{tenant.id}/activate/'
        )
        assert response.status_code == status.HTTP_200_OK
        tenant.refresh_from_db()
        assert tenant.is_active is True


@pytest.mark.django_db
class TestTenantViewSetDeactivate:
    """Tests for TenantViewSet deactivate action."""

    def test_deactivate_tenant(self, authenticated_superuser_client, tenant):
        """Test deactivating a tenant."""
        assert tenant.is_active is True
        response = authenticated_superuser_client.post(
            f'/api/tenants/{tenant.id}/deactivate/'
        )
        assert response.status_code == status.HTTP_200_OK
        assert 'deactivated' in response.data['message']
        tenant.refresh_from_db()
        assert tenant.is_active is False

    def test_deactivate_already_inactive_tenant(self, authenticated_superuser_client, tenant):
        """Test deactivating an already inactive tenant still succeeds."""
        tenant.is_active = False
        tenant.save()
        response = authenticated_superuser_client.post(
            f'/api/tenants/{tenant.id}/deactivate/'
        )
        assert response.status_code == status.HTTP_200_OK
        tenant.refresh_from_db()
        assert tenant.is_active is False


@pytest.mark.django_db
class TestTenantViewSetTrialStatus:
    """Tests for TenantViewSet trial_status action."""

    def test_trial_status_not_on_trial(self, authenticated_superuser_client, tenant):
        """Test trial_status for non-trial tenant."""
        response = authenticated_superuser_client.get(
            f'/api/tenants/{tenant.id}/trial_status/'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_trial'] is False
        assert response.data['is_on_trial'] is False

    def test_trial_status_on_trial(self, authenticated_superuser_client, tenant_with_trial):
        """Test trial_status for tenant on trial."""
        response = authenticated_superuser_client.get(
            f'/api/tenants/{tenant_with_trial.id}/trial_status/'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_trial'] is True
        assert response.data['is_on_trial'] is True
        assert response.data['days_remaining'] > 0
        assert response.data['trial_ends_at'] is not None

    def test_trial_status_expired(self, authenticated_superuser_client, tenant_with_trial):
        """Test trial_status for expired trial."""
        tenant_with_trial.trial_ends_at = timezone.now() - timedelta(days=1)
        tenant_with_trial.save()
        response = authenticated_superuser_client.get(
            f'/api/tenants/{tenant_with_trial.id}/trial_status/'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_trial'] is True
        assert response.data['is_on_trial'] is False
        assert response.data['days_remaining'] == 0


# ============================================================================
# DomainViewSet Tests
# ============================================================================

@pytest.mark.django_db
class TestDomainViewSetList:
    """Tests for DomainViewSet list action."""

    def test_list_domains_as_superuser(self, authenticated_superuser_client, domain):
        """Test superuser can list all domains."""
        response = authenticated_superuser_client.get('/api/domains/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_domains_unauthenticated(self, api_client):
        """Test unauthenticated user cannot list domains."""
        response = api_client.get('/api/domains/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestDomainViewSetCRUD:
    """Tests for DomainViewSet CRUD actions."""

    def test_create_domain(self, authenticated_superuser_client, tenant):
        """Test creating a new domain."""
        data = {
            'tenant': tenant.id,
            'domain': 'new-domain.aureon.local',
            'is_primary': False,
            'ssl_enabled': True,
        }
        response = authenticated_superuser_client.post('/api/domains/', data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['domain'] == 'new-domain.aureon.local'

    def test_retrieve_domain(self, authenticated_superuser_client, domain):
        """Test retrieving a domain by ID."""
        response = authenticated_superuser_client.get(f'/api/domains/{domain.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['domain'] == 'test-org.aureon.local'

    def test_update_domain(self, authenticated_superuser_client, domain):
        """Test updating a domain."""
        data = {'ssl_enabled': False}
        response = authenticated_superuser_client.patch(
            f'/api/domains/{domain.id}/', data
        )
        assert response.status_code == status.HTTP_200_OK
        domain.refresh_from_db()
        assert domain.ssl_enabled is False

    def test_delete_domain(self, authenticated_superuser_client, domain):
        """Test deleting a domain."""
        domain_id = domain.id
        response = authenticated_superuser_client.delete(f'/api/domains/{domain_id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Domain.objects.filter(id=domain_id).exists()


@pytest.mark.django_db
class TestDomainViewSetVerify:
    """Tests for DomainViewSet verify action."""

    def test_verify_domain(self, authenticated_superuser_client, tenant):
        """Test verifying a domain."""
        unverified_domain = Domain.objects.create(
            tenant=tenant,
            domain='unverified.aureon.local',
            is_primary=False,
            is_verified=False,
        )
        response = authenticated_superuser_client.post(
            f'/api/domains/{unverified_domain.id}/verify/'
        )
        assert response.status_code == status.HTTP_200_OK
        assert 'verified' in response.data['message'].lower()
        unverified_domain.refresh_from_db()
        assert unverified_domain.is_verified is True
        assert unverified_domain.verified_at is not None

    def test_verify_already_verified_domain(self, authenticated_superuser_client, domain):
        """Test verifying an already verified domain still succeeds."""
        response = authenticated_superuser_client.post(
            f'/api/domains/{domain.id}/verify/'
        )
        assert response.status_code == status.HTTP_200_OK
        domain.refresh_from_db()
        assert domain.is_verified is True


@pytest.mark.django_db
class TestDomainViewSetSetPrimary:
    """Tests for DomainViewSet set_primary action."""

    def test_set_primary_domain(self, authenticated_superuser_client, tenant, domain):
        """Test setting a domain as primary."""
        secondary = Domain.objects.create(
            tenant=tenant,
            domain='secondary.aureon.local',
            is_primary=False,
        )
        response = authenticated_superuser_client.post(
            f'/api/domains/{secondary.id}/set_primary/'
        )
        assert response.status_code == status.HTTP_200_OK
        assert 'primary' in response.data['message'].lower()
        secondary.refresh_from_db()
        assert secondary.is_primary is True
        # Original primary should now be non-primary
        domain.refresh_from_db()
        assert domain.is_primary is False

    def test_set_primary_on_already_primary(self, authenticated_superuser_client, domain):
        """Test setting primary on an already primary domain succeeds."""
        response = authenticated_superuser_client.post(
            f'/api/domains/{domain.id}/set_primary/'
        )
        assert response.status_code == status.HTTP_200_OK
        domain.refresh_from_db()
        assert domain.is_primary is True


@pytest.mark.django_db
class TestDomainViewSetQuerysetFiltering:
    """Tests for DomainViewSet queryset filtering."""

    def test_superuser_sees_all_domains(self, authenticated_superuser_client, domain, tenant_with_trial):
        """Test superuser sees all domains across tenants."""
        Domain.objects.create(
            tenant=tenant_with_trial,
            domain='trial.aureon.local',
            is_primary=True,
        )
        response = authenticated_superuser_client.get('/api/domains/')
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        if isinstance(results, list):
            assert len(results) >= 2
