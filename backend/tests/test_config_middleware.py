"""
Tests for config/middleware/security.py.

Tests security middleware including:
- HoneypotMiddleware
- XSSSanitizationMiddleware
- RequestLoggingMiddleware
- SecurityHeadersMiddleware
- CSRFEnhancementMiddleware
"""

import json
import time
import pytest
from unittest.mock import patch, MagicMock, call

from django.test import RequestFactory, override_settings
from django.http import HttpResponse, HttpResponseForbidden, QueryDict
from django.utils import timezone

from config.middleware.security import (
    HoneypotMiddleware,
    XSSSanitizationMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
    CSRFEnhancementMiddleware,
)


@pytest.fixture
def rf():
    """Provide a RequestFactory instance."""
    return RequestFactory()


def get_response_200(request):
    """Simple response callable for middleware."""
    return HttpResponse("OK", status=200)


def get_response_403(request):
    """403 response callable for middleware."""
    return HttpResponse("Forbidden", status=403)


def get_response_401(request):
    """401 response callable for middleware."""
    return HttpResponse("Unauthorized", status=401)


def get_response_429(request):
    """429 response callable for middleware."""
    return HttpResponse("Rate Limited", status=429)


def get_response_500(request):
    """500 response callable for middleware."""
    return HttpResponse("Error", status=500)


# =============================================================================
# HoneypotMiddleware Tests
# =============================================================================


