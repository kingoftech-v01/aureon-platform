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

    def test_home_url_resolves(self):
        """Test that the home URL resolves to HomeView."""
        match = resolve("/")
        assert match.url_name == "home"

    def test_admin_url_resolves(self):
        """Test that the admin URL resolves."""
        match = resolve("/admin/")
        assert match.app_name == "admin" or "admin" in match.route

    def test_dashboard_url_resolves(self):
        """Test that the dashboard URL resolves."""
        match = resolve("/dashboard/")
        assert match.url_name == "dashboard"

    def test_dashboard_with_path_resolves(self):
        """Test that the dashboard with sub-path resolves."""
        match = resolve("/dashboard/some/nested/path")
        assert match.url_name == "dashboard_path"

    def test_clients_url_resolves(self):
        """Test that the clients URL resolves to DashboardView."""
        match = resolve("/clients/")
        assert match.url_name == "clients"

    def test_clients_with_path_resolves(self):
        """Test that the clients URL with sub-path resolves."""
        match = resolve("/clients/123/edit")
        assert match.url_name == "clients_path"

    def test_contracts_url_resolves(self):
        """Test that the contracts URL resolves."""
        match = resolve("/contracts/")
        assert match.url_name == "contracts"

    def test_contracts_with_path_resolves(self):
        """Test that contracts URL with sub-path resolves."""
        match = resolve("/contracts/new")
        assert match.url_name == "contracts_path"

    def test_invoices_url_resolves(self):
        """Test that the invoices URL resolves."""
        match = resolve("/invoices/")
        assert match.url_name == "invoices"

    def test_invoices_with_path_resolves(self):
        """Test that invoices URL with sub-path resolves."""
        match = resolve("/invoices/detail/42")
        assert match.url_name == "invoices_path"

    def test_payments_url_resolves(self):
        """Test that the payments URL resolves."""
        match = resolve("/payments/")
        assert match.url_name == "payments"

    def test_payments_with_path_resolves(self):
        """Test that payments URL with sub-path resolves."""
        match = resolve("/payments/history")
        assert match.url_name == "payments_path"

    def test_analytics_url_resolves(self):
        """Test that the analytics URL resolves."""
        match = resolve("/analytics/")
        assert match.url_name == "analytics"

    def test_documents_url_resolves(self):
        """Test that the documents URL resolves."""
        match = resolve("/documents/")
        assert match.url_name == "documents"

    def test_documents_with_path_resolves(self):
        """Test that documents URL with sub-path resolves."""
        match = resolve("/documents/upload")
        assert match.url_name == "documents_path"

    def test_settings_url_resolves(self):
        """Test that the settings URL resolves."""
        match = resolve("/settings/")
        assert match.url_name == "settings"

    def test_settings_with_path_resolves(self):
        """Test that settings URL with sub-path resolves."""
        match = resolve("/settings/billing")
        assert match.url_name == "settings_path"

    def test_auth_path_resolves(self):
        """Test that auth catch-all path resolves."""
        match = resolve("/auth/login")
        assert match.url_name == "auth"

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

    def test_reverse_home(self):
        """Test that the home URL can be reversed."""
        url = reverse("home")
        assert url == "/"

    def test_reverse_dashboard(self):
        """Test that the dashboard URL can be reversed."""
        url = reverse("dashboard")
        assert url == "/dashboard/"

    def test_reverse_dashboard_with_path(self):
        """Test that the dashboard path URL can be reversed."""
        url = reverse("dashboard_path", kwargs={"path": "overview"})
        assert url == "/dashboard/overview"

    def test_reverse_clients(self):
        """Test that the clients URL can be reversed."""
        url = reverse("clients")
        assert url == "/clients/"

    def test_reverse_clients_with_path(self):
        """Test that the clients path URL can be reversed."""
        url = reverse("clients_path", kwargs={"path": "123/edit"})
        assert url == "/clients/123/edit"

    def test_reverse_contracts(self):
        """Test that the contracts URL can be reversed."""
        url = reverse("contracts")
        assert url == "/contracts/"

    def test_reverse_contracts_with_path(self):
        """Test that the contracts path URL can be reversed."""
        url = reverse("contracts_path", kwargs={"path": "new"})
        assert url == "/contracts/new"

    def test_reverse_invoices(self):
        """Test that the invoices URL can be reversed."""
        url = reverse("invoices")
        assert url == "/invoices/"

    def test_reverse_invoices_with_path(self):
        """Test that the invoices path URL can be reversed."""
        url = reverse("invoices_path", kwargs={"path": "detail/42"})
        assert url == "/invoices/detail/42"

    def test_reverse_payments(self):
        """Test that the payments URL can be reversed."""
        url = reverse("payments")
        assert url == "/payments/"

    def test_reverse_payments_with_path(self):
        """Test that the payments path URL can be reversed."""
        url = reverse("payments_path", kwargs={"path": "history"})
        assert url == "/payments/history"

    def test_reverse_analytics(self):
        """Test that the analytics URL can be reversed."""
        url = reverse("analytics")
        assert url == "/analytics/"

    def test_reverse_documents(self):
        """Test that the documents URL can be reversed."""
        url = reverse("documents")
        assert url == "/documents/"

    def test_reverse_documents_with_path(self):
        """Test that the documents path URL can be reversed."""
        url = reverse("documents_path", kwargs={"path": "upload"})
        assert url == "/documents/upload"

    def test_reverse_settings(self):
        """Test that the settings URL can be reversed."""
        url = reverse("settings")
        assert url == "/settings/"

    def test_reverse_settings_with_path(self):
        """Test that the settings path URL can be reversed."""
        url = reverse("settings_path", kwargs={"path": "billing"})
        assert url == "/settings/billing"

    def test_reverse_auth(self):
        """Test that the auth URL can be reversed."""
        url = reverse("auth", kwargs={"path": "login"})
        assert url == "/auth/login"

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

    def test_all_spa_routes_present(self):
        """Test that all SPA catch-all routes are present."""
        spa_routes = [
            "dashboard",
            "clients",
            "contracts",
            "invoices",
            "payments",
            "analytics",
            "documents",
            "settings",
        ]
        for route_name in spa_routes:
            url = reverse(route_name)
            assert url is not None, f"Route {route_name} should be reversible"

    def test_auth_route_present(self):
        """Test that the auth catch-all route is present."""
        url = reverse("auth", kwargs={"path": "login"})
        assert url is not None, "Route auth should be reversible"

    def test_all_path_routes_have_named_patterns(self):
        """Test routes with path parameters have distinct names."""
        path_routes = [
            ("dashboard_path", {"path": "test"}),
            ("clients_path", {"path": "test"}),
            ("contracts_path", {"path": "test"}),
            ("invoices_path", {"path": "test"}),
            ("payments_path", {"path": "test"}),
            ("documents_path", {"path": "test"}),
            ("settings_path", {"path": "test"}),
        ]
        for route_name, kwargs in path_routes:
            url = reverse(route_name, kwargs=kwargs)
            assert url is not None, f"Route {route_name} should be reversible"
