"""
Tests for config/cache.py.

Tests cache configuration including:
- Cache aliases
- CacheTimeout constants
- CachePrefix constants
- CacheKeyBuilder
- get_cache_config
- get_redis_cluster_config
- get_redis_sentinel_config
- CacheInvalidator
- cached decorator
- multi_layer_cached decorator
- DistributedLock
- with_lock decorator
- CacheWarmer
- check_cache_health
"""

import pytest
import hashlib
from unittest.mock import patch, MagicMock, PropertyMock
from django.core.cache import caches

from config.cache import (
    CACHE_ALIAS_DEFAULT,
    CACHE_ALIAS_SESSIONS,
    CACHE_ALIAS_LOCKS,
    CACHE_ALIAS_THROTTLE,
    CACHE_ALIAS_LOCAL,
    CacheTimeout,
    CachePrefix,
    CacheKeyBuilder,
    get_cache_config,
    get_redis_cluster_config,
    get_redis_sentinel_config,
    CacheInvalidator,
    cached,
    multi_layer_cached,
    DistributedLock,
    with_lock,
    CacheWarmer,
    check_cache_health,
)


class TestCacheAliases:
    """Test cache alias constants."""

    def test_default_alias(self):
        assert CACHE_ALIAS_DEFAULT == "default"

    def test_sessions_alias(self):
        assert CACHE_ALIAS_SESSIONS == "sessions"

    def test_locks_alias(self):
        assert CACHE_ALIAS_LOCKS == "locks"

    def test_throttle_alias(self):
        assert CACHE_ALIAS_THROTTLE == "throttle"

    def test_local_alias(self):
        assert CACHE_ALIAS_LOCAL == "local"


class TestCacheTimeout:
    """Test CacheTimeout constants."""

    def test_instant(self):
        assert CacheTimeout.INSTANT == 30

    def test_short(self):
        assert CacheTimeout.SHORT == 300

    def test_medium(self):
        assert CacheTimeout.MEDIUM == 900

    def test_long(self):
        assert CacheTimeout.LONG == 3600

    def test_extended(self):
        assert CacheTimeout.EXTENDED == 14400

    def test_day(self):
        assert CacheTimeout.DAY == 86400

    def test_week(self):
        assert CacheTimeout.WEEK == 604800

    def test_month(self):
        assert CacheTimeout.MONTH == 2592000

    def test_session(self):
        assert CacheTimeout.SESSION == 1209600

    def test_api_response(self):
        assert CacheTimeout.API_RESPONSE == 60

    def test_user_profile(self):
        assert CacheTimeout.USER_PROFILE == 900

    def test_permissions(self):
        assert CacheTimeout.PERMISSIONS == 300

    def test_settings(self):
        assert CacheTimeout.SETTINGS == 3600

    def test_analytics(self):
        assert CacheTimeout.ANALYTICS == 1800

    def test_invoice(self):
        assert CacheTimeout.INVOICE == 600

    def test_contract(self):
        assert CacheTimeout.CONTRACT == 600


class TestCachePrefix:
    """Test CachePrefix constants."""

    def test_user_prefix(self):
        assert CachePrefix.USER == "user"

    def test_session_prefix(self):
        assert CachePrefix.SESSION == "session"

    def test_client_prefix(self):
        assert CachePrefix.CLIENT == "client"

    def test_contract_prefix(self):
        assert CachePrefix.CONTRACT == "contract"

    def test_invoice_prefix(self):
        assert CachePrefix.INVOICE == "invoice"

    def test_payment_prefix(self):
        assert CachePrefix.PAYMENT == "payment"

    def test_document_prefix(self):
        assert CachePrefix.DOCUMENT == "document"

    def test_notification_prefix(self):
        assert CachePrefix.NOTIFICATION == "notification"

    def test_analytics_prefix(self):
        assert CachePrefix.ANALYTICS == "analytics"

    def test_settings_prefix(self):
        assert CachePrefix.SETTINGS == "settings"

    def test_permissions_prefix(self):
        assert CachePrefix.PERMISSIONS == "perms"

    def test_rate_limit_prefix(self):
        assert CachePrefix.RATE_LIMIT == "rl"

    def test_lock_prefix(self):
        assert CachePrefix.LOCK == "lock"

    def test_throttle_prefix(self):
        assert CachePrefix.THROTTLE == "throttle"

    def test_api_prefix(self):
        assert CachePrefix.API == "api"


