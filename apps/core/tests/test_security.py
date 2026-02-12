"""
Tests for core security module.

Tests cover:
- RateLimiter: token bucket rate limiting
- rate_limit / rate_limit_by_user / rate_limit_by_ip decorators
- IPBlocker: IP blocking with whitelist support
- Convenience functions: block_ip, unblock_ip, is_ip_blocked
- LoginTracker: failed login tracking and progressive lockout
- BruteForceProtector: comprehensive brute force protection
- SecurityMonitor: alert sending, alert deduplication, and hourly stats
- Utility functions: get_client_ip, generate_secure_token, hash_sensitive_data, mask_email, mask_ip
- View decorators: require_secure_request, check_ip_block, log_security_event
"""
import time

import pytest
from unittest.mock import patch, MagicMock, call

from django.http import HttpResponse, JsonResponse
from django.test import RequestFactory
from django.utils import timezone


# Override CACHES to use in-memory cache before importing security module.
# security.py creates global IPBlocker() at import time which calls cache.get(),
# so the cache backend must be available before the import.
from django.conf import settings as _django_settings
_django_settings.CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
# Reset cached cache connections so new CACHES setting takes effect
from django.core.cache import caches as _caches
try:
    _caches._connections.caches = {}
except AttributeError:
    pass

from django.core.cache import cache
from apps.core.security import (
    RateLimiter,
    rate_limit,
    rate_limit_by_user,
    rate_limit_by_ip,
    IPBlocker,
    block_ip,
    unblock_ip,
    is_ip_blocked,
    ip_blocker,
    LoginTracker,
    login_tracker,
    BruteForceProtector,
    brute_force_protector,
    SecurityMonitor,
    security_monitor,
    get_client_ip,
    generate_secure_token,
    hash_sensitive_data,
    mask_email,
    mask_ip,
    require_secure_request,
    check_ip_block,
    log_security_event,
)


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before each test."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def rf():
    """RequestFactory fixture."""
    return RequestFactory()


# =============================================================================
# RateLimiter Tests
# =============================================================================


class TestRateLimiterInit:
    """Tests for RateLimiter.__init__."""

    def test_default_values(self):
        limiter = RateLimiter()
        assert limiter.key_prefix == 'ratelimit'
        assert limiter.rate == 100
        assert limiter.period == 3600
        assert limiter.block_duration == 300

    def test_custom_values(self):
        limiter = RateLimiter(
            key_prefix='custom',
            rate=10,
            period=60,
            block_duration=120,
        )
        assert limiter.key_prefix == 'custom'
        assert limiter.rate == 10
        assert limiter.period == 60
        assert limiter.block_duration == 120


class TestRateLimiterCacheKeys:
    """Tests for RateLimiter cache key generation."""

    def test_get_cache_key(self):
        limiter = RateLimiter(key_prefix='test')
        assert limiter._get_cache_key('user123') == 'test:user123'

    def test_get_block_key(self):
        limiter = RateLimiter(key_prefix='test')
        assert limiter._get_block_key('user123') == 'test:blocked:user123'


class TestRateLimiterIsBlocked:
    """Tests for RateLimiter.is_blocked."""

    def test_not_blocked_when_no_block_exists(self):
        limiter = RateLimiter()
        assert limiter.is_blocked('user1') is False

    def test_blocked_when_block_exists(self):
        limiter = RateLimiter(key_prefix='blk_test')
        cache.set('blk_test:blocked:user1', {'blocked_at': 'now'}, timeout=60)
        assert limiter.is_blocked('user1') is True


class TestRateLimiterBlock:
    """Tests for RateLimiter.block."""

    def test_block_with_default_duration(self):
        limiter = RateLimiter(key_prefix='blk', block_duration=120)
        limiter.block('ident1')
        data = cache.get('blk:blocked:ident1')
        assert data is not None
        assert data['duration'] == 120
        assert 'blocked_at' in data

    def test_block_with_custom_duration(self):
        limiter = RateLimiter(key_prefix='blk', block_duration=120)
        limiter.block('ident2', duration=600)
        data = cache.get('blk:blocked:ident2')
        assert data is not None
        assert data['duration'] == 600


class TestRateLimiterUnblock:
    """Tests for RateLimiter.unblock."""

    def test_unblock_removes_block(self):
        limiter = RateLimiter(key_prefix='ub')
        limiter.block('ident1')
        assert limiter.is_blocked('ident1') is True
        limiter.unblock('ident1')
        assert limiter.is_blocked('ident1') is False

    def test_unblock_nonexistent_block_does_not_error(self):
        limiter = RateLimiter(key_prefix='ub')
        limiter.unblock('nonexistent')  # Should not raise


class TestRateLimiterCheckRateLimit:
    """Tests for RateLimiter.check_rate_limit."""

    def test_allowed_when_under_limit(self):
        limiter = RateLimiter(key_prefix='crl', rate=5, period=60)
        allowed, info = limiter.check_rate_limit('user1')
        assert allowed is True
        assert info['allowed'] is True
        assert info['remaining'] == 4
        assert info['blocked'] is False
        assert info['reset_at'] is not None

    def test_blocked_identifier_returns_false(self):
        limiter = RateLimiter(key_prefix='crl2', rate=5, period=60)
        limiter.block('user1')
        allowed, info = limiter.check_rate_limit('user1')
        assert allowed is False
        assert info['allowed'] is False
        assert info['remaining'] == 0
        assert info['blocked'] is True

    def test_rate_limit_exceeded_triggers_block(self):
        limiter = RateLimiter(key_prefix='crl3', rate=3, period=60, block_duration=120)
        # Make 3 requests to hit the limit
        for _ in range(3):
            limiter.check_rate_limit('user1')
        # Fourth request should be blocked
        allowed, info = limiter.check_rate_limit('user1')
        assert allowed is False
        assert info['allowed'] is False
        assert info['blocked'] is True
        assert info['remaining'] == 0

    def test_remaining_decreases_with_each_request(self):
        limiter = RateLimiter(key_prefix='crl4', rate=5, period=60)
        _, info1 = limiter.check_rate_limit('user1')
        assert info1['remaining'] == 4
        _, info2 = limiter.check_rate_limit('user1')
        assert info2['remaining'] == 3
        _, info3 = limiter.check_rate_limit('user1')
        assert info3['remaining'] == 2

    def test_different_identifiers_have_separate_limits(self):
        limiter = RateLimiter(key_prefix='crl5', rate=2, period=60)
        limiter.check_rate_limit('user1')
        limiter.check_rate_limit('user1')
        # user1 is at limit
        allowed_u1, _ = limiter.check_rate_limit('user1')
        assert allowed_u1 is False
        # user2 is fine
        allowed_u2, info_u2 = limiter.check_rate_limit('user2')
        assert allowed_u2 is True
        assert info_u2['remaining'] == 1

    def test_reset_at_is_set_when_rate_exceeded(self):
        limiter = RateLimiter(key_prefix='crl6', rate=1, period=60)
        limiter.check_rate_limit('user1')
        allowed, info = limiter.check_rate_limit('user1')
        assert allowed is False
        assert info['reset_at'] is not None

    def test_old_entries_are_filtered(self):
        """Entries outside the window should be filtered out."""
        limiter = RateLimiter(key_prefix='crl7', rate=2, period=60)
        # Manually set old entries in cache
        old_time = time.time() - 120  # 2 minutes ago, outside 60s window
        cache.set('crl7:user1', [old_time], timeout=60)
        # The old entry should be filtered, so this should be allowed
        allowed, info = limiter.check_rate_limit('user1')
        assert allowed is True
        assert info['remaining'] == 1  # only the current request counts


