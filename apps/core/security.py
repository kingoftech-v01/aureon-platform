"""
Security Utilities for Aureon SaaS Platform
===========================================

Comprehensive security utilities:
1. Rate limiting decorators
2. IP blocking utilities
3. Failed login tracking
4. Brute force protection
5. Security monitoring

Author: Rhematek Solutions
Version: 2.0.0
"""

import functools
import hashlib
import logging
import time
from datetime import timedelta
from typing import Callable, Optional, Set, Dict, Any, List, Tuple

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import timezone
from django.contrib.auth import get_user_model


# Configure logger
security_logger = logging.getLogger('security')


# =============================================================================
# RATE LIMITING
# =============================================================================

class RateLimiter:
    """
    Token bucket rate limiter with Redis/cache backend.

    Supports:
    - Per-user rate limiting
    - Per-IP rate limiting
    - Per-endpoint rate limiting
    - Sliding window algorithm
    """

    def __init__(
        self,
        key_prefix: str = 'ratelimit',
        rate: int = 100,
        period: int = 3600,
        block_duration: int = 300,
    ):
        """
        Initialize rate limiter.

        Args:
            key_prefix: Cache key prefix
            rate: Maximum requests per period
            period: Time period in seconds
            block_duration: Block duration when limit exceeded (seconds)
        """
        self.key_prefix = key_prefix
        self.rate = rate
        self.period = period
        self.block_duration = block_duration

    def _get_cache_key(self, identifier: str) -> str:
        """Generate cache key for identifier."""
        return f"{self.key_prefix}:{identifier}"

    def _get_block_key(self, identifier: str) -> str:
        """Generate block cache key for identifier."""
        return f"{self.key_prefix}:blocked:{identifier}"

    def is_blocked(self, identifier: str) -> bool:
        """Check if identifier is currently blocked."""
        return cache.get(self._get_block_key(identifier)) is not None

    def block(self, identifier: str, duration: Optional[int] = None) -> None:
        """Block identifier for specified duration."""
        duration = duration or self.block_duration
        cache.set(
            self._get_block_key(identifier),
            {'blocked_at': timezone.now().isoformat(), 'duration': duration},
            timeout=duration
        )
        security_logger.warning(
            f"Rate limit block applied - Identifier: {identifier}, Duration: {duration}s"
        )

    def unblock(self, identifier: str) -> None:
        """Manually unblock identifier."""
        cache.delete(self._get_block_key(identifier))

    def check_rate_limit(self, identifier: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request should be rate limited.

        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        # Check if blocked
        if self.is_blocked(identifier):
            return False, {
                'allowed': False,
                'remaining': 0,
                'reset_at': None,
                'blocked': True,
            }

        cache_key = self._get_cache_key(identifier)
        current_time = time.time()
        window_start = current_time - self.period

        # Get current window data
        window_data = cache.get(cache_key, [])

        # Filter out old entries
        window_data = [ts for ts in window_data if ts > window_start]

        # Check limit
        current_count = len(window_data)

        if current_count >= self.rate:
            # Rate limit exceeded - apply block
            self.block(identifier)
            return False, {
                'allowed': False,
                'remaining': 0,
                'reset_at': window_data[0] + self.period if window_data else current_time + self.period,
                'blocked': True,
            }

        # Add current request
        window_data.append(current_time)
        cache.set(cache_key, window_data, timeout=self.period)

        return True, {
            'allowed': True,
            'remaining': self.rate - len(window_data),
            'reset_at': window_data[0] + self.period if window_data else current_time + self.period,
            'blocked': False,
        }


def rate_limit(
    rate: int = 100,
    period: int = 3600,
    key_func: Optional[Callable] = None,
    block_duration: int = 300,
):
    """
    Rate limiting decorator for views.

    Args:
        rate: Maximum requests per period
        period: Time period in seconds
        key_func: Function to extract rate limit key from request
        block_duration: Block duration when exceeded

    Usage:
        @rate_limit(rate=10, period=60)  # 10 requests per minute
        def my_view(request):
            ...
    """
    def decorator(view_func: Callable) -> Callable:
        limiter = RateLimiter(
            key_prefix=f'ratelimit:{view_func.__module__}.{view_func.__name__}',
            rate=rate,
            period=period,
            block_duration=block_duration,
        )

        @functools.wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            # Get rate limit key
            if key_func:
                identifier = key_func(request)
            else:
                identifier = get_client_ip(request)

            # Check rate limit
            allowed, info = limiter.check_rate_limit(identifier)

            if not allowed:
                response = JsonResponse(
                    {
                        'error': 'Rate limit exceeded',
                        'retry_after': int(info['reset_at'] - time.time()) if info['reset_at'] else block_duration,
                    },
                    status=429
                )
                response['Retry-After'] = str(int(info['reset_at'] - time.time()) if info['reset_at'] else block_duration)
                response['X-RateLimit-Limit'] = str(rate)
                response['X-RateLimit-Remaining'] = '0'
                return response

            # Process request
            response = view_func(request, *args, **kwargs)

            # Add rate limit headers
            response['X-RateLimit-Limit'] = str(rate)
            response['X-RateLimit-Remaining'] = str(info['remaining'])
            response['X-RateLimit-Reset'] = str(int(info['reset_at']))

            return response

        return wrapper
    return decorator


def rate_limit_by_user(rate: int = 100, period: int = 3600, block_duration: int = 300):
    """Rate limit by authenticated user."""
    def key_func(request: HttpRequest) -> str:
        if request.user.is_authenticated:
            return f"user:{request.user.id}"
        return f"ip:{get_client_ip(request)}"

    return rate_limit(rate=rate, period=period, key_func=key_func, block_duration=block_duration)


def rate_limit_by_ip(rate: int = 100, period: int = 3600, block_duration: int = 300):
    """Rate limit by IP address."""
    return rate_limit(rate=rate, period=period, key_func=lambda r: get_client_ip(r), block_duration=block_duration)


# =============================================================================
# IP BLOCKING
# =============================================================================

class IPBlocker:
    """
    IP blocking utility with persistence.

    Features:
    - Manual IP blocking
    - Automatic blocking based on patterns
    - Whitelist support
    - Block expiration
    """

    BLOCK_CACHE_PREFIX = 'ip_block'
    WHITELIST_CACHE_KEY = 'ip_whitelist'

    def __init__(self):
        self.whitelist = self._load_whitelist()

    def _load_whitelist(self) -> Set[str]:
        """Load IP whitelist from settings/cache."""
        whitelist = set(getattr(settings, 'IP_WHITELIST', []))

        # Always whitelist localhost
        whitelist.add('127.0.0.1')
        whitelist.add('::1')

        cached_whitelist = cache.get(self.WHITELIST_CACHE_KEY, set())
        return whitelist.union(cached_whitelist)

    def _get_block_key(self, ip: str) -> str:
        """Get cache key for IP block."""
        return f"{self.BLOCK_CACHE_PREFIX}:{ip}"

    def is_blocked(self, ip: str) -> bool:
        """Check if IP is blocked."""
        if ip in self.whitelist:
            return False
        return cache.get(self._get_block_key(ip)) is not None

    def block_ip(
        self,
        ip: str,
        reason: str = 'Manual block',
        duration: int = 86400,  # 24 hours
    ) -> bool:
        """
        Block an IP address.

        Args:
            ip: IP address to block
            reason: Reason for blocking
            duration: Block duration in seconds

        Returns:
            True if blocked, False if whitelisted
        """
        if ip in self.whitelist:
            security_logger.warning(f"Cannot block whitelisted IP: {ip}")
            return False

        block_data = {
            'blocked_at': timezone.now().isoformat(),
            'reason': reason,
            'duration': duration,
        }

        cache.set(self._get_block_key(ip), block_data, timeout=duration)

        security_logger.warning(
            f"IP blocked - IP: {ip}, Reason: {reason}, Duration: {duration}s"
        )

        return True

    def unblock_ip(self, ip: str) -> None:
        """Unblock an IP address."""
        cache.delete(self._get_block_key(ip))
        security_logger.info(f"IP unblocked - IP: {ip}")

    def add_to_whitelist(self, ip: str) -> None:
        """Add IP to whitelist."""
        self.whitelist.add(ip)
        cache.set(self.WHITELIST_CACHE_KEY, self.whitelist, timeout=None)
        # Unblock if currently blocked
        self.unblock_ip(ip)

    def remove_from_whitelist(self, ip: str) -> None:
        """Remove IP from whitelist."""
        self.whitelist.discard(ip)
        cache.set(self.WHITELIST_CACHE_KEY, self.whitelist, timeout=None)

    def get_block_info(self, ip: str) -> Optional[Dict[str, Any]]:
        """Get blocking information for an IP."""
        return cache.get(self._get_block_key(ip))


# Global IP blocker instance
ip_blocker = IPBlocker()


def block_ip(ip: str, reason: str = 'Manual block', duration: int = 86400) -> bool:
    """Convenience function to block an IP."""
    return ip_blocker.block_ip(ip, reason, duration)


def unblock_ip(ip: str) -> None:
    """Convenience function to unblock an IP."""
    ip_blocker.unblock_ip(ip)


def is_ip_blocked(ip: str) -> bool:
    """Convenience function to check if IP is blocked."""
    return ip_blocker.is_blocked(ip)


# =============================================================================
# FAILED LOGIN TRACKING
# =============================================================================

class LoginTracker:
    """
    Track failed login attempts and implement account lockout.

    Features:
    - Track failed attempts by IP and username
    - Progressive lockout (increasing lockout times)
    - Account lockout notification
    - Suspicious activity detection
    """

    CACHE_PREFIX = 'login_tracker'
    MAX_ATTEMPTS = 5
    LOCKOUT_TIMES = [60, 300, 900, 3600, 86400]  # Progressive: 1min, 5min, 15min, 1hr, 24hr

    def __init__(self):
        self.max_attempts = getattr(settings, 'LOGIN_MAX_ATTEMPTS', self.MAX_ATTEMPTS)
        self.lockout_times = getattr(settings, 'LOGIN_LOCKOUT_TIMES', self.LOCKOUT_TIMES)

    def _get_attempt_key(self, identifier: str) -> str:
        """Get cache key for login attempts."""
        return f"{self.CACHE_PREFIX}:attempts:{identifier}"

    def _get_lockout_key(self, identifier: str) -> str:
        """Get cache key for lockout."""
        return f"{self.CACHE_PREFIX}:lockout:{identifier}"

    def _get_lockout_count_key(self, identifier: str) -> str:
        """Get cache key for lockout count (for progressive lockout)."""
        return f"{self.CACHE_PREFIX}:lockout_count:{identifier}"

    def record_failed_attempt(self, ip: str, username: Optional[str] = None) -> Dict[str, Any]:
        """
        Record a failed login attempt.

        Returns:
            Dict with lockout status and remaining attempts
        """
        # Track by IP
        ip_key = self._get_attempt_key(f"ip:{ip}")
        ip_attempts = cache.get(ip_key, 0) + 1
        cache.set(ip_key, ip_attempts, timeout=3600)  # 1 hour window

        # Track by username if provided
        if username:
            user_key = self._get_attempt_key(f"user:{username}")
            user_attempts = cache.get(user_key, 0) + 1
            cache.set(user_key, user_attempts, timeout=3600)
        else:
            user_attempts = 0

        # Check if lockout needed
        max_attempts_reached = ip_attempts >= self.max_attempts or user_attempts >= self.max_attempts

        result = {
            'ip_attempts': ip_attempts,
            'user_attempts': user_attempts,
            'remaining_attempts': max(0, self.max_attempts - max(ip_attempts, user_attempts)),
            'locked_out': False,
            'lockout_duration': 0,
        }

        if max_attempts_reached:
            # Determine lockout identifier (use username if available)
            lockout_id = f"user:{username}" if username else f"ip:{ip}"

            # Get current lockout count for progressive lockout
            lockout_count_key = self._get_lockout_count_key(lockout_id)
            lockout_count = cache.get(lockout_count_key, 0)

            # Calculate lockout duration
            duration_index = min(lockout_count, len(self.lockout_times) - 1)
            lockout_duration = self.lockout_times[duration_index]

            # Apply lockout
            cache.set(
                self._get_lockout_key(lockout_id),
                {
                    'locked_at': timezone.now().isoformat(),
                    'duration': lockout_duration,
                    'ip': ip,
                    'username': username,
                },
                timeout=lockout_duration
            )

            # Increment lockout count (persists longer for progressive lockout)
            cache.set(lockout_count_key, lockout_count + 1, timeout=86400)  # 24 hours

            result['locked_out'] = True
            result['lockout_duration'] = lockout_duration

            security_logger.warning(
                f"Account locked - IP: {ip}, Username: {username}, "
                f"Duration: {lockout_duration}s, Lockout #{lockout_count + 1}"
            )

            # Also block IP if too many attempts
            if ip_attempts >= self.max_attempts * 2:
                ip_blocker.block_ip(ip, reason="Excessive login attempts", duration=lockout_duration * 2)

        return result

    def record_successful_login(self, ip: str, username: str) -> None:
        """Record successful login, clearing failed attempts."""
        # Clear IP attempts
        cache.delete(self._get_attempt_key(f"ip:{ip}"))

        # Clear user attempts
        cache.delete(self._get_attempt_key(f"user:{username}"))

        # Note: Don't clear lockout count - keeps progressive lockout history
        security_logger.info(f"Successful login - IP: {ip}, Username: {username}")

    def is_locked_out(self, ip: str, username: Optional[str] = None) -> Tuple[bool, Optional[int]]:
        """
        Check if IP or username is locked out.

        Returns:
            Tuple of (is_locked, remaining_seconds)
        """
        # Check username lockout
        if username:
            lockout_data = cache.get(self._get_lockout_key(f"user:{username}"))
            if lockout_data:
                return True, lockout_data.get('duration', 0)

        # Check IP lockout
        lockout_data = cache.get(self._get_lockout_key(f"ip:{ip}"))
        if lockout_data:
            return True, lockout_data.get('duration', 0)

        return False, None

    def get_remaining_attempts(self, ip: str, username: Optional[str] = None) -> int:
        """Get remaining login attempts."""
        ip_attempts = cache.get(self._get_attempt_key(f"ip:{ip}"), 0)
        user_attempts = cache.get(self._get_attempt_key(f"user:{username}"), 0) if username else 0

        return max(0, self.max_attempts - max(ip_attempts, user_attempts))

    def clear_lockout(self, identifier: str) -> None:
        """Manually clear lockout for identifier."""
        cache.delete(self._get_lockout_key(f"user:{identifier}"))
        cache.delete(self._get_lockout_key(f"ip:{identifier}"))
        cache.delete(self._get_attempt_key(f"user:{identifier}"))
        cache.delete(self._get_attempt_key(f"ip:{identifier}"))


# Global login tracker instance
login_tracker = LoginTracker()


# =============================================================================
# BRUTE FORCE PROTECTION
# =============================================================================

class BruteForceProtector:
    """
    Comprehensive brute force protection.

    Protects against:
    - Login brute force
    - Password reset abuse
    - API key guessing
    - Form submission spam
    """

    def __init__(self):
        self.login_tracker = login_tracker
        self.rate_limiters: Dict[str, RateLimiter] = {}

    def get_rate_limiter(
        self,
        name: str,
        rate: int = 10,
        period: int = 60,
        block_duration: int = 300,
    ) -> RateLimiter:
        """Get or create rate limiter for specific action."""
        if name not in self.rate_limiters:
            self.rate_limiters[name] = RateLimiter(
                key_prefix=f"bruteforce:{name}",
                rate=rate,
                period=period,
                block_duration=block_duration,
            )
        return self.rate_limiters[name]

    def check_login(self, request: HttpRequest, username: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if login attempt should be allowed.

        Returns:
            Tuple of (allowed, info_dict)
        """
        ip = get_client_ip(request)

        # Check IP block
        if ip_blocker.is_blocked(ip):
            return False, {'reason': 'ip_blocked', 'message': 'Access temporarily blocked'}

        # Check lockout
        locked_out, duration = self.login_tracker.is_locked_out(ip, username)
        if locked_out:
            return False, {
                'reason': 'locked_out',
                'message': f'Account temporarily locked. Try again in {duration} seconds.',
                'duration': duration,
            }

        remaining = self.login_tracker.get_remaining_attempts(ip, username)
        return True, {'remaining_attempts': remaining}

    def record_login_failure(self, request: HttpRequest, username: str) -> Dict[str, Any]:
        """Record failed login attempt."""
        ip = get_client_ip(request)
        return self.login_tracker.record_failed_attempt(ip, username)

    def record_login_success(self, request: HttpRequest, username: str) -> None:
        """Record successful login."""
        ip = get_client_ip(request)
        self.login_tracker.record_successful_login(ip, username)

    def check_password_reset(self, request: HttpRequest, email: str) -> Tuple[bool, str]:
        """
        Check if password reset request should be allowed.

        Returns:
            Tuple of (allowed, message)
        """
        ip = get_client_ip(request)
        limiter = self.get_rate_limiter('password_reset', rate=3, period=3600)

        # Check by IP
        allowed_ip, _ = limiter.check_rate_limit(ip)
        if not allowed_ip:
            return False, 'Too many password reset requests. Please try again later.'

        # Check by email
        email_hash = hashlib.sha256(email.lower().encode()).hexdigest()[:16]
        allowed_email, _ = limiter.check_rate_limit(f"email:{email_hash}")
        if not allowed_email:
            return False, 'Too many password reset requests for this email.'

        return True, ''

    def check_api_key_guess(self, request: HttpRequest) -> Tuple[bool, str]:
        """
        Check for API key guessing attempts.

        Returns:
            Tuple of (allowed, message)
        """
        ip = get_client_ip(request)
        limiter = self.get_rate_limiter('api_key', rate=5, period=60, block_duration=3600)

        allowed, _ = limiter.check_rate_limit(ip)
        if not allowed:
            # Block IP for extended period
            ip_blocker.block_ip(ip, reason="API key brute force attempt", duration=7200)
            return False, 'Suspicious activity detected. Access blocked.'

        return True, ''

    def check_form_submission(
        self,
        request: HttpRequest,
        form_name: str,
        rate: int = 10,
        period: int = 60,
    ) -> Tuple[bool, str]:
        """
        Check form submission rate limit.

        Returns:
            Tuple of (allowed, message)
        """
        ip = get_client_ip(request)
        limiter = self.get_rate_limiter(f"form:{form_name}", rate=rate, period=period)

        allowed, _ = limiter.check_rate_limit(ip)
        if not allowed:
            return False, 'Too many submissions. Please wait before trying again.'

        return True, ''


# Global brute force protector instance
brute_force_protector = BruteForceProtector()


# =============================================================================
# SECURITY MONITORING
# =============================================================================

class SecurityMonitor:
    """
    Security monitoring and alerting.

    Features:
    - Suspicious activity detection
    - Security event aggregation
    - Alert threshold management
    """

    CACHE_PREFIX = 'security_monitor'

    # Alert thresholds
    THRESHOLDS = {
        'failed_logins_per_hour': 100,
        'blocked_ips_per_hour': 50,
        'rate_limits_per_hour': 200,
        'suspicious_requests_per_hour': 100,
    }

    def __init__(self):
        self.thresholds = getattr(settings, 'SECURITY_THRESHOLDS', self.THRESHOLDS)

    def _get_counter_key(self, event_type: str) -> str:
        """Get cache key for event counter."""
        hour = timezone.now().strftime('%Y%m%d%H')
        return f"{self.CACHE_PREFIX}:counter:{event_type}:{hour}"

    def record_event(self, event_type: str, details: Optional[Dict] = None) -> None:
        """
        Record a security event.

        Args:
            event_type: Type of security event
            details: Additional event details
        """
        # Increment counter
        counter_key = self._get_counter_key(event_type)
        current_count = cache.get(counter_key, 0) + 1
        cache.set(counter_key, current_count, timeout=3600)

        # Check threshold
        threshold = self.thresholds.get(f"{event_type}_per_hour")
        if threshold and current_count >= threshold:
            self._trigger_alert(event_type, current_count, threshold, details)

        # Log event
        security_logger.info(
            f"Security event - Type: {event_type}, Count: {current_count}, "
            f"Details: {details}"
        )

    def _trigger_alert(
        self,
        event_type: str,
        count: int,
        threshold: int,
        details: Optional[Dict],
    ) -> None:
        """Trigger security alert."""
        alert_key = f"{self.CACHE_PREFIX}:alert:{event_type}:{timezone.now().strftime('%Y%m%d%H')}"

        # Only alert once per hour per event type
        if cache.get(alert_key):
            return

        cache.set(alert_key, True, timeout=3600)

        security_logger.critical(
            f"SECURITY ALERT - {event_type} threshold exceeded! "
            f"Count: {count}, Threshold: {threshold}, Details: {details}"
        )

        # Send alert notification (hook for email/Slack/PagerDuty)
        self._send_alert_notification(event_type, count, threshold, details)

    def _send_alert_notification(
        self,
        event_type: str,
        count: int,
        threshold: int,
        details: Optional[Dict],
    ) -> None:
        """Send alert notification via email to admins."""
        try:
            from django.core.mail import mail_admins
            subject = f"Security Alert: {event_type} threshold exceeded"
            message = (
                f"Security alert triggered:\n\n"
                f"Event Type: {event_type}\n"
                f"Count: {count}\n"
                f"Threshold: {threshold}\n"
                f"Details: {details}\n\n"
                f"Please investigate immediately."
            )
            mail_admins(subject, message, fail_silently=False)
            security_logger.info(f"Security alert sent to admins: {event_type}")
        except Exception as e:
            security_logger.critical(
                f"FAILED to send security alert for {event_type}: {e}. "
                f"Count={count}, threshold={threshold}. Manual investigation required."
            )

    def get_hourly_stats(self) -> Dict[str, int]:
        """Get current hour's security statistics."""
        hour = timezone.now().strftime('%Y%m%d%H')
        stats = {}

        for event_type in ['failed_logins', 'blocked_ips', 'rate_limits', 'suspicious_requests']:
            key = f"{self.CACHE_PREFIX}:counter:{event_type}:{hour}"
            stats[event_type] = cache.get(key, 0)

        return stats


# Global security monitor instance
security_monitor = SecurityMonitor()


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_client_ip(request: HttpRequest) -> str:
    """
    Get client IP address from request.

    Handles:
    - X-Forwarded-For header (behind proxy)
    - X-Real-IP header
    - REMOTE_ADDR fallback
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Take first IP from comma-separated list
        return x_forwarded_for.split(',')[0].strip()

    x_real_ip = request.META.get('HTTP_X_REAL_IP')
    if x_real_ip:
        return x_real_ip.strip()

    return request.META.get('REMOTE_ADDR', 'Unknown')


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    import secrets
    return secrets.token_urlsafe(length)


def hash_sensitive_data(data: str, salt: Optional[str] = None) -> str:
    """Hash sensitive data for logging/storage."""
    if salt is None:
        salt = getattr(settings, 'SECRET_KEY', '')[:16]

    return hashlib.sha256(f"{salt}{data}".encode()).hexdigest()


def mask_email(email: str) -> str:
    """Mask email for logging (e.g., j***@example.com)."""
    if '@' not in email:
        return '***'

    local, domain = email.split('@')
    if len(local) <= 1:
        masked_local = '*'
    else:
        masked_local = local[0] + '*' * (len(local) - 1)

    return f"{masked_local}@{domain}"


def mask_ip(ip: str) -> str:
    """Mask IP for logging (e.g., 192.168.*.*)."""
    parts = ip.split('.')
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.*.*"
    return '***'


# =============================================================================
# DECORATORS FOR VIEW PROTECTION
# =============================================================================

def require_secure_request(view_func: Callable) -> Callable:
    """
    Decorator to require secure (HTTPS) requests.
    """
    @functools.wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not request.is_secure() and not settings.DEBUG:
            return HttpResponse('HTTPS required', status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


def check_ip_block(view_func: Callable) -> Callable:
    """
    Decorator to check IP block before processing request.
    """
    @functools.wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        ip = get_client_ip(request)
        if ip_blocker.is_blocked(ip):
            return HttpResponse('Access denied', status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


def log_security_event(event_type: str):
    """
    Decorator to log security events for views.
    """
    def decorator(view_func: Callable) -> Callable:
        @functools.wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            ip = get_client_ip(request)
            security_monitor.record_event(
                event_type,
                {
                    'ip': mask_ip(ip),
                    'path': request.path,
                    'user': str(request.user) if hasattr(request, 'user') else 'Anonymous',
                }
            )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