class TestCacheKeyBuilder:
    """Test CacheKeyBuilder class."""

    def test_build_simple_key(self):
        """Test building a simple key with prefix only."""
        key = CacheKeyBuilder.build("user")
        assert key == "v1:user"

    def test_build_with_args(self):
        """Test building key with additional arguments."""
        key = CacheKeyBuilder.build("user", 123)
        assert key == "v1:user:123"

    def test_build_with_multiple_args(self):
        """Test building key with multiple arguments."""
        key = CacheKeyBuilder.build("user", 123, "profile")
        assert key == "v1:user:123:profile"

    def test_build_with_custom_version(self):
        """Test building key with custom version."""
        key = CacheKeyBuilder.build("user", version="v2")
        assert key == "v2:user"

    def test_build_skips_none_args(self):
        """Test that None arguments are skipped."""
        key = CacheKeyBuilder.build("user", 123, None, "active")
        assert key == "v1:user:123:active"

    def test_build_hash_creates_consistent_key(self):
        """Test build_hash creates consistent key from data."""
        key1 = CacheKeyBuilder.build_hash("query", {"page": 1, "sort": "name"})
        key2 = CacheKeyBuilder.build_hash("query", {"page": 1, "sort": "name"})
        assert key1 == key2

    def test_build_hash_different_data_different_key(self):
        """Test build_hash creates different keys for different data."""
        key1 = CacheKeyBuilder.build_hash("query", {"page": 1})
        key2 = CacheKeyBuilder.build_hash("query", {"page": 2})
        assert key1 != key2

    def test_build_hash_format(self):
        """Test build_hash key format includes hash."""
        data = "test_data"
        expected_hash = hashlib.md5(str(data).encode()).hexdigest()[:12]
        key = CacheKeyBuilder.build_hash("prefix", data)
        assert expected_hash in key

    def test_separator_constant(self):
        """Test the separator constant."""
        assert CacheKeyBuilder.SEPARATOR == ":"

    def test_version_constant(self):
        """Test the version constant."""
        assert CacheKeyBuilder.VERSION == "v1"


