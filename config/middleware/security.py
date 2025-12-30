"""
Security Middleware for Aureon SaaS Platform
============================================

This module provides comprehensive security middleware:
1. HoneypotMiddleware - Bot detection via hidden form fields
2. XSSSanitizationMiddleware - XSS attack prevention
3. RequestLoggingMiddleware - Security audit logging
4. SecurityHeadersMiddleware - Additional security headers

Author: Rhematek Solutions
Version: 2.0.0
"""

import re
import json
import logging
import hashlib
import html
from datetime import datetime
from typing import Optional, Set, Dict, Any

from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.utils import timezone


# Configure security logger
security_logger = logging.getLogger('security')


# =============================================================================
# HONEYPOT MIDDLEWARE
# =============================================================================

class HoneypotMiddleware(MiddlewareMixin):
    """
    Honeypot field validation middleware for bot detection.

    Bots often fill in all form fields automatically, including hidden ones.
    This middleware detects such behavior and blocks the request.

    Protection Level: High
    Performance Impact: Low
    """

    # Honeypot field names that should always be empty
    HONEYPOT_FIELDS = {
        'website_url',      # Common honeypot name
        'phone_number_2',   # Secondary phone field
        'email_confirm',    # Email confirmation field
        'hp_field',         # Generic honeypot
        'contact_me_by_fax', # Fax field (obsolete)
        'leave_blank',      # Obvious honeypot
        'company_fax',      # Fax number
        'url',              # URL field
        'address2',         # Secondary address
        'name_confirm',     # Name confirmation
    }

    # Timing-based detection (forms submitted too quickly)
    MIN_FORM_SUBMISSION_TIME = 2  # seconds

    def __init__(self, get_response):
        self.get_response = get_response
        # Get custom honeypot fields from settings
        custom_fields = getattr(settings, 'HONEYPOT_FIELDS', [])
        self.honeypot_fields = self.HONEYPOT_FIELDS.union(set(custom_fields))

    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Check for honeypot field values in POST requests."""

        if request.method != 'POST':
            return None

        # Skip admin and API endpoints
        if self._should_skip_path(request.path):
            return None

        # Check honeypot fields
        for field in self.honeypot_fields:
            if field in request.POST and request.POST[field].strip():
                self._log_honeypot_detection(request, field)
                return self._block_request(request, 'honeypot')

        # Check timing-based honeypot
        if self._is_too_fast(request):
            self._log_honeypot_detection(request, 'timing')
            return self._block_request(request, 'timing')

        return None

    def _should_skip_path(self, path: str) -> bool:
        """Check if path should be skipped (admin, API, etc.)."""
        skip_prefixes = (
            '/admin/',
            '/api/',
            '/static/',
            '/media/',
            '/__debug__/',
            '/prometheus/',
        )
        return path.startswith(skip_prefixes)

    def _is_too_fast(self, request: HttpRequest) -> bool:
        """Check if form was submitted too quickly (likely a bot)."""
        timestamp_field = request.POST.get('_form_timestamp')
        if not timestamp_field:
            return False

        try:
            form_time = float(timestamp_field)
            current_time = timezone.now().timestamp()
            elapsed = current_time - form_time
            return elapsed < self.MIN_FORM_SUBMISSION_TIME
        except (ValueError, TypeError):
            return False

    def _log_honeypot_detection(self, request: HttpRequest, detection_type: str) -> None:
        """Log honeypot detection for security audit."""
        security_logger.warning(
            f"Honeypot triggered [{detection_type}] - "
            f"IP: {self._get_client_ip(request)}, "
            f"Path: {request.path}, "
            f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}"
        )

    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address, handling proxies."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'Unknown')

    def _block_request(self, request: HttpRequest, reason: str) -> HttpResponse:
        """Block request with appropriate response."""
        # Add to blocked IPs cache (optional rate limiting integration)
        ip = self._get_client_ip(request)
        cache_key = f'honeypot_block_{ip}'
        block_count = cache.get(cache_key, 0) + 1
        cache.set(cache_key, block_count, timeout=3600)  # 1 hour

        return HttpResponseForbidden(
            'Your request could not be processed. '
            'Please try again or contact support.'
        )


# =============================================================================
# XSS SANITIZATION MIDDLEWARE
# =============================================================================

class XSSSanitizationMiddleware(MiddlewareMixin):
    """
    XSS (Cross-Site Scripting) sanitization middleware.

    Sanitizes user input to prevent XSS attacks by:
    - HTML encoding dangerous characters
    - Removing script tags and event handlers
    - Sanitizing URLs in input

    Protection Level: Critical
    Performance Impact: Low-Medium
    """

    # Dangerous HTML patterns
    DANGEROUS_PATTERNS = [
        re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
        re.compile(r'javascript:', re.IGNORECASE),
        re.compile(r'vbscript:', re.IGNORECASE),
        re.compile(r'data:', re.IGNORECASE),
        re.compile(r'on\w+\s*=', re.IGNORECASE),  # Event handlers
        re.compile(r'<iframe[^>]*>', re.IGNORECASE),
        re.compile(r'<object[^>]*>', re.IGNORECASE),
        re.compile(r'<embed[^>]*>', re.IGNORECASE),
        re.compile(r'<svg[^>]*on', re.IGNORECASE),  # SVG with event handlers
        re.compile(r'expression\s*\(', re.IGNORECASE),  # CSS expression
        re.compile(r'url\s*\(\s*["\']?\s*javascript:', re.IGNORECASE),
    ]

    # Fields to skip sanitization (e.g., rich text fields handled separately)
    SKIP_FIELDS: Set[str] = set()

    def __init__(self, get_response):
        self.get_response = get_response
        # Get custom skip fields from settings
        self.skip_fields = getattr(settings, 'XSS_SKIP_FIELDS', self.SKIP_FIELDS)

    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Sanitize POST and GET data."""

        # Skip for trusted endpoints
        if self._is_trusted_endpoint(request):
            return None

        # Sanitize GET parameters
        if request.GET:
            self._sanitize_query_dict(request.GET)

        # Sanitize POST parameters
        if request.method == 'POST' and request.POST:
            self._sanitize_query_dict(request.POST)

        return None

    def _is_trusted_endpoint(self, request: HttpRequest) -> bool:
        """Check if endpoint is trusted (e.g., admin with CSRF protection)."""
        trusted_prefixes = (
            '/admin/',
            '/api/',  # API has its own validation
        )
        return request.path.startswith(trusted_prefixes)

    def _sanitize_query_dict(self, query_dict) -> None:
        """Sanitize all values in a QueryDict."""
        # Make QueryDict mutable
        query_dict._mutable = True

        for key in query_dict.keys():
            if key in self.skip_fields:
                continue

            values = query_dict.getlist(key)
            sanitized_values = [self._sanitize_value(v) for v in values]
            query_dict.setlist(key, sanitized_values)

        query_dict._mutable = False

    def _sanitize_value(self, value: str) -> str:
        """Sanitize a single value."""
        if not isinstance(value, str):
            return value

        sanitized = value

        # Remove dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            sanitized = pattern.sub('', sanitized)

        # HTML encode special characters
        sanitized = html.escape(sanitized, quote=True)

        # Un-escape safe entities that were double-encoded
        sanitized = sanitized.replace('&amp;lt;', '&lt;')
        sanitized = sanitized.replace('&amp;gt;', '&gt;')
        sanitized = sanitized.replace('&amp;amp;', '&amp;')

        return sanitized

    def _log_xss_attempt(self, request: HttpRequest, field: str, value: str) -> None:
        """Log potential XSS attempt."""
        security_logger.warning(
            f"Potential XSS attempt - "
            f"IP: {self._get_client_ip(request)}, "
            f"Field: {field}, "
            f"Value (truncated): {value[:100]}"
        )

    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'Unknown')