# =============================================================================
# rate_limit Decorator Tests
# =============================================================================


class TestRateLimitDecorator:
    """Tests for the rate_limit decorator."""

    def test_allows_request_within_limit(self, rf):
        @rate_limit(rate=5, period=60)
        def my_view(request):
            return HttpResponse('OK')

        request = rf.get('/')
        request.META['REMOTE_ADDR'] = '10.0.0.1'
        response = my_view(request)
        assert response.status_code == 200
        assert response.content == b'OK'
        assert response['X-RateLimit-Limit'] == '5'
        assert int(response['X-RateLimit-Remaining']) == 4

    def test_blocks_request_when_limit_exceeded(self, rf):
        @rate_limit(rate=2, period=60, block_duration=120)
        def my_view(request):
            return HttpResponse('OK')

        request = rf.get('/')
        request.META['REMOTE_ADDR'] = '10.0.0.50'
        # First two requests OK
        my_view(request)
        my_view(request)
        # Third request should be rate limited
        response = my_view(request)
        assert response.status_code == 429
        assert 'Retry-After' in response
        assert response['X-RateLimit-Limit'] == '2'
        assert response['X-RateLimit-Remaining'] == '0'

    def test_returns_json_error_on_limit(self, rf):
        @rate_limit(rate=1, period=60)
        def my_view(request):
            return HttpResponse('OK')

        request = rf.get('/')
        request.META['REMOTE_ADDR'] = '10.0.0.51'
        my_view(request)
        response = my_view(request)
        assert response.status_code == 429
        import json
        data = json.loads(response.content)
        assert 'error' in data
        assert data['error'] == 'Rate limit exceeded'

    def test_custom_key_func(self, rf):
        def custom_key(request):
            return f"custom:{request.META.get('HTTP_X_API_KEY', 'none')}"

        @rate_limit(rate=2, period=60, key_func=custom_key)
        def my_view(request):
            return HttpResponse('OK')

        request = rf.get('/', HTTP_X_API_KEY='key1')
        request.META['REMOTE_ADDR'] = '10.0.0.52'
        response = my_view(request)
        assert response.status_code == 200

    def test_default_key_func_uses_client_ip(self, rf):
        @rate_limit(rate=2, period=60)
        def my_view(request):
            return HttpResponse('OK')

        request = rf.get('/')
        request.META['REMOTE_ADDR'] = '10.0.0.53'
        response = my_view(request)
        assert response.status_code == 200

    def test_headers_set_on_success(self, rf):
        @rate_limit(rate=10, period=60)
        def my_view(request):
            return HttpResponse('OK')

        request = rf.get('/')
        request.META['REMOTE_ADDR'] = '10.0.0.54'
        response = my_view(request)
        assert 'X-RateLimit-Limit' in response
        assert 'X-RateLimit-Remaining' in response
        assert 'X-RateLimit-Reset' in response

    def test_preserves_function_name(self):
        @rate_limit(rate=10, period=60)
        def my_special_view(request):
            return HttpResponse('OK')

        assert my_special_view.__name__ == 'my_special_view'

    def test_blocked_returns_429_with_reset_at_none(self, rf):
        """Test the branch where info['reset_at'] is None (blocked without reset)."""
        @rate_limit(rate=5, period=60, block_duration=300)
        def my_view(request):
            return HttpResponse('OK')

        request = rf.get('/')
        request.META['REMOTE_ADDR'] = '10.0.0.55'

        # Manually block the identifier to trigger the blocked-at-check path
        # The rate_limit decorator builds a RateLimiter internally, so we
        # block via cache directly using the IP-based identifier
        # First, let the decorator fire once to establish itself, then saturate
        for _ in range(5):
            my_view(request)
        # Now blocked
        response = my_view(request)
        assert response.status_code == 429


class TestRateLimitByUser:
    """Tests for rate_limit_by_user decorator."""

    def test_authenticated_user_key(self, rf):
        @rate_limit_by_user(rate=5, period=60)
        def my_view(request):
            return HttpResponse('OK')

        request = rf.get('/')
        request.META['REMOTE_ADDR'] = '10.0.0.60'
        user = MagicMock()
        user.is_authenticated = True
        user.id = 42
        request.user = user
        response = my_view(request)
        assert response.status_code == 200

    def test_anonymous_user_falls_back_to_ip(self, rf):
        @rate_limit_by_user(rate=5, period=60)
        def my_view(request):
            return HttpResponse('OK')

        request = rf.get('/')
        request.META['REMOTE_ADDR'] = '10.0.0.61'
        user = MagicMock()
        user.is_authenticated = False
        request.user = user
        response = my_view(request)
        assert response.status_code == 200

    def test_rate_limit_by_user_blocks_when_exceeded(self, rf):
        @rate_limit_by_user(rate=2, period=60)
        def my_view(request):
            return HttpResponse('OK')

        request = rf.get('/')
        request.META['REMOTE_ADDR'] = '10.0.0.62'
        user = MagicMock()
        user.is_authenticated = True
        user.id = 99
        request.user = user
        my_view(request)
        my_view(request)
        response = my_view(request)
        assert response.status_code == 429


class TestRateLimitByIP:
    """Tests for rate_limit_by_ip decorator."""

    def test_rate_limits_by_ip(self, rf):
        @rate_limit_by_ip(rate=3, period=60)
        def my_view(request):
            return HttpResponse('OK')

        request = rf.get('/')
        request.META['REMOTE_ADDR'] = '10.0.0.70'
        response = my_view(request)
        assert response.status_code == 200

    def test_different_ips_have_separate_limits(self, rf):
        @rate_limit_by_ip(rate=2, period=60)
        def my_view(request):
            return HttpResponse('OK')

        req1 = rf.get('/')
        req1.META['REMOTE_ADDR'] = '10.0.0.71'
        req2 = rf.get('/')
        req2.META['REMOTE_ADDR'] = '10.0.0.72'

        # Exhaust limit for IP 71
        my_view(req1)
        my_view(req1)
        response1 = my_view(req1)
        assert response1.status_code == 429

        # IP 72 should still be fine
        response2 = my_view(req2)
        assert response2.status_code == 200


# =============================================================================
# IPBlocker Tests
# =============================================================================


class TestIPBlockerInit:
    """Tests for IPBlocker initialization."""

    def test_whitelist_includes_localhost(self):
        blocker = IPBlocker()
        assert '127.0.0.1' in blocker.whitelist
        assert '::1' in blocker.whitelist

    @patch.object(_django_settings, 'IP_WHITELIST', ['10.10.10.10'], create=True)
    def test_whitelist_loads_from_settings(self):
        blocker = IPBlocker()
        assert '10.10.10.10' in blocker.whitelist

    def test_whitelist_loads_from_cache(self):
        cache.set('ip_whitelist', {'192.168.1.100'}, timeout=None)
        blocker = IPBlocker()
        assert '192.168.1.100' in blocker.whitelist