class TestHoneypotMiddleware:
    """Test the HoneypotMiddleware."""

    def setup_method(self):
        self.middleware = HoneypotMiddleware(get_response_200)

    def test_get_request_passes_through(self, rf):
        """Test that GET requests are not checked."""
        request = rf.get("/form-page/")
        result = self.middleware.process_request(request)
        assert result is None

    def test_post_without_honeypot_passes(self, rf):
        """Test that POST without honeypot fields passes."""
        request = rf.post("/submit/", {"name": "John", "email": "john@test.com"})
        result = self.middleware.process_request(request)
        assert result is None

    def test_post_with_filled_honeypot_blocked(self, rf):
        """Test that POST with filled honeypot field is blocked."""
        request = rf.post("/submit/", {"name": "John", "website_url": "spam.com"})
        result = self.middleware.process_request(request)
        assert isinstance(result, HttpResponseForbidden)

    def test_post_with_empty_honeypot_passes(self, rf):
        """Test that POST with empty honeypot field passes."""
        request = rf.post("/submit/", {"name": "John", "website_url": ""})
        result = self.middleware.process_request(request)
        assert result is None

    def test_post_with_whitespace_honeypot_passes(self, rf):
        """Test that POST with whitespace-only honeypot passes."""
        request = rf.post("/submit/", {"name": "John", "website_url": "   "})
        result = self.middleware.process_request(request)
        assert result is None

    def test_multiple_honeypot_fields(self, rf):
        """Test detection of various honeypot field names."""
        honeypot_fields = [
            "phone_number_2",
            "email_confirm",
            "hp_field",
            "contact_me_by_fax",
            "leave_blank",
            "company_fax",
            "url",
            "address2",
            "name_confirm",
        ]
        for field in honeypot_fields:
            request = rf.post("/submit/", {field: "filled_by_bot"})
            result = self.middleware.process_request(request)
            assert isinstance(result, HttpResponseForbidden), f"Field {field} was not detected"

    def test_skips_admin_paths(self, rf):
        """Test that admin paths are skipped."""
        request = rf.post("/admin/login/", {"website_url": "spam.com"})
        result = self.middleware.process_request(request)
        assert result is None

    def test_skips_api_paths(self, rf):
        """Test that API paths are skipped."""
        request = rf.post("/api/submit/", {"website_url": "spam.com"})
        result = self.middleware.process_request(request)
        assert result is None

    def test_skips_static_paths(self, rf):
        """Test that static file paths are skipped."""
        request = rf.post("/static/file.js", {"website_url": "spam.com"})
        result = self.middleware.process_request(request)
        assert result is None

    def test_skips_media_paths(self, rf):
        """Test that media file paths are skipped."""
        request = rf.post("/media/upload/", {"website_url": "spam.com"})
        result = self.middleware.process_request(request)
        assert result is None

    def test_skips_debug_toolbar_paths(self, rf):
        """Test that debug toolbar paths are skipped."""
        request = rf.post("/__debug__/render_panel/", {"website_url": "spam.com"})
        result = self.middleware.process_request(request)
        assert result is None

    def test_skips_prometheus_paths(self, rf):
        """Test that prometheus paths are skipped."""
        request = rf.post("/prometheus/metrics/", {"website_url": "spam.com"})
        result = self.middleware.process_request(request)
        assert result is None

    def test_timing_based_detection_too_fast(self, rf):
        """Test that forms submitted too quickly are detected."""
        # Submit form 0.5 seconds after creation (< 2 second threshold)
        form_time = timezone.now().timestamp() - 0.5
        request = rf.post(
            "/submit/", {"name": "Bot", "_form_timestamp": str(form_time)}
        )
        result = self.middleware.process_request(request)
        assert isinstance(result, HttpResponseForbidden)

    def test_timing_based_detection_normal_speed(self, rf):
        """Test that normally submitted forms pass timing check."""
        form_time = timezone.now().timestamp() - 5.0
        request = rf.post(
            "/submit/", {"name": "Human", "_form_timestamp": str(form_time)}
        )
        result = self.middleware.process_request(request)
        assert result is None

    def test_timing_no_timestamp_field(self, rf):
        """Test that forms without timestamp field pass timing check."""
        request = rf.post("/submit/", {"name": "User"})
        result = self.middleware.process_request(request)
        assert result is None

    def test_timing_invalid_timestamp(self, rf):
        """Test that invalid timestamp values are handled."""
        request = rf.post(
            "/submit/", {"name": "User", "_form_timestamp": "not_a_number"}
        )
        result = self.middleware.process_request(request)
        assert result is None

    def test_logs_honeypot_detection(self, rf):
        """Test that honeypot detection is logged."""
        with patch("config.middleware.security.security_logger") as mock_logger:
            request = rf.post("/submit/", {"website_url": "spam"})
            self.middleware.process_request(request)
            mock_logger.warning.assert_called_once()
            log_msg = mock_logger.warning.call_args[0][0]
            assert "Honeypot triggered" in log_msg

    def test_logs_timing_detection(self, rf):
        """Test that timing-based detection is logged."""
        with patch("config.middleware.security.security_logger") as mock_logger:
            form_time = timezone.now().timestamp() - 0.1
            request = rf.post(
                "/submit/", {"name": "Bot", "_form_timestamp": str(form_time)}
            )
            self.middleware.process_request(request)
            mock_logger.warning.assert_called_once()

    def test_block_increments_cache_counter(self, rf):
        """Test that blocking increments the cache counter."""
        with patch("config.middleware.security.cache") as mock_cache:
            mock_cache.get.return_value = 2
            request = rf.post("/submit/", {"website_url": "spam"})
            request.META["REMOTE_ADDR"] = "192.168.1.1"
            self.middleware.process_request(request)
            mock_cache.set.assert_called_once()
            # Block count should be 3 (2 + 1)
            args = mock_cache.set.call_args
            assert args[0][1] == 3

    def test_get_client_ip_from_remote_addr(self, rf):
        """Test getting client IP from REMOTE_ADDR."""
        request = rf.post("/submit/", {"website_url": "spam"})
        request.META["REMOTE_ADDR"] = "10.0.0.1"
        ip = self.middleware._get_client_ip(request)
        assert ip == "10.0.0.1"

    def test_get_client_ip_from_x_forwarded_for(self, rf):
        """Test getting client IP from X-Forwarded-For."""
        request = rf.get("/")
        request.META["HTTP_X_FORWARDED_FOR"] = "203.0.113.1, 70.41.3.18"
        ip = self.middleware._get_client_ip(request)
        assert ip == "203.0.113.1"

    def test_get_client_ip_no_headers(self, rf):
        """Test getting client IP when no headers present."""
        request = rf.get("/")
        # RequestFactory sets REMOTE_ADDR to 127.0.0.1 by default
        ip = self.middleware._get_client_ip(request)
        assert ip == "127.0.0.1"

    @override_settings(HONEYPOT_FIELDS=["custom_trap_field"])
    def test_custom_honeypot_fields_from_settings(self, rf):
        """Test that custom honeypot fields from settings are used."""
        middleware = HoneypotMiddleware(get_response_200)
        assert "custom_trap_field" in middleware.honeypot_fields
        # Original fields should still be present
        assert "website_url" in middleware.honeypot_fields

    def test_block_request_returns_forbidden_message(self, rf):
        """Test that blocked request returns appropriate message."""
        request = rf.post("/submit/", {"website_url": "spam"})
        with patch("config.middleware.security.cache"):
            result = self.middleware._block_request(request, "honeypot")
            assert result.status_code == 403
            assert b"could not be processed" in result.content


