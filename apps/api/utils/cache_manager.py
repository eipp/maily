"""
Cache Manager for Maily.

This module provides utilities for caching data using Redis,
with support for different cache strategies and TTLs.
"""
import json
import logging
import os
import time
import hashlib
from typing import Dict, Any, Optional, Union, List, Callable, TypeVar, Generic, cast, Tuple
from datetime import datetime, timedelta
from functools import wraps

import redis
from redis.client import Pipeline
from redis.exceptions import RedisError, ConnectionError, TimeoutError
from redis.backoff import ExponentialBackoff
from redis.retry import Retry

logger = logging.getLogger(__name__)

# Redis connection
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", None)
REDIS_SSL = os.environ.get("REDIS_SSL", "false").lower() == "true"

# Redis connection pool settings
REDIS_MAX_CONNECTIONS = int(os.environ.get("REDIS_MAX_CONNECTIONS", "50"))
REDIS_SOCKET_TIMEOUT = float(os.environ.get("REDIS_SOCKET_TIMEOUT", "5.0"))
REDIS_SOCKET_CONNECT_TIMEOUT = float(os.environ.get("REDIS_SOCKET_CONNECT_TIMEOUT", "2.0"))
REDIS_RETRY_ON_TIMEOUT = os.environ.get("REDIS_RETRY_ON_TIMEOUT", "true").lower() == "true"
REDIS_MAX_RETRIES = int(os.environ.get("REDIS_MAX_RETRIES", "3"))
REDIS_RETRY_BACKOFF = float(os.environ.get("REDIS_RETRY_BACKOFF", "0.1"))
REDIS_HEALTH_CHECK_INTERVAL = int(os.environ.get("REDIS_HEALTH_CHECK_INTERVAL", "30"))

# Cache settings
DEFAULT_TTL = int(os.environ.get("CACHE_DEFAULT_TTL", "3600"))  # 1 hour
ANALYTICS_TTL = int(os.environ.get("CACHE_ANALYTICS_TTL", "86400"))  # 24 hours
CAMPAIGN_TTL = int(os.environ.get("CACHE_CAMPAIGN_TTL", "300"))  # 5 minutes
USER_TTL = int(os.environ.get("CACHE_USER_TTL", "1800"))  # 30 minutes
CACHE_ENABLED = os.environ.get("CACHE_ENABLED", "true").lower() == "true"

# Cache compression threshold (compress values larger than this, in bytes)
COMPRESSION_THRESHOLD = int(os.environ.get("CACHE_COMPRESSION_THRESHOLD", "1024"))  # 1KB
COMPRESSION_ENABLED = os.environ.get("CACHE_COMPRESSION_ENABLED", "true").lower() == "true"

# Cache prefixes
ENV_PREFIX = os.environ.get("CACHE_ENV_PREFIX", os.environ.get("NODE_ENV", "dev"))
CACHE_PREFIX = f"maily:{ENV_PREFIX}:"
CAMPAIGN_PREFIX = f"{CACHE_PREFIX}campaign:"
USER_PREFIX = f"{CACHE_PREFIX}user:"
ANALYTICS_PREFIX = f"{CACHE_PREFIX}analytics:"
RATE_LIMIT_PREFIX = f"{CACHE_PREFIX}rate_limit:"

# Cache regions
class CacheRegion:
    """Enum-like class for cache regions."""
    DEFAULT = "default"
    ANALYTICS = "analytics"
    CAMPAIGN = "campaign"
    USER = "user"

# TTL mapping for different cache regions
TTL_MAPPING = {
    CacheRegion.DEFAULT: DEFAULT_TTL,
    CacheRegion.ANALYTICS: ANALYTICS_TTL,
    CacheRegion.CAMPAIGN: CAMPAIGN_TTL,
    CacheRegion.USER: USER_TTL,
}

# Type variable for generic return type
T = TypeVar('T')