class TestIPBlockerGetBlockKey:
    """Tests for IPBlocker._get_block_key."""

    def test_generates_correct_key(self):
        blocker = IPBlocker()
        assert blocker._get_block_key('10.0.0.1') == 'ip_block:10.0.0.1'


class TestIPBlockerIsBlocked:
    """Tests for IPBlocker.is_blocked."""

    def test_whitelisted_ip_is_never_blocked(self):
        blocker = IPBlocker()
        # Manually set a block for localhost
        cache.set('ip_block:127.0.0.1', {'blocked': True}, timeout=60)
        # Localhost is whitelisted so always returns False
        assert blocker.is_blocked('127.0.0.1') is False

    def test_non_blocked_ip_returns_false(self):
        blocker = IPBlocker()
        assert blocker.is_blocked('10.0.0.99') is False

    def test_blocked_ip_returns_true(self):
        blocker = IPBlocker()
        cache.set('ip_block:10.0.0.99', {'blocked': True}, timeout=60)
        assert blocker.is_blocked('10.0.0.99') is True


class TestIPBlockerBlockIP:
    """Tests for IPBlocker.block_ip."""

    def test_blocks_non_whitelisted_ip(self):
        blocker = IPBlocker()
        result = blocker.block_ip('10.0.0.200', reason='Test block', duration=300)
        assert result is True
        data = cache.get('ip_block:10.0.0.200')
        assert data is not None
        assert data['reason'] == 'Test block'
        assert data['duration'] == 300
        assert 'blocked_at' in data

    def test_cannot_block_whitelisted_ip(self):
        blocker = IPBlocker()
        result = blocker.block_ip('127.0.0.1', reason='Try to block localhost')
        assert result is False
        assert cache.get('ip_block:127.0.0.1') is None

    def test_block_with_default_duration(self):
        blocker = IPBlocker()
        result = blocker.block_ip('10.0.0.201')
        assert result is True
        data = cache.get('ip_block:10.0.0.201')
        assert data['duration'] == 86400  # default 24 hours


class TestIPBlockerUnblockIP:
    """Tests for IPBlocker.unblock_ip."""

    def test_unblocks_blocked_ip(self):
        blocker = IPBlocker()
        blocker.block_ip('10.0.0.210')
        assert blocker.is_blocked('10.0.0.210') is True
        blocker.unblock_ip('10.0.0.210')
        assert blocker.is_blocked('10.0.0.210') is False

    def test_unblock_non_blocked_ip_does_not_error(self):
        blocker = IPBlocker()
        blocker.unblock_ip('10.0.0.211')  # Should not raise


class TestIPBlockerAddToWhitelist:
    """Tests for IPBlocker.add_to_whitelist."""

    def test_adds_ip_to_whitelist(self):
        blocker = IPBlocker()
        blocker.add_to_whitelist('10.0.0.220')
        assert '10.0.0.220' in blocker.whitelist

    def test_adding_to_whitelist_unblocks_ip(self):
        blocker = IPBlocker()
        blocker.block_ip('10.0.0.221')
        assert blocker.is_blocked('10.0.0.221') is True
        blocker.add_to_whitelist('10.0.0.221')
        assert blocker.is_blocked('10.0.0.221') is False

    def test_whitelist_persisted_to_cache(self):
        blocker = IPBlocker()
        blocker.add_to_whitelist('10.0.0.222')
        cached = cache.get('ip_whitelist')
        assert '10.0.0.222' in cached


class TestIPBlockerRemoveFromWhitelist:
    """Tests for IPBlocker.remove_from_whitelist."""

    def test_removes_ip_from_whitelist(self):
        blocker = IPBlocker()
        blocker.add_to_whitelist('10.0.0.230')
        assert '10.0.0.230' in blocker.whitelist
        blocker.remove_from_whitelist('10.0.0.230')
        assert '10.0.0.230' not in blocker.whitelist

    def test_remove_nonexistent_ip_does_not_error(self):
        blocker = IPBlocker()
        blocker.remove_from_whitelist('10.0.0.231')  # Should not raise

    def test_whitelist_update_persisted_to_cache(self):
        blocker = IPBlocker()
        blocker.add_to_whitelist('10.0.0.232')
        blocker.remove_from_whitelist('10.0.0.232')
        cached = cache.get('ip_whitelist')
        assert '10.0.0.232' not in cached


class TestIPBlockerGetBlockInfo:
    """Tests for IPBlocker.get_block_info."""

    def test_returns_block_data_when_blocked(self):
        blocker = IPBlocker()
        blocker.block_ip('10.0.0.240', reason='Suspicious', duration=600)
        info = blocker.get_block_info('10.0.0.240')
        assert info is not None
        assert info['reason'] == 'Suspicious'
        assert info['duration'] == 600

    def test_returns_none_when_not_blocked(self):
        blocker = IPBlocker()
        info = blocker.get_block_info('10.0.0.241')
        assert info is None


# =============================================================================
# IP Convenience Function Tests
# =============================================================================


class TestIPConvenienceFunctions:
    """Tests for block_ip, unblock_ip, is_ip_blocked convenience functions."""

    def test_block_ip_function(self):
        result = block_ip('10.0.0.250', reason='Test', duration=300)
        assert result is True
        assert is_ip_blocked('10.0.0.250') is True

    def test_unblock_ip_function(self):
        block_ip('10.0.0.251', reason='Test', duration=300)
        assert is_ip_blocked('10.0.0.251') is True
        unblock_ip('10.0.0.251')
        assert is_ip_blocked('10.0.0.251') is False

    def test_is_ip_blocked_returns_false_for_unknown(self):
        assert is_ip_blocked('10.0.0.252') is False


# =============================================================================
# LoginTracker Tests
# =============================================================================


class TestLoginTrackerKeyGeneration:
    """Tests for LoginTracker key generation methods."""

    def test_get_attempt_key(self):
        tracker = LoginTracker()
        assert tracker._get_attempt_key('ip:10.0.0.1') == 'login_tracker:attempts:ip:10.0.0.1'

    def test_get_lockout_key(self):
        tracker = LoginTracker()
        assert tracker._get_lockout_key('user:admin') == 'login_tracker:lockout:user:admin'

    def test_get_lockout_count_key(self):
        tracker = LoginTracker()
        assert tracker._get_lockout_count_key('user:admin') == 'login_tracker:lockout_count:user:admin'