# =============================================================================
# XSSSanitizationMiddleware Tests
# =============================================================================


class TestXSSSanitizationMiddleware:
    """Test the XSSSanitizationMiddleware."""

    def setup_method(self):
        self.middleware = XSSSanitizationMiddleware(get_response_200)

    def test_get_request_sanitizes_params(self, rf):
        """Test that GET parameters are sanitized."""
        request = rf.get("/page/?q=<script>alert(1)</script>")
        self.middleware.process_request(request)
        assert "<script>" not in request.GET.get("q", "")

    def test_post_request_sanitizes_params(self, rf):
        """Test that POST parameters are sanitized."""
        request = rf.post("/submit/", {"name": '<script>alert("XSS")</script>'})
        self.middleware.process_request(request)
        assert "<script>" not in request.POST.get("name", "")

    def test_skips_admin_paths(self, rf):
        """Test that admin paths are skipped."""
        request = rf.post("/admin/save/", {"content": '<script>alert("XSS")</script>'})
        result = self.middleware.process_request(request)
        assert result is None
        # Admin content should not be sanitized
        assert "<script>" in request.POST.get("content", "")

    def test_skips_api_paths(self, rf):
        """Test that API paths are skipped."""
        request = rf.post("/api/create/", {"content": '<script>alert("XSS")</script>'})
        result = self.middleware.process_request(request)
        assert result is None

    def test_removes_script_tags(self, rf):
        """Test that script tags are removed."""
        request = rf.get("/page/?q=hello<script>evil()</script>world")
        self.middleware.process_request(request)
        value = request.GET.get("q", "")
        assert "<script>" not in value
        assert "</script>" not in value

    def test_removes_javascript_protocol(self, rf):
        """Test that javascript: protocol is removed."""
        request = rf.get("/page/?url=javascript:alert(1)")
        self.middleware.process_request(request)
        value = request.GET.get("url", "")
        assert "javascript:" not in value

    def test_removes_vbscript_protocol(self, rf):
        """Test that vbscript: protocol is removed."""
        request = rf.get("/page/?url=vbscript:alert(1)")
        self.middleware.process_request(request)
        value = request.GET.get("url", "")
        assert "vbscript:" not in value.lower()

    def test_removes_event_handlers(self, rf):
        """Test that inline event handlers are removed."""
        request = rf.get("/page/?q=<img onerror=alert(1) src=x>")
        self.middleware.process_request(request)
        value = request.GET.get("q", "")
        assert "onerror=" not in value

    def test_removes_iframe_tags(self, rf):
        """Test that iframe tags are removed."""
        request = rf.get('/page/?q=<iframe src="evil.com">')
        self.middleware.process_request(request)
        value = request.GET.get("q", "")
        assert "<iframe" not in value.lower()

    def test_removes_object_tags(self, rf):
        """Test that object tags are removed."""
        request = rf.get('/page/?q=<object data="evil.swf">')
        self.middleware.process_request(request)
        value = request.GET.get("q", "")
        assert "<object" not in value.lower()

    def test_removes_embed_tags(self, rf):
        """Test that embed tags are removed."""
        request = rf.get('/page/?q=<embed src="evil.swf">')
        self.middleware.process_request(request)
        value = request.GET.get("q", "")
        assert "<embed" not in value.lower()

    def test_removes_css_expression(self, rf):
        """Test that CSS expression() is removed."""
        request = rf.get("/page/?style=expression(alert(1))")
        self.middleware.process_request(request)
        value = request.GET.get("style", "")
        assert "expression(" not in value.lower()

    def test_html_escapes_special_chars(self, rf):
        """Test that special characters are HTML-escaped."""
        request = rf.get('/page/?q=<b>"test"&foo</b>')
        self.middleware.process_request(request)
        value = request.GET.get("q", "")
        assert "&lt;" in value or "<b>" not in value

    def test_safe_content_passes_through(self, rf):
        """Test that safe content is not mangled."""
        request = rf.get("/page/?q=Hello+World")
        self.middleware.process_request(request)
        value = request.GET.get("q", "")
        assert "Hello" in value
        assert "World" in value

    def test_non_string_values_pass_through(self):
        """Test that non-string values are returned as-is."""
        result = self.middleware._sanitize_value(12345)
        assert result == 12345

    def test_empty_string_passes_through(self):
        """Test that empty strings pass through."""
        result = self.middleware._sanitize_value("")
        assert result == ""

    def test_skip_fields_from_settings(self, rf):
        """Test that skip fields from settings are respected."""
        with override_settings(XSS_SKIP_FIELDS={"rich_content"}):
            middleware = XSSSanitizationMiddleware(get_response_200)
            assert "rich_content" in middleware.skip_fields

    def test_get_client_ip_from_forwarded(self, rf):
        """Test getting client IP from X-Forwarded-For."""
        request = rf.get("/")
        request.META["HTTP_X_FORWARDED_FOR"] = "1.2.3.4"
        ip = self.middleware._get_client_ip(request)
        assert ip == "1.2.3.4"

    def test_get_client_ip_from_remote_addr(self, rf):
        """Test getting client IP from REMOTE_ADDR."""
        request = rf.get("/")
        ip = self.middleware._get_client_ip(request)
        assert ip == "127.0.0.1"

    def test_log_xss_attempt(self, rf):
        """Test XSS attempt logging."""
        with patch("config.middleware.security.security_logger") as mock_logger:
            request = rf.get("/page/")
            request.META["REMOTE_ADDR"] = "10.0.0.1"
            self.middleware._log_xss_attempt(request, "field_name", "<script>evil</script>")
            mock_logger.warning.assert_called_once()

    def test_removes_data_protocol(self, rf):
        """Test that data: protocol is removed."""
        request = rf.get("/page/?url=data:text/html,<h1>evil</h1>")
        self.middleware.process_request(request)
        value = request.GET.get("url", "")
        assert "data:" not in value.lower()

    def test_removes_svg_with_events(self, rf):
        """Test that SVG tags with event handlers are removed."""
        request = rf.get("/page/?q=<svg onload=alert(1)>")
        self.middleware.process_request(request)
        value = request.GET.get("q", "")
        assert "<svg" not in value.lower() or "onload" not in value.lower()

    def test_empty_get_params_no_error(self, rf):
        """Test that empty GET params don't cause errors."""
        request = rf.get("/page/")
        result = self.middleware.process_request(request)
        assert result is None

    def test_empty_post_no_error(self, rf):
        """Test that empty POST body doesn't cause errors."""
        request = rf.post("/page/")
        result = self.middleware.process_request(request)
        assert result is None


