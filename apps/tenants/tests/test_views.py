"""
Tests for tenants app views.

Uses APIRequestFactory to test views directly since tenants URLs
are not mounted in the main URL configuration.
"""

import pytest
from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate
from apps.tenants.models import Tenant, Domain
from apps.tenants.views import TenantViewSet, DomainViewSet

factory = APIRequestFactory()


# ============================================================================
# TenantViewSet Tests
# ============================================================================

@pytest.mark.django_db
class TestTenantViewSetList:
    """Tests for TenantViewSet list action."""

    def test_list_tenants_as_superuser(self, superuser, tenant):
        """Test superuser can list all tenants."""
        request = factory.get('/tenants/')
        force_authenticate(request, user=superuser)
        view = TenantViewSet.as_view({'get': 'list'})
        response = view(request)
        assert response.status_code == status.HTTP_200_OK

    def test_list_tenants_unauthenticated(self):
        """Test unauthenticated users cannot list tenants."""
        request = factory.get('/tenants/')
        view = TenantViewSet.as_view({'get': 'list'})
        response = view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_tenants_as_regular_user(self, admin_user, tenant):
        """Test regular user sees only their own tenant."""
        request = factory.get('/tenants/')
        force_authenticate(request, user=admin_user)
        view = TenantViewSet.as_view({'get': 'list'})
        response = view(request)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestTenantViewSetRetrieve:
    """Tests for TenantViewSet retrieve action."""

    def test_retrieve_tenant(self, superuser, tenant):
        """Test retrieving a tenant by ID."""
        request = factory.get(f'/tenants/{tenant.id}/')
        force_authenticate(request, user=superuser)
        view = TenantViewSet.as_view({'get': 'retrieve'})
        response = view(request, pk=tenant.id)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Test Organization'
        assert response.data['slug'] == 'test-org'

    def test_retrieve_nonexistent_tenant(self, superuser):
        """Test retrieving a non-existent tenant returns 404."""
        import uuid
        fake_id = uuid.uuid4()
        request = factory.get(f'/tenants/{fake_id}/')
        force_authenticate(request, user=superuser)
        view = TenantViewSet.as_view({'get': 'retrieve'})
        response = view(request, pk=fake_id)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestTenantViewSetCreate:
    """Tests for TenantViewSet create action."""

    def test_create_tenant(self, superuser):
        """Test creating a new tenant with default trial period."""
        data = {
            'name': 'Created Tenant',
            'slug': 'created-tenant',
            'tenant_type': Tenant.FREELANCER,
            'contact_email': 'created@tenant.com',
        }
        request = factory.post('/tenants/', data, format='json')
        force_authenticate(request, user=superuser)
        view = TenantViewSet.as_view({'post': 'create'})
        response = view(request)
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

    def test_create_tenant_with_duplicate_slug(self, superuser, tenant):
        """Test creating tenant with duplicate slug fails."""
        data = {
            'name': 'Duplicate Slug',
            'slug': 'test-org',
            'contact_email': 'dup@test.com',
        }
        request = factory.post('/tenants/', data, format='json')
        force_authenticate(request, user=superuser)
        view = TenantViewSet.as_view({'post': 'create'})
        response = view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_tenant_missing_required_fields(self, superuser):
        """Test creating tenant without required fields fails."""
        data = {}
        request = factory.post('/tenants/', data, format='json')
        force_authenticate(request, user=superuser)
        view = TenantViewSet.as_view({'post': 'create'})
        response = view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestTenantViewSetUpdate:
    """Tests for TenantViewSet update actions."""

    def test_partial_update_tenant(self, superuser, tenant):
        """Test partial update of tenant."""
        data = {'name': 'Updated Org Name'}
        request = factory.patch(f'/tenants/{tenant.id}/', data, format='json')
        force_authenticate(request, user=superuser)
        view = TenantViewSet.as_view({'patch': 'partial_update'})
        response = view(request, pk=tenant.id)
        assert response.status_code == status.HTTP_200_OK
        tenant.refresh_from_db()
        assert tenant.name == 'Updated Org Name'

    def test_update_tenant_contact_info(self, superuser, tenant):
        """Test updating tenant contact information."""
        data = {
            'name': tenant.name,
            'contact_email': 'newemail@org.com',
            'contact_phone': '+9876543210',
        }
        request = factory.patch(f'/tenants/{tenant.id}/', data, format='json')
        force_authenticate(request, user=superuser)
        view = TenantViewSet.as_view({'patch': 'partial_update'})
        response = view(request, pk=tenant.id)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestTenantViewSetUpgradePlan:
    """Tests for TenantViewSet upgrade_plan action."""

    def test_upgrade_plan(self, superuser, tenant):
        """Test upgrading tenant plan."""
        data = {'plan': Tenant.BUSINESS}
        request = factory.post(
            f'/tenants/{tenant.id}/upgrade_plan/', data, format='json'
        )
        force_authenticate(request, user=superuser)
        view = TenantViewSet.as_view({'post': 'upgrade_plan'})
        response = view(request, pk=tenant.id)
        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data
        tenant.refresh_from_db()
        assert tenant.plan == Tenant.BUSINESS

    def test_upgrade_plan_downgrade_rejected(self, superuser, tenant):
        """Test downgrade is rejected."""
        data = {'plan': Tenant.STARTER}
        request = factory.post(
            f'/tenants/{tenant.id}/upgrade_plan/', data, format='json'
        )
        force_authenticate(request, user=superuser)
        view = TenantViewSet.as_view({'post': 'upgrade_plan'})
        response = view(request, pk=tenant.id)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_upgrade_plan_invalid_plan(self, superuser, tenant):
        """Test upgrade with invalid plan value."""
        data = {'plan': 'nonexistent'}
        request = factory.post(
            f'/tenants/{tenant.id}/upgrade_plan/', data, format='json'
        )
        force_authenticate(request, user=superuser)
        view = TenantViewSet.as_view({'post': 'upgrade_plan'})
        response = view(request, pk=tenant.id)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestTenantViewSetUsageStats:
    """Tests for TenantViewSet usage_stats action."""

    def test_usage_stats(self, superuser, tenant):
        """Test getting usage stats for a tenant."""
        request = factory.get(f'/tenants/{tenant.id}/usage_stats/')
        force_authenticate(request, user=superuser)
        view = TenantViewSet.as_view({'get': 'usage_stats'})
        response = view(request, pk=tenant.id)
        assert response.status_code == status.HTTP_200_OK
        assert 'users' in response.data
        assert 'clients' in response.data
        assert 'contracts' in response.data
        assert 'invoices_this_month' in response.data
        assert 'current' in response.data['users']
        assert 'limit' in response.data['users']

    def test_usage_stats_unauthenticated(self, tenant):
        """Test unauthenticated user cannot access usage stats."""
        request = factory.get(f'/tenants/{tenant.id}/usage_stats/')
        view = TenantViewSet.as_view({'get': 'usage_stats'})
        response = view(request, pk=tenant.id)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestTenantViewSetActivate:
    """Tests for TenantViewSet activate action."""

    def test_activate_tenant(self, superuser, tenant):
        """Test activating a tenant."""
        tenant.is_active = False
        tenant.save()
        request = factory.post(f'/tenants/{tenant.id}/activate/')
        force_authenticate(request, user=superuser)
        view = TenantViewSet.as_view({'post': 'activate'})
        response = view(request, pk=tenant.id)
        assert response.status_code == status.HTTP_200_OK
        assert 'activated' in response.data['message']
        tenant.refresh_from_db()
        assert tenant.is_active is True

    def test_activate_already_active_tenant(self, superuser, tenant):
        """Test activating an already active tenant still succeeds."""
        assert tenant.is_active is True
        request = factory.post(f'/tenants/{tenant.id}/activate/')
        force_authenticate(request, user=superuser)
        view = TenantViewSet.as_view({'post': 'activate'})
        response = view(request, pk=tenant.id)
        assert response.status_code == status.HTTP_200_OK
        tenant.refresh_from_db()
        assert tenant.is_active is True