class TestGetCacheConfig:
    """Test get_cache_config function."""

    @patch.dict("os.environ", {"REDIS_PASSWORD": "testpass", "REDIS_CACHE_HOST": "redis-test", "REDIS_CACHE_PORT": "6380"})
    def test_returns_dict_with_all_backends(self):
        """Test that config contains all cache backends."""
        config = get_cache_config()
        assert "default" in config
        assert "sessions" in config
        assert "locks" in config
        assert "throttle" in config
        assert "local" in config

    @patch.dict("os.environ", {"REDIS_PASSWORD": "testpass", "REDIS_CACHE_HOST": "redis-test", "REDIS_CACHE_PORT": "6380"})
    def test_default_backend_config(self):
        """Test default backend configuration."""
        config = get_cache_config()
        default = config["default"]
        assert default["BACKEND"] == "django_redis.cache.RedisCache"
        assert "redis-test" in default["LOCATION"]
        assert "6380" in default["LOCATION"]
        assert "testpass" in default["LOCATION"]
        assert default["KEY_PREFIX"] == "aureon"
        assert default["TIMEOUT"] == CacheTimeout.MEDIUM

    @patch.dict("os.environ", {"REDIS_PASSWORD": "", "REDIS_CACHE_HOST": "redis-cache", "REDIS_CACHE_PORT": "6379"})
    def test_default_values(self):
        """Test default environment values."""
        config = get_cache_config()
        assert "redis-cache" in config["default"]["LOCATION"]
        assert "6379" in config["default"]["LOCATION"]

    @patch.dict("os.environ", {"REDIS_PASSWORD": "p", "REDIS_CACHE_HOST": "h", "REDIS_CACHE_PORT": "6379"})
    def test_sessions_backend_config(self):
        """Test sessions backend uses separate database."""
        config = get_cache_config()
        sessions = config["sessions"]
        assert sessions["KEY_PREFIX"] == "aureon_session"
        assert sessions["TIMEOUT"] == CacheTimeout.SESSION
        assert "/1" in sessions["LOCATION"]

    @patch.dict("os.environ", {"REDIS_PASSWORD": "p", "REDIS_CACHE_HOST": "h", "REDIS_CACHE_PORT": "6379"})
    def test_locks_backend_config(self):
        """Test locks backend configuration."""
        config = get_cache_config()
        locks = config["locks"]
        assert locks["KEY_PREFIX"] == "aureon_lock"
        assert locks["TIMEOUT"] == 300
        assert "/2" in locks["LOCATION"]

    @patch.dict("os.environ", {"REDIS_PASSWORD": "p", "REDIS_CACHE_HOST": "h", "REDIS_CACHE_PORT": "6379"})
    def test_throttle_backend_config(self):
        """Test throttle backend configuration."""
        config = get_cache_config()
        throttle = config["throttle"]
        assert throttle["KEY_PREFIX"] == "aureon_throttle"
        assert throttle["TIMEOUT"] == CacheTimeout.LONG
        assert "/3" in throttle["LOCATION"]

    @patch.dict("os.environ", {"REDIS_PASSWORD": "p", "REDIS_CACHE_HOST": "h", "REDIS_CACHE_PORT": "6379"})
    def test_local_backend_config(self):
        """Test local memory backend configuration."""
        config = get_cache_config()
        local = config["local"]
        assert local["BACKEND"] == "django.core.cache.backends.locmem.LocMemCache"
        assert local["LOCATION"] == "aureon-local-cache"
        assert local["OPTIONS"]["MAX_ENTRIES"] == 10000
        assert local["OPTIONS"]["CULL_FREQUENCY"] == 4
        assert local["TIMEOUT"] == CacheTimeout.SHORT


class TestGetRedisClusterConfig:
    """Test get_redis_cluster_config function."""

    @patch.dict("os.environ", {"REDIS_PASSWORD": "clusterpass"})
    def test_returns_cluster_config(self):
        """Test that cluster config is returned."""
        config = get_redis_cluster_config()
        assert "startup_nodes" in config
        assert len(config["startup_nodes"]) == 3
        assert config["password"] == "clusterpass"

    @patch.dict("os.environ", {"REDIS_PASSWORD": ""})
    def test_cluster_config_empty_password(self):
        """Test cluster config with empty password."""
        config = get_redis_cluster_config()
        assert config["password"] == ""

    @patch.dict("os.environ", {"REDIS_PASSWORD": "pass"})
    def test_cluster_config_options(self):
        """Test cluster config options."""
        config = get_redis_cluster_config()
        assert config["skip_full_coverage_check"] is True
        assert config["read_from_replicas"] is True
        assert config["reinitialize_steps"] == 10
        assert config["cluster_error_retry_attempts"] == 3


class TestGetRedisSentinelConfig:
    """Test get_redis_sentinel_config function."""

    @patch.dict("os.environ", {"REDIS_PASSWORD": "sentinelpass"})
    def test_returns_sentinel_config(self):
        """Test that sentinel config is returned."""
        config = get_redis_sentinel_config()
        assert "sentinels" in config
        assert len(config["sentinels"]) == 3
        assert config["master_name"] == "aureon-master"
        assert config["password"] == "sentinelpass"

    @patch.dict("os.environ", {"REDIS_PASSWORD": "p1", "REDIS_SENTINEL_PASSWORD": "sp1"})
    def test_sentinel_separate_password(self):
        """Test sentinel config with separate sentinel password."""
        config = get_redis_sentinel_config()
        assert config["password"] == "p1"
        assert config["sentinel_kwargs"]["password"] == "sp1"

    @patch.dict("os.environ", {"REDIS_PASSWORD": "p1"}, clear=False)
    def test_sentinel_fallback_password(self):
        """Test sentinel password falls back to redis password."""
        import os
        # Ensure REDIS_SENTINEL_PASSWORD is not set
        os.environ.pop("REDIS_SENTINEL_PASSWORD", None)
        config = get_redis_sentinel_config()
        assert config["sentinel_kwargs"]["password"] == "p1"

    @patch.dict("os.environ", {"REDIS_PASSWORD": "p"})
    def test_sentinel_config_options(self):
        """Test sentinel config options."""
        config = get_redis_sentinel_config()
        assert config["socket_timeout"] == 5
        assert config["db"] == 0