class TestLoginTrackerRecordFailedAttempt:
    """Tests for LoginTracker.record_failed_attempt."""

    def test_records_ip_attempt(self):
        tracker = LoginTracker()
        result = tracker.record_failed_attempt('10.0.0.1')
        assert result['ip_attempts'] == 1
        assert result['user_attempts'] == 0
        assert result['locked_out'] is False
        assert result['remaining_attempts'] == 4

    def test_records_ip_and_username_attempt(self):
        tracker = LoginTracker()
        result = tracker.record_failed_attempt('10.0.0.2', username='testuser')
        assert result['ip_attempts'] == 1
        assert result['user_attempts'] == 1
        assert result['remaining_attempts'] == 4

    def test_attempts_increment(self):
        tracker = LoginTracker()
        tracker.record_failed_attempt('10.0.0.3')
        result = tracker.record_failed_attempt('10.0.0.3')
        assert result['ip_attempts'] == 2
        assert result['remaining_attempts'] == 3

    def test_lockout_after_max_attempts_by_ip(self):
        tracker = LoginTracker()
        tracker.max_attempts = 3
        tracker.record_failed_attempt('10.0.0.4')
        tracker.record_failed_attempt('10.0.0.4')
        result = tracker.record_failed_attempt('10.0.0.4')
        assert result['locked_out'] is True
        assert result['lockout_duration'] == tracker.lockout_times[0]
        assert result['remaining_attempts'] == 0

    def test_lockout_after_max_attempts_by_username(self):
        tracker = LoginTracker()
        tracker.max_attempts = 3
        # Use different IPs but same username
        tracker.record_failed_attempt('10.0.1.1', username='victim')
        tracker.record_failed_attempt('10.0.1.2', username='victim')
        result = tracker.record_failed_attempt('10.0.1.3', username='victim')
        assert result['locked_out'] is True

    def test_progressive_lockout_increases_duration(self):
        tracker = LoginTracker()
        tracker.max_attempts = 2

        # First lockout
        tracker.record_failed_attempt('10.0.0.5')
        result1 = tracker.record_failed_attempt('10.0.0.5')
        assert result1['locked_out'] is True
        duration1 = result1['lockout_duration']

        # Clear the lockout and attempt counts to trigger second lockout
        cache.delete(tracker._get_lockout_key('ip:10.0.0.5'))
        cache.delete(tracker._get_attempt_key('ip:10.0.0.5'))

        # Second lockout should have longer duration
        tracker.record_failed_attempt('10.0.0.5')
        result2 = tracker.record_failed_attempt('10.0.0.5')
        assert result2['locked_out'] is True
        duration2 = result2['lockout_duration']
        assert duration2 > duration1

    def test_ip_blocked_on_excessive_attempts(self):
        tracker = LoginTracker()
        tracker.max_attempts = 3
        ip = '10.0.0.6'
        # Need max_attempts * 2 = 6 IP attempts
        for _ in range(6):
            # Clear lockout between batches so we keep accumulating IP attempts
            cache.delete(tracker._get_lockout_key(f'ip:{ip}'))
            tracker.record_failed_attempt(ip)

        # At 6 attempts (max_attempts * 2), IP should be blocked
        assert ip_blocker.is_blocked(ip) is True

    def test_lockout_uses_username_identifier_when_available(self):
        tracker = LoginTracker()
        tracker.max_attempts = 2
        tracker.record_failed_attempt('10.0.0.7', username='lockeduser')
        result = tracker.record_failed_attempt('10.0.0.7', username='lockeduser')
        assert result['locked_out'] is True
        # Lockout should be set for user:lockeduser
        lockout_data = cache.get(tracker._get_lockout_key('user:lockeduser'))
        assert lockout_data is not None
        assert lockout_data['username'] == 'lockeduser'

    def test_lockout_uses_ip_identifier_when_no_username(self):
        tracker = LoginTracker()
        tracker.max_attempts = 2
        tracker.record_failed_attempt('10.0.0.8')
        result = tracker.record_failed_attempt('10.0.0.8')
        assert result['locked_out'] is True
        lockout_data = cache.get(tracker._get_lockout_key('ip:10.0.0.8'))
        assert lockout_data is not None


class TestLoginTrackerRecordSuccessfulLogin:
    """Tests for LoginTracker.record_successful_login."""

    def test_clears_ip_attempts(self):
        tracker = LoginTracker()
        tracker.record_failed_attempt('10.0.0.10', username='user1')
        tracker.record_failed_attempt('10.0.0.10', username='user1')
        tracker.record_successful_login('10.0.0.10', 'user1')
        ip_attempts = cache.get(tracker._get_attempt_key('ip:10.0.0.10'))
        assert ip_attempts is None

    def test_clears_user_attempts(self):
        tracker = LoginTracker()
        tracker.record_failed_attempt('10.0.0.11', username='user2')
        tracker.record_successful_login('10.0.0.11', 'user2')
        user_attempts = cache.get(tracker._get_attempt_key('user:user2'))
        assert user_attempts is None

    def test_does_not_clear_lockout_count(self):
        tracker = LoginTracker()
        tracker.max_attempts = 2
        # Trigger lockout to set lockout count
        tracker.record_failed_attempt('10.0.0.12', username='user3')
        tracker.record_failed_attempt('10.0.0.12', username='user3')
        # Successful login
        tracker.record_successful_login('10.0.0.12', 'user3')
        # Lockout count should still persist
        count = cache.get(tracker._get_lockout_count_key('user:user3'))
        assert count is not None
        assert count >= 1


class TestLoginTrackerIsLockedOut:
    """Tests for LoginTracker.is_locked_out."""

    def test_not_locked_out_initially(self):
        tracker = LoginTracker()
        locked, duration = tracker.is_locked_out('10.0.0.20')
        assert locked is False
        assert duration is None

    def test_locked_out_by_username(self):
        tracker = LoginTracker()
        tracker.max_attempts = 2
        tracker.record_failed_attempt('10.0.0.21', username='locked_user')
        tracker.record_failed_attempt('10.0.0.21', username='locked_user')
        locked, duration = tracker.is_locked_out('10.0.0.21', username='locked_user')
        assert locked is True
        assert duration is not None
        assert duration > 0

    def test_locked_out_by_ip(self):
        tracker = LoginTracker()
        tracker.max_attempts = 2
        tracker.record_failed_attempt('10.0.0.22')
        tracker.record_failed_attempt('10.0.0.22')
        locked, duration = tracker.is_locked_out('10.0.0.22')
        assert locked is True
        assert duration is not None

    def test_not_locked_out_when_under_threshold(self):
        tracker = LoginTracker()
        tracker.max_attempts = 5
        tracker.record_failed_attempt('10.0.0.23', username='safe_user')
        locked, duration = tracker.is_locked_out('10.0.0.23', username='safe_user')
        assert locked is False
        assert duration is None

    def test_username_lockout_checked_first(self):
        tracker = LoginTracker()
        # Manually set username lockout
        cache.set(
            tracker._get_lockout_key('user:priority_user'),
            {'locked_at': 'now', 'duration': 900, 'ip': '10.0.0.24', 'username': 'priority_user'},
            timeout=900,
        )
        locked, duration = tracker.is_locked_out('10.0.0.24', username='priority_user')
        assert locked is True
        assert duration == 900


