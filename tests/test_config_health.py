"""
Tests for config/health.py.

Tests health check endpoints including:
- HealthCheckView (basic health)
- DeepHealthCheckView (comprehensive health)
- ReadinessCheckView (Kubernetes readiness)
- LivenessCheckView (Kubernetes liveness)
- get_health_urls helper
"""

import os
import json
import pytest
from unittest.mock import patch, MagicMock, PropertyMock

from django.test import RequestFactory
from django.http import JsonResponse

from config.health import (
    HealthCheckView,
    DeepHealthCheckView,
    ReadinessCheckView,
    LivenessCheckView,
    get_health_urls,
)


class TestHealthCheckView:
    """Test the basic HealthCheckView."""

    def test_returns_200(self, rf):
        """Test that health check returns 200 OK."""
        request = rf.get("/api/health/")
        response = HealthCheckView.as_view()(request)
        assert response.status_code == 200

    def test_returns_json(self, rf):
        """Test that health check returns JSON."""
        request = rf.get("/api/health/")
        response = HealthCheckView.as_view()(request)
        data = json.loads(response.content)
        assert isinstance(data, dict)

    def test_status_is_healthy(self, rf):
        """Test that status is 'healthy'."""
        request = rf.get("/api/health/")
        response = HealthCheckView.as_view()(request)
        data = json.loads(response.content)
        assert data["status"] == "healthy"

    def test_contains_timestamp(self, rf):
        """Test that response contains timestamp."""
        request = rf.get("/api/health/")
        response = HealthCheckView.as_view()(request)
        data = json.loads(response.content)
        assert "timestamp" in data
        assert len(data["timestamp"]) > 0

    def test_contains_service_name(self, rf):
        """Test that response contains service name."""
        request = rf.get("/api/health/")
        response = HealthCheckView.as_view()(request)
        data = json.loads(response.content)
        assert data["service"] == "aureon-api"

    def test_contains_version(self, rf):
        """Test that response contains version."""
        request = rf.get("/api/health/")
        response = HealthCheckView.as_view()(request)
        data = json.loads(response.content)
        assert "version" in data

    def test_csrf_exempt(self, rf):
        """Test that health check is CSRF-exempt (responds to GET without CSRF)."""
        request = rf.get("/api/health/")
        response = HealthCheckView.as_view()(request)
        assert response.status_code == 200