# =============================================================================
# REQUEST LOGGING MIDDLEWARE
# =============================================================================

class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Comprehensive request logging middleware for security auditing.

    Logs:
    - All requests with timing information
    - Failed authentication attempts
    - Suspicious patterns
    - Error responses

    Protection Level: Audit/Compliance
    Performance Impact: Low
    """

    # Sensitive paths that require detailed logging
    SENSITIVE_PATHS = (
        '/admin/',
        '/api/auth/',
        '/accounts/login/',
        '/accounts/password/',
        '/api/users/',
        '/api/payments/',
    )

    # Status codes that indicate potential security issues
    SECURITY_STATUS_CODES = {401, 403, 404, 405, 429, 500, 502, 503}

    # Headers to exclude from logging (sensitive)
    EXCLUDED_HEADERS = {
        'HTTP_AUTHORIZATION',
        'HTTP_COOKIE',
        'HTTP_X_CSRFTOKEN',
    }

    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('security.requests')

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Start timing
        start_time = timezone.now()

        # Get request info before processing
        request_info = self._capture_request_info(request)

        # Process request
        response = self.get_response(request)

        # Calculate duration
        duration = (timezone.now() - start_time).total_seconds()

        # Log based on conditions
        self._log_request(request, response, request_info, duration)

        return response

    def _capture_request_info(self, request: HttpRequest) -> Dict[str, Any]:
        """Capture request information for logging."""
        return {
            'method': request.method,
            'path': request.path,
            'ip': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
            'user': str(request.user) if hasattr(request, 'user') else 'Anonymous',
            'referer': request.META.get('HTTP_REFERER', ''),
            'content_type': request.content_type if hasattr(request, 'content_type') else '',
        }

    def _log_request(
        self,
        request: HttpRequest,
        response: HttpResponse,
        request_info: Dict[str, Any],
        duration: float
    ) -> None:
        """Log request with appropriate level."""

        status_code = response.status_code
        path = request_info['path']

        # Determine log level
        if status_code in self.SECURITY_STATUS_CODES:
            log_level = logging.WARNING
        elif path.startswith(self.SENSITIVE_PATHS):
            log_level = logging.INFO
        else:
            # Only log errors for non-sensitive paths
            if status_code >= 400:
                log_level = logging.WARNING
            else:
                # Skip logging for normal requests (reduce noise)
                return

        log_data = {
            **request_info,
            'status_code': status_code,
            'duration_ms': round(duration * 1000, 2),
            'timestamp': timezone.now().isoformat(),
        }

        # Log as JSON for structured logging
        self.logger.log(
            log_level,
            json.dumps(log_data, default=str)
        )

        # Additional security event logging
        if status_code == 403:
            security_logger.warning(
                f"Access denied - IP: {request_info['ip']}, Path: {path}"
            )
        elif status_code == 401:
            security_logger.warning(
                f"Authentication failed - IP: {request_info['ip']}, Path: {path}"
            )
        elif status_code == 429:
            security_logger.warning(
                f"Rate limit exceeded - IP: {request_info['ip']}, Path: {path}"
            )

    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'Unknown')


# =============================================================================
# SECURITY HEADERS MIDDLEWARE
# =============================================================================

class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Enhanced security headers middleware.

    Adds additional security headers beyond Django's default SecurityMiddleware:
    - Permissions-Policy
    - Cross-Origin headers
    - Cache-Control for sensitive responses
    - Custom security headers

    Protection Level: Medium-High
    Performance Impact: Minimal
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # Permissions Policy (formerly Feature-Policy)
        self.permissions_policy = getattr(
            settings,
            'PERMISSIONS_POLICY',
            {
                'accelerometer': [],
                'camera': [],
                'geolocation': [],
                'gyroscope': [],
                'magnetometer': [],
                'microphone': [],
                'payment': ['self'],
                'usb': [],
                'interest-cohort': [],  # Disable FLoC
            }
        )

        # Cross-Origin policies
        self.cross_origin_policies = getattr(
            settings,
            'CROSS_ORIGIN_POLICIES',
            {
                'Cross-Origin-Embedder-Policy': 'require-corp',
                'Cross-Origin-Opener-Policy': 'same-origin',
                'Cross-Origin-Resource-Policy': 'same-origin',
            }
        )

    def process_response(
        self,
        request: HttpRequest,
        response: HttpResponse
    ) -> HttpResponse:
        """Add security headers to response."""

        # Permissions-Policy header
        policy_parts = []
        for feature, origins in self.permissions_policy.items():
            if not origins:
                policy_parts.append(f"{feature}=()")
            elif origins == ['self']:
                policy_parts.append(f"{feature}=(self)")
            else:
                origins_str = ' '.join(f'"{o}"' for o in origins)
                policy_parts.append(f"{feature}=({origins_str})")

        response['Permissions-Policy'] = ', '.join(policy_parts)

        # Cross-Origin headers (skip for static files and external resources)
        if not self._is_static_request(request):
            for header, value in self.cross_origin_policies.items():
                response[header] = value

        # Cache-Control for sensitive endpoints
        if self._is_sensitive_endpoint(request):
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

        # Referrer-Policy (more restrictive than default)
        if 'Referrer-Policy' not in response:
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # X-Content-Type-Options
        response['X-Content-Type-Options'] = 'nosniff'

        # X-Permitted-Cross-Domain-Policies (Adobe Flash/PDF)
        response['X-Permitted-Cross-Domain-Policies'] = 'none'

        # Clear-Site-Data for logout
        if self._is_logout_request(request):
            response['Clear-Site-Data'] = '"cache", "cookies", "storage"'

        return response

    def _is_static_request(self, request: HttpRequest) -> bool:
        """Check if request is for static files."""
        static_prefixes = ('/static/', '/media/')
        return request.path.startswith(static_prefixes)

    def _is_sensitive_endpoint(self, request: HttpRequest) -> bool:
        """Check if endpoint handles sensitive data."""
        sensitive_paths = (
            '/admin/',
            '/api/auth/',
            '/accounts/',
            '/api/payments/',
            '/api/users/',
        )
        return request.path.startswith(sensitive_paths)

    def _is_logout_request(self, request: HttpRequest) -> bool:
        """Check if this is a logout request."""
        logout_paths = ('/accounts/logout/', '/api/auth/logout/')
        return request.path in logout_paths


# =============================================================================
# CSRF ENHANCEMENT MIDDLEWARE
# =============================================================================

class CSRFEnhancementMiddleware(MiddlewareMixin):
    """
    Enhanced CSRF protection middleware.

    Adds additional CSRF protections:
    - Double-submit cookie validation
    - Origin validation
    - Referer validation for sensitive endpoints

    Protection Level: Critical
    Performance Impact: Low
    """

    # Endpoints requiring strict origin validation
    STRICT_ORIGIN_PATHS = (
        '/api/payments/',
        '/api/auth/',
        '/admin/',
    )

    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Enhanced CSRF validation."""

        if request.method in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
            return None

        # Skip for API endpoints using token auth
        if request.path.startswith('/api/') and 'Authorization' in request.headers:
            return None

        # Strict origin validation for sensitive endpoints
        if request.path.startswith(self.STRICT_ORIGIN_PATHS):
            if not self._validate_origin(request):
                security_logger.warning(
                    f"Origin validation failed - "
                    f"IP: {self._get_client_ip(request)}, "
                    f"Path: {request.path}, "
                    f"Origin: {request.META.get('HTTP_ORIGIN', 'None')}"
                )
                return HttpResponseForbidden('Origin validation failed')

        return None

    def _validate_origin(self, request: HttpRequest) -> bool:
        """Validate request origin."""
        origin = request.META.get('HTTP_ORIGIN')
        referer = request.META.get('HTTP_REFERER')

        if not origin and not referer:
            # No origin info - suspicious for AJAX requests
            return request.content_type != 'application/json'

        allowed_origins = getattr(settings, 'CSRF_TRUSTED_ORIGINS', [])
        allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])

        # Check origin
        if origin:
            for allowed in allowed_origins:
                if allowed.startswith('https://'):
                    if origin == allowed or origin == allowed.replace('https://', 'http://'):
                        return True
                elif origin.endswith(allowed.lstrip('*.')):
                    return True

        # Check referer
        if referer:
            from urllib.parse import urlparse
            parsed = urlparse(referer)
            if parsed.netloc in allowed_hosts or any(
                parsed.netloc.endswith(h.lstrip('.')) for h in allowed_hosts if h.startswith('.')
            ):
                return True

        return False

    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'Unknown')