# =============================================================================
# RequestLoggingMiddleware Tests
# =============================================================================


class TestRequestLoggingMiddleware:
    """Test the RequestLoggingMiddleware."""

    def test_normal_200_response_not_logged(self, rf):
        """Test that normal 200 responses to non-sensitive paths are not logged."""
        middleware = RequestLoggingMiddleware(get_response_200)
        request = rf.get("/dashboard/")
        request.user = MagicMock(spec=[])

        with patch.object(middleware, "logger") as mock_logger:
            response = middleware(request)
            assert response.status_code == 200
            mock_logger.log.assert_not_called()

    def test_403_response_logged_as_warning(self, rf):
        """Test that 403 responses are logged as warnings."""
        middleware = RequestLoggingMiddleware(get_response_403)
        request = rf.get("/restricted/")
        request.user = MagicMock(spec=[])

        with patch.object(middleware, "logger") as mock_logger, \
             patch("config.middleware.security.security_logger") as mock_sec_logger:
            response = middleware(request)
            mock_logger.log.assert_called_once()
            mock_sec_logger.warning.assert_called_once()
            assert "Access denied" in mock_sec_logger.warning.call_args[0][0]

    def test_401_response_logged(self, rf):
        """Test that 401 responses are logged."""
        middleware = RequestLoggingMiddleware(get_response_401)
        request = rf.get("/api/auth/login/")
        request.user = MagicMock(spec=[])

        with patch.object(middleware, "logger"), \
             patch("config.middleware.security.security_logger") as mock_sec_logger:
            response = middleware(request)
            mock_sec_logger.warning.assert_called_once()
            assert "Authentication failed" in mock_sec_logger.warning.call_args[0][0]

    def test_429_response_logged(self, rf):
        """Test that 429 responses are logged."""
        middleware = RequestLoggingMiddleware(get_response_429)
        request = rf.get("/api/data/")
        request.user = MagicMock(spec=[])

        with patch.object(middleware, "logger"), \
             patch("config.middleware.security.security_logger") as mock_sec_logger:
            response = middleware(request)
            mock_sec_logger.warning.assert_called_once()
            assert "Rate limit" in mock_sec_logger.warning.call_args[0][0]

    def test_sensitive_path_logged(self, rf):
        """Test that requests to sensitive paths are logged."""
        middleware = RequestLoggingMiddleware(get_response_200)
        request = rf.get("/admin/")
        request.user = MagicMock(spec=[])

        with patch.object(middleware, "logger") as mock_logger:
            response = middleware(request)
            mock_logger.log.assert_called_once()

    def test_api_auth_path_logged(self, rf):
        """Test that API auth paths are logged."""
        middleware = RequestLoggingMiddleware(get_response_200)
        request = rf.get("/api/auth/login/")
        request.user = MagicMock(spec=[])

        with patch.object(middleware, "logger") as mock_logger:
            response = middleware(request)
            mock_logger.log.assert_called_once()

    def test_api_payments_path_logged(self, rf):
        """Test that API payments paths are logged."""
        middleware = RequestLoggingMiddleware(get_response_200)
        request = rf.get("/api/payments/")
        request.user = MagicMock(spec=[])

        with patch.object(middleware, "logger") as mock_logger:
            response = middleware(request)
            mock_logger.log.assert_called_once()

    def test_capture_request_info(self, rf):
        """Test that request info is captured correctly."""
        middleware = RequestLoggingMiddleware(get_response_200)
        request = rf.get("/test/", HTTP_USER_AGENT="TestAgent/1.0")
        request.user = MagicMock(__str__=MagicMock(return_value="testuser"))
        request.META["REMOTE_ADDR"] = "192.168.1.100"

        info = middleware._capture_request_info(request)
        assert info["method"] == "GET"
        assert info["path"] == "/test/"
        assert info["ip"] == "192.168.1.100"
        assert info["user_agent"] == "TestAgent/1.0"

    def test_capture_anonymous_user(self, rf):
        """Test request info capture without user attribute."""
        middleware = RequestLoggingMiddleware(get_response_200)
        request = rf.get("/test/")
        # No user attribute
        if hasattr(request, "user"):
            delattr(request, "user")
        info = middleware._capture_request_info(request)
        assert info["user"] == "Anonymous"

    def test_get_client_ip_with_forwarded(self, rf):
        """Test client IP extraction from X-Forwarded-For."""
        middleware = RequestLoggingMiddleware(get_response_200)
        request = rf.get("/")
        request.META["HTTP_X_FORWARDED_FOR"] = "10.0.0.1, 10.0.0.2"
        ip = middleware._get_client_ip(request)
        assert ip == "10.0.0.1"

    def test_log_data_includes_duration(self, rf):
        """Test that logged data includes request duration."""
        middleware = RequestLoggingMiddleware(get_response_200)
        request = rf.get("/admin/")
        request.user = MagicMock(spec=[])

        with patch.object(middleware, "logger") as mock_logger:
            middleware(request)
            call_args = mock_logger.log.call_args
            log_json = json.loads(call_args[0][1])
            assert "duration_ms" in log_json

    def test_500_response_logged(self, rf):
        """Test that 500 responses are logged."""
        middleware = RequestLoggingMiddleware(get_response_500)
        request = rf.get("/page/")
        request.user = MagicMock(spec=[])

        with patch.object(middleware, "logger") as mock_logger:
            response = middleware(request)
            mock_logger.log.assert_called_once()

    def test_sensitive_paths_constant(self):
        """Test that SENSITIVE_PATHS contains expected paths."""
        expected = (
            "/admin/",
            "/api/auth/",
            "/accounts/login/",
            "/accounts/password/",
            "/api/users/",
            "/api/payments/",
        )
        assert RequestLoggingMiddleware.SENSITIVE_PATHS == expected

    def test_security_status_codes_constant(self):
        """Test that SECURITY_STATUS_CODES contains expected codes."""
        expected = {401, 403, 404, 405, 429, 500, 502, 503}
        assert RequestLoggingMiddleware.SECURITY_STATUS_CODES == expected


