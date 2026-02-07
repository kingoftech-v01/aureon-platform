"""
Tests for tenants app URL configuration.

Note: The tenants app URLs are not currently mounted in the main URL
configuration (config/urls.py). These tests verify the app's internal
URL patterns are correctly defined by resolving against the app's own
URL module.
"""

import pytest
import uuid
from django.urls import resolve, URLResolver, URLPattern
from apps.tenants.views import TenantViewSet, DomainViewSet


class TestTenantURLs:
    """Tests for tenant URL patterns defined in the app."""

    def _get_url_patterns(self):
        """Get all URL patterns from the tenants app."""
        from apps.tenants.urls import urlpatterns
        patterns = []
        for pattern in urlpatterns:
            if hasattr(pattern, 'url_patterns'):
                for sub in pattern.url_patterns:
                    patterns.append(sub)
            else:
                patterns.append(pattern)
        return patterns

    def _get_pattern_names(self):
        """Get all URL pattern names from the tenants app."""
        patterns = self._get_url_patterns()
        return [p.name for p in patterns if hasattr(p, 'name') and p.name]

    def test_app_name(self):
        """Test the app_name is set to 'tenants'."""
        from apps.tenants import urls
        assert urls.app_name == 'tenants'

    def test_router_registered_viewsets(self):
        """Test the router has all expected viewsets registered."""
        from apps.tenants.urls import router
        registered_names = [prefix for prefix, viewset, basename in router.registry]
        assert 'tenants' in registered_names
        assert 'domains' in registered_names

    def test_tenant_list_pattern_exists(self):
        """Test tenant-list URL pattern is registered."""
        names = self._get_pattern_names()
        assert 'tenant-list' in names

    def test_tenant_detail_pattern_exists(self):
        """Test tenant-detail URL pattern is registered."""
        names = self._get_pattern_names()
        assert 'tenant-detail' in names

    def test_domain_list_pattern_exists(self):
        """Test domain-list URL pattern is registered."""
        names = self._get_pattern_names()
        assert 'domain-list' in names

    def test_domain_detail_pattern_exists(self):
        """Test domain-detail URL pattern is registered."""
        names = self._get_pattern_names()
        assert 'domain-detail' in names

    def test_tenant_upgrade_plan_pattern_exists(self):
        """Test tenant-upgrade-plan URL pattern is registered."""
        names = self._get_pattern_names()
        assert 'tenant-upgrade-plan' in names

    def test_tenant_usage_stats_pattern_exists(self):
        """Test tenant-usage-stats URL pattern is registered."""
        names = self._get_pattern_names()
        assert 'tenant-usage-stats' in names

    def test_tenant_activate_pattern_exists(self):
        """Test tenant-activate URL pattern is registered."""
        names = self._get_pattern_names()
        assert 'tenant-activate' in names

    def test_tenant_deactivate_pattern_exists(self):
        """Test tenant-deactivate URL pattern is registered."""
        names = self._get_pattern_names()
        assert 'tenant-deactivate' in names

    def test_tenant_trial_status_pattern_exists(self):
        """Test tenant-trial-status URL pattern is registered."""
        names = self._get_pattern_names()
        assert 'tenant-trial-status' in names

    def test_domain_verify_pattern_exists(self):
        """Test domain-verify URL pattern is registered."""
        names = self._get_pattern_names()
        assert 'domain-verify' in names

    def test_domain_set_primary_pattern_exists(self):
        """Test domain-set-primary URL pattern is registered."""
        names = self._get_pattern_names()
        assert 'domain-set-primary' in names

    def test_urlpatterns_is_list(self):
        """Test that urlpatterns is a list."""
        from apps.tenants.urls import urlpatterns
        assert isinstance(urlpatterns, list)
        assert len(urlpatterns) > 0