class TestLoginTrackerGetRemainingAttempts:
    """Tests for LoginTracker.get_remaining_attempts."""

    def test_full_attempts_remaining(self):
        tracker = LoginTracker()
        remaining = tracker.get_remaining_attempts('10.0.0.30')
        assert remaining == tracker.max_attempts

    def test_remaining_decreases_after_failed_attempt(self):
        tracker = LoginTracker()
        tracker.record_failed_attempt('10.0.0.31')
        remaining = tracker.get_remaining_attempts('10.0.0.31')
        assert remaining == tracker.max_attempts - 1

    def test_remaining_with_username(self):
        tracker = LoginTracker()
        tracker.record_failed_attempt('10.0.0.32', username='testuser')
        remaining = tracker.get_remaining_attempts('10.0.0.32', username='testuser')
        assert remaining == tracker.max_attempts - 1

    def test_zero_remaining_at_max(self):
        tracker = LoginTracker()
        for _ in range(tracker.max_attempts):
            tracker.record_failed_attempt('10.0.0.33')
        remaining = tracker.get_remaining_attempts('10.0.0.33')
        assert remaining == 0


class TestLoginTrackerClearLockout:
    """Tests for LoginTracker.clear_lockout."""

    def test_clears_all_related_keys(self):
        tracker = LoginTracker()
        tracker.max_attempts = 2
        tracker.record_failed_attempt('10.0.0.40', username='clearme')
        tracker.record_failed_attempt('10.0.0.40', username='clearme')

        tracker.clear_lockout('clearme')
        # All keys should be cleared
        assert cache.get(tracker._get_lockout_key('user:clearme')) is None
        assert cache.get(tracker._get_lockout_key('ip:clearme')) is None
        assert cache.get(tracker._get_attempt_key('user:clearme')) is None
        assert cache.get(tracker._get_attempt_key('ip:clearme')) is None

    def test_clear_lockout_for_ip_identifier(self):
        tracker = LoginTracker()
        tracker.max_attempts = 2
        tracker.record_failed_attempt('10.0.0.41')
        tracker.record_failed_attempt('10.0.0.41')

        tracker.clear_lockout('10.0.0.41')
        assert cache.get(tracker._get_lockout_key('ip:10.0.0.41')) is None
        assert cache.get(tracker._get_attempt_key('ip:10.0.0.41')) is None


# =============================================================================
# BruteForceProtector Tests
# =============================================================================


class TestBruteForceProtectorGetRateLimiter:
    """Tests for BruteForceProtector.get_rate_limiter."""

    def test_creates_new_rate_limiter(self):
        protector = BruteForceProtector()
        limiter = protector.get_rate_limiter('test_action', rate=10, period=60)
        assert isinstance(limiter, RateLimiter)
        assert limiter.rate == 10
        assert limiter.period == 60

    def test_returns_existing_rate_limiter(self):
        protector = BruteForceProtector()
        limiter1 = protector.get_rate_limiter('same_action', rate=10, period=60)
        limiter2 = protector.get_rate_limiter('same_action', rate=20, period=120)
        # Should return the same instance, ignoring new params
        assert limiter1 is limiter2
        assert limiter2.rate == 10  # keeps original params

    def test_different_names_create_different_limiters(self):
        protector = BruteForceProtector()
        limiter1 = protector.get_rate_limiter('action_a')
        limiter2 = protector.get_rate_limiter('action_b')
        assert limiter1 is not limiter2


class TestBruteForceProtectorCheckLogin:
    """Tests for BruteForceProtector.check_login."""

    def test_allows_normal_login(self, rf):
        protector = BruteForceProtector()
        request = rf.post('/login/')
        request.META['REMOTE_ADDR'] = '10.0.1.10'
        allowed, info = protector.check_login(request, 'testuser')
        assert allowed is True
        assert 'remaining_attempts' in info

    def test_blocks_when_ip_blocked(self, rf):
        protector = BruteForceProtector()
        request = rf.post('/login/')
        request.META['REMOTE_ADDR'] = '10.0.1.11'
        # Block the IP
        ip_blocker.block_ip('10.0.1.11', reason='Test')
        allowed, info = protector.check_login(request, 'testuser')
        assert allowed is False
        assert info['reason'] == 'ip_blocked'
        # Cleanup
        ip_blocker.unblock_ip('10.0.1.11')

    def test_blocks_when_locked_out(self, rf):
        protector = BruteForceProtector()
        request = rf.post('/login/')
        request.META['REMOTE_ADDR'] = '10.0.1.12'

        # Trigger lockout by failing enough times
        tracker = protector.login_tracker
        tracker.max_attempts = 2
        tracker.record_failed_attempt('10.0.1.12', username='locktest')
        tracker.record_failed_attempt('10.0.1.12', username='locktest')

        allowed, info = protector.check_login(request, 'locktest')
        assert allowed is False
        assert info['reason'] == 'locked_out'
        assert 'duration' in info


class TestBruteForceProtectorRecordLoginFailure:
    """Tests for BruteForceProtector.record_login_failure."""

    def test_records_failure(self, rf):
        protector = BruteForceProtector()
        request = rf.post('/login/')
        request.META['REMOTE_ADDR'] = '10.0.1.20'
        result = protector.record_login_failure(request, 'failuser')
        assert result['ip_attempts'] == 1
        assert result['user_attempts'] == 1


class TestBruteForceProtectorRecordLoginSuccess:
    """Tests for BruteForceProtector.record_login_success."""

    def test_records_success(self, rf):
        protector = BruteForceProtector()
        request = rf.post('/login/')
        request.META['REMOTE_ADDR'] = '10.0.1.30'
        # Record some failures first
        protector.record_login_failure(request, 'successuser')
        # Then record success
        protector.record_login_success(request, 'successuser')
        # Attempts should be cleared
        tracker = protector.login_tracker
        ip_attempts = cache.get(tracker._get_attempt_key('ip:10.0.1.30'))
        assert ip_attempts is None


class TestBruteForceProtectorCheckPasswordReset:
    """Tests for BruteForceProtector.check_password_reset."""

    def test_allows_first_reset_request(self, rf):
        protector = BruteForceProtector()
        request = rf.post('/reset/')
        request.META['REMOTE_ADDR'] = '10.0.1.40'
        allowed, message = protector.check_password_reset(request, 'user@example.com')
        assert allowed is True
        assert message == ''

    def test_blocks_after_too_many_ip_requests(self, rf):
        protector = BruteForceProtector()
        request = rf.post('/reset/')
        request.META['REMOTE_ADDR'] = '10.0.1.41'
        # rate=3 for password_reset
        for _ in range(3):
            protector.check_password_reset(request, 'a@b.com')
        allowed, message = protector.check_password_reset(request, 'a@b.com')
        assert allowed is False
        assert 'too many' in message.lower()

    def test_blocks_after_too_many_email_requests(self, rf):
        protector = BruteForceProtector()
        # Use different IPs but same email
        for i in range(3):
            request = rf.post('/reset/')
            request.META['REMOTE_ADDR'] = f'10.0.2.{i}'
            protector.check_password_reset(request, 'same@email.com')
        request = rf.post('/reset/')
        request.META['REMOTE_ADDR'] = '10.0.2.99'
        allowed, message = protector.check_password_reset(request, 'same@email.com')
        assert allowed is False
        assert 'email' in message.lower() or 'too many' in message.lower()