class TestCacheInvalidator:
    """Test CacheInvalidator class."""

    def test_get_cache_returns_cache_instance(self):
        """Test that get_cache returns a valid cache instance."""
        cache = CacheInvalidator.get_cache()
        assert cache is not None

    def test_get_cache_with_alias(self):
        """Test get_cache with specific alias."""
        cache = CacheInvalidator.get_cache(CACHE_ALIAS_DEFAULT)
        assert cache is not None

    @patch.object(CacheInvalidator, "get_cache")
    def test_invalidate_user(self, mock_get_cache):
        """Test invalidating user cache."""
        mock_cache = MagicMock()
        mock_get_cache.return_value = mock_cache

        CacheInvalidator.invalidate_user(123)
        assert mock_cache.delete_pattern.call_count == 3

    @patch.object(CacheInvalidator, "get_cache")
    def test_invalidate_contract(self, mock_get_cache):
        """Test invalidating contract cache."""
        mock_cache = MagicMock()
        mock_get_cache.return_value = mock_cache

        CacheInvalidator.invalidate_contract(456)
        mock_cache.delete.assert_called_once()

    @patch.object(CacheInvalidator, "get_cache")
    def test_invalidate_invoice(self, mock_get_cache):
        """Test invalidating invoice cache."""
        mock_cache = MagicMock()
        mock_get_cache.return_value = mock_cache

        CacheInvalidator.invalidate_invoice(789)
        mock_cache.delete.assert_called_once()

    @patch.object(CacheInvalidator, "get_cache")
    def test_invalidate_client(self, mock_get_cache):
        """Test invalidating client cache."""
        mock_cache = MagicMock()
        mock_get_cache.return_value = mock_cache

        CacheInvalidator.invalidate_client(101)
        assert mock_cache.delete_pattern.call_count == 3

    @patch.object(CacheInvalidator, "get_cache")
    def test_invalidate_analytics(self, mock_get_cache):
        """Test invalidating analytics cache."""
        mock_cache = MagicMock()
        mock_get_cache.return_value = mock_cache

        CacheInvalidator.invalidate_analytics()
        mock_cache.delete_pattern.assert_called_once()

    @patch.object(CacheInvalidator, "get_cache")
    def test_invalidate_all(self, mock_get_cache):
        """Test invalidating all cache entries."""
        mock_cache = MagicMock()
        mock_get_cache.return_value = mock_cache

        CacheInvalidator.invalidate_all()
        mock_cache.clear.assert_called_once()


