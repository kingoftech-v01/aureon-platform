"""
Cache configuration for Aureon SaaS Platform.
Multi-layer caching strategy optimized for 1M users.

Features:
- Multi-layer caching (L1: Local memory, L2: Redis cluster)
- Redis clustering configuration
- Cache invalidation patterns
- Cache key prefixing and versioning
- Automatic cache warming strategies
"""
import os
import hashlib
from functools import wraps
from typing import Any, Callable, Optional, Union
from datetime import timedelta

from django.core.cache import caches
from django.conf import settings

# ====================
# CACHE ALIASES
# ====================
CACHE_ALIAS_DEFAULT = 'default'
CACHE_ALIAS_SESSIONS = 'sessions'
CACHE_ALIAS_LOCKS = 'locks'
CACHE_ALIAS_THROTTLE = 'throttle'
CACHE_ALIAS_LOCAL = 'local'

# ====================
# CACHE TIMEOUTS (seconds)
# ====================
class CacheTimeout:
    """Standard cache timeout values."""
    INSTANT = 30  # 30 seconds
    SHORT = 300  # 5 minutes
    MEDIUM = 900  # 15 minutes
    LONG = 3600  # 1 hour
    EXTENDED = 14400  # 4 hours
    DAY = 86400  # 24 hours
    WEEK = 604800  # 7 days
    MONTH = 2592000  # 30 days

    # Specific use cases
    SESSION = 1209600  # 14 days
    API_RESPONSE = 60  # 1 minute
    USER_PROFILE = 900  # 15 minutes
    PERMISSIONS = 300  # 5 minutes
    SETTINGS = 3600  # 1 hour
    ANALYTICS = 1800  # 30 minutes
    INVOICE = 600  # 10 minutes
    CONTRACT = 600  # 10 minutes


# ====================
# CACHE KEY PREFIXES
# ====================
class CachePrefix:
    """Cache key prefixes for different data types."""
    USER = 'user'
    SESSION = 'session'
    CLIENT = 'client'
    CONTRACT = 'contract'
    INVOICE = 'invoice'
    PAYMENT = 'payment'
    DOCUMENT = 'document'
    NOTIFICATION = 'notification'
    ANALYTICS = 'analytics'
    SETTINGS = 'settings'
    PERMISSIONS = 'perms'
    RATE_LIMIT = 'rl'
    LOCK = 'lock'
    THROTTLE = 'throttle'
    API = 'api'


# ====================
# CACHE KEY BUILDER
# ====================
class CacheKeyBuilder:
    """
    Build consistent cache keys with versioning and namespacing.
    """
    VERSION = 'v1'
    SEPARATOR = ':'

    @classmethod
    def build(
        cls,
        prefix: str,
        *args,
        version: Optional[str] = None,
    ) -> str:
        """
        Build a cache key with consistent formatting.

        Args:
            prefix: Key prefix from CachePrefix
            *args: Additional key components
            version: Optional version override

        Returns:
            Formatted cache key string
        """
        parts = [version or cls.VERSION]

        parts.append(prefix)
        parts.extend(str(arg) for arg in args if arg is not None)

        return cls.SEPARATOR.join(parts)

    @classmethod
    def build_hash(cls, prefix: str, data: Any, **kwargs) -> str:
        """
        Build a cache key with hashed data component.
        Useful for complex query parameters.
        """
        data_hash = hashlib.md5(str(data).encode()).hexdigest()[:12]
        return cls.build(prefix, data_hash, **kwargs)


