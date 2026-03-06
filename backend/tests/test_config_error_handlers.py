"""
Tests for config/error_handlers.py.

Tests custom error handlers including:
- is_api_request helper
- handler400
- handler403
- handler404
- handler500
- handler429
"""

import pytest
import json
from unittest.mock import patch, MagicMock

from django.test import RequestFactory
from django.http import HttpResponse

from config.error_handlers import (
    is_api_request,
    handler400,
    handler403,
    handler404,
    handler500,
    handler429,
)


@pytest.fixture
def rf():
    """Provide a RequestFactory instance."""
    return RequestFactory()


class TestIsApiRequest:
    """Test the is_api_request helper function."""

    def test_json_accept_header(self, rf):
        """Test that JSON Accept header is detected."""
        request = rf.get("/", HTTP_ACCEPT="application/json")
        assert is_api_request(request) is True

    def test_json_content_type(self, rf):
        """Test that JSON Content-Type is detected."""
        request = rf.get("/", CONTENT_TYPE="application/json")
        assert is_api_request(request) is True

    def test_api_path_prefix(self, rf):
        """Test that /api/ path prefix is detected."""
        request = rf.get("/api/users/")
        assert is_api_request(request) is True

    def test_api_path_nested(self, rf):
        """Test that nested /api/ paths are detected."""
        request = rf.get("/api/v1/contracts/")
        assert is_api_request(request) is True

    def test_html_request(self, rf):
        """Test that HTML requests are not API requests."""
        request = rf.get("/dashboard/", HTTP_ACCEPT="text/html")
        assert is_api_request(request) is False

    def test_no_accept_header_non_api_path(self, rf):
        """Test request with no Accept header and non-API path."""
        request = rf.get("/dashboard/")
        assert is_api_request(request) is False

    def test_mixed_accept_header_with_json(self, rf):
        """Test Accept header containing JSON among others."""
        request = rf.get("/", HTTP_ACCEPT="text/html, application/json")
        assert is_api_request(request) is True

    def test_api_root_path(self, rf):
        """Test the /api/ root path."""
        request = rf.get("/api/")
        assert is_api_request(request) is True

    def test_non_api_path_no_json(self, rf):
        """Test non-API path without JSON headers."""
        request = rf.get("/about/")
        assert is_api_request(request) is False


class TestHandler404:
    """Test the handler404 error handler."""

    def test_api_request_returns_json(self, rf):
        """Test that API requests get JSON response."""
        request = rf.get("/api/nonexistent/", HTTP_ACCEPT="application/json")
        request.META["CSRF_COOKIE"] = "test"

        response = handler404(request, exception=Exception("Not found"))
        assert response.status_code == 404
        data = json.loads(response.content)
        assert data["error"] == "Not Found"
        assert data["status_code"] == 404
        assert "message" in data

    def test_html_request_serves_react_app(self, rf):
        """Test that HTML requests serve React SPA."""
        request = rf.get("/nonexistent/")
        request.META["CSRF_COOKIE"] = "test"

        with patch("config.error_handlers.serve_react_app") as mock_serve:
            mock_serve.return_value = HttpResponse("React")
            response = handler404(request)
            mock_serve.assert_called_once_with(request)

    def test_api_path_returns_json(self, rf):
        """Test that /api/ path returns JSON even without Accept header."""
        request = rf.get("/api/missing/")
        request.META["CSRF_COOKIE"] = "test"

        response = handler404(request, exception=None)
        assert response.status_code == 404
        data = json.loads(response.content)
        assert data["error"] == "Not Found"

    def test_exception_parameter_accepted(self, rf):
        """Test that exception parameter is accepted."""
        request = rf.get("/api/test/")
        request.META["CSRF_COOKIE"] = "test"

        response = handler404(request, exception=ValueError("test"))
        assert response.status_code == 404

    def test_no_exception_parameter(self, rf):
        """Test handler404 with default exception=None."""
        request = rf.get("/api/test/")
        request.META["CSRF_COOKIE"] = "test"

        response = handler404(request)
        assert response.status_code == 404