class TestCachedDecorator:
    """Test the @cached decorator."""

    @patch("config.cache.caches")
    def test_caches_function_result(self, mock_caches):
        """Test that function result is cached."""
        mock_cache = MagicMock()
        mock_cache.get.return_value = None  # First call: cache miss
        mock_caches.__getitem__.return_value = mock_cache

        call_count = 0

        @cached(timeout=300, cache_alias="default")
        def my_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = my_func(5)
        assert result1 == 10
        assert call_count == 1
        mock_cache.set.assert_called_once()

    @patch("config.cache.caches")
    def test_cache_hit_returns_cached_value(self, mock_caches):
        """Test that cache hit returns cached value without calling function."""
        mock_cache = MagicMock()
        mock_cache.get.return_value = 20  # Cache hit
        mock_caches.__getitem__.return_value = mock_cache

        call_count = 0

        @cached(timeout=300, cache_alias="default")
        def my_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result = my_func(5)
        assert result == 20
        assert call_count == 0  # Function not called
        mock_cache.set.assert_not_called()

    @patch("config.cache.caches")
    def test_different_args_cached_separately(self, mock_caches):
        """Test that different arguments result in separate cache entries."""
        mock_cache = MagicMock()
        mock_cache.get.return_value = None  # Cache miss
        mock_caches.__getitem__.return_value = mock_cache

        @cached(timeout=300, cache_alias="default")
        def add(a, b):
            return a + b

        result1 = add(1, 2)
        result2 = add(3, 4)
        assert result1 == 3
        assert result2 == 7
        # Two different cache keys set
        assert mock_cache.set.call_count == 2

    @patch("config.cache.caches")
    def test_custom_key_prefix(self, mock_caches):
        """Test using a custom key prefix."""
        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        mock_caches.__getitem__.return_value = mock_cache

        @cached(timeout=300, key_prefix="custom_prefix", cache_alias="default")
        def my_func():
            return "result"

        result = my_func()
        assert result == "result"
        # Verify the cache key uses the custom prefix
        cache_key = mock_cache.set.call_args[0][0]
        assert "custom_prefix" in cache_key

    def test_invalidate_method_exists(self):
        """Test that the decorated function has an invalidate method."""
        @cached(timeout=300, cache_alias="default")
        def my_func(x):
            return x

        assert hasattr(my_func, "invalidate")
        assert callable(my_func.invalidate)

    @patch("config.cache.caches")
    def test_invalidate_clears_cache(self, mock_caches):
        """Test that calling invalidate clears the cache for those args."""
        mock_cache = MagicMock()
        mock_caches.__getitem__.return_value = mock_cache

        @cached(timeout=300, cache_alias="default")
        def counter_func(x):
            return x

        counter_func.invalidate(42)
        mock_cache.delete.assert_called_once()

    def test_preserves_function_name(self):
        """Test that the decorator preserves the function name."""
        @cached(timeout=300, cache_alias="default")
        def my_special_function():
            return "test"

        assert my_special_function.__name__ == "my_special_function"

    @patch("config.cache.caches")
    def test_cached_with_kwargs(self, mock_caches):
        """Test cached decorator with keyword arguments."""
        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        mock_caches.__getitem__.return_value = mock_cache

        @cached(timeout=300, cache_alias="default")
        def func_with_kwargs(a, b=10):
            return a + b

        result = func_with_kwargs(5, b=20)
        assert result == 25

    @patch("config.cache.caches")
    def test_cached_with_custom_version(self, mock_caches):
        """Test cached decorator with custom version."""
        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        mock_caches.__getitem__.return_value = mock_cache

        @cached(timeout=300, version="v2", cache_alias="default")
        def versioned_func():
            return "v2_result"

        result = versioned_func()
        assert result == "v2_result"
        # Verify v2 in cache key
        cache_key = mock_cache.set.call_args[0][0]
        assert "v2" in cache_key


