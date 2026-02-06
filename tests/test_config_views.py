"""
Tests for config/views.py.

Tests the view layer including:
- HomeView (domain-based routing)
- TenantDashboardView
- TenantLoginView (GET and POST)
- TenantLogoutView (GET and POST)
- ReactCatchAllView
- serve_marketing_site helper function
- serve_react_app helper function
"""

import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock

from django.test import RequestFactory, TestCase, override_settings
from django.http import HttpResponse, JsonResponse
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.models import AnonymousUser

from config.views import (
    HomeView,
    TenantDashboardView,
    TenantLoginView,
    TenantLogoutView,
    ReactCatchAllView,
    serve_marketing_site,
    serve_react_app,
)


@pytest.fixture
def rf():
    """Provide a RequestFactory instance."""
    return RequestFactory()


def _add_session(request):
    """Add session support to a RequestFactory request."""
    middleware = SessionMiddleware(lambda req: HttpResponse())
    middleware.process_request(request)
    request.session.save()


class TestServeMarketingSite:
    """Test the serve_marketing_site helper function."""

    def test_returns_fallback_when_no_build(self, rf):
        """Test fallback HTML when marketing site is not built."""
        request = rf.get("/")
        response = serve_marketing_site(request, "")
        assert response.status_code == 200
        assert b"Marketing Site Setup Required" in response.content

    def test_strips_leading_slash_from_path(self, rf):
        """Test that leading slashes are stripped from path."""
        request = rf.get("/about/")
        response = serve_marketing_site(request, "/about/")
        assert response.status_code == 200

    def test_strips_trailing_slash_from_path(self, rf):
        """Test that trailing slashes are stripped from path."""
        request = rf.get("/about/")
        response = serve_marketing_site(request, "about/")
        assert response.status_code == 200

    def test_serves_index_html_for_root(self, rf):
        """Test that root path serves index.html from a marketing directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            marketing_dir = os.path.join(tmpdir, "frontend-marketing", "out")
            os.makedirs(marketing_dir)
            index_path = os.path.join(marketing_dir, "index.html")
            with open(index_path, "w") as f:
                f.write("<html><body>Marketing Home</body></html>")

            with override_settings(
                BASE_DIR=tmpdir,
                STATIC_ROOT=None,
                STATICFILES_DIRS=[],
            ):
                request = rf.get("/")
                response = serve_marketing_site(request, "")
                assert response.status_code == 200
                assert b"Marketing Home" in response.content
                assert response["Content-Type"] == "text/html"

    def test_serves_subpage_index_html(self, rf):
        """Test that a subpage path resolves to path/index.html."""
        with tempfile.TemporaryDirectory() as tmpdir:
            marketing_dir = os.path.join(tmpdir, "frontend-marketing", "out", "about")
            os.makedirs(marketing_dir)
            with open(os.path.join(marketing_dir, "index.html"), "w") as f:
                f.write("<html><body>About Page</body></html>")

            with override_settings(
                BASE_DIR=tmpdir,
                STATIC_ROOT=None,
                STATICFILES_DIRS=[],
            ):
                request = rf.get("/about/")
                response = serve_marketing_site(request, "about")
                assert response.status_code == 200
                assert b"About Page" in response.content

    def test_serves_subpage_html_file(self, rf):
        """Test that a subpage path resolves to path.html."""
        with tempfile.TemporaryDirectory() as tmpdir:
            marketing_dir = os.path.join(tmpdir, "frontend-marketing", "out")
            os.makedirs(marketing_dir)
            with open(os.path.join(marketing_dir, "pricing.html"), "w") as f:
                f.write("<html><body>Pricing Page</body></html>")

            with override_settings(
                BASE_DIR=tmpdir,
                STATIC_ROOT=None,
                STATICFILES_DIRS=[],
            ):
                request = rf.get("/pricing/")
                response = serve_marketing_site(request, "pricing")
                assert response.status_code == 200
                assert b"Pricing Page" in response.content

    def test_checks_static_root(self, rf):
        """Test that STATIC_ROOT/marketing is checked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            marketing_dir = os.path.join(tmpdir, "staticroot", "marketing")
            os.makedirs(marketing_dir)
            with open(os.path.join(marketing_dir, "index.html"), "w") as f:
                f.write("<html><body>Static Root Marketing</body></html>")

            with override_settings(
                BASE_DIR=tmpdir,
                STATIC_ROOT=os.path.join(tmpdir, "staticroot"),
                STATICFILES_DIRS=[],
            ):
                request = rf.get("/")
                response = serve_marketing_site(request, "")
                assert response.status_code == 200
                assert b"Static Root Marketing" in response.content

    def test_checks_staticfiles_dirs(self, rf):
        """Test that STATICFILES_DIRS are checked for marketing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            static_dir = os.path.join(tmpdir, "mystaticdir")
            marketing_dir = os.path.join(static_dir, "marketing")
            os.makedirs(marketing_dir)
            with open(os.path.join(marketing_dir, "index.html"), "w") as f:
                f.write("<html><body>StaticFiles Dir Marketing</body></html>")

            with override_settings(
                BASE_DIR=tmpdir,
                STATIC_ROOT=None,
                STATICFILES_DIRS=[static_dir],
            ):
                request = rf.get("/")
                response = serve_marketing_site(request, "")
                assert response.status_code == 200
                assert b"StaticFiles Dir Marketing" in response.content

    def test_fallback_contains_build_instructions(self, rf):
        """Test that fallback page contains build instructions."""
        request = rf.get("/")
        response = serve_marketing_site(request, "")
        content = response.content.decode()
        assert "cd frontend-marketing" in content
        assert "npm install" in content
        assert "npm run build" in content
        assert "Rhematek Solutions" in content


class TestServeReactApp:
    """Test the serve_react_app helper function."""

    def test_returns_fallback_when_no_build(self, rf):
        """Test fallback HTML when React build is not found."""
        request = rf.get("/dashboard/")
        response = serve_react_app(request)
        assert response.status_code == 200
        assert b"Setup Required" in response.content

    def test_serves_react_index_from_static_root(self, rf):
        """Test serving React app from STATIC_ROOT."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dashboard_dir = os.path.join(tmpdir, "staticroot", "dashboard")
            os.makedirs(dashboard_dir)
            with open(os.path.join(dashboard_dir, "index.html"), "w") as f:
                f.write("<html><body>React Dashboard</body></html>")

            with override_settings(
                BASE_DIR=tmpdir,
                STATIC_ROOT=os.path.join(tmpdir, "staticroot"),
                STATICFILES_DIRS=[],
            ):
                request = rf.get("/dashboard/")
                response = serve_react_app(request)
                assert response.status_code == 200
                assert b"React Dashboard" in response.content
                assert response["Content-Type"] == "text/html"

    def test_serves_react_from_frontend_dist(self, rf):
        """Test serving React app from frontend/dist for development."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dist_dir = os.path.join(tmpdir, "frontend", "dist")
            os.makedirs(dist_dir)
            with open(os.path.join(dist_dir, "index.html"), "w") as f:
                f.write("<html><body>React Dev</body></html>")

            with override_settings(
                BASE_DIR=tmpdir,
                STATIC_ROOT=None,
                STATICFILES_DIRS=[],
            ):
                request = rf.get("/dashboard/")
                response = serve_react_app(request)
                assert response.status_code == 200
                assert b"React Dev" in response.content

    def test_serves_from_staticfiles_dirs(self, rf):
        """Test serving React from STATICFILES_DIRS."""
        with tempfile.TemporaryDirectory() as tmpdir:
            static_dir = os.path.join(tmpdir, "mystaticdir")
            dashboard_dir = os.path.join(static_dir, "dashboard")
            os.makedirs(dashboard_dir)
            with open(os.path.join(dashboard_dir, "index.html"), "w") as f:
                f.write("<html><body>React Static</body></html>")

            with override_settings(
                BASE_DIR=tmpdir,
                STATIC_ROOT=None,
                STATICFILES_DIRS=[static_dir],
            ):
                request = rf.get("/dashboard/")
                response = serve_react_app(request)
                assert response.status_code == 200
                assert b"React Static" in response.content

    def test_fallback_contains_build_instructions(self, rf):
        """Test that fallback page contains build instructions."""
        request = rf.get("/dashboard/")
        response = serve_react_app(request)
        content = response.content.decode()
        assert "cd frontend" in content
        assert "npm install" in content
        assert "npm run build" in content
        assert "Rhematek Solutions" in content

    def test_context_parameter_is_accepted(self, rf):
        """Test that context parameter is accepted (even if unused)."""
        request = rf.get("/dashboard/")
        response = serve_react_app(request, context={"key": "value"})
        assert response.status_code == 200


class TestHomeView:
    """Test the HomeView class."""

    def test_main_domain_serves_marketing_site(self, rf):
        """Test that main domain serves the marketing site."""
        request = rf.get("/")
        request.META["HTTP_HOST"] = "localhost"

        with patch("config.views.serve_marketing_site") as mock_serve:
            mock_serve.return_value = HttpResponse("Marketing")
            response = HomeView.as_view()(request)
            mock_serve.assert_called_once_with(request, "")

    def test_main_domain_with_port_serves_marketing_site(self, rf):
        """Test that main domain with port serves marketing site."""
        request = rf.get("/")
        request.META["HTTP_HOST"] = "localhost:8000"

        with patch("config.views.serve_marketing_site") as mock_serve:
            mock_serve.return_value = HttpResponse("Marketing")
            response = HomeView.as_view()(request)
            mock_serve.assert_called_once()

    def test_www_domain_serves_marketing_site(self, rf):
        """Test that www domain serves marketing site."""
        request = rf.get("/")
        request.META["HTTP_HOST"] = "www.aureon.rhematek-solutions.com"

        with patch("config.views.serve_marketing_site") as mock_serve:
            mock_serve.return_value = HttpResponse("Marketing")
            response = HomeView.as_view()(request)
            mock_serve.assert_called_once()

    def test_aureon_domain_serves_marketing_site(self, rf):
        """Test that the main aureon domain serves marketing site."""
        request = rf.get("/")
        request.META["HTTP_HOST"] = "aureon.rhematek-solutions.com"

        with patch("config.views.serve_marketing_site") as mock_serve:
            mock_serve.return_value = HttpResponse("Marketing")
            response = HomeView.as_view()(request)
            mock_serve.assert_called_once()

    def test_127_0_0_1_serves_marketing_site(self, rf):
        """Test that 127.0.0.1 serves marketing site."""
        request = rf.get("/")
        request.META["HTTP_HOST"] = "127.0.0.1"

        with patch("config.views.serve_marketing_site") as mock_serve:
            mock_serve.return_value = HttpResponse("Marketing")
            response = HomeView.as_view()(request)
            mock_serve.assert_called_once()

    def test_tenant_subdomain_serves_react_app(self, rf):
        """Test that tenant subdomain serves the React dashboard."""
        request = rf.get("/")
        request.META["HTTP_HOST"] = "testorg.aureon.local"

        with patch("config.views.serve_react_app") as mock_serve:
            mock_serve.return_value = HttpResponse("React")
            response = HomeView.as_view()(request)
            mock_serve.assert_called_once_with(request)

    def test_unknown_domain_serves_react_app(self, rf):
        """Test that unknown domain falls through to React app."""
        request = rf.get("/")
        request.META["HTTP_HOST"] = "unknown-host.example.com"

        with patch("config.views.serve_react_app") as mock_serve:
            mock_serve.return_value = HttpResponse("React")
            response = HomeView.as_view()(request)
            mock_serve.assert_called_once()

    def test_main_domains_constant(self):
        """Test that MAIN_DOMAINS contains expected values."""
        expected = [
            "aureon.rhematek-solutions.com",
            "www.aureon.rhematek-solutions.com",
            "localhost",
            "127.0.0.1",
        ]
        assert HomeView.MAIN_DOMAINS == expected


class TestTenantDashboardView:
    """Test the TenantDashboardView class."""

    def test_get_without_path(self, rf):
        """Test GET request to dashboard root."""
        request = rf.get("/dashboard/")

        with patch("config.views.serve_react_app") as mock_serve:
            mock_serve.return_value = HttpResponse("Dashboard")
            response = TenantDashboardView.as_view()(request)
            mock_serve.assert_called_once_with(request)

    def test_get_with_nested_path(self, rf):
        """Test GET request to dashboard with nested path."""
        request = rf.get("/dashboard/settings/billing")

        with patch("config.views.serve_react_app") as mock_serve:
            mock_serve.return_value = HttpResponse("Dashboard")
            response = TenantDashboardView.as_view()(request, path="settings/billing")
            mock_serve.assert_called_once_with(request)

    def test_get_with_empty_path(self, rf):
        """Test GET request with explicitly empty path."""
        request = rf.get("/dashboard/")

        with patch("config.views.serve_react_app") as mock_serve:
            mock_serve.return_value = HttpResponse("Dashboard")
            response = TenantDashboardView.as_view()(request, path="")
            mock_serve.assert_called_once()


class TestTenantLoginView:
    """Test the TenantLoginView class."""

    def test_get_serves_react_app(self, rf):
        """Test that GET request serves React SPA."""
        request = rf.get("/login/")

        with patch("config.views.serve_react_app") as mock_serve:
            mock_serve.return_value = HttpResponse("Login Page")
            response = TenantLoginView.as_view()(request)
            mock_serve.assert_called_once_with(request)

    @pytest.mark.django_db
    def test_post_missing_credentials(self, rf):
        """Test POST with missing credentials returns 400."""
        request = rf.post("/login/", {"email": "", "password": ""})
        request.META["HTTP_HOST"] = "localhost:8000"
        _add_session(request)

        response = TenantLoginView.as_view()(request)
        assert response.status_code == 400
        import json
        data = json.loads(response.content)
        assert data["success"] is False
        assert "email and password" in data["error"]

    @pytest.mark.django_db
    def test_post_missing_email(self, rf):
        """Test POST with missing email returns 400."""
        request = rf.post("/login/", {"email": "", "password": "somepass"})
        request.META["HTTP_HOST"] = "localhost:8000"
        _add_session(request)

        response = TenantLoginView.as_view()(request)
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_post_missing_password(self, rf):
        """Test POST with missing password returns 400."""
        request = rf.post("/login/", {"email": "user@test.com", "password": ""})
        request.META["HTTP_HOST"] = "localhost:8000"
        _add_session(request)

        response = TenantLoginView.as_view()(request)
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_post_invalid_credentials(self, rf):
        """Test POST with invalid credentials returns 401."""
        request = rf.post("/login/", {"email": "bad@test.com", "password": "wrong"})
        request.META["HTTP_HOST"] = "localhost:8000"
        _add_session(request)

        response = TenantLoginView.as_view()(request)
        assert response.status_code == 401
        import json
        data = json.loads(response.content)
        assert data["success"] is False
        assert "Invalid" in data["error"]

    @pytest.mark.django_db
    def test_post_successful_login_superuser(self, rf, superuser):
        """Test successful login for superuser."""
        request = rf.post(
            "/login/",
            {"email": "superadmin@aureon.com", "password": "SuperSecurePass123!"},
        )
        request.META["HTTP_HOST"] = "localhost:8000"
        _add_session(request)

        response = TenantLoginView.as_view()(request)
        assert response.status_code == 200
        import json
        data = json.loads(response.content)
        assert data["success"] is True
        assert data["redirect"] == "/dashboard"

    @pytest.mark.django_db
    def test_post_custom_next_url(self, rf, superuser):
        """Test login with custom next URL."""
        request = rf.post(
            "/login/",
            {
                "email": "superadmin@aureon.com",
                "password": "SuperSecurePass123!",
                "next": "/invoices/",
            },
        )
        request.META["HTTP_HOST"] = "localhost:8000"
        _add_session(request)

        response = TenantLoginView.as_view()(request)
        assert response.status_code == 200
        import json
        data = json.loads(response.content)
        assert data["redirect"] == "/invoices/"

    @pytest.mark.django_db
    def test_post_tenant_mismatch(self, rf, admin_user, tenant, domain):
        """Test that a user from a different tenant is rejected."""
        from apps.tenants.models import Tenant, Domain

        # Create a second tenant
        other_tenant = Tenant(
            name="Other Organization",
            slug="other-org",
            schema_name="other_org",
            tenant_type=Tenant.FREELANCER,
            plan=Tenant.FREE,
            contact_email="other@testorg.com",
            is_active=True,
        )
        other_tenant.save()
        other_domain = Domain.objects.create(
            tenant=other_tenant,
            domain="other-org.aureon.local",
            is_primary=True,
        )

        request = rf.post(
            "/login/",
            {"email": "admin@testorg.com", "password": "SecurePass123!"},
        )
        # Use the other tenant's domain so tenant lookup finds other_tenant
        request.META["HTTP_HOST"] = "other-org.aureon.local"
        _add_session(request)

        response = TenantLoginView.as_view()(request)
        assert response.status_code == 403
        import json
        data = json.loads(response.content)
        assert "access" in data["error"].lower()

    @pytest.mark.django_db
    def test_get_tenant_returns_none_for_unknown_domain(self, rf):
        """Test that get_tenant returns None for unknown domain."""
        view = TenantLoginView()
        request = rf.get("/login/")
        request.META["HTTP_HOST"] = "nonexistent.aureon.local"
        tenant = view.get_tenant(request)
        assert tenant is None

    @pytest.mark.django_db
    def test_get_tenant_returns_tenant_for_valid_domain(self, rf, tenant, domain):
        """Test that get_tenant returns correct tenant for valid domain."""
        view = TenantLoginView()
        request = rf.get("/login/")
        request.META["HTTP_HOST"] = "test-org.aureon.local"
        result = view.get_tenant(request)
        assert result is not None
        assert result.id == tenant.id

    @pytest.mark.django_db
    def test_login_with_no_tenant_domain(self, rf, superuser):
        """Test login when no tenant domain exists (tenant=None scenario)."""
        request = rf.post(
            "/login/",
            {"email": "superadmin@aureon.com", "password": "SuperSecurePass123!"},
        )
        request.META["HTTP_HOST"] = "nonexistent.aureon.local"
        _add_session(request)

        response = TenantLoginView.as_view()(request)
        # Superuser should still be able to login even when tenant is None
        assert response.status_code == 200


class TestTenantLogoutView:
    """Test the TenantLogoutView class."""

    @pytest.mark.django_db
    def test_get_logout_redirects(self, rf, admin_user):
        """Test that GET logout redirects to /auth/login."""
        request = rf.get("/logout/")
        request.user = admin_user
        _add_session(request)

        response = TenantLogoutView.as_view()(request)
        assert response.status_code == 302
        assert response.url == "/auth/login"

    @pytest.mark.django_db
    def test_post_logout_returns_json(self, rf, admin_user):
        """Test that POST logout returns JSON success response."""
        request = rf.post("/logout/")
        request.user = admin_user
        _add_session(request)

        response = TenantLogoutView.as_view()(request)
        assert response.status_code == 200
        import json
        data = json.loads(response.content)
        assert data["success"] is True

    @pytest.mark.django_db
    def test_get_logout_anonymous_user(self, rf):
        """Test GET logout for anonymous user."""
        request = rf.get("/logout/")
        request.user = AnonymousUser()
        _add_session(request)

        response = TenantLogoutView.as_view()(request)
        assert response.status_code == 302

    @pytest.mark.django_db
    def test_post_logout_anonymous_user(self, rf):
        """Test POST logout for anonymous user."""
        request = rf.post("/logout/")
        request.user = AnonymousUser()
        _add_session(request)

        response = TenantLogoutView.as_view()(request)
        assert response.status_code == 200


class TestReactCatchAllView:
    """Test the ReactCatchAllView class."""

    def test_get_serves_react_app(self, rf):
        """Test that GET serves the React SPA."""
        request = rf.get("/some/path")

        with patch("config.views.serve_react_app") as mock_serve:
            mock_serve.return_value = HttpResponse("React")
            response = ReactCatchAllView.as_view()(request)
            mock_serve.assert_called_once_with(request)

    def test_get_with_path_parameter(self, rf):
        """Test that GET with path parameter serves React SPA."""
        request = rf.get("/some/nested/path")

        with patch("config.views.serve_react_app") as mock_serve:
            mock_serve.return_value = HttpResponse("React")
            response = ReactCatchAllView.as_view()(request, path="some/nested/path")
            mock_serve.assert_called_once()

    def test_get_with_empty_path(self, rf):
        """Test that GET with empty path defaults correctly."""
        request = rf.get("/")

        with patch("config.views.serve_react_app") as mock_serve:
            mock_serve.return_value = HttpResponse("React")
            response = ReactCatchAllView.as_view()(request, path="")
            mock_serve.assert_called_once()