class CacheManager:
    """
    Manager for Redis caching with advanced features.

    Features:
    - Different cache regions with different TTLs
    - Automatic serialization/deserialization of complex objects
    - Cache invalidation by prefix
    - Rate limiting
    - Cache statistics
    - Connection pooling and retry logic
    - Optional compression for large values
    """

    _instance = None
    _redis_client = None
    _last_connection_attempt = 0
    _connection_backoff = 5  # seconds

    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(CacheManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the cache manager."""
        if self._initialized:
            return

        self._initialized = True
        self.redis = self._create_redis_client()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "errors": 0,
            "timeouts": 0,
            "connection_errors": 0,
        }
        self.cache_enabled = CACHE_ENABLED
        self.compression_enabled = COMPRESSION_ENABLED
        self.compression_threshold = COMPRESSION_THRESHOLD

        if not self.cache_enabled:
            logger.warning("Cache is disabled. All cache operations will be no-ops.")

        logger.info(
            f"Cache initialized with prefix '{CACHE_PREFIX}'. "
            f"Compression: {'enabled' if self.compression_enabled else 'disabled'}. "
            f"Enabled: {'yes' if self.cache_enabled else 'no'}"
        )

    def _create_redis_client(self) -> redis.Redis:
        """Create a Redis client with connection pooling and retry logic."""
        if CacheManager._redis_client is not None:
            return CacheManager._redis_client

        # Implement connection attempt throttling
        current_time = time.time()
        if (current_time - CacheManager._last_connection_attempt) < CacheManager._connection_backoff:
            logger.warning(f"Redis connection attempt throttled. Returning dummy client.")
            return DummyRedis()

        CacheManager._last_connection_attempt = current_time

        try:
            # Configure retry logic
            retry = Retry(
                ExponentialBackoff(cap=REDIS_RETRY_BACKOFF),
                REDIS_MAX_RETRIES
            )

            # Create the client with optimized connection pool
            client = redis.from_url(
                REDIS_URL,
                password=REDIS_PASSWORD,
                ssl=REDIS_SSL,
                socket_timeout=REDIS_SOCKET_TIMEOUT,
                socket_connect_timeout=REDIS_SOCKET_CONNECT_TIMEOUT,
                retry_on_timeout=REDIS_RETRY_ON_TIMEOUT,
                retry=retry,
                max_connections=REDIS_MAX_CONNECTIONS,
                health_check_interval=REDIS_HEALTH_CHECK_INTERVAL,
                decode_responses=True,
            )

            # Test the connection
            client.ping()

            logger.info(
                f"Connected to Redis at {self._mask_redis_url(REDIS_URL)} "
                f"with pool size {REDIS_MAX_CONNECTIONS}, "
                f"timeout {REDIS_SOCKET_TIMEOUT}s"
            )

            CacheManager._redis_client = client
            return client

        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            self.stats["connection_errors"] += 1
            return DummyRedis()
        except RedisError as e:
            logger.error(f"Redis error during initialization: {str(e)}")
            self.stats["errors"] += 1
            return DummyRedis()
        except Exception as e:
            logger.error(f"Unexpected error creating Redis client: {str(e)}", exc_info=True)
            self.stats["errors"] += 1
            return DummyRedis()

    def _mask_redis_url(self, url: str) -> str:
        """Mask sensitive information in Redis URL."""
        if "@" not in url:
            return url

        parts = url.split("@")
        auth_part = parts[0]

        if ":" in auth_part and "//" in auth_part:
            protocol = auth_part.split("//")[0] + "//"
            auth = auth_part.split("//")[1]
            if ":" in auth:
                username = auth.split(":")[0]
                return f"{protocol}{username}:****@{parts[1]}"

        return f"{parts[0].split(':')[0]}:****@{parts[1]}"

    def get(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """
        Get a value from the cache.

        Args:
            key: Cache key
            default: Default value if key not found

        Returns:
            Cached value or default
        """
        try:
            value = self.redis.get(key)
            if value is None:
                self.stats["misses"] += 1
                return default

            self.stats["hits"] += 1
            return self._deserialize(value)
        except Exception as e:
            logger.error(f"Error getting value from cache: {e}")
            self.stats["errors"] += 1
            return default

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        region: str = CacheRegion.DEFAULT
    ) -> bool:
        """
        Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (overrides region TTL)
            region: Cache region (determines TTL if not specified)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Determine TTL
            if ttl is None:
                ttl = TTL_MAPPING.get(region, DEFAULT_TTL)

            # Serialize value
            serialized = self._serialize(value)

            # Set in Redis
            self.redis.set(key, serialized, ex=ttl)
            self.stats["sets"] += 1
            return True
        except Exception as e:
            logger.error(f"Error setting value in cache: {e}")
            self.stats["errors"] += 1
            return False

    def delete(self, key: str) -> bool:
        """
        Delete a key from the cache.

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting key from cache: {e}")
            self.stats["errors"] += 1
            return False

    def delete_by_prefix(self, prefix: str) -> int:
        """
        Delete all keys with a given prefix.

        Args:
            prefix: Key prefix

        Returns:
            Number of keys deleted
        """
        try:
            # Get all keys with prefix
            keys = self.redis.keys(f"{prefix}*")
            if not keys:
                return 0

            # Delete keys
            return self.redis.delete(*keys)
        except Exception as e:
            logger.error(f"Error deleting keys with prefix {prefix}: {e}")
            self.stats["errors"] += 1
            return 0

    def invalidate_campaign(self, campaign_id: int) -> int:
        """
        Invalidate all cache entries for a campaign.

        Args:
            campaign_id: Campaign ID

        Returns:
            Number of keys deleted
        """
        return self.delete_by_prefix(f"{CAMPAIGN_PREFIX}{campaign_id}:")

    def invalidate_user(self, user_id: int) -> int:
        """
        Invalidate all cache entries for a user.

        Args:
            user_id: User ID

        Returns:
            Number of keys deleted
        """
        return self.delete_by_prefix(f"{USER_PREFIX}{user_id}:")

    def invalidate_analytics(self, campaign_id: Optional[int] = None) -> int:
        """
        Invalidate analytics cache entries.

        Args:
            campaign_id: Optional campaign ID (if None, invalidate all analytics)

        Returns:
            Number of keys deleted
        """
        if campaign_id is None:
            return self.delete_by_prefix(ANALYTICS_PREFIX)
        else:
            return self.delete_by_prefix(f"{ANALYTICS_PREFIX}campaign:{campaign_id}:")

    def rate_limit(
        self,
        key: str,
        limit: int,
        period: int = 60
    ) -> Tuple[bool, int]:
        """
        Apply rate limiting.

        Args:
            key: Rate limit key
            limit: Maximum number of requests
            period: Time period in seconds

        Returns:
            Tuple of (allowed, remaining)
        """
        redis_key = f"{RATE_LIMIT_PREFIX}{key}"

        try:
            # Get current count
            count = self.redis.get(redis_key)
            if count is None:
                # First request
                self.redis.set(redis_key, 1, ex=period)
                return True, limit - 1

            # Increment count
            count = int(count)
            if count >= limit:
                # Rate limit exceeded
                return False, 0

            # Increment and return
            self.redis.incr(redis_key)
            return True, limit - count - 1
        except Exception as e:
            logger.error(f"Error applying rate limit: {e}")
            self.stats["errors"] += 1
            # Allow request on error
            return True, 0

    def get_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dictionary of cache statistics
        """
        return self.stats.copy()

    def reset_stats(self) -> None:
        """Reset cache statistics."""
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "errors": 0,
            "timeouts": 0,
            "connection_errors": 0,
        }

    def _serialize(self, value: Any) -> str:
        """
        Serialize a value for storage in Redis.

        Args:
            value: Value to serialize

        Returns:
            Serialized value
        """
        if isinstance(value, (str, int, float, bool)) or value is None:
            return json.dumps(value)
        else:
            return json.dumps(value, default=self._json_serializer)

    def _deserialize(self, value: str) -> Any:
        """
        Deserialize a value from Redis.

        Args:
            value: Serialized value

        Returns:
            Deserialized value
        """
        return json.loads(value)

    def _json_serializer(self, obj: Any) -> Any:
        """
        JSON serializer for objects not serializable by default json code.

        Args:
            obj: Object to serialize

        Returns:
            Serialized object
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, "__dict__"):
            return obj.__dict__
        else:
            return str(obj)

class DummyRedis:
    """Dummy Redis client that fails gracefully."""

    def __getattr__(self, name):
        """Return a dummy method for any attribute."""
        def dummy_method(*args, **kwargs):
            return None
        return dummy_method

# Create a singleton instance
cache_manager = CacheManager()

def cached(
    key_prefix: str,
    key_func: Optional[Callable[..., str]] = None,
    ttl: Optional[int] = None,
    region: str = CacheRegion.DEFAULT
) -> Callable:
    """
    Decorator for caching function results.

    Args:
        key_prefix: Prefix for cache key
        key_func: Function to generate cache key from arguments
        ttl: Time to live in seconds
        region: Cache region

    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Generate cache key
            if key_func:
                key = f"{key_prefix}:{key_func(*args, **kwargs)}"
            else:
                # Default key generation based on arguments
                arg_str = ":".join(str(arg) for arg in args)
                kwarg_str = ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
                key_parts = [key_prefix]
                if arg_str:
                    key_parts.append(arg_str)
                if kwarg_str:
                    key_parts.append(kwarg_str)
                key = ":".join(key_parts)

            # Try to get from cache
            cached_value = cache_manager.get(key)
            if cached_value is not None:
                return cast(T, cached_value)

            # Call function
            result = func(*args, **kwargs)

            # Cache result
            cache_manager.set(key, result, ttl=ttl, region=region)

            return result
        return wrapper
    return decorator

def campaign_cached(
    key_func: Optional[Callable[..., str]] = None,
    ttl: Optional[int] = None
) -> Callable:
    """
    Decorator for caching campaign-related function results.

    Args:
        key_func: Function to generate cache key from arguments
        ttl: Time to live in seconds

    Returns:
        Decorated function
    """
    return cached(CAMPAIGN_PREFIX, key_func, ttl, CacheRegion.CAMPAIGN)

def user_cached(
    key_func: Optional[Callable[..., str]] = None,
    ttl: Optional[int] = None
) -> Callable:
    """
    Decorator for caching user-related function results.

    Args:
        key_func: Function to generate cache key from arguments
        ttl: Time to live in seconds

    Returns:
        Decorated function
    """
    return cached(USER_PREFIX, key_func, ttl, CacheRegion.USER)

def analytics_cached(
    key_func: Optional[Callable[..., str]] = None,
    ttl: Optional[int] = None
) -> Callable:
    """
    Decorator for caching analytics-related function results.

    Args:
        key_func: Function to generate cache key from arguments
        ttl: Time to live in seconds

    Returns:
        Decorated function
    """
    return cached(ANALYTICS_PREFIX, key_func, ttl, CacheRegion.ANALYTICS)
