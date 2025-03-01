"""
Redis-based Caching Service

Provides a robust caching implementation using Redis with features like
automatic serialization/deserialization, key management, and cache invalidation strategies.
"""

import json
import time
import hashlib
import logging
from typing import Any, Dict, List, Optional, Set, Tuple, Type, TypeVar, Union, Generic, Callable
from pydantic import BaseModel
import redis
import asyncio
import pickle
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')

class CacheSettings(BaseModel):
    """Configuration for the Redis cache."""

    redis_url: str = "redis://localhost:6379/0"
    default_ttl: int = 3600  # 1 hour in seconds
    key_prefix: str = "maily:"
    serialization_format: str = "json"  # 'json' or 'pickle'
    enable_key_tracking: bool = True
    enable_metrics: bool = True

class CacheMetrics(BaseModel):
    """Metrics for cache usage."""

    hits: int = 0
    misses: int = 0
    errors: int = 0
    total_get_time: float = 0
    total_set_time: float = 0

    def record_hit(self, latency: float) -> None:
        """Record a cache hit."""
        self.hits += 1
        self.total_get_time += latency

    def record_miss(self, latency: float) -> None:
        """Record a cache miss."""
        self.misses += 1
        self.total_get_time += latency

    def record_error(self) -> None:
        """Record a cache error."""
        self.errors += 1

    def record_set(self, latency: float) -> None:
        """Record a cache set operation."""
        self.total_set_time += latency

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total

    @property
    def avg_get_latency(self) -> float:
        """Calculate average get latency."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.total_get_time / total

    @property
    def avg_set_latency(self) -> float:
        """Calculate average set latency."""
        if self.total_set_time == 0:
            return 0.0
        return self.total_set_time / (self.hits + self.misses)

    def to_dict(self) -> Dict[str, Union[int, float]]:
        """Convert metrics to a dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "errors": self.errors,
            "hit_rate": self.hit_rate,
            "avg_get_latency": self.avg_get_latency,
            "avg_set_latency": self.avg_set_latency
        }