@pytest.mark.django_db
class TestTenantViewSetDeactivate:
    """Tests for TenantViewSet deactivate action."""

    def test_deactivate_tenant(self, superuser, tenant):
        """Test deactivating a tenant."""
        assert tenant.is_active is True
        request = factory.post(f'/tenants/{tenant.id}/deactivate/')
        force_authenticate(request, user=superuser)
        view = TenantViewSet.as_view({'post': 'deactivate'})
        response = view(request, pk=tenant.id)
        assert response.status_code == status.HTTP_200_OK
        assert 'deactivated' in response.data['message']
        tenant.refresh_from_db()
        assert tenant.is_active is False

    def test_deactivate_already_inactive_tenant(self, superuser, tenant):
        """Test deactivating an already inactive tenant still succeeds."""
        tenant.is_active = False
        tenant.save()
        request = factory.post(f'/tenants/{tenant.id}/deactivate/')
        force_authenticate(request, user=superuser)
        view = TenantViewSet.as_view({'post': 'deactivate'})
        response = view(request, pk=tenant.id)
        assert response.status_code == status.HTTP_200_OK
        tenant.refresh_from_db()
        assert tenant.is_active is False


@pytest.mark.django_db
class TestTenantViewSetTrialStatus:
    """Tests for TenantViewSet trial_status action."""

    def test_trial_status_not_on_trial(self, superuser, tenant):
        """Test trial_status for non-trial tenant."""
        request = factory.get(f'/tenants/{tenant.id}/trial_status/')
        force_authenticate(request, user=superuser)
        view = TenantViewSet.as_view({'get': 'trial_status'})
        response = view(request, pk=tenant.id)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_trial'] is False
        assert response.data['is_on_trial'] is False

    def test_trial_status_on_trial(self, superuser, tenant_with_trial):
        """Test trial_status for tenant on trial."""
        request = factory.get(f'/tenants/{tenant_with_trial.id}/trial_status/')
        force_authenticate(request, user=superuser)
        view = TenantViewSet.as_view({'get': 'trial_status'})
        response = view(request, pk=tenant_with_trial.id)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_trial'] is True
        assert response.data['is_on_trial'] is True
        assert response.data['days_remaining'] > 0
        assert response.data['trial_ends_at'] is not None

    def test_trial_status_expired(self, superuser, tenant_with_trial):
        """Test trial_status for expired trial."""
        tenant_with_trial.trial_ends_at = timezone.now() - timedelta(days=1)
        tenant_with_trial.save()
        request = factory.get(f'/tenants/{tenant_with_trial.id}/trial_status/')
        force_authenticate(request, user=superuser)
        view = TenantViewSet.as_view({'get': 'trial_status'})
        response = view(request, pk=tenant_with_trial.id)
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

    def test_list_domains_as_superuser(self, superuser, domain):
        """Test superuser can list all domains."""
        request = factory.get('/domains/')
        force_authenticate(request, user=superuser)
        view = DomainViewSet.as_view({'get': 'list'})
        response = view(request)
        assert response.status_code == status.HTTP_200_OK

    def test_list_domains_unauthenticated(self):
        """Test unauthenticated user cannot list domains."""
        request = factory.get('/domains/')
        view = DomainViewSet.as_view({'get': 'list'})
        response = view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestDomainViewSetCRUD:
    """Tests for DomainViewSet CRUD actions."""

    def test_create_domain(self, superuser, tenant):
        """Test creating a new domain."""
        data = {
            'tenant': tenant.id,
            'domain': 'new-domain.aureon.local',
            'is_primary': False,
            'ssl_enabled': True,
        }
        request = factory.post('/domains/', data, format='json')
        force_authenticate(request, user=superuser)
        view = DomainViewSet.as_view({'post': 'create'})
        response = view(request)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['domain'] == 'new-domain.aureon.local'

    def test_retrieve_domain(self, superuser, domain):
        """Test retrieving a domain by ID."""
        request = factory.get(f'/domains/{domain.id}/')
        force_authenticate(request, user=superuser)
        view = DomainViewSet.as_view({'get': 'retrieve'})
        response = view(request, pk=domain.id)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['domain'] == 'test-org.aureon.local'

    def test_update_domain(self, superuser, domain):
        """Test updating a domain."""
        data = {'ssl_enabled': False}
        request = factory.patch(f'/domains/{domain.id}/', data, format='json')
        force_authenticate(request, user=superuser)
        view = DomainViewSet.as_view({'patch': 'partial_update'})
        response = view(request, pk=domain.id)
        assert response.status_code == status.HTTP_200_OK
        domain.refresh_from_db()
        assert domain.ssl_enabled is False

    def test_delete_domain(self, superuser, domain):
        """Test deleting a domain."""
        domain_id = domain.id
        request = factory.delete(f'/domains/{domain_id}/')
        force_authenticate(request, user=superuser)
        view = DomainViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=domain_id)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Domain.objects.filter(id=domain_id).exists()