class TestDeepHealthCheckView:
    """Test the DeepHealthCheckView."""

    @patch.object(DeepHealthCheckView, "_check_celery")
    @patch.object(DeepHealthCheckView, "_check_memory")
    @patch.object(DeepHealthCheckView, "_check_disk_space")
    @patch.object(DeepHealthCheckView, "_check_cache")
    @patch.object(DeepHealthCheckView, "_check_database")
    def test_all_healthy(self, mock_db, mock_cache, mock_disk, mock_mem, mock_celery, rf):
        """Test when all checks pass."""
        mock_db.return_value = {"status": "healthy", "latency_ms": 1.5}
        mock_cache.return_value = {"status": "healthy", "latency_ms": 0.5}
        mock_disk.return_value = {"status": "healthy", "free_gb": 50}
        mock_mem.return_value = {"status": "healthy", "used_percent": 60}
        mock_celery.return_value = {"status": "healthy", "workers": 2}

        request = rf.get("/api/health/deep/")
        response = DeepHealthCheckView.as_view()(request)
        assert response.status_code == 200

        data = json.loads(response.content)
        assert data["status"] == "healthy"
        assert "checks" in data
        assert data["checks"]["database"]["status"] == "healthy"
        assert data["checks"]["cache"]["status"] == "healthy"
        assert data["checks"]["disk"]["status"] == "healthy"
        assert data["checks"]["memory"]["status"] == "healthy"
        assert data["checks"]["celery"]["status"] == "healthy"

    @patch.object(DeepHealthCheckView, "_check_celery")
    @patch.object(DeepHealthCheckView, "_check_memory")
    @patch.object(DeepHealthCheckView, "_check_disk_space")
    @patch.object(DeepHealthCheckView, "_check_cache")
    @patch.object(DeepHealthCheckView, "_check_database")
    def test_database_unhealthy(self, mock_db, mock_cache, mock_disk, mock_mem, mock_celery, rf):
        """Test when database check fails."""
        mock_db.return_value = {"status": "unhealthy", "error": "Connection refused"}
        mock_cache.return_value = {"status": "healthy"}
        mock_disk.return_value = {"status": "healthy"}
        mock_mem.return_value = {"status": "healthy"}
        mock_celery.return_value = {"status": "healthy"}

        request = rf.get("/api/health/deep/")
        response = DeepHealthCheckView.as_view()(request)
        assert response.status_code == 503

        data = json.loads(response.content)
        assert data["status"] == "degraded"
        assert "database" in data["errors"]

    @patch.object(DeepHealthCheckView, "_check_celery")
    @patch.object(DeepHealthCheckView, "_check_memory")
    @patch.object(DeepHealthCheckView, "_check_disk_space")
    @patch.object(DeepHealthCheckView, "_check_cache")
    @patch.object(DeepHealthCheckView, "_check_database")
    def test_cache_unhealthy(self, mock_db, mock_cache, mock_disk, mock_mem, mock_celery, rf):
        """Test when cache check fails."""
        mock_db.return_value = {"status": "healthy"}
        mock_cache.return_value = {"status": "unhealthy", "error": "Redis down"}
        mock_disk.return_value = {"status": "healthy"}
        mock_mem.return_value = {"status": "healthy"}
        mock_celery.return_value = {"status": "healthy"}

        request = rf.get("/api/health/deep/")
        response = DeepHealthCheckView.as_view()(request)
        assert response.status_code == 503

        data = json.loads(response.content)
        assert data["status"] == "degraded"
        assert "cache" in data["errors"]

    @patch.object(DeepHealthCheckView, "_check_celery")
    @patch.object(DeepHealthCheckView, "_check_memory")
    @patch.object(DeepHealthCheckView, "_check_disk_space")
    @patch.object(DeepHealthCheckView, "_check_cache")
    @patch.object(DeepHealthCheckView, "_check_database")
    def test_multiple_failures(self, mock_db, mock_cache, mock_disk, mock_mem, mock_celery, rf):
        """Test when multiple checks fail."""
        mock_db.return_value = {"status": "unhealthy"}
        mock_cache.return_value = {"status": "unhealthy"}
        mock_disk.return_value = {"status": "unhealthy"}
        mock_mem.return_value = {"status": "unhealthy"}
        mock_celery.return_value = {"status": "warning"}

        request = rf.get("/api/health/deep/")
        response = DeepHealthCheckView.as_view()(request)
        assert response.status_code == 503

        data = json.loads(response.content)
        assert data["status"] == "degraded"
        assert len(data["errors"]) == 4

    @patch.object(DeepHealthCheckView, "_check_celery")
    @patch.object(DeepHealthCheckView, "_check_memory")
    @patch.object(DeepHealthCheckView, "_check_disk_space")
    @patch.object(DeepHealthCheckView, "_check_cache")
    @patch.object(DeepHealthCheckView, "_check_database")
    def test_celery_warning_not_in_errors(self, mock_db, mock_cache, mock_disk, mock_mem, mock_celery, rf):
        """Test that celery warning does not cause degraded status."""
        mock_db.return_value = {"status": "healthy"}
        mock_cache.return_value = {"status": "healthy"}
        mock_disk.return_value = {"status": "healthy"}
        mock_mem.return_value = {"status": "healthy"}
        mock_celery.return_value = {"status": "warning", "message": "No workers"}

        request = rf.get("/api/health/deep/")
        response = DeepHealthCheckView.as_view()(request)
        assert response.status_code == 200

        data = json.loads(response.content)
        assert data["status"] == "healthy"

    def test_contains_version_and_service(self, rf):
        """Test response contains version and service info."""
        with patch.object(DeepHealthCheckView, "_check_database", return_value={"status": "healthy"}), \
             patch.object(DeepHealthCheckView, "_check_cache", return_value={"status": "healthy"}), \
             patch.object(DeepHealthCheckView, "_check_disk_space", return_value={"status": "healthy"}), \
             patch.object(DeepHealthCheckView, "_check_memory", return_value={"status": "healthy"}), \
             patch.object(DeepHealthCheckView, "_check_celery", return_value={"status": "healthy"}):

            request = rf.get("/api/health/deep/")
            response = DeepHealthCheckView.as_view()(request)
            data = json.loads(response.content)
            assert data["service"] == "aureon-api"
            assert "version" in data
            assert "timestamp" in data