class TestBruteForceProtectorCheckApiKeyGuess:
    """Tests for BruteForceProtector.check_api_key_guess."""

    def test_allows_initial_request(self, rf):
        protector = BruteForceProtector()
        request = rf.get('/api/')
        request.META['REMOTE_ADDR'] = '10.0.1.50'
        allowed, message = protector.check_api_key_guess(request)
        assert allowed is True
        assert message == ''

    def test_blocks_after_too_many_guesses(self, rf):
        protector = BruteForceProtector()
        request = rf.get('/api/')
        request.META['REMOTE_ADDR'] = '10.0.1.51'
        # rate=5 for api_key
        for _ in range(5):
            protector.check_api_key_guess(request)
        allowed, message = protector.check_api_key_guess(request)
        assert allowed is False
        assert 'blocked' in message.lower() or 'suspicious' in message.lower()

    def test_blocks_ip_on_brute_force(self, rf):
        protector = BruteForceProtector()
        request = rf.get('/api/')
        request.META['REMOTE_ADDR'] = '10.0.1.52'
        for _ in range(5):
            protector.check_api_key_guess(request)
        protector.check_api_key_guess(request)
        # IP should be blocked
        assert ip_blocker.is_blocked('10.0.1.52') is True
        # Cleanup
        ip_blocker.unblock_ip('10.0.1.52')


class TestBruteForceProtectorCheckFormSubmission:
    """Tests for BruteForceProtector.check_form_submission."""

    def test_allows_initial_submission(self, rf):
        protector = BruteForceProtector()
        request = rf.post('/form/')
        request.META['REMOTE_ADDR'] = '10.0.1.60'
        allowed, message = protector.check_form_submission(request, 'contact_form')
        assert allowed is True
        assert message == ''

    def test_blocks_after_too_many_submissions(self, rf):
        protector = BruteForceProtector()
        request = rf.post('/form/')
        request.META['REMOTE_ADDR'] = '10.0.1.61'
        for _ in range(10):
            protector.check_form_submission(request, 'spam_form', rate=10, period=60)
        allowed, message = protector.check_form_submission(request, 'spam_form', rate=10, period=60)
        assert allowed is False
        assert 'too many' in message.lower()

    def test_custom_rate_and_period(self, rf):
        protector = BruteForceProtector()
        request = rf.post('/form/')
        request.META['REMOTE_ADDR'] = '10.0.1.62'
        # Very low rate
        for _ in range(2):
            protector.check_form_submission(request, 'low_rate_form', rate=2, period=60)
        allowed, message = protector.check_form_submission(request, 'low_rate_form', rate=2, period=60)
        assert allowed is False


# =============================================================================
# SecurityMonitor Tests (existing tests preserved)
# =============================================================================


@pytest.mark.django_db
class TestSecurityMonitorSendAlert:
    """Tests for SecurityMonitor._send_alert_notification."""

    @patch('django.core.mail.mail_admins')
    def test_sends_email_to_admins(self, mock_mail_admins):
        """Test that _send_alert_notification sends an email to admins."""
        monitor = SecurityMonitor()

        monitor._send_alert_notification(
            event_type='failed_logins',
            count=150,
            threshold=100,
            details={'ip': '10.0.0.1'},
        )

        mock_mail_admins.assert_called_once()
        call_args = mock_mail_admins.call_args
        subject = call_args[0][0]
        message = call_args[0][1]

        assert 'failed_logins' in subject
        assert '150' in message
        assert '100' in message

    @patch('django.core.mail.mail_admins')
    def test_email_includes_event_details(self, mock_mail_admins):
        """Test that the email body includes event details."""
        monitor = SecurityMonitor()

        details = {'ip': '192.168.1.50', 'user_agent': 'bad-bot/1.0'}
        monitor._send_alert_notification(
            event_type='suspicious_requests',
            count=200,
            threshold=100,
            details=details,
        )

        message = mock_mail_admins.call_args[0][1]
        assert '192.168.1.50' in message
        assert 'suspicious_requests' in message

    @patch('django.core.mail.mail_admins')
    def test_uses_fail_silently_false(self, mock_mail_admins):
        """Test that mail_admins is called with fail_silently=False to ensure delivery."""
        monitor = SecurityMonitor()

        monitor._send_alert_notification('failed_logins', 100, 50, None)

        mock_mail_admins.assert_called_once()
        assert mock_mail_admins.call_args[1]['fail_silently'] is False

    @patch('django.core.mail.mail_admins')
    def test_handles_mail_exception_gracefully(self, mock_mail_admins):
        """Test that email sending failure does not raise an exception."""
        mock_mail_admins.side_effect = Exception("SMTP connection failed")
        monitor = SecurityMonitor()

        # Should not raise
        monitor._send_alert_notification('failed_logins', 100, 50, None)

    @patch('django.core.mail.mail_admins')
    def test_sends_alert_with_none_details(self, mock_mail_admins):
        """Test that sending alert with None details works."""
        monitor = SecurityMonitor()

        monitor._send_alert_notification(
            event_type='rate_limits',
            count=300,
            threshold=200,
            details=None,
        )

        mock_mail_admins.assert_called_once()
        message = mock_mail_admins.call_args[0][1]
        assert 'None' in message or 'rate_limits' in message


@pytest.mark.django_db
class TestSecurityMonitorTriggerAlert:
    """Tests for SecurityMonitor._trigger_alert and record_event."""

    @patch.object(SecurityMonitor, '_send_alert_notification')
    def test_triggers_alert_when_threshold_exceeded(self, mock_send_alert):
        """Test that an alert is triggered when event count exceeds threshold."""
        monitor = SecurityMonitor()
        monitor.thresholds = {'failed_logins_per_hour': 3}

        # Record events up to threshold
        for _ in range(3):
            monitor.record_event('failed_logins', {'ip': '10.0.0.1'})

        mock_send_alert.assert_called_once()
        positional = mock_send_alert.call_args[0]

        assert positional[0] == 'failed_logins'
        assert positional[1] == 3  # count
        assert positional[2] == 3  # threshold

    @patch.object(SecurityMonitor, '_send_alert_notification')
    def test_does_not_trigger_below_threshold(self, mock_send_alert):
        """Test that no alert is triggered when below threshold."""
        monitor = SecurityMonitor()
        monitor.thresholds = {'failed_logins_per_hour': 10}

        for _ in range(5):
            monitor.record_event('failed_logins')

        mock_send_alert.assert_not_called()

    @patch.object(SecurityMonitor, '_send_alert_notification')
    def test_only_alerts_once_per_hour(self, mock_send_alert):
        """Test that duplicate alerts are suppressed within the same hour."""
        monitor = SecurityMonitor()
        monitor.thresholds = {'failed_logins_per_hour': 2}

        # First threshold breach triggers alert
        monitor.record_event('failed_logins')
        monitor.record_event('failed_logins')

        # Second threshold breach in same hour should not trigger
        monitor.record_event('failed_logins')
        monitor.record_event('failed_logins')

        assert mock_send_alert.call_count == 1

    @patch.object(SecurityMonitor, '_send_alert_notification')
    def test_increments_counter_on_each_event(self, mock_send_alert):
        """Test that the counter increments with each recorded event."""
        monitor = SecurityMonitor()
        monitor.thresholds = {'test_event_per_hour': 1000}  # high threshold

        monitor.record_event('test_event')
        monitor.record_event('test_event')
        monitor.record_event('test_event')

        counter_key = monitor._get_counter_key('test_event')
        count = cache.get(counter_key, 0)
        assert count == 3

    @patch.object(SecurityMonitor, '_send_alert_notification')
    def test_separate_counters_per_event_type(self, mock_send_alert):
        """Test that different event types have separate counters."""
        monitor = SecurityMonitor()
        monitor.thresholds = {}

        monitor.record_event('failed_logins')
        monitor.record_event('failed_logins')
        monitor.record_event('blocked_ips')

        login_key = monitor._get_counter_key('failed_logins')
        ip_key = monitor._get_counter_key('blocked_ips')

        assert cache.get(login_key) == 2
        assert cache.get(ip_key) == 1

    @patch.object(SecurityMonitor, '_send_alert_notification')
    def test_no_alert_for_unconfigured_event_type(self, mock_send_alert):
        """Test that events without a threshold do not trigger alerts."""
        monitor = SecurityMonitor()
        monitor.thresholds = {}  # No thresholds configured

        for _ in range(100):
            monitor.record_event('custom_event')

        mock_send_alert.assert_not_called()