class TestMultiLayerCachedDecorator:
    """Test the @multi_layer_cached decorator."""

    @patch("config.cache.caches")
    def test_multi_layer_caches_result(self, mock_caches):
        """Test that multi-layer caching works."""
        mock_local = MagicMock()
        mock_redis = MagicMock()
        mock_local.get.return_value = None
        mock_redis.get.return_value = None

        def cache_side_effect(alias):
            if alias == CACHE_ALIAS_LOCAL:
                return mock_local
            return mock_redis

        mock_caches.__getitem__.side_effect = cache_side_effect

        @multi_layer_cached(timeout=300, local_timeout=60)
        def my_func():
            return "multi_cached"

        result = my_func()
        assert result == "multi_cached"
        # Both caches should be populated
        mock_redis.set.assert_called_once()
        mock_local.set.assert_called_once()

    def test_multi_layer_preserves_function_name(self):
        """Test that multi_layer_cached preserves function name."""
        @multi_layer_cached(timeout=300)
        def my_func():
            return "test"

        assert my_func.__name__ == "my_func"

    @patch("config.cache.caches")
    def test_multi_layer_with_args(self, mock_caches):
        """Test multi-layer caching with arguments."""
        mock_local = MagicMock()
        mock_redis = MagicMock()
        mock_local.get.return_value = None
        mock_redis.get.return_value = None

        def cache_side_effect(alias):
            if alias == CACHE_ALIAS_LOCAL:
                return mock_local
            return mock_redis

        mock_caches.__getitem__.side_effect = cache_side_effect

        @multi_layer_cached(timeout=300, key_prefix="ml_test")
        def multiply(a, b):
            return a * b

        result = multiply(3, 4)
        assert result == 12

    @patch("config.cache.caches")
    def test_multi_layer_l1_hit(self, mock_caches):
        """Test that L1 cache hit returns without checking L2."""
        mock_local = MagicMock()
        mock_redis = MagicMock()
        mock_local.get.return_value = "cached_result"  # L1 hit

        def cache_side_effect(alias):
            if alias == CACHE_ALIAS_LOCAL:
                return mock_local
            return mock_redis

        mock_caches.__getitem__.side_effect = cache_side_effect

        call_count = 0

        @multi_layer_cached(timeout=300, local_timeout=60)
        def tracked_func():
            nonlocal call_count
            call_count += 1
            return "result"

        result = tracked_func()
        assert result == "cached_result"
        assert call_count == 0  # Function not called
        mock_redis.get.assert_not_called()  # L2 not checked

    @patch("config.cache.caches")
    def test_multi_layer_l2_hit_populates_l1(self, mock_caches):
        """Test that L2 hit populates L1 cache."""
        mock_local = MagicMock()
        mock_redis = MagicMock()
        mock_local.get.return_value = None  # L1 miss
        mock_redis.get.return_value = "l2_cached"  # L2 hit

        def cache_side_effect(alias):
            if alias == CACHE_ALIAS_LOCAL:
                return mock_local
            return mock_redis

        mock_caches.__getitem__.side_effect = cache_side_effect

        @multi_layer_cached(timeout=300, local_timeout=60)
        def my_func():
            return "fresh"

        result = my_func()
        assert result == "l2_cached"
        # L1 should be populated
        mock_local.set.assert_called_once()