# ====================
# CACHE CONFIGURATION
# ====================
def get_cache_config() -> dict:
    """
    Get the complete cache configuration for Django settings.
    Optimized for Redis cluster with multi-layer caching.
    """
    redis_password = os.environ.get('REDIS_PASSWORD', '')
    redis_cache_host = os.environ.get('REDIS_CACHE_HOST', 'redis-cache')
    redis_cache_port = int(os.environ.get('REDIS_CACHE_PORT', 6379))

    # Base Redis options
    base_redis_options = {
        'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        'PASSWORD': redis_password,
        'SOCKET_CONNECT_TIMEOUT': 5,
        'SOCKET_TIMEOUT': 5,
        'RETRY_ON_TIMEOUT': True,
        'CONNECTION_POOL_KWARGS': {
            'max_connections': 100,
            'retry_on_timeout': True,
            'socket_keepalive': True,
            'socket_keepalive_options': {},
        },
        'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
    }

    return {
        # Default cache - General purpose caching
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': f'redis://:{redis_password}@{redis_cache_host}:{redis_cache_port}/0',
            'OPTIONS': {
                **base_redis_options,
                'CONNECTION_POOL_CLASS': 'redis.connection.BlockingConnectionPool',
                'CONNECTION_POOL_KWARGS': {
                    **base_redis_options['CONNECTION_POOL_KWARGS'],
                    'max_connections': 200,
                    'timeout': 20,
                },
            },
            'KEY_PREFIX': 'aureon',
            'TIMEOUT': CacheTimeout.MEDIUM,
        },

        # Session cache - User sessions
        'sessions': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': f'redis://:{redis_password}@{redis_cache_host}:{redis_cache_port}/1',
            'OPTIONS': {
                **base_redis_options,
                'CONNECTION_POOL_CLASS': 'redis.connection.BlockingConnectionPool',
                'CONNECTION_POOL_KWARGS': {
                    **base_redis_options['CONNECTION_POOL_KWARGS'],
                    'max_connections': 150,
                    'timeout': 20,
                },
            },
            'KEY_PREFIX': 'aureon_session',
            'TIMEOUT': CacheTimeout.SESSION,
        },

        # Lock cache - Distributed locking
        'locks': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': f'redis://:{redis_password}@{redis_cache_host}:{redis_cache_port}/2',
            'OPTIONS': {
                **base_redis_options,
                'CONNECTION_POOL_CLASS': 'redis.connection.BlockingConnectionPool',
                'CONNECTION_POOL_KWARGS': {
                    **base_redis_options['CONNECTION_POOL_KWARGS'],
                    'max_connections': 50,
                },
            },
            'KEY_PREFIX': 'aureon_lock',
            'TIMEOUT': 300,  # 5 minutes max lock time
        },

        # Throttle cache - Rate limiting
        'throttle': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': f'redis://:{redis_password}@{redis_cache_host}:{redis_cache_port}/3',
            'OPTIONS': {
                **base_redis_options,
                'CONNECTION_POOL_KWARGS': {
                    **base_redis_options['CONNECTION_POOL_KWARGS'],
                    'max_connections': 100,
                },
            },
            'KEY_PREFIX': 'aureon_throttle',
            'TIMEOUT': CacheTimeout.LONG,
        },

        # Local memory cache - L1 cache layer
        'local': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'aureon-local-cache',
            'OPTIONS': {
                'MAX_ENTRIES': 10000,
                'CULL_FREQUENCY': 4,
            },
            'TIMEOUT': CacheTimeout.SHORT,
        },
    }


# ====================
# REDIS CLUSTER CONFIGURATION
# ====================
def get_redis_cluster_config() -> dict:
    """
    Get Redis cluster configuration for direct cluster mode.
    Use this when deploying with Redis Cluster (not Sentinel).
    """
    redis_password = os.environ.get('REDIS_PASSWORD', '')

    return {
        'startup_nodes': [
            {'host': 'redis-cache', 'port': 6379},
            {'host': 'redis-queue', 'port': 6379},
            {'host': 'redis-result', 'port': 6379},
        ],
        'password': redis_password,
        'skip_full_coverage_check': True,
        'read_from_replicas': True,
        'reinitialize_steps': 10,
        'cluster_error_retry_attempts': 3,
    }


def get_redis_sentinel_config() -> dict:
    """
    Get Redis Sentinel configuration for high availability.
    Use this when deploying with Redis Sentinel.
    """
    redis_password = os.environ.get('REDIS_PASSWORD', '')
    sentinel_password = os.environ.get('REDIS_SENTINEL_PASSWORD', redis_password)

    return {
        'sentinels': [
            ('redis-sentinel-1', 26379),
            ('redis-sentinel-2', 26379),
            ('redis-sentinel-3', 26379),
        ],
        'master_name': 'aureon-master',
        'socket_timeout': 5,
        'password': redis_password,
        'sentinel_kwargs': {
            'password': sentinel_password,
        },
        'db': 0,
    }


