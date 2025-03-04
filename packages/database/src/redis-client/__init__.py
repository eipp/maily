"""
Redis Client Package

This package provides a standardized Redis client implementation
with connection pooling, circuit breaker pattern, and error handling.
"""

from .redisClient import (
    RedisClient,
    RedisPipeline, 
    DummyRedisClient,
    DummyPubSub,
    get_redis_client,
    close_redis
)

__all__ = [
    "RedisClient",
    "RedisPipeline",
    "DummyRedisClient", 
    "DummyPubSub",
    "get_redis_client",
    "close_redis"
]