class TestDistributedLock:
    """Test the DistributedLock class."""

    def test_init(self):
        """Test lock initialization."""
        lock = DistributedLock("test_lock", timeout=60, blocking=True)
        assert lock.lock_name == "test_lock"
        assert lock.timeout == 60
        assert lock.blocking is True
        assert lock._lock is None

    def test_init_defaults(self):
        """Test lock initialization with defaults."""
        lock = DistributedLock("test_lock")
        assert lock.timeout == 30
        assert lock.blocking is True
        assert lock.blocking_timeout is None

    def test_key_property(self):
        """Test that key property builds correct cache key."""
        lock = DistributedLock("my_resource")
        key = lock.key
        assert "lock" in key
        assert "my_resource" in key

    @patch("config.cache.caches")
    def test_acquire_success(self, mock_caches):
        """Test successful lock acquisition."""
        mock_client = MagicMock()
        mock_redis_lock = MagicMock()
        mock_redis_lock.acquire.return_value = True
        mock_client.lock.return_value = mock_redis_lock
        mock_cache = MagicMock()
        mock_cache.client.get_client.return_value = mock_client
        mock_caches.__getitem__.return_value = mock_cache

        lock = DistributedLock("test_lock")
        result = lock.acquire()
        assert result is True

    @patch("config.cache.caches")
    def test_release(self, mock_caches):
        """Test lock release."""
        mock_redis_lock = MagicMock()
        lock = DistributedLock("test_lock")
        lock._lock = mock_redis_lock

        lock.release()
        mock_redis_lock.release.assert_called_once()

    def test_release_without_lock(self):
        """Test release when no lock was acquired."""
        lock = DistributedLock("test_lock")
        lock._lock = None
        # Should not raise
        lock.release()

    @patch("config.cache.caches")
    def test_release_handles_exception(self, mock_caches):
        """Test that release handles exceptions gracefully."""
        mock_redis_lock = MagicMock()
        mock_redis_lock.release.side_effect = Exception("Redis error")
        lock = DistributedLock("test_lock")
        lock._lock = mock_redis_lock

        # Should not raise
        lock.release()

    @patch("config.cache.caches")
    def test_context_manager_success(self, mock_caches):
        """Test lock as context manager with successful acquire."""
        mock_client = MagicMock()
        mock_redis_lock = MagicMock()
        mock_redis_lock.acquire.return_value = True
        mock_client.lock.return_value = mock_redis_lock
        mock_cache = MagicMock()
        mock_cache.client.get_client.return_value = mock_client
        mock_caches.__getitem__.return_value = mock_cache

        with DistributedLock("test_lock") as lock:
            assert lock is not None

    @patch("config.cache.caches")
    def test_context_manager_failure(self, mock_caches):
        """Test lock as context manager with failed acquire raises RuntimeError."""
        mock_client = MagicMock()
        mock_redis_lock = MagicMock()
        mock_redis_lock.acquire.return_value = False
        mock_client.lock.return_value = mock_redis_lock
        mock_cache = MagicMock()
        mock_cache.client.get_client.return_value = mock_client
        mock_caches.__getitem__.return_value = mock_cache

        with pytest.raises(RuntimeError, match="Could not acquire lock"):
            with DistributedLock("test_lock"):
                pass

    @patch("config.cache.caches")
    def test_context_manager_exit_releases_lock(self, mock_caches):
        """Test that exiting context manager releases the lock."""
        mock_client = MagicMock()
        mock_redis_lock = MagicMock()
        mock_redis_lock.acquire.return_value = True
        mock_client.lock.return_value = mock_redis_lock
        mock_cache = MagicMock()
        mock_cache.client.get_client.return_value = mock_client
        mock_caches.__getitem__.return_value = mock_cache

        with DistributedLock("test_lock"):
            pass
        mock_redis_lock.release.assert_called_once()


class TestWithLockDecorator:
    """Test the @with_lock decorator."""

    @patch("config.cache.DistributedLock")
    def test_with_lock_acquires_and_releases(self, mock_lock_cls):
        """Test that with_lock acquires and releases the lock."""
        mock_lock_instance = MagicMock()
        mock_lock_instance.__enter__ = MagicMock(return_value=mock_lock_instance)
        mock_lock_instance.__exit__ = MagicMock(return_value=False)
        mock_lock_cls.return_value = mock_lock_instance

        @with_lock("test_{0}", timeout=30)
        def my_func(name):
            return f"result_{name}"

        result = my_func("hello")
        assert result == "result_hello"
        mock_lock_cls.assert_called_once_with("test_hello", timeout=30, blocking=True)

    @patch("config.cache.DistributedLock")
    def test_with_lock_preserves_function_name(self, mock_lock_cls):
        """Test that with_lock preserves function name."""
        mock_lock_instance = MagicMock()
        mock_lock_instance.__enter__ = MagicMock(return_value=mock_lock_instance)
        mock_lock_instance.__exit__ = MagicMock(return_value=False)
        mock_lock_cls.return_value = mock_lock_instance

        @with_lock("lock_name", timeout=30)
        def my_named_func():
            return "test"

        assert my_named_func.__name__ == "my_named_func"