# ====================
# CACHE INVALIDATION PATTERNS
# ====================
class CacheInvalidator:
    """
    Centralized cache invalidation patterns.
    Ensures consistent cache invalidation across the application.
    """

    @staticmethod
    def get_cache(alias: str = CACHE_ALIAS_DEFAULT):
        """Get cache instance by alias."""
        return caches[alias]

    @classmethod
    def invalidate_user(cls, user_id: int) -> None:
        """Invalidate all cache entries for a user."""
        cache = cls.get_cache()
        patterns = [
            CacheKeyBuilder.build(CachePrefix.USER, user_id),
            CacheKeyBuilder.build(CachePrefix.PERMISSIONS, user_id),
            CacheKeyBuilder.build(CachePrefix.SESSION, user_id),
        ]
        for pattern in patterns:
            cache.delete_pattern(f'{pattern}*')

    @classmethod
    def invalidate_contract(cls, contract_id: int) -> None:
        """Invalidate cache entries related to a contract."""
        cache = cls.get_cache()
        cache.delete(CacheKeyBuilder.build(CachePrefix.CONTRACT, contract_id))

    @classmethod
    def invalidate_invoice(cls, invoice_id: int) -> None:
        """Invalidate cache entries related to an invoice."""
        cache = cls.get_cache()
        cache.delete(CacheKeyBuilder.build(CachePrefix.INVOICE, invoice_id))

    @classmethod
    def invalidate_client(cls, client_id: int) -> None:
        """Invalidate cache entries related to a client."""
        cache = cls.get_cache()
        patterns = [
            CacheKeyBuilder.build(CachePrefix.CLIENT, client_id),
            CacheKeyBuilder.build(CachePrefix.CONTRACT, 'client', client_id),
            CacheKeyBuilder.build(CachePrefix.INVOICE, 'client', client_id),
        ]
        for pattern in patterns:
            cache.delete_pattern(f'{pattern}*')

    @classmethod
    def invalidate_analytics(cls) -> None:
        """Invalidate analytics cache entries."""
        cache = cls.get_cache()
        pattern = CacheKeyBuilder.build(CachePrefix.ANALYTICS)
        cache.delete_pattern(f'{pattern}*')

    @classmethod
    def invalidate_all(cls) -> None:
        """Invalidate all cache entries (use with caution)."""
        cache = cls.get_cache()
        cache.clear()


# ====================
# CACHE DECORATORS
# ====================
def cached(
    timeout: int = CacheTimeout.MEDIUM,
    key_prefix: str = '',
    cache_alias: str = CACHE_ALIAS_DEFAULT,
    version: Optional[str] = None,
) -> Callable:
    """
    Decorator for caching function results.

    Args:
        timeout: Cache timeout in seconds
        key_prefix: Prefix for cache key
        cache_alias: Cache backend alias
        version: Optional version for cache key

    Example:
        @cached(timeout=300, key_prefix='user_stats')
        def get_user_stats(user_id):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = caches[cache_alias]

            # Build cache key from function name and arguments
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f'{k}={v}' for k, v in sorted(kwargs.items()))

            cache_key = CacheKeyBuilder.build(
                key_parts[0],
                *key_parts[1:],
                version=version,
            )

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result

        # Add method to invalidate this specific cache
        def invalidate(*args, **kwargs):
            cache = caches[cache_alias]
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f'{k}={v}' for k, v in sorted(kwargs.items()))
            cache_key = CacheKeyBuilder.build(key_parts[0], *key_parts[1:], version=version)
            cache.delete(cache_key)

        wrapper.invalidate = invalidate
        return wrapper

    return decorator


def multi_layer_cached(
    timeout: int = CacheTimeout.MEDIUM,
    local_timeout: int = CacheTimeout.SHORT,
    key_prefix: str = '',
) -> Callable:
    """
    Decorator for multi-layer caching (L1: local, L2: Redis).

    This provides faster access for frequently accessed data by
    using local memory as L1 cache and Redis as L2 cache.

    Args:
        timeout: L2 (Redis) cache timeout
        local_timeout: L1 (local) cache timeout
        key_prefix: Prefix for cache key
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            local_cache = caches[CACHE_ALIAS_LOCAL]
            redis_cache = caches[CACHE_ALIAS_DEFAULT]

            # Build cache key
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(arg) for arg in args)
            cache_key = CacheKeyBuilder.build(key_parts[0], *key_parts[1:])

            # Try L1 cache first
            result = local_cache.get(cache_key)
            if result is not None:
                return result

            # Try L2 cache
            result = redis_cache.get(cache_key)
            if result is not None:
                # Populate L1 cache
                local_cache.set(cache_key, result, local_timeout)
                return result

            # Execute function and cache in both layers
            result = func(*args, **kwargs)
            redis_cache.set(cache_key, result, timeout)
            local_cache.set(cache_key, result, local_timeout)
            return result

        return wrapper

    return decorator