@pytest.mark.django_db
class TestDeepHealthCheckDatabaseCheck:
    """Test the _check_database method of DeepHealthCheckView."""

    def test_database_healthy(self):
        """Test database health check with working database."""
        view = DeepHealthCheckView()
        result = view._check_database()
        assert result["status"] == "healthy"
        assert "latency_ms" in result
        assert result["latency_ms"] >= 0
        assert "engine" in result

    def test_database_unhealthy(self):
        """Test database health check with error."""
        view = DeepHealthCheckView()
        with patch("config.health.connection") as mock_conn:
            mock_conn.cursor.side_effect = Exception("Connection refused")
            result = view._check_database()
            assert result["status"] == "unhealthy"
            assert "error" in result


class TestDeepHealthCheckCacheCheck:
    """Test the _check_cache method of DeepHealthCheckView."""

    def test_cache_healthy(self):
        """Test cache health check with working cache."""
        view = DeepHealthCheckView()
        with patch("config.health.cache") as mock_cache:
            mock_cache.get.return_value = "ok"
            result = view._check_cache()
            assert result["status"] == "healthy"
            assert "latency_ms" in result

    def test_cache_value_mismatch(self):
        """Test cache health check with value mismatch."""
        view = DeepHealthCheckView()
        with patch("config.health.cache") as mock_cache:
            mock_cache.get.return_value = "wrong"
            result = view._check_cache()
            assert result["status"] == "unhealthy"
            assert "mismatch" in result["error"].lower()

    def test_cache_exception(self):
        """Test cache health check with exception."""
        view = DeepHealthCheckView()
        with patch("config.health.cache") as mock_cache:
            mock_cache.set.side_effect = Exception("Redis down")
            result = view._check_cache()
            assert result["status"] == "unhealthy"
            assert "Redis down" in result["error"]


class TestDeepHealthCheckDiskCheck:
    """Test the _check_disk_space method of DeepHealthCheckView."""

    def test_disk_healthy(self):
        """Test disk health check with plenty of space."""
        view = DeepHealthCheckView()
        with patch("shutil.disk_usage") as mock_du:
            # 100GB total, 50GB used, 50GB free
            mock_du.return_value = (
                100 * (1024 ** 3),
                50 * (1024 ** 3),
                50 * (1024 ** 3),
            )
            result = view._check_disk_space()
            assert result["status"] == "healthy"
            assert result["free_gb"] == 50
            assert result["total_gb"] == 100

    def test_disk_warning(self):
        """Test disk health check with low free space (warning)."""
        view = DeepHealthCheckView()
        with patch("shutil.disk_usage") as mock_du:
            # 100GB total, 93GB used, 7GB free
            mock_du.return_value = (
                100 * (1024 ** 3),
                93 * (1024 ** 3),
                7 * (1024 ** 3),
            )
            result = view._check_disk_space()
            assert result["status"] == "warning"

    def test_disk_critical(self):
        """Test disk health check with very low free space (critical)."""
        view = DeepHealthCheckView()
        with patch("shutil.disk_usage") as mock_du:
            # 100GB total, 97GB used, 3GB free
            mock_du.return_value = (
                100 * (1024 ** 3),
                97 * (1024 ** 3),
                3 * (1024 ** 3),
            )
            result = view._check_disk_space()
            assert result["status"] == "critical"

    def test_disk_exception(self):
        """Test disk health check with exception."""
        view = DeepHealthCheckView()
        with patch("shutil.disk_usage") as mock_du:
            mock_du.side_effect = OSError("Permission denied")
            result = view._check_disk_space()
            assert result["status"] == "unhealthy"
            assert "Permission denied" in result["error"]

    def test_disk_used_percent(self):
        """Test disk used percentage calculation."""
        view = DeepHealthCheckView()
        with patch("shutil.disk_usage") as mock_du:
            # 200GB total, 100GB used, 100GB free
            mock_du.return_value = (
                200 * (1024 ** 3),
                100 * (1024 ** 3),
                100 * (1024 ** 3),
            )
            result = view._check_disk_space()
            assert result["used_percent"] == 50.0


