"""Tests for analytics URL configuration."""

import pytest
from django.urls import reverse, resolve
from apps.analytics import urls


class TestAnalyticsUrls:
    """Tests for analytics URL configuration."""

    def test_app_name(self):
        """Test app_name is set correctly."""
        assert urls.app_name == 'analytics'

    def test_urlpatterns_is_list(self):
        """Test that urlpatterns is a list."""
        assert isinstance(urls.urlpatterns, list)

    def test_dashboard_url_resolves(self):
        """Test dashboard summary URL resolves."""
        url = reverse('analytics:dashboard_summary')
        assert url == '/api/analytics/dashboard/'

        resolver = resolve('/api/analytics/dashboard/')
        assert resolver.view_name == 'analytics:dashboard_summary'

    def test_revenue_url_resolves(self):
        """Test revenue metrics URL resolves."""
        url = reverse('analytics:revenue_metrics')
        assert url == '/api/analytics/revenue/'

        resolver = resolve('/api/analytics/revenue/')
        assert resolver.view_name == 'analytics:revenue_metrics'

    def test_clients_url_resolves(self):
        """Test client metrics URL resolves."""
        url = reverse('analytics:client_metrics')
        assert url == '/api/analytics/clients/'

        resolver = resolve('/api/analytics/clients/')
        assert resolver.view_name == 'analytics:client_metrics'

    def test_activity_url_resolves(self):
        """Test activity feed URL resolves."""
        url = reverse('analytics:activity_feed')
        assert url == '/api/analytics/activity/'

        resolver = resolve('/api/analytics/activity/')
        assert resolver.view_name == 'analytics:activity_feed'

    def test_recalculate_url_resolves(self):
        """Test recalculate metrics URL resolves."""
        url = reverse('analytics:recalculate_metrics')
        assert url == '/api/analytics/recalculate/'

        resolver = resolve('/api/analytics/recalculate/')
        assert resolver.view_name == 'analytics:recalculate_metrics'

    def test_router_is_default_router(self):
        """Test that router is a DefaultRouter."""
        from rest_framework.routers import DefaultRouter
        assert isinstance(urls.router, DefaultRouter)

    def test_url_count(self):
        """Test expected number of URL patterns."""
        # 5 named paths + 1 router include = at least 6
        assert len(urls.urlpatterns) >= 6
