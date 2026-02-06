"""
Tests for tenants app URL configuration.
"""

import pytest
import uuid
from django.urls import reverse, resolve
from apps.tenants.views import TenantViewSet, DomainViewSet


class TestTenantURLs:
    """Tests for tenant URL resolution."""

    def test_tenant_list_url_resolves(self):
        """Test tenant-list URL resolves to TenantViewSet."""
        url = reverse('tenants:tenant-list')
        assert '/api/tenants/' in url
        resolver = resolve(url)
        assert resolver.func.cls == TenantViewSet

    def test_tenant_detail_url_resolves(self):
        """Test tenant-detail URL resolves correctly."""
        pk = uuid.uuid4()
        url = reverse('tenants:tenant-detail', kwargs={'pk': pk})
        assert f'/api/tenants/{pk}/' in url
        resolver = resolve(url)
        assert resolver.func.cls == TenantViewSet

    def test_tenant_upgrade_plan_url_resolves(self):
        """Test upgrade_plan action URL resolves."""
        pk = uuid.uuid4()
        url = reverse('tenants:tenant-upgrade-plan', kwargs={'pk': pk})
        assert f'/api/tenants/{pk}/upgrade_plan/' in url

    def test_tenant_usage_stats_url_resolves(self):
        """Test usage_stats action URL resolves."""
        pk = uuid.uuid4()
        url = reverse('tenants:tenant-usage-stats', kwargs={'pk': pk})
        assert f'/api/tenants/{pk}/usage_stats/' in url

    def test_tenant_activate_url_resolves(self):
        """Test activate action URL resolves."""
        pk = uuid.uuid4()
        url = reverse('tenants:tenant-activate', kwargs={'pk': pk})
        assert f'/api/tenants/{pk}/activate/' in url

    def test_tenant_deactivate_url_resolves(self):
        """Test deactivate action URL resolves."""
        pk = uuid.uuid4()
        url = reverse('tenants:tenant-deactivate', kwargs={'pk': pk})
        assert f'/api/tenants/{pk}/deactivate/' in url

    def test_tenant_trial_status_url_resolves(self):
        """Test trial_status action URL resolves."""
        pk = uuid.uuid4()
        url = reverse('tenants:tenant-trial-status', kwargs={'pk': pk})
        assert f'/api/tenants/{pk}/trial_status/' in url

    def test_domain_list_url_resolves(self):
        """Test domain-list URL resolves to DomainViewSet."""
        url = reverse('tenants:domain-list')
        assert '/api/domains/' in url
        resolver = resolve(url)
        assert resolver.func.cls == DomainViewSet

    def test_domain_detail_url_resolves(self):
        """Test domain-detail URL resolves correctly."""
        pk = uuid.uuid4()
        url = reverse('tenants:domain-detail', kwargs={'pk': pk})
        assert f'/api/domains/{pk}/' in url
        resolver = resolve(url)
        assert resolver.func.cls == DomainViewSet

    def test_domain_verify_url_resolves(self):
        """Test domain verify action URL resolves."""
        pk = uuid.uuid4()
        url = reverse('tenants:domain-verify', kwargs={'pk': pk})
        assert f'/api/domains/{pk}/verify/' in url

    def test_domain_set_primary_url_resolves(self):
        """Test domain set_primary action URL resolves."""
        pk = uuid.uuid4()
        url = reverse('tenants:domain-set-primary', kwargs={'pk': pk})
        assert f'/api/domains/{pk}/set_primary/' in url

    def test_app_name(self):
        """Test the app_name is set to 'tenants'."""
        from apps.tenants import urls
        assert urls.app_name == 'tenants'