class TestCacheWarmer:
    """Test the CacheWarmer class."""

    @patch("config.cache.caches")
    def test_warm_user_cache(self, mock_caches):
        """Test warming user cache."""
        mock_cache = MagicMock()
        mock_caches.__getitem__.return_value = mock_cache

        mock_services = MagicMock()
        mock_services.get_user_permissions.return_value = ["read", "write"]

        with patch("apps.accounts.models.User") as mock_user_model, \
             patch.dict("sys.modules", {"apps.accounts.services": mock_services}):
            mock_user = MagicMock()
            mock_user.id = 1
            mock_user.email = "test@test.com"
            mock_user.get_full_name.return_value = "Test User"
            mock_user_model.objects.select_related.return_value.get.return_value = mock_user

            CacheWarmer.warm_user_cache(1)
            assert mock_cache.set.call_count == 2

    @patch("config.cache.caches")
    def test_warm_user_cache_nonexistent_user(self, mock_caches):
        """Test warming cache for nonexistent user."""
        mock_cache = MagicMock()
        mock_caches.__getitem__.return_value = mock_cache

        mock_services = MagicMock()

        with patch("apps.accounts.models.User") as mock_user_model, \
             patch.dict("sys.modules", {"apps.accounts.services": mock_services}):
            mock_user_model.DoesNotExist = Exception
            mock_user_model.objects.select_related.return_value.get.side_effect = mock_user_model.DoesNotExist

            # Should not raise
            CacheWarmer.warm_user_cache(999)
            mock_cache.set.assert_not_called()

    @patch("config.cache.caches")
    def test_warm_analytics_cache(self, mock_caches):
        """Test warming analytics cache."""
        mock_cache = MagicMock()
        mock_caches.__getitem__.return_value = mock_cache

        with patch("apps.analytics.services.compute_dashboard_stats", create=True) as mock_stats:
            mock_stats.return_value = {"revenue": 1000}
            CacheWarmer.warm_analytics_cache()
            mock_cache.set.assert_called_once()


class TestCheckCacheHealth:
    """Test the check_cache_health function."""

    @patch("config.cache.caches")
    def test_all_healthy(self, mock_caches):
        """Test health check when all caches are healthy."""
        mock_cache = MagicMock()
        mock_cache.get.return_value = "ok"
        mock_caches.__getitem__.return_value = mock_cache

        results = check_cache_health()
        assert "default" in results
        assert "sessions" in results
        assert "locks" in results
        assert "throttle" in results
        assert "local" in results

        for alias in ["default", "sessions", "locks", "throttle", "local"]:
            assert results[alias]["status"] == "healthy"

    @patch("config.cache.caches")
    def test_cache_unhealthy_on_exception(self, mock_caches):
        """Test health check marks cache as unhealthy on exception."""
        mock_cache = MagicMock()
        mock_cache.set.side_effect = Exception("Connection refused")
        mock_caches.__getitem__.return_value = mock_cache

        results = check_cache_health()
        for alias in ["default", "sessions", "locks", "throttle"]:
            assert results[alias]["status"] == "unhealthy"
            assert "Connection refused" in results[alias]["error"]

    @patch("config.cache.caches")
    def test_cache_degraded_on_mismatch(self, mock_caches):
        """Test health check marks cache as degraded on value mismatch."""
        mock_cache = MagicMock()
        mock_cache.get.return_value = "wrong_value"
        mock_caches.__getitem__.return_value = mock_cache

        results = check_cache_health()
        assert results["default"]["status"] == "degraded"

    @patch("config.cache.caches")
    def test_local_cache_unhealthy(self, mock_caches):
        """Test local cache health check failure."""
        # Redis caches succeed, local fails
        def side_effect(key):
            cache = MagicMock()
            if key == CACHE_ALIAS_LOCAL:
                cache.set.side_effect = Exception("locmem error")
            else:
                cache.get.return_value = "ok"
            return cache

        mock_caches.__getitem__.side_effect = side_effect
        results = check_cache_health()
        assert results["local"]["status"] == "unhealthy"

    @patch("config.cache.caches")
    def test_health_check_result_types(self, mock_caches):
        """Test that health check results have correct types."""
        mock_cache = MagicMock()
        mock_cache.get.return_value = "ok"
        mock_caches.__getitem__.return_value = mock_cache

        results = check_cache_health()
        for alias, info in results.items():
            assert "status" in info
            assert "type" in info