@pytest.mark.django_db
class TestDomainViewSetVerify:
    """Tests for DomainViewSet verify action."""

    def test_verify_domain(self, superuser, tenant):
        """Test verifying a domain."""
        unverified_domain = Domain.objects.create(
            tenant=tenant,
            domain='unverified.aureon.local',
            is_primary=False,
            is_verified=False,
        )
        request = factory.post(f'/domains/{unverified_domain.id}/verify/')
        force_authenticate(request, user=superuser)
        view = DomainViewSet.as_view({'post': 'verify'})
        response = view(request, pk=unverified_domain.id)
        assert response.status_code == status.HTTP_200_OK
        assert 'verified' in response.data['message'].lower()
        unverified_domain.refresh_from_db()
        assert unverified_domain.is_verified is True
        assert unverified_domain.verified_at is not None

    def test_verify_already_verified_domain(self, superuser, domain):
        """Test verifying an already verified domain still succeeds."""
        request = factory.post(f'/domains/{domain.id}/verify/')
        force_authenticate(request, user=superuser)
        view = DomainViewSet.as_view({'post': 'verify'})
        response = view(request, pk=domain.id)
        assert response.status_code == status.HTTP_200_OK
        domain.refresh_from_db()
        assert domain.is_verified is True


@pytest.mark.django_db
class TestDomainViewSetSetPrimary:
    """Tests for DomainViewSet set_primary action."""

    def test_set_primary_domain(self, superuser, tenant, domain):
        """Test setting a domain as primary."""
        secondary = Domain.objects.create(
            tenant=tenant,
            domain='secondary.aureon.local',
            is_primary=False,
        )
        request = factory.post(f'/domains/{secondary.id}/set_primary/')
        force_authenticate(request, user=superuser)
        view = DomainViewSet.as_view({'post': 'set_primary'})
        response = view(request, pk=secondary.id)
        assert response.status_code == status.HTTP_200_OK
        assert 'primary' in response.data['message'].lower()
        secondary.refresh_from_db()
        assert secondary.is_primary is True
        # Original primary should now be non-primary
        domain.refresh_from_db()
        assert domain.is_primary is False

    def test_set_primary_on_already_primary(self, superuser, domain):
        """Test setting primary on an already primary domain succeeds."""
        request = factory.post(f'/domains/{domain.id}/set_primary/')
        force_authenticate(request, user=superuser)
        view = DomainViewSet.as_view({'post': 'set_primary'})
        response = view(request, pk=domain.id)
        assert response.status_code == status.HTTP_200_OK
        domain.refresh_from_db()
        assert domain.is_primary is True


@pytest.mark.django_db
class TestDomainViewSetQuerysetFiltering:
    """Tests for DomainViewSet queryset filtering."""

    def test_superuser_sees_all_domains(self, superuser, domain, tenant_with_trial):
        """Test superuser sees all domains across tenants."""
        Domain.objects.create(
            tenant=tenant_with_trial,
            domain='trial.aureon.local',
            is_primary=True,
        )
        request = factory.get('/domains/')
        force_authenticate(request, user=superuser)
        view = DomainViewSet.as_view({'get': 'list'})
        response = view(request)
        assert response.status_code == status.HTTP_200_OK
        results = response.data if isinstance(response.data, list) else response.data.get('results', [])
        assert len(results) >= 2