@pytest.mark.django_db
class TestSecurityMonitorHourlyStats:
    """Tests for SecurityMonitor.get_hourly_stats."""

    def test_returns_zero_counts_initially(self):
        """Test that hourly stats are all zero when no events recorded."""
        monitor = SecurityMonitor()

        stats = monitor.get_hourly_stats()

        assert stats['failed_logins'] == 0
        assert stats['blocked_ips'] == 0
        assert stats['rate_limits'] == 0
        assert stats['suspicious_requests'] == 0

    def test_returns_correct_counts(self):
        """Test that hourly stats reflect recorded events."""
        monitor = SecurityMonitor()
        monitor.thresholds = {}

        monitor.record_event('failed_logins')
        monitor.record_event('failed_logins')
        monitor.record_event('failed_logins')
        monitor.record_event('blocked_ips')
        monitor.record_event('suspicious_requests')
        monitor.record_event('suspicious_requests')

        stats = monitor.get_hourly_stats()

        assert stats['failed_logins'] == 3
        assert stats['blocked_ips'] == 1
        assert stats['rate_limits'] == 0
        assert stats['suspicious_requests'] == 2

    def test_returns_dict_with_expected_keys(self):
        """Test that hourly stats returns all expected event types."""
        monitor = SecurityMonitor()

        stats = monitor.get_hourly_stats()

        expected_keys = {'failed_logins', 'blocked_ips', 'rate_limits', 'suspicious_requests'}
        assert set(stats.keys()) == expected_keys

    def test_custom_events_not_in_hourly_stats(self):
        """Test that custom event types are not included in standard hourly stats."""
        monitor = SecurityMonitor()
        monitor.thresholds = {}

        monitor.record_event('custom_event_type')

        stats = monitor.get_hourly_stats()
        assert 'custom_event_type' not in stats

    def test_stats_reflect_current_hour_only(self):
        """Test that stats use the current hour's cache keys."""
        monitor = SecurityMonitor()
        monitor.thresholds = {}

        # Record an event
        monitor.record_event('failed_logins')

        stats = monitor.get_hourly_stats()
        assert stats['failed_logins'] == 1

        # Manually expire the counter by deleting from cache
        counter_key = monitor._get_counter_key('failed_logins')
        cache.delete(counter_key)

        stats = monitor.get_hourly_stats()
        assert stats['failed_logins'] == 0

    def test_concurrent_event_recording(self):
        """Test that multiple concurrent events are counted correctly."""
        monitor = SecurityMonitor()
        monitor.thresholds = {}

        # Record many events
        for _ in range(50):
            monitor.record_event('rate_limits')

        stats = monitor.get_hourly_stats()
        assert stats['rate_limits'] == 50


# =============================================================================
# Utility Function Tests
# =============================================================================


class TestGetClientIP:
    """Tests for get_client_ip."""

    def test_from_x_forwarded_for(self, rf):
        request = rf.get('/', HTTP_X_FORWARDED_FOR='203.0.113.1, 70.41.3.18, 150.172.238.178')
        assert get_client_ip(request) == '203.0.113.1'

    def test_from_x_forwarded_for_single_ip(self, rf):
        request = rf.get('/', HTTP_X_FORWARDED_FOR='203.0.113.2')
        assert get_client_ip(request) == '203.0.113.2'

    def test_from_x_forwarded_for_strips_whitespace(self, rf):
        request = rf.get('/', HTTP_X_FORWARDED_FOR='  203.0.113.3  , 10.0.0.1')
        assert get_client_ip(request) == '203.0.113.3'

    def test_from_x_real_ip(self, rf):
        request = rf.get('/', HTTP_X_REAL_IP='198.51.100.1')
        assert get_client_ip(request) == '198.51.100.1'

    def test_from_x_real_ip_strips_whitespace(self, rf):
        request = rf.get('/', HTTP_X_REAL_IP='  198.51.100.2  ')
        assert get_client_ip(request) == '198.51.100.2'

    def test_from_remote_addr(self, rf):
        request = rf.get('/')
        request.META['REMOTE_ADDR'] = '192.0.2.1'
        # Remove X-Forwarded-For and X-Real-IP if present
        request.META.pop('HTTP_X_FORWARDED_FOR', None)
        request.META.pop('HTTP_X_REAL_IP', None)
        assert get_client_ip(request) == '192.0.2.1'

    def test_fallback_to_unknown(self, rf):
        request = rf.get('/')
        request.META.pop('HTTP_X_FORWARDED_FOR', None)
        request.META.pop('HTTP_X_REAL_IP', None)
        request.META.pop('REMOTE_ADDR', None)
        assert get_client_ip(request) == 'Unknown'

    def test_x_forwarded_for_takes_precedence_over_x_real_ip(self, rf):
        request = rf.get('/', HTTP_X_FORWARDED_FOR='1.1.1.1', HTTP_X_REAL_IP='2.2.2.2')
        assert get_client_ip(request) == '1.1.1.1'


class TestGenerateSecureToken:
    """Tests for generate_secure_token."""

    def test_generates_token(self):
        token = generate_secure_token()
        assert isinstance(token, str)
        assert len(token) > 0

    def test_generates_different_tokens(self):
        token1 = generate_secure_token()
        token2 = generate_secure_token()
        assert token1 != token2

    def test_custom_length(self):
        token_short = generate_secure_token(length=8)
        token_long = generate_secure_token(length=64)
        assert isinstance(token_short, str)
        assert isinstance(token_long, str)
        # URL-safe base64 encodes 6 bits per char, so length 8 gives ~11 chars
        # length 64 gives ~86 chars
        assert len(token_long) > len(token_short)

    def test_default_length(self):
        token = generate_secure_token()
        # Default length=32 bytes -> ~43 base64 chars
        assert len(token) > 10