# ====================
# DISTRIBUTED LOCKING
# ====================
class DistributedLock:
    """
    Distributed lock using Redis for cluster-safe operations.
    """

    def __init__(
        self,
        lock_name: str,
        timeout: int = 30,
        blocking: bool = True,
        blocking_timeout: Optional[float] = None,
    ):
        self.lock_name = lock_name
        self.timeout = timeout
        self.blocking = blocking
        self.blocking_timeout = blocking_timeout
        self._lock = None

    @property
    def cache(self):
        return caches[CACHE_ALIAS_LOCKS]

    @property
    def key(self):
        return CacheKeyBuilder.build(CachePrefix.LOCK, self.lock_name)

    def acquire(self) -> bool:
        """Acquire the lock."""
        client = self.cache.client.get_client()
        self._lock = client.lock(
            self.key,
            timeout=self.timeout,
            blocking=self.blocking,
            blocking_timeout=self.blocking_timeout,
        )
        return self._lock.acquire()

    def release(self) -> None:
        """Release the lock."""
        if self._lock:
            try:
                self._lock.release()
            except Exception:
                pass

    def __enter__(self):
        if not self.acquire():
            raise RuntimeError(f"Could not acquire lock: {self.lock_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


def with_lock(
    lock_name: str,
    timeout: int = 30,
    blocking: bool = True,
) -> Callable:
    """
    Decorator for functions that require distributed locking.

    Args:
        lock_name: Name of the lock
        timeout: Lock timeout in seconds
        blocking: Whether to block waiting for lock
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build dynamic lock name if needed
            dynamic_lock = lock_name.format(*args, **kwargs)
            with DistributedLock(dynamic_lock, timeout=timeout, blocking=blocking):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# ====================
# CACHE WARMING
# ====================
class CacheWarmer:
    """
    Cache warming utilities for preloading frequently accessed data.
    """

    @staticmethod
    def warm_user_cache(user_id: int) -> None:
        """Warm cache for a specific user."""
        from apps.accounts.models import User
        from apps.accounts.services import get_user_permissions

        cache = caches[CACHE_ALIAS_DEFAULT]
        try:
            user = User.objects.select_related('profile').get(id=user_id)

            # Cache user data
            cache_key = CacheKeyBuilder.build(CachePrefix.USER, user_id)
            cache.set(cache_key, {
                'id': user.id,
                'email': user.email,
                'name': user.get_full_name(),
            }, CacheTimeout.USER_PROFILE)

            # Cache permissions
            perms_key = CacheKeyBuilder.build(CachePrefix.PERMISSIONS, user_id)
            permissions = get_user_permissions(user)
            cache.set(perms_key, permissions, CacheTimeout.PERMISSIONS)

        except User.DoesNotExist:
            pass

    @staticmethod
    def warm_analytics_cache() -> None:
        """Pre-compute and cache analytics data."""
        from apps.analytics.services import compute_dashboard_stats

        cache = caches[CACHE_ALIAS_DEFAULT]
        stats = compute_dashboard_stats()
        cache_key = CacheKeyBuilder.build(
            CachePrefix.ANALYTICS,
            'dashboard',
        )
        cache.set(cache_key, stats, CacheTimeout.ANALYTICS)


# ====================
# CACHE HEALTH CHECK
# ====================
def check_cache_health() -> dict:
    """
    Check health of all cache backends.
    Returns status dict for each cache.
    """
    results = {}

    for alias in [CACHE_ALIAS_DEFAULT, CACHE_ALIAS_SESSIONS, CACHE_ALIAS_LOCKS, CACHE_ALIAS_THROTTLE]:
        try:
            cache = caches[alias]
            # Try to set and get a value
            test_key = f'health_check_{alias}'
            cache.set(test_key, 'ok', 10)
            value = cache.get(test_key)
            cache.delete(test_key)

            results[alias] = {
                'status': 'healthy' if value == 'ok' else 'degraded',
                'type': 'redis',
            }
        except Exception as e:
            results[alias] = {
                'status': 'unhealthy',
                'type': 'redis',
                'error': str(e),
            }

    # Check local cache
    try:
        local = caches[CACHE_ALIAS_LOCAL]
        local.set('health_check', 'ok', 10)
        value = local.get('health_check')
        results['local'] = {
            'status': 'healthy' if value == 'ok' else 'degraded',
            'type': 'locmem',
        }
    except Exception as e:
        results['local'] = {
            'status': 'unhealthy',
            'type': 'locmem',
            'error': str(e),
        }

    return results