class TestDeepHealthCheckMemoryCheck:
    """Test the _check_memory method of DeepHealthCheckView."""

    def test_memory_healthy(self):
        """Test memory health check with healthy memory."""
        view = DeepHealthCheckView()
        mock_memory = MagicMock()
        mock_memory.available = 8 * (1024 ** 3)  # 8GB available
        mock_memory.percent = 50.0

        with patch("psutil.virtual_memory", return_value=mock_memory):
            result = view._check_memory()
            assert result["status"] == "healthy"
            assert "available_gb" in result
            assert "used_percent" in result

    def test_memory_warning(self):
        """Test memory health check with high usage (warning)."""
        view = DeepHealthCheckView()
        mock_memory = MagicMock()
        mock_memory.available = 2 * (1024 ** 3)
        mock_memory.percent = 90.0

        with patch("psutil.virtual_memory", return_value=mock_memory):
            result = view._check_memory()
            assert result["status"] == "warning"

    def test_memory_critical(self):
        """Test memory health check with very high usage (critical)."""
        view = DeepHealthCheckView()
        mock_memory = MagicMock()
        mock_memory.available = 0.5 * (1024 ** 3)
        mock_memory.percent = 96.0

        with patch("psutil.virtual_memory", return_value=mock_memory):
            result = view._check_memory()
            assert result["status"] == "critical"

    def test_memory_psutil_not_installed(self):
        """Test memory health check when psutil is not available."""
        view = DeepHealthCheckView()
        with patch.dict("sys.modules", {"psutil": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module named 'psutil'")):
                result = view._check_memory()
                assert result["status"] == "unknown"
                assert "psutil" in result["error"]

    def test_memory_exception(self):
        """Test memory health check with exception."""
        view = DeepHealthCheckView()
        with patch("psutil.virtual_memory", side_effect=RuntimeError("OS error")):
            result = view._check_memory()
            assert result["status"] == "unhealthy"
            assert "OS error" in result["error"]


class TestDeepHealthCheckCeleryCheck:
    """Test the _check_celery method of DeepHealthCheckView."""

    def test_celery_healthy(self):
        """Test celery health check with active workers."""
        view = DeepHealthCheckView()
        mock_inspector = MagicMock()
        mock_inspector.active.return_value = {"worker1": [], "worker2": []}

        with patch("celery.current_app") as mock_app:
            mock_app.control.inspect.return_value = mock_inspector
            result = view._check_celery()
            assert result["status"] == "healthy"
            assert result["workers"] == 2

    def test_celery_no_workers(self):
        """Test celery health check with no active workers."""
        view = DeepHealthCheckView()
        mock_inspector = MagicMock()
        mock_inspector.active.return_value = None

        with patch("celery.current_app") as mock_app:
            mock_app.control.inspect.return_value = mock_inspector
            result = view._check_celery()
            assert result["status"] == "warning"
            assert "No active workers" in result["message"]

    def test_celery_exception(self):
        """Test celery health check with exception."""
        view = DeepHealthCheckView()
        with patch("celery.current_app") as mock_app:
            mock_app.control.inspect.side_effect = Exception("Broker unreachable")
            result = view._check_celery()
            assert result["status"] == "unknown"
            assert "Broker unreachable" in result["error"]


@pytest.mark.django_db
class TestReadinessCheckView:
    """Test the ReadinessCheckView."""

    def test_ready_when_all_good(self, rf):
        """Test readiness check returns ready when all services are up."""
        request = rf.get("/api/health/ready/")
        with patch("config.health.cache") as mock_cache:
            mock_cache.get.return_value = None
            response = ReadinessCheckView.as_view()(request)
            assert response.status_code == 200
            data = json.loads(response.content)
            assert data["status"] == "ready"

    def test_not_ready_database_down(self, rf):
        """Test readiness check returns not_ready when database is down."""
        request = rf.get("/api/health/ready/")
        with patch("config.health.connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.execute.side_effect = Exception("DB down")
            mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
            mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

            response = ReadinessCheckView.as_view()(request)
            assert response.status_code == 503
            data = json.loads(response.content)
            assert data["status"] == "not_ready"
            assert data["reason"] == "database_unavailable"

    def test_not_ready_cache_down(self, rf):
        """Test readiness check returns not_ready when cache is down."""
        request = rf.get("/api/health/ready/")
        with patch("config.health.cache") as mock_cache:
            mock_cache.get.side_effect = Exception("Redis down")
            response = ReadinessCheckView.as_view()(request)
            assert response.status_code == 503
            data = json.loads(response.content)
            assert data["status"] == "not_ready"
            assert data["reason"] == "cache_unavailable"

    def test_csrf_exempt(self, rf):
        """Test that readiness check is CSRF-exempt."""
        request = rf.get("/api/health/ready/")
        with patch("config.health.connection") as mock_conn, \
             patch("config.health.cache") as mock_cache:
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
            mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
            mock_cache.get.return_value = None
            response = ReadinessCheckView.as_view()(request)
            assert response.status_code == 200


class TestLivenessCheckView:
    """Test the LivenessCheckView."""

    def test_returns_200(self, rf):
        """Test that liveness check returns 200."""
        request = rf.get("/api/health/live/")
        response = LivenessCheckView.as_view()(request)
        assert response.status_code == 200

    def test_returns_alive_status(self, rf):
        """Test that liveness check returns alive status."""
        request = rf.get("/api/health/live/")
        response = LivenessCheckView.as_view()(request)
        data = json.loads(response.content)
        assert data["status"] == "alive"

    def test_returns_pid(self, rf):
        """Test that liveness check returns process ID."""
        request = rf.get("/api/health/live/")
        response = LivenessCheckView.as_view()(request)
        data = json.loads(response.content)
        assert "pid" in data
        assert data["pid"] == os.getpid()

    def test_csrf_exempt(self, rf):
        """Test that liveness check is CSRF-exempt."""
        request = rf.get("/api/health/live/")
        response = LivenessCheckView.as_view()(request)
        assert response.status_code == 200


class TestGetHealthUrls:
    """Test the get_health_urls helper function."""

    def test_returns_four_url_patterns(self):
        """Test that four URL patterns are returned."""
        urls = get_health_urls()
        assert len(urls) == 4

    def test_url_names(self):
        """Test URL pattern names."""
        urls = get_health_urls()
        names = {url.name for url in urls}
        assert names == {"health-check", "health-check-deep", "readiness-check", "liveness-check"}

    def test_url_paths(self):
        """Test URL pattern paths."""
        urls = get_health_urls()
        patterns = {str(url.pattern) for url in urls}
        assert "api/health/" in patterns
        assert "api/health/deep/" in patterns
        assert "api/health/ready/" in patterns
        assert "api/health/live/" in patterns