class RedisCache:
    """
    Redis-based cache implementation with advanced features.

    Features:
    - Automatic serialization/deserialization
    - Key prefix management
    - TTL support
    - Cache invalidation by pattern
    - Transaction support
    - Metrics collection
    """

    def __init__(
        self,
        settings: Optional[CacheSettings] = None,
        redis_client: Optional[redis.Redis] = None
    ):
        """
        Initialize the Redis cache.

        Args:
            settings: Cache configuration settings
            redis_client: Optional pre-configured Redis client
        """
        self.settings = settings or CacheSettings()

        # Create or use provided Redis client
        if redis_client:
            self.redis = redis_client
        else:
            self.redis = redis.from_url(
                self.settings.redis_url,
                decode_responses=(self.settings.serialization_format == 'json')
            )

        self.metrics = CacheMetrics() if self.settings.enable_metrics else None

        # Verify Redis connection
        try:
            self.redis.ping()
            logger.info(f"Connected to Redis at {self.settings.redis_url}")
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection failed: {str(e)}. Cache will be non-functional.")

    def _build_key(self, key: str) -> str:
        """
        Build a full cache key with prefix.

        Args:
            key: The base key

        Returns:
            The full cache key with prefix
        """
        return f"{self.settings.key_prefix}{key}"

    def _track_key(self, key: str, ttl: Optional[int] = None) -> None:
        """
        Track a key for cache invalidation.

        Args:
            key: The cache key to track
            ttl: Optional TTL in seconds
        """
        if not self.settings.enable_key_tracking:
            return

        # Record this key in a set for tracking
        tracking_key = f"{self.settings.key_prefix}_all_keys"
        try:
            self.redis.sadd(tracking_key, key)

            # If the tracking key doesn't have an expiry, set it to a long time
            if not self.redis.ttl(tracking_key) > 0:
                self.redis.expire(tracking_key, 86400 * 30)  # 30 days
        except Exception as e:
            logger.warning(f"Failed to track key {key}: {str(e)}")

    def _serialize(self, value: Any) -> str:
        """
        Serialize a value to string.

        Args:
            value: The value to serialize

        Returns:
            Serialized value as string

        Raises:
            ValueError: If serialization fails
        """
        try:
            if self.settings.serialization_format == 'json':
                return json.dumps(value)
            else:  # pickle
                return pickle.dumps(value)
        except Exception as e:
            raise ValueError(f"Serialization failed: {str(e)}")

    def _deserialize(self, value: Any, default_type: Optional[Type[T]] = None) -> T:
        """
        Deserialize a value from string.

        Args:
            value: The value to deserialize
            default_type: Optional type to cast to

        Returns:
            Deserialized value

        Raises:
            ValueError: If deserialization fails
        """
        if value is None:
            return None

        try:
            if self.settings.serialization_format == 'json':
                result = json.loads(value) if value else None
            else:  # pickle
                result = pickle.loads(value) if value else None

            # Cast to default type if provided
            if default_type and result is not None:
                if issubclass(default_type, BaseModel) and isinstance(result, dict):
                    return default_type(**result)
                else:
                    return default_type(result)

            return result
        except Exception as e:
            raise ValueError(f"Deserialization failed: {str(e)}")

    def get(self, key: str, default: Any = None, type_cast: Optional[Type[T]] = None) -> Optional[T]:
        """
        Get a value from the cache.

        Args:
            key: The cache key
            default: Default value if key doesn't exist
            type_cast: Optional type to cast the result to

        Returns:
            Cached value or default if not found
        """
        full_key = self._build_key(key)
        start_time = time.time()

        try:
            value = self.redis.get(full_key)
            latency = time.time() - start_time

            if value is not None:
                # Cache hit
                if self.metrics:
                    self.metrics.record_hit(latency)

                logger.debug(f"Cache hit for key: {key} in {latency:.3f}s")
                return self._deserialize(value, type_cast)
            else:
                # Cache miss
                if self.metrics:
                    self.metrics.record_miss(latency)

                logger.debug(f"Cache miss for key: {key} in {latency:.3f}s")
                return default
        except Exception as e:
            # Cache error
            if self.metrics:
                self.metrics.record_error()

            logger.warning(f"Cache error for key {key}: {str(e)}")
            return default

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        nx: bool = False,  # Only set if key doesn't exist
        xx: bool = False,  # Only set if key exists
        compress: bool = False  # Apply compression (for large values)
    ) -> bool:
        """
        Set a value in the cache.

        Args:
            key: The cache key
            value: The value to cache
            ttl: Time-to-live in seconds (None for default)
            nx: Only set if key doesn't exist
            xx: Only set if key exists
            compress: Whether to compress the value

        Returns:
            True if successful, False otherwise
        """
        full_key = self._build_key(key)
        ttl = ttl if ttl is not None else self.settings.default_ttl
        start_time = time.time()

        try:
            # Serialize value
            serialized_value = self._serialize(value)

            # Set options
            options = {}
            if nx:
                options['nx'] = True
            if xx:
                options['xx'] = True

            # Set value with TTL
            if self.settings.serialization_format == 'json':
                self.redis.set(full_key, serialized_value, ex=ttl, **options)
            else:
                self.redis.set(full_key, serialized_value, ex=ttl, **options)

            # Track the key if enabled
            self._track_key(full_key, ttl)

            # Record metrics
            if self.metrics:
                self.metrics.record_set(time.time() - start_time)

            logger.debug(f"Cache set for key: {key} with TTL: {ttl}s")
            return True
        except Exception as e:
            if self.metrics:
                self.metrics.record_error()

            logger.warning(f"Cache set error for key {key}: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete a key from the cache.

        Args:
            key: The cache key

        Returns:
            True if deleted, False otherwise
        """
        full_key = self._build_key(key)

        try:
            result = self.redis.delete(full_key)

            # Remove from tracked keys if enabled
            if self.settings.enable_key_tracking:
                tracking_key = f"{self.settings.key_prefix}_all_keys"
                self.redis.srem(tracking_key, full_key)

            return result > 0
        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {str(e)}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Delete keys matching a pattern.

        Args:
            pattern: The pattern to match

        Returns:
            Number of keys deleted
        """
        full_pattern = self._build_key(pattern)

        try:
            # Use scan for efficient iteration
            keys = []
            cursor = 0

            while True:
                cursor, partial_keys = self.redis.scan(cursor, match=full_pattern, count=100)
                keys.extend(partial_keys)

                if cursor == 0:
                    break

            if not keys:
                return 0

            # Delete the keys
            deleted = self.redis.delete(*keys)

            # Remove from tracked keys if enabled
            if self.settings.enable_key_tracking:
                tracking_key = f"{self.settings.key_prefix}_all_keys"
                if keys:
                    self.redis.srem(tracking_key, *keys)

            logger.info(f"Deleted {deleted} keys matching pattern: {pattern}")
            return deleted
        except Exception as e:
            logger.warning(f"Cache delete pattern error for {pattern}: {str(e)}")
            return 0

    def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.

        Args:
            key: The cache key

        Returns:
            True if the key exists, False otherwise
        """
        full_key = self._build_key(key)

        try:
            return self.redis.exists(full_key) > 0
        except Exception as e:
            logger.warning(f"Cache exists error for key {key}: {str(e)}")
            return False

    def ttl(self, key: str) -> int:
        """
        Get the TTL of a key in seconds.

        Args:
            key: The cache key

        Returns:
            TTL in seconds, -1 if no TTL, -2 if key doesn't exist
        """
        full_key = self._build_key(key)

        try:
            return self.redis.ttl(full_key)
        except Exception as e:
            logger.warning(f"Cache TTL error for key {key}: {str(e)}")
            return -2

    def set_ttl(self, key: str, ttl: int) -> bool:
        """
        Set the TTL of a key.

        Args:
            key: The cache key
            ttl: TTL in seconds

        Returns:
            True if successful, False otherwise
        """
        full_key = self._build_key(key)

        try:
            return self.redis.expire(full_key, ttl)
        except Exception as e:
            logger.warning(f"Cache set TTL error for key {key}: {str(e)}")
            return False

    def get_metrics(self) -> Dict[str, Union[int, float]]:
        """
        Get cache metrics.

        Returns:
            Dictionary of cache metrics
        """
        if not self.metrics:
            return {"enabled": False}

        return self.metrics.to_dict()

    def clear_all(self) -> int:
        """
        Clear all keys with this cache's prefix.

        Returns:
            Number of keys deleted
        """
        pattern = f"{self.settings.key_prefix}*"

        try:
            # Use scan for efficient iteration
            keys = []
            cursor = 0

            while True:
                cursor, partial_keys = self.redis.scan(cursor, match=pattern, count=100)
                keys.extend(partial_keys)

                if cursor == 0:
                    break

            if not keys:
                return 0

            # Delete the keys
            deleted = self.redis.delete(*keys)

            logger.info(f"Cleared all {deleted} keys with prefix: {self.settings.key_prefix}")
            return deleted
        except Exception as e:
            logger.warning(f"Cache clear all error: {str(e)}")
            return 0

    def get_all_keys(self) -> List[str]:
        """
        Get all keys with this cache's prefix.

        Returns:
            List of keys
        """
        if self.settings.enable_key_tracking:
            # Use the tracking set if available
            tracking_key = f"{self.settings.key_prefix}_all_keys"

            try:
                keys = self.redis.smembers(tracking_key)
                # Remove the prefix for easier use
                prefix_len = len(self.settings.key_prefix)
                return [key[prefix_len:] for key in keys]
            except Exception as e:
                logger.warning(f"Failed to get tracked keys: {str(e)}")

        # Fall back to scan
        pattern = f"{self.settings.key_prefix}*"

        try:
            keys = []
            cursor = 0

            while True:
                cursor, partial_keys = self.redis.scan(cursor, match=pattern, count=100)
                keys.extend(partial_keys)

                if cursor == 0:
                    break

            # Remove the prefix for easier use
            prefix_len = len(self.settings.key_prefix)
            return [key[prefix_len:] for key in keys]
        except Exception as e:
            logger.warning(f"Failed to get all keys: {str(e)}")
            return []

    def get_key_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all keys.

        Returns:
            Dictionary of key information
        """
        keys = self.get_all_keys()
        result = {}

        for key in keys:
            try:
                full_key = self._build_key(key)
                ttl = self.redis.ttl(full_key)

                result[key] = {
                    "ttl": ttl,
                    "exists": ttl > -2,
                    "type": self.redis.type(full_key).decode('utf-8')
                    if hasattr(self.redis.type(full_key), 'decode') else self.redis.type(full_key)
                }
            except Exception as e:
                result[key] = {"error": str(e)}

        return result


def cached(
    ttl: Optional[int] = None,
    key_prefix: Optional[str] = None,
    key_builder: Optional[Callable] = None,
    cache: Optional[RedisCache] = None
):
    """
    Decorator for caching function results.

    Args:
        ttl: Time-to-live in seconds
        key_prefix: Prefix for cache keys
        key_builder: Function to build cache key from arguments
        cache: Cache instance to use

    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            nonlocal cache

            # Get or create cache instance
            if cache is None:
                cache = RedisCache()

            # Build cache key
            if key_builder:
                key = key_builder(*args, **kwargs)
            else:
                # Default key builder: function name + args + kwargs
                key_parts = [func.__name__]

                # Add args to key
                if args:
                    for arg in args:
                        if isinstance(arg, BaseModel):
                            key_parts.append(arg.json())
                        elif hasattr(arg, '__dict__'):
                            key_parts.append(str(arg.__dict__))
                        else:
                            key_parts.append(str(arg))

                # Add kwargs to key
                if kwargs:
                    for k, v in sorted(kwargs.items()):
                        if isinstance(v, BaseModel):
                            key_parts.append(f"{k}={v.json()}")
                        elif hasattr(v, '__dict__'):
                            key_parts.append(f"{k}={v.__dict__}")
                        else:
                            key_parts.append(f"{k}={v}")

                # Create a hash of the key parts
                key_str = "".join(key_parts)
                key = hashlib.md5(key_str.encode()).hexdigest()

            # Add prefix if provided
            if key_prefix:
                key = f"{key_prefix}:{key}"

            # Check cache
            cached_result = cache.get(key)
            if cached_result is not None:
                return cached_result

            # Call function
            result = await func(*args, **kwargs)

            # Cache result
            if result is not None:
                cache.set(key, result, ttl=ttl)

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            nonlocal cache

            # Get or create cache instance
            if cache is None:
                cache = RedisCache()

            # Build cache key
            if key_builder:
                key = key_builder(*args, **kwargs)
            else:
                # Default key builder: function name + args + kwargs
                key_parts = [func.__name__]

                # Add args to key
                if args:
                    for arg in args:
                        if isinstance(arg, BaseModel):
                            key_parts.append(arg.json())
                        elif hasattr(arg, '__dict__'):
                            key_parts.append(str(arg.__dict__))
                        else:
                            key_parts.append(str(arg))

                # Add kwargs to key
                if kwargs:
                    for k, v in sorted(kwargs.items()):
                        if isinstance(v, BaseModel):
                            key_parts.append(f"{k}={v.json()}")
                        elif hasattr(v, '__dict__'):
                            key_parts.append(f"{k}={v.__dict__}")
                        else:
                            key_parts.append(f"{k}={v}")

                # Create a hash of the key parts
                key_str = "".join(key_parts)
                key = hashlib.md5(key_str.encode()).hexdigest()

            # Add prefix if provided
            if key_prefix:
                key = f"{key_prefix}:{key}"

            # Check cache
            cached_result = cache.get(key)
            if cached_result is not None:
                return cached_result

            # Call function
            result = func(*args, **kwargs)

            # Cache result
            if result is not None:
                cache.set(key, result, ttl=ttl)

            return result

        # Choose the right wrapper based on whether the function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# Create a default cache instance
default_cache = RedisCache()
