"""
Redis Client Package for Maily

This package provides a shared, resilient Redis client implementation with:
- Connection pooling and connection management
- Circuit breaker pattern for resilience
- Standardized error handling with detailed logging
- Retry mechanisms with exponential backoff
- Pipeline support for batch operations
- PubSub support for real-time messaging
- Health checks and monitoring statistics

Usage:
    from packages.database.src.redis import get_redis_client, close_redis

    # Get Redis client
    redis = await get_redis_client()
    
    # Use Redis client
    await redis.set("key", "value")
    value = await redis.get("key")
    
    # Use Redis pipeline
    async with redis.pipeline() as pipe:
        pipe.set("key1", "value1")
        pipe.set("key2", "value2")
        await pipe.execute()
    
    # Close Redis connection
    await close_redis()

Circuit Breaker:
    The circuit breaker prevents cascading failures by stopping operations
    when Redis is unavailable. It automatically recovers when Redis becomes
    available again.

Environment Variables:
    REDIS_URL: Redis connection URL (optional)
    REDIS_HOST: Redis host (default: localhost)
    REDIS_PORT: Redis port (default: 6379)
    REDIS_DB: Redis database number (default: 0)
    REDIS_PASSWORD: Redis password (optional)
    REDIS_CB_FAILURE_THRESHOLD: Circuit breaker failure threshold (default: 5)
    REDIS_CB_RESET_TIMEOUT: Circuit breaker reset timeout in seconds (default: 30.0)
    REDIS_POOL_MIN_SIZE: Connection pool minimum size (default: 5)
    REDIS_POOL_MAX_SIZE: Connection pool maximum size (default: 20)
"""

from .redis_client import (
    get_redis_client,
    close_redis,
    RedisClient,
    DummyRedisClient,
    RedisPipeline,
    CircuitBreaker,
)

__all__ = [
    "get_redis_client",
    "close_redis",
    "RedisClient",
    "DummyRedisClient",
    "RedisPipeline",
    "CircuitBreaker",
]