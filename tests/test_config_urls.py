"""
Tests for config URL configurations.

Tests URL resolution and reversibility for:
- config/urls.py (main URLs)
"""

import pytest
from django.urls import resolve, reverse, URLResolver, URLPattern
from django.test import RequestFactory


class TestMainUrls:
    """Test the main URL configuration (config/urls.py)."""

    def test_admin_url_resolves(self):
        """Test that the admin URL resolves."""
        match = resolve("/admin/")
        assert match.app_name == "admin" or "admin" in match.route

    def test_health_check_url_resolves(self):
        """Test that the health check URL resolves."""
        match = resolve("/api/health/")
        assert match.url_name == "health-check"

    def test_deep_health_check_url_resolves(self):
        """Test that the deep health check URL resolves."""
        match = resolve("/api/health/deep/")
        assert match.url_name == "health-check-deep"

    def test_readiness_check_url_resolves(self):
        """Test that the readiness check URL resolves."""
        match = resolve("/api/health/ready/")
        assert match.url_name == "readiness-check"

    def test_liveness_check_url_resolves(self):
        """Test that the liveness check URL resolves."""
        match = resolve("/api/health/live/")
        assert match.url_name == "liveness-check"

    def test_api_schema_url_resolves(self):
        """Test that the API schema URL resolves."""
        match = resolve("/api/schema/")
        assert match.url_name == "schema"

    def test_swagger_ui_url_resolves(self):
        """Test that the Swagger UI URL resolves."""
        match = resolve("/api/docs/")
        assert match.url_name == "swagger-ui"

    def test_redoc_url_resolves(self):
        """Test that the ReDoc URL resolves."""
        match = resolve("/api/redoc/")
        assert match.url_name == "redoc"

    def test_reverse_health_check(self):
        """Test that health check URL can be reversed."""
        url = reverse("health-check")
        assert url == "/api/health/"

    def test_reverse_deep_health_check(self):
        """Test that deep health check URL can be reversed."""
        url = reverse("health-check-deep")
        assert url == "/api/health/deep/"

    def test_reverse_readiness_check(self):
        """Test that readiness check URL can be reversed."""
        url = reverse("readiness-check")
        assert url == "/api/health/ready/"

    def test_reverse_liveness_check(self):
        """Test that liveness check URL can be reversed."""
        url = reverse("liveness-check")
        assert url == "/api/health/live/"

    def test_reverse_schema(self):
        """Test that API schema URL can be reversed."""
        url = reverse("schema")
        assert url == "/api/schema/"

    def test_reverse_swagger_ui(self):
        """Test that Swagger UI URL can be reversed."""
        url = reverse("swagger-ui")
        assert url == "/api/docs/"

    def test_reverse_redoc(self):
        """Test that ReDoc URL can be reversed."""
        url = reverse("redoc")
        assert url == "/api/redoc/"

    def test_reverse_token_obtain_pair(self):
        """Test that the token obtain pair URL can be reversed."""
        url = reverse("token_obtain_pair")
        assert url == "/api/token/"

    def test_reverse_token_refresh(self):
        """Test that the token refresh URL can be reversed."""
        url = reverse("token_refresh")
        assert url == "/api/token/refresh/"

    def test_reverse_token_verify(self):
        """Test that the token verify URL can be reversed."""
        url = reverse("token_verify")
        assert url == "/api/token/verify/"

    def test_api_auth_urls_included(self):
        """Test that API auth URLs are included."""
        match = resolve("/api/auth/login/")
        assert match is not None
        assert match.url_name == "token_obtain_pair"

    def test_accounts_urls_included(self):
        """Test that allauth accounts URLs are included."""
        match = resolve("/accounts/login/")
        assert match is not None

    def test_error_handlers_defined(self):
        """Test that custom error handlers are defined in URL config."""
        from config import urls
        assert hasattr(urls, "handler400")
        assert hasattr(urls, "handler403")
        assert hasattr(urls, "handler404")
        assert hasattr(urls, "handler500")
        assert urls.handler400 == "config.error_handlers.handler400"
        assert urls.handler403 == "config.error_handlers.handler403"
        assert urls.handler404 == "config.error_handlers.handler404"
        assert urls.handler500 == "config.error_handlers.handler500"

    def test_admin_site_customization(self):
        """Test that admin site is customized."""
        from django.contrib import admin
        assert admin.site.site_header == "Aureon Platform Administration"
        assert admin.site.site_title == "Aureon Admin"
        assert admin.site.index_title == "Welcome to Aureon by Rhematek Solutions"


class TestGetHealthUrls:
    """Test the get_health_urls function."""

    def test_returns_list_of_url_patterns(self):
        """Test that get_health_urls returns a list of URL patterns."""
        from config.health import get_health_urls
        urls = get_health_urls()
        assert isinstance(urls, list)
        assert len(urls) == 4

    def test_url_pattern_names(self):
        """Test that URL patterns have correct names."""
        from config.health import get_health_urls
        urls = get_health_urls()
        names = [url.name for url in urls]
        assert "health-check" in names
        assert "health-check-deep" in names
        assert "readiness-check" in names
        assert "liveness-check" in names


class TestUrlPatternCompleteness:
    """Test that all expected URL patterns are present."""

    def test_main_urlpatterns_is_list(self):
        """Test that urlpatterns is a list."""
        from config.urls import urlpatterns
        assert isinstance(urlpatterns, list)
        assert len(urlpatterns) > 0
