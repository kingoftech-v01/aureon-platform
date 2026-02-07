"""
Tests for config/views.py.

Tests the view layer including:
- HomeView (serves marketing site)
- DashboardView (serves React SPA)
- ReactCatchAllView (serves React SPA)
- serve_marketing_site helper function
- serve_react_app helper function
"""

import os
import tempfile
from unittest.mock import patch

from django.test import override_settings
from django.http import HttpResponse

from config.views import (
    HomeView,
    DashboardView,
    ReactCatchAllView,
    serve_marketing_site,
    serve_react_app,
)


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

    def test_get_serves_marketing_site(self, rf):
        """Test that GET request serves the marketing site."""
        request = rf.get("/")

        with patch("config.views.serve_marketing_site") as mock_serve:
            mock_serve.return_value = HttpResponse("Marketing")
            response = HomeView.as_view()(request)
            mock_serve.assert_called_once_with(request, "")

    def test_get_returns_200(self, rf):
        """Test that GET request returns 200 status code."""
        request = rf.get("/")
        response = HomeView.as_view()(request)
        assert response.status_code == 200


class TestDashboardView:
    """Test the DashboardView class."""

    def test_get_without_path(self, rf):
        """Test GET request to dashboard root."""
        request = rf.get("/dashboard/")

        with patch("config.views.serve_react_app") as mock_serve:
            mock_serve.return_value = HttpResponse("Dashboard")
            response = DashboardView.as_view()(request)
            mock_serve.assert_called_once_with(request)

    def test_get_with_nested_path(self, rf):
        """Test GET request to dashboard with nested path."""
        request = rf.get("/dashboard/settings/billing")

        with patch("config.views.serve_react_app") as mock_serve:
            mock_serve.return_value = HttpResponse("Dashboard")
            response = DashboardView.as_view()(request, path="settings/billing")
            mock_serve.assert_called_once_with(request)

    def test_get_with_empty_path(self, rf):
        """Test GET request with explicitly empty path."""
        request = rf.get("/dashboard/")

        with patch("config.views.serve_react_app") as mock_serve:
            mock_serve.return_value = HttpResponse("Dashboard")
            response = DashboardView.as_view()(request, path="")
            mock_serve.assert_called_once()

    def test_get_returns_200(self, rf):
        """Test that GET request returns 200 status code."""
        request = rf.get("/dashboard/")
        response = DashboardView.as_view()(request)
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