class TestHashSensitiveData:
    """Tests for hash_sensitive_data."""

    def test_hashes_data(self):
        result = hash_sensitive_data('test_data')
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex digest

    def test_same_data_produces_same_hash(self):
        hash1 = hash_sensitive_data('test_data')
        hash2 = hash_sensitive_data('test_data')
        assert hash1 == hash2

    def test_different_data_produces_different_hash(self):
        hash1 = hash_sensitive_data('data1')
        hash2 = hash_sensitive_data('data2')
        assert hash1 != hash2

    def test_custom_salt(self):
        hash1 = hash_sensitive_data('test', salt='salt1')
        hash2 = hash_sensitive_data('test', salt='salt2')
        assert hash1 != hash2

    def test_default_salt_uses_secret_key(self):
        # With no salt, it uses settings.SECRET_KEY[:16]
        result = hash_sensitive_data('test_data')
        assert isinstance(result, str)
        assert len(result) == 64


class TestMaskEmail:
    """Tests for mask_email."""

    def test_masks_normal_email(self):
        result = mask_email('john@example.com')
        assert result == 'j***@example.com'

    def test_masks_long_local_part(self):
        result = mask_email('alexander@example.com')
        assert result == 'a********@example.com'

    def test_masks_single_char_local(self):
        result = mask_email('j@example.com')
        assert result == '*@example.com'

    def test_masks_two_char_local(self):
        result = mask_email('ab@example.com')
        assert result == 'a*@example.com'

    def test_no_at_sign_returns_stars(self):
        result = mask_email('invalidemail')
        assert result == '***'

    def test_empty_string_returns_stars(self):
        result = mask_email('')
        assert result == '***'


class TestMaskIP:
    """Tests for mask_ip."""

    def test_masks_ipv4(self):
        result = mask_ip('192.168.1.100')
        assert result == '192.168.*.*'

    def test_masks_another_ipv4(self):
        result = mask_ip('10.0.0.1')
        assert result == '10.0.*.*'

    def test_non_ipv4_returns_stars(self):
        result = mask_ip('::1')
        assert result == '***'

    def test_partial_ip_returns_stars(self):
        result = mask_ip('10.0.0')
        assert result == '***'

    def test_empty_string_returns_stars(self):
        result = mask_ip('')
        assert result == '***'


# =============================================================================
# View Decorator Tests
# =============================================================================


class TestRequireSecureRequest:
    """Tests for require_secure_request decorator."""

    def test_allows_secure_request(self, rf):
        @require_secure_request
        def my_view(request):
            return HttpResponse('Secure OK')

        request = rf.get('/')
        request.is_secure = lambda: True
        response = my_view(request)
        assert response.status_code == 200
        assert response.content == b'Secure OK'

    def test_blocks_insecure_request_in_production(self, rf, settings):
        settings.DEBUG = False

        @require_secure_request
        def my_view(request):
            return HttpResponse('Should not see this')

        request = rf.get('/')
        request.is_secure = lambda: False
        response = my_view(request)
        assert response.status_code == 403
        assert b'HTTPS required' in response.content

    def test_allows_insecure_request_in_debug_mode(self, rf, settings):
        settings.DEBUG = True

        @require_secure_request
        def my_view(request):
            return HttpResponse('Debug OK')

        request = rf.get('/')
        request.is_secure = lambda: False
        response = my_view(request)
        assert response.status_code == 200
        assert response.content == b'Debug OK'

    def test_preserves_function_name(self):
        @require_secure_request
        def my_named_view(request):
            return HttpResponse('OK')

        assert my_named_view.__name__ == 'my_named_view'


class TestCheckIPBlock:
    """Tests for check_ip_block decorator."""

    def test_allows_non_blocked_ip(self, rf):
        @check_ip_block
        def my_view(request):
            return HttpResponse('Allowed')

        request = rf.get('/')
        request.META['REMOTE_ADDR'] = '10.0.2.1'
        response = my_view(request)
        assert response.status_code == 200
        assert response.content == b'Allowed'

    def test_blocks_blocked_ip(self, rf):
        @check_ip_block
        def my_view(request):
            return HttpResponse('Should not see this')

        ip = '10.0.2.2'
        ip_blocker.block_ip(ip, reason='Test block')

        request = rf.get('/')
        request.META['REMOTE_ADDR'] = ip
        response = my_view(request)
        assert response.status_code == 403
        assert b'Access denied' in response.content

        # Cleanup
        ip_blocker.unblock_ip(ip)

    def test_preserves_function_name(self):
        @check_ip_block
        def my_blocked_view(request):
            return HttpResponse('OK')

        assert my_blocked_view.__name__ == 'my_blocked_view'


class TestLogSecurityEvent:
    """Tests for log_security_event decorator."""

    @patch.object(SecurityMonitor, '_send_alert_notification')
    def test_logs_event_and_calls_view(self, mock_send, rf):
        @log_security_event('test_event')
        def my_view(request):
            return HttpResponse('Logged')

        request = rf.get('/test-path/')
        request.META['REMOTE_ADDR'] = '10.0.3.1'
        user = MagicMock()
        user.__str__ = lambda s: 'testuser'
        request.user = user

        response = my_view(request)
        assert response.status_code == 200
        assert response.content == b'Logged'

    @patch.object(SecurityMonitor, '_send_alert_notification')
    def test_records_event_in_monitor(self, mock_send, rf):
        monitor = SecurityMonitor()
        monitor.thresholds = {'access_per_hour': 1000}

        @log_security_event('access')
        def my_view(request):
            return HttpResponse('OK')

        request = rf.get('/path/')
        request.META['REMOTE_ADDR'] = '10.0.3.2'
        request.user = MagicMock()
        my_view(request)

        # The event should have been recorded
        counter_key = security_monitor._get_counter_key('access')
        count = cache.get(counter_key, 0)
        assert count >= 1

    @patch.object(SecurityMonitor, '_send_alert_notification')
    def test_handles_request_without_user(self, mock_send, rf):
        @log_security_event('anon_event')
        def my_view(request):
            return HttpResponse('Anon OK')

        request = rf.get('/anon/')
        request.META['REMOTE_ADDR'] = '10.0.3.3'
        # Don't set request.user
        if hasattr(request, 'user'):
            delattr(request, 'user')

        response = my_view(request)
        assert response.status_code == 200

    def test_preserves_function_name(self):
        @log_security_event('event')
        def my_event_view(request):
            return HttpResponse('OK')

        assert my_event_view.__name__ == 'my_event_view'

    @patch.object(SecurityMonitor, '_send_alert_notification')
    def test_passes_masked_ip_in_details(self, mock_send, rf):
        recorded_details = []
        original_record_event = security_monitor.record_event

        def capture_record_event(event_type, details=None):
            recorded_details.append(details)
            return original_record_event(event_type, details)

        @log_security_event('detail_event')
        def my_view(request):
            return HttpResponse('OK')

        request = rf.get('/detail/')
        request.META['REMOTE_ADDR'] = '192.168.1.50'
        request.user = MagicMock()

        with patch.object(security_monitor, 'record_event', side_effect=capture_record_event):
            my_view(request)

        assert len(recorded_details) >= 1
        details = recorded_details[0]
        assert details['ip'] == '192.168.*.*'
        assert details['path'] == '/detail/'