# =============================================================================
# SecurityHeadersMiddleware Tests
# =============================================================================


class TestSecurityHeadersMiddleware:
    """Test the SecurityHeadersMiddleware."""

    def setup_method(self):
        self.middleware = SecurityHeadersMiddleware(get_response_200)

    def test_permissions_policy_header_set(self, rf):
        """Test that Permissions-Policy header is set."""
        request = rf.get("/page/")
        response = self.middleware(request)
        assert "Permissions-Policy" in response

    def test_permissions_policy_disables_camera(self, rf):
        """Test that camera is disabled in Permissions-Policy."""
        request = rf.get("/page/")
        response = self.middleware(request)
        policy = response["Permissions-Policy"]
        assert "camera=()" in policy

    def test_permissions_policy_disables_microphone(self, rf):
        """Test that microphone is disabled in Permissions-Policy."""
        request = rf.get("/page/")
        response = self.middleware(request)
        policy = response["Permissions-Policy"]
        assert "microphone=()" in policy

    def test_permissions_policy_allows_payment_self(self, rf):
        """Test that payment is allowed for self only."""
        request = rf.get("/page/")
        response = self.middleware(request)
        policy = response["Permissions-Policy"]
        assert "payment=(self)" in policy

    def test_permissions_policy_disables_floc(self, rf):
        """Test that FLoC (interest-cohort) is disabled."""
        request = rf.get("/page/")
        response = self.middleware(request)
        policy = response["Permissions-Policy"]
        assert "interest-cohort=()" in policy

    def test_cross_origin_headers_set_for_non_static(self, rf):
        """Test that cross-origin headers are set for non-static requests."""
        request = rf.get("/page/")
        response = self.middleware(request)
        assert response["Cross-Origin-Embedder-Policy"] == "require-corp"
        assert response["Cross-Origin-Opener-Policy"] == "same-origin"
        assert response["Cross-Origin-Resource-Policy"] == "same-origin"

    def test_cross_origin_headers_not_set_for_static(self, rf):
        """Test that cross-origin headers are not set for static files."""
        request = rf.get("/static/js/app.js")
        response = self.middleware(request)
        assert "Cross-Origin-Embedder-Policy" not in response

    def test_cross_origin_headers_not_set_for_media(self, rf):
        """Test that cross-origin headers are not set for media files."""
        request = rf.get("/media/uploads/file.pdf")
        response = self.middleware(request)
        assert "Cross-Origin-Embedder-Policy" not in response

    def test_cache_control_for_admin(self, rf):
        """Test that Cache-Control is set for admin endpoint."""
        request = rf.get("/admin/")
        response = self.middleware(request)
        assert response["Cache-Control"] == "no-store, no-cache, must-revalidate, private"
        assert response["Pragma"] == "no-cache"
        assert response["Expires"] == "0"

    def test_cache_control_for_api_auth(self, rf):
        """Test that Cache-Control is set for API auth endpoint."""
        request = rf.get("/api/auth/login/")
        response = self.middleware(request)
        assert "no-store" in response["Cache-Control"]

    def test_cache_control_for_accounts(self, rf):
        """Test that Cache-Control is set for accounts endpoint."""
        request = rf.get("/accounts/login/")
        response = self.middleware(request)
        assert "no-store" in response["Cache-Control"]

    def test_cache_control_for_payments(self, rf):
        """Test that Cache-Control is set for payments endpoint."""
        request = rf.get("/api/payments/")
        response = self.middleware(request)
        assert "no-store" in response["Cache-Control"]

    def test_cache_control_not_set_for_regular_page(self, rf):
        """Test that Cache-Control is not set for regular pages."""
        request = rf.get("/dashboard/")
        response = self.middleware(request)
        assert response.get("Cache-Control") != "no-store, no-cache, must-revalidate, private"

    def test_referrer_policy_set(self, rf):
        """Test that Referrer-Policy header is set."""
        request = rf.get("/page/")
        response = self.middleware(request)
        assert response["Referrer-Policy"] == "strict-origin-when-cross-origin"

    def test_referrer_policy_not_overridden_if_present(self, rf):
        """Test that existing Referrer-Policy is not overridden."""
        def custom_response(req):
            resp = HttpResponse("OK")
            resp["Referrer-Policy"] = "no-referrer"
            return resp

        middleware = SecurityHeadersMiddleware(custom_response)
        request = rf.get("/page/")
        response = middleware(request)
        assert response["Referrer-Policy"] == "no-referrer"

    def test_x_content_type_options_set(self, rf):
        """Test that X-Content-Type-Options is set."""
        request = rf.get("/page/")
        response = self.middleware(request)
        assert response["X-Content-Type-Options"] == "nosniff"

    def test_x_permitted_cross_domain_policies_set(self, rf):
        """Test that X-Permitted-Cross-Domain-Policies is set."""
        request = rf.get("/page/")
        response = self.middleware(request)
        assert response["X-Permitted-Cross-Domain-Policies"] == "none"

    def test_clear_site_data_on_logout(self, rf):
        """Test that Clear-Site-Data header is set on logout."""
        request = rf.get("/accounts/logout/")
        response = self.middleware(request)
        assert "Clear-Site-Data" in response
        assert '"cache"' in response["Clear-Site-Data"]
        assert '"cookies"' in response["Clear-Site-Data"]
        assert '"storage"' in response["Clear-Site-Data"]

    def test_clear_site_data_on_api_logout(self, rf):
        """Test that Clear-Site-Data header is set on API logout."""
        request = rf.get("/api/auth/logout/")
        response = self.middleware(request)
        assert "Clear-Site-Data" in response

    def test_no_clear_site_data_on_regular_page(self, rf):
        """Test that Clear-Site-Data is not set on regular pages."""
        request = rf.get("/dashboard/")
        response = self.middleware(request)
        assert "Clear-Site-Data" not in response

    @override_settings(PERMISSIONS_POLICY={"camera": ["self"], "geolocation": ["https://maps.example.com"]})
    def test_custom_permissions_policy(self, rf):
        """Test custom permissions policy from settings."""
        middleware = SecurityHeadersMiddleware(get_response_200)
        request = rf.get("/page/")
        response = middleware(request)
        policy = response["Permissions-Policy"]
        assert "camera=(self)" in policy
        assert 'geolocation=("https://maps.example.com")' in policy

    @override_settings(CROSS_ORIGIN_POLICIES={"Cross-Origin-Opener-Policy": "same-origin-allow-popups"})
    def test_custom_cross_origin_policies(self, rf):
        """Test custom cross-origin policies from settings."""
        middleware = SecurityHeadersMiddleware(get_response_200)
        request = rf.get("/page/")
        response = middleware(request)
        assert response["Cross-Origin-Opener-Policy"] == "same-origin-allow-popups"


