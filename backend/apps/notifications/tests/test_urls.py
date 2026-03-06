"""Tests for notifications URL configuration."""

import pytest
from django.urls import reverse, resolve
from apps.notifications.urls import urlpatterns, router


class TestNotificationUrls:
    """Tests for notification URL configuration."""

    def test_urlpatterns_is_list(self):
        """Test that urlpatterns is a list."""
        assert isinstance(urlpatterns, list)

    def test_router_is_default_router(self):
        """Test that router is a DefaultRouter."""
        from rest_framework.routers import DefaultRouter
        assert isinstance(router, DefaultRouter)

    def test_app_name(self):
        """Test app_name is set correctly."""
        from apps.notifications import urls
        assert urls.app_name == 'notifications'

    def test_router_urls_included(self):
        """Test that router URLs are included in urlpatterns."""
        # The router is empty, so urlpatterns should contain the router include
        assert len(urlpatterns) >= 1
