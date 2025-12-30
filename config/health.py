"""
Aureon SaaS Platform - Health Check Endpoints
Rhematek Production Shield + Scale8

Provides comprehensive health monitoring for:
- Database connectivity
- Redis cache connectivity
- Celery worker status
- Disk space
- Memory usage
"""

import os
import shutil
import time
from datetime import datetime
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


@method_decorator(csrf_exempt, name='dispatch')
class HealthCheckView(View):
    """
    Basic health check endpoint.
    Returns 200 if the application is running.
    Used by load balancers and container orchestration.
    """

    def get(self, request):
        return JsonResponse({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "aureon-api",
            "version": getattr(settings, 'VERSION', '2.0.0-FINAL'),
        })


@method_decorator(csrf_exempt, name='dispatch')
class DeepHealthCheckView(View):
    """
    Deep health check endpoint.
    Verifies all critical dependencies.
    Used for comprehensive system monitoring.
    """

    def get(self, request):
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "aureon-api",
            "version": getattr(settings, 'VERSION', '2.0.0-FINAL'),
            "checks": {}
        }

        errors = []

        # Check Database
        db_status = self._check_database()
        health_status["checks"]["database"] = db_status
        if db_status["status"] != "healthy":
            errors.append("database")

        # Check Redis Cache
        cache_status = self._check_cache()
        health_status["checks"]["cache"] = cache_status
        if cache_status["status"] != "healthy":
            errors.append("cache")

        # Check Disk Space
        disk_status = self._check_disk_space()
        health_status["checks"]["disk"] = disk_status
        if disk_status["status"] != "healthy":
            errors.append("disk")

        # Check Memory
        memory_status = self._check_memory()
        health_status["checks"]["memory"] = memory_status
        if memory_status["status"] != "healthy":
            errors.append("memory")

        # Check Celery (optional, may not be running in all environments)
        celery_status = self._check_celery()
        health_status["checks"]["celery"] = celery_status

        # Overall status
        if errors:
            health_status["status"] = "degraded"
            health_status["errors"] = errors
            return JsonResponse(health_status, status=503)

        return JsonResponse(health_status)

    def _check_database(self):
        """Check database connectivity and response time."""
        try:
            start = time.time()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            latency = (time.time() - start) * 1000

            return {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "engine": connection.vendor,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    def _check_cache(self):
        """Check Redis cache connectivity."""
        try:
            start = time.time()
            test_key = "health_check_test"
            test_value = "ok"

            cache.set(test_key, test_value, timeout=10)
            result = cache.get(test_key)
            cache.delete(test_key)

            latency = (time.time() - start) * 1000

            if result == test_value:
                return {
                    "status": "healthy",
                    "latency_ms": round(latency, 2),
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": "Cache read/write mismatch",
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    def _check_disk_space(self):
        """Check available disk space."""
        try:
            total, used, free = shutil.disk_usage("/")
            free_gb = free // (1024 ** 3)
            total_gb = total // (1024 ** 3)
            used_percent = (used / total) * 100

            status = "healthy"
            if free_gb < 5:
                status = "critical"
            elif free_gb < 10:
                status = "warning"

            return {
                "status": status,
                "total_gb": total_gb,
                "free_gb": free_gb,
                "used_percent": round(used_percent, 2),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    def _check_memory(self):
        """Check available memory."""
        try:
            import psutil
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024 ** 3)
            used_percent = memory.percent

            status = "healthy"
            if memory.percent > 95:
                status = "critical"
            elif memory.percent > 85:
                status = "warning"

            return {
                "status": status,
                "available_gb": round(available_gb, 2),
                "used_percent": round(used_percent, 2),
            }
        except ImportError:
            return {
                "status": "unknown",
                "error": "psutil not installed",
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    def _check_celery(self):
        """Check Celery worker status."""
        try:
            from django_celery_results.models import TaskResult
            from celery import current_app

            # Try to ping workers
            inspector = current_app.control.inspect()
            active_workers = inspector.active()

            if active_workers:
                worker_count = len(active_workers)
                return {
                    "status": "healthy",
                    "workers": worker_count,
                }
            else:
                return {
                    "status": "warning",
                    "message": "No active workers detected",
                }
        except Exception as e:
            return {
                "status": "unknown",
                "error": str(e),
            }


@method_decorator(csrf_exempt, name='dispatch')
class ReadinessCheckView(View):
    """
    Kubernetes-style readiness check.
    Returns 200 only when the app is ready to serve traffic.
    """

    def get(self, request):
        # Check database connectivity
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            return JsonResponse(
                {"status": "not_ready", "reason": "database_unavailable"},
                status=503
            )

        # Check cache connectivity
        try:
            cache.get("readiness_check")
        except Exception:
            return JsonResponse(
                {"status": "not_ready", "reason": "cache_unavailable"},
                status=503
            )

        return JsonResponse({"status": "ready"})


@method_decorator(csrf_exempt, name='dispatch')
class LivenessCheckView(View):
    """
    Kubernetes-style liveness check.
    Returns 200 if the application process is alive.
    """

    def get(self, request):
        return JsonResponse({
            "status": "alive",
            "pid": os.getpid(),
        })


# URL patterns to include in main urls.py
def get_health_urls():
    """Get URL patterns for health checks."""
    from django.urls import path

    return [
        path('api/health/', HealthCheckView.as_view(), name='health-check'),
        path('api/health/deep/', DeepHealthCheckView.as_view(), name='health-check-deep'),
        path('api/health/ready/', ReadinessCheckView.as_view(), name='readiness-check'),
        path('api/health/live/', LivenessCheckView.as_view(), name='liveness-check'),
    ]