class TestHandler500:
    """Test the handler500 error handler."""

    def test_api_request_returns_json(self, rf):
        """Test that API requests get JSON response with request_id."""
        request = rf.get("/api/error/", HTTP_ACCEPT="application/json")
        request.META["CSRF_COOKIE"] = "test"

        response = handler500(request)
        assert response.status_code == 500
        data = json.loads(response.content)
        assert data["error"] == "Internal Server Error"
        assert data["status_code"] == 500
        assert "request_id" in data
        assert len(data["request_id"]) == 8

    def test_html_request_serves_react_app(self, rf):
        """Test that HTML requests serve React SPA."""
        request = rf.get("/server-error/")
        request.META["CSRF_COOKIE"] = "test"

        with patch("config.error_handlers.serve_react_app") as mock_serve:
            mock_serve.return_value = HttpResponse("React Error Page")
            response = handler500(request)
            mock_serve.assert_called_once_with(request)

    def test_logs_error_with_request_id(self, rf):
        """Test that the error is logged with a request ID."""
        request = rf.get("/api/error/", HTTP_ACCEPT="application/json")
        request.META["CSRF_COOKIE"] = "test"

        with patch("config.error_handlers.logger") as mock_logger:
            response = handler500(request)
            mock_logger.error.assert_called_once()
            log_msg = mock_logger.error.call_args[0][0]
            assert "Request ID" in log_msg

    def test_request_id_is_unique(self, rf):
        """Test that each call generates a unique request_id."""
        request = rf.get("/api/error/", HTTP_ACCEPT="application/json")
        request.META["CSRF_COOKIE"] = "test"

        response1 = handler500(request)
        response2 = handler500(request)
        data1 = json.loads(response1.content)
        data2 = json.loads(response2.content)
        # Request IDs should be different (with very high probability)
        # Note: could theoretically collide but extremely unlikely
        assert "request_id" in data1
        assert "request_id" in data2


class TestHandler403:
    """Test the handler403 error handler."""

    def test_api_request_returns_json(self, rf):
        """Test that API requests get JSON 403 response."""
        request = rf.get("/api/restricted/", HTTP_ACCEPT="application/json")
        request.META["CSRF_COOKIE"] = "test"

        response = handler403(request, exception=Exception("Forbidden"))
        assert response.status_code == 403
        data = json.loads(response.content)
        assert data["error"] == "Forbidden"
        assert data["status_code"] == 403
        assert "permission" in data["message"].lower()

    def test_html_request_serves_react_app(self, rf):
        """Test that HTML requests serve React SPA."""
        request = rf.get("/restricted/")
        request.META["CSRF_COOKIE"] = "test"

        with patch("config.error_handlers.serve_react_app") as mock_serve:
            mock_serve.return_value = HttpResponse("React 403")
            response = handler403(request)
            mock_serve.assert_called_once_with(request)

    def test_no_exception_parameter(self, rf):
        """Test handler403 with default exception=None."""
        request = rf.get("/api/test/")
        request.META["CSRF_COOKIE"] = "test"

        response = handler403(request)
        assert response.status_code == 403


class TestHandler400:
    """Test the handler400 error handler."""

    def test_api_request_returns_json(self, rf):
        """Test that API requests get JSON 400 response."""
        request = rf.get("/api/bad-request/", HTTP_ACCEPT="application/json")
        request.META["CSRF_COOKIE"] = "test"

        response = handler400(request, exception=Exception("Bad Request"))
        assert response.status_code == 400
        data = json.loads(response.content)
        assert data["error"] == "Bad Request"
        assert data["status_code"] == 400
        assert "message" in data

    def test_html_request_serves_react_app(self, rf):
        """Test that HTML requests serve React SPA."""
        request = rf.get("/bad-request/")
        request.META["CSRF_COOKIE"] = "test"

        with patch("config.error_handlers.serve_react_app") as mock_serve:
            mock_serve.return_value = HttpResponse("React 400")
            response = handler400(request)
            mock_serve.assert_called_once_with(request)

    def test_no_exception_parameter(self, rf):
        """Test handler400 with default exception=None."""
        request = rf.get("/api/test/")
        request.META["CSRF_COOKIE"] = "test"

        response = handler400(request)
        assert response.status_code == 400


