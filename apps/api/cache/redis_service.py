"""
Standardized Redis service with dependency injection pattern.
"""
from typing import Optional, Any, Dict, List, Union, Callable
import json
import redis
from fastapi import Depends
from pydantic import BaseModel

from ..config.settings import get_settings

class TTLConfig(BaseModel):
    """Configuration for TTL policies by data type."""
    campaign_content: int = 3600      # 1 hour
    analytics: int = 300              # 5 minutes
    user_preferences: int = 86400     # 1 day
    ai_responses: int = 43200         # 12 hours
    generated_content: int = 7200     # 2 hours
    token_verification: int = 120     # 2 minutes
    session: int = 1800               # 30 minutes
    default: int = 3600               # Default 1 hour

class CacheService:
    """Service for managing Redis caching with TTL policies."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.ttl_config = TTLConfig().dict()

    def get(self, key: str) -> Optional[Any]:
        """Get cached item with deserialization.

        Args:
            key: The cache key to retrieve

        Returns:
            Deserialized data or None if not found
        """
        data = self.redis.get(key)
        if not data:
            return None

        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return data.decode("utf-8")

    def set(self, key: str, value: Any, cache_type: str = "default"):
        """Set cached item with appropriate TTL.

        Args:
            key: The cache key
            value: The value to cache
            cache_type: Type of data for TTL selection
        """
        ttl = self.ttl_config.get(cache_type, self.ttl_config["default"])

        if isinstance(value, (dict, list)):
            value = json.dumps(value)

        self.redis.setex(key, ttl, value)

    def invalidate(self, pattern: str):
        """Invalidate all keys matching pattern.

        Args:
            pattern: Redis key pattern to match
        """
        keys = self.redis.keys(pattern)
        if keys:
            self.redis.delete(*keys)

    def exists(self, key: str) -> bool:
        """Check if a key exists.

        Args:
            key: The cache key to check

        Returns:
            Boolean indicating if key exists
        """
        return bool(self.redis.exists(key))

    def increment(self, key: str, amount: int = 1) -> int:
        """Increment a counter.

        Args:
            key: The counter key
            amount: Amount to increment

        Returns:
            New counter value
        """
        return self.redis.incrby(key, amount)

    def expire(self, key: str, ttl: int):
        """Set expiration on key.

        Args:
            key: The cache key
            ttl: Time to live in seconds
        """
        self.redis.expire(key, ttl)

    def pipeline(self) -> redis.client.Pipeline:
        """Get a Redis pipeline for batch operations.

        Returns:
            Redis pipeline object
        """
        return self.redis.pipeline()

def get_redis_client() -> redis.Redis:
    """Get Redis client from environment configuration.

    Returns:
        Configured Redis client
    """
    settings = get_settings()

    # Build Redis URL
    if settings.REDIS_PASSWORD:
        redis_url = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
    else:
        redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"

    return redis.Redis.from_url(
        redis_url,
        decode_responses=True,
        socket_timeout=5.0,
        socket_connect_timeout=5.0,
        health_check_interval=30
    )

def get_cache_service(redis_client: redis.Redis = Depends(get_redis_client)) -> CacheService:
    """Dependency for getting the cache service.

    Args:
        redis_client: Redis client dependency

    Returns:
        Configured CacheService instance
    """
    return CacheService(redis_client)