# =============================================================================
# CSRFEnhancementMiddleware Tests
# =============================================================================


class TestCSRFEnhancementMiddleware:
    """Test the CSRFEnhancementMiddleware."""

    def setup_method(self):
        self.middleware = CSRFEnhancementMiddleware(get_response_200)

    def test_get_request_passes_through(self, rf):
        """Test that GET requests are not checked."""
        request = rf.get("/api/payments/")
        result = self.middleware.process_request(request)
        assert result is None

    def test_head_request_passes_through(self, rf):
        """Test that HEAD requests are not checked."""
        request = rf.head("/api/payments/")
        result = self.middleware.process_request(request)
        assert result is None

    def test_options_request_passes_through(self, rf):
        """Test that OPTIONS requests are not checked."""
        request = rf.options("/api/payments/")
        result = self.middleware.process_request(request)
        assert result is None

    def test_api_with_authorization_passes(self, rf):
        """Test that API requests with Authorization header pass."""
        request = rf.post(
            "/api/payments/create/",
            HTTP_AUTHORIZATION="Bearer token123",
        )
        result = self.middleware.process_request(request)
        assert result is None

    @override_settings(
        CSRF_TRUSTED_ORIGINS=["https://aureon.rhematek-solutions.com"],
        ALLOWED_HOSTS=["aureon.rhematek-solutions.com"],
    )
    def test_valid_origin_passes(self, rf):
        """Test that valid origin passes validation."""
        request = rf.post(
            "/api/payments/create/",
            HTTP_ORIGIN="https://aureon.rhematek-solutions.com",
            content_type="application/json",
        )
        result = self.middleware.process_request(request)
        assert result is None

    @override_settings(
        CSRF_TRUSTED_ORIGINS=["https://aureon.rhematek-solutions.com"],
        ALLOWED_HOSTS=["aureon.rhematek-solutions.com"],
    )
    def test_invalid_origin_blocked(self, rf):
        """Test that invalid origin is blocked for strict paths."""
        request = rf.post(
            "/api/payments/create/",
            HTTP_ORIGIN="https://evil.com",
            content_type="application/json",
        )
        result = self.middleware.process_request(request)
        assert isinstance(result, HttpResponseForbidden)

    @override_settings(
        CSRF_TRUSTED_ORIGINS=[],
        ALLOWED_HOSTS=["localhost"],
    )
    def test_no_origin_no_referer_blocks_json(self, rf):
        """Test that AJAX request without origin/referer is blocked."""
        request = rf.post(
            "/api/payments/create/",
            content_type="application/json",
        )
        result = self.middleware.process_request(request)
        assert isinstance(result, HttpResponseForbidden)

    @override_settings(
        CSRF_TRUSTED_ORIGINS=[],
        ALLOWED_HOSTS=["localhost"],
    )
    def test_no_origin_no_referer_non_json_passes(self, rf):
        """Test that non-JSON request without origin/referer passes."""
        request = rf.post(
            "/api/payments/create/",
            content_type="application/x-www-form-urlencoded",
        )
        result = self.middleware.process_request(request)
        assert result is None

    def test_non_strict_path_passes(self, rf):
        """Test that non-strict paths are not subject to origin validation."""
        request = rf.post(
            "/submit-form/",
            HTTP_ORIGIN="https://evil.com",
        )
        result = self.middleware.process_request(request)
        assert result is None

    @override_settings(
        CSRF_TRUSTED_ORIGINS=["https://aureon.rhematek-solutions.com"],
        ALLOWED_HOSTS=["aureon.rhematek-solutions.com"],
    )
    def test_valid_referer_passes(self, rf):
        """Test that valid referer passes validation."""
        request = rf.post(
            "/api/auth/login/",
            HTTP_REFERER="https://aureon.rhematek-solutions.com/login/",
            content_type="application/json",
        )
        result = self.middleware.process_request(request)
        assert result is None

    @override_settings(
        CSRF_TRUSTED_ORIGINS=["https://*.rhematek-solutions.com"],
        ALLOWED_HOSTS=[".rhematek-solutions.com"],
    )
    def test_wildcard_origin_passes(self, rf):
        """Test that wildcard origin matching works."""
        request = rf.post(
            "/api/payments/create/",
            HTTP_ORIGIN="https://tenant.rhematek-solutions.com",
            content_type="application/json",
        )
        result = self.middleware.process_request(request)
        assert result is None

    @override_settings(
        CSRF_TRUSTED_ORIGINS=["https://aureon.rhematek-solutions.com"],
        ALLOWED_HOSTS=[".rhematek-solutions.com"],
    )
    def test_subdomain_referer_passes(self, rf):
        """Test that subdomain referer passes with dotted allowed host."""
        request = rf.post(
            "/admin/",
            HTTP_REFERER="https://app.rhematek-solutions.com/admin/",
            content_type="application/json",
        )
        result = self.middleware.process_request(request)
        assert result is None

    def test_logs_origin_validation_failure(self, rf):
        """Test that origin validation failure is logged."""
        with patch("config.middleware.security.security_logger") as mock_logger, \
             override_settings(CSRF_TRUSTED_ORIGINS=[], ALLOWED_HOSTS=[]):
            request = rf.post(
                "/api/payments/create/",
                HTTP_ORIGIN="https://evil.com",
                content_type="application/json",
            )
            self.middleware.process_request(request)
            mock_logger.warning.assert_called_once()
            assert "Origin validation failed" in mock_logger.warning.call_args[0][0]

    def test_get_client_ip(self, rf):
        """Test client IP extraction."""
        request = rf.post("/api/payments/")
        request.META["HTTP_X_FORWARDED_FOR"] = "5.6.7.8"
        ip = self.middleware._get_client_ip(request)
        assert ip == "5.6.7.8"

    def test_get_client_ip_fallback(self, rf):
        """Test client IP fallback to REMOTE_ADDR."""
        request = rf.post("/api/payments/")
        ip = self.middleware._get_client_ip(request)
        assert ip == "127.0.0.1"

    def test_strict_origin_paths_constant(self):
        """Test that STRICT_ORIGIN_PATHS contains expected paths."""
        expected = (
            "/api/payments/",
            "/api/auth/",
            "/admin/",
        )
        assert CSRFEnhancementMiddleware.STRICT_ORIGIN_PATHS == expected

    @override_settings(
        CSRF_TRUSTED_ORIGINS=["https://aureon.rhematek-solutions.com"],
    )
    def test_http_origin_variant_passes(self, rf):
        """Test that http:// variant of https:// origin passes."""
        request = rf.post(
            "/api/payments/create/",
            HTTP_ORIGIN="http://aureon.rhematek-solutions.com",
            content_type="application/json",
        )
        result = self.middleware.process_request(request)
        assert result is None