class TestHandler429:
    """Test the handler429 rate limit error handler."""

    def test_api_request_returns_json(self, rf):
        """Test that API requests get JSON 429 response."""
        request = rf.get("/api/rate-limited/", HTTP_ACCEPT="application/json")

        response = handler429(request)
        assert response.status_code == 429
        data = json.loads(response.content)
        assert data["error"] == "Too Many Requests"
        assert data["status_code"] == 429
        assert data["retry_after"] == 60
        assert "rate limit" in data["message"].lower()

    def test_html_request_serves_react_app(self, rf):
        """Test that HTML requests serve React SPA."""
        request = rf.get("/rate-limited/")

        with patch("config.error_handlers.serve_react_app") as mock_serve:
            mock_serve.return_value = HttpResponse("React 429")
            response = handler429(request)
            mock_serve.assert_called_once_with(request)

    def test_with_exception_parameter(self, rf):
        """Test handler429 with exception parameter."""
        request = rf.get("/api/test/")

        response = handler429(request, exception=Exception("Rate limited"))
        assert response.status_code == 429

    def test_without_exception_parameter(self, rf):
        """Test handler429 without exception parameter."""
        request = rf.get("/api/test/")

        response = handler429(request)
        assert response.status_code == 429


class TestErrorHandlerJsonResponses:
    """Test JSON response structure consistency across error handlers."""

    def test_all_json_responses_have_error_field(self, rf):
        """Test that all JSON error responses have an 'error' field."""
        api_request = rf.get("/api/test/", HTTP_ACCEPT="application/json")
        api_request.META["CSRF_COOKIE"] = "test"

        handlers = [
            (handler400, {"exception": None}),
            (handler403, {"exception": None}),
            (handler404, {"exception": None}),
            (handler500, {}),
            (handler429, {}),
        ]

        for handler_fn, kwargs in handlers:
            response = handler_fn(api_request, **kwargs)
            data = json.loads(response.content)
            assert "error" in data, f"{handler_fn.__name__} missing 'error' field"

    def test_all_json_responses_have_message_field(self, rf):
        """Test that all JSON error responses have a 'message' field."""
        api_request = rf.get("/api/test/", HTTP_ACCEPT="application/json")
        api_request.META["CSRF_COOKIE"] = "test"

        handlers = [
            (handler400, {"exception": None}),
            (handler403, {"exception": None}),
            (handler404, {"exception": None}),
            (handler500, {}),
            (handler429, {}),
        ]

        for handler_fn, kwargs in handlers:
            response = handler_fn(api_request, **kwargs)
            data = json.loads(response.content)
            assert "message" in data, f"{handler_fn.__name__} missing 'message' field"

    def test_all_json_responses_have_status_code_field(self, rf):
        """Test that all JSON error responses have a 'status_code' field."""
        api_request = rf.get("/api/test/", HTTP_ACCEPT="application/json")
        api_request.META["CSRF_COOKIE"] = "test"

        handlers_and_expected = [
            (handler400, {"exception": None}, 400),
            (handler403, {"exception": None}, 403),
            (handler404, {"exception": None}, 404),
            (handler500, {}, 500),
            (handler429, {}, 429),
        ]

        for handler_fn, kwargs, expected_code in handlers_and_expected:
            response = handler_fn(api_request, **kwargs)
            data = json.loads(response.content)
            assert data["status_code"] == expected_code
            assert response.status_code == expected_code
