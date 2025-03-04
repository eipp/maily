"""
Redis Client (Compatibility Module)

This module is for backward compatibility only.
It re-exports the Redis client from the standardized location.
New code should import directly from packages/database/src/redis-client/redisClient.py
"""

import sys
import os
import warnings

# Show deprecation warning
warnings.warn(
    "Importing from packages/database/src/redis/redis_client.py is deprecated. "
    "Please import from packages/database/src/redis-client/redisClient.py instead.",
    DeprecationWarning, stacklevel=2
)

# Import from standardized location
from ..redis-client.redisClient import (
    RedisClient,
    RedisPipeline,
    DummyRedisClient,
    DummyPubSub,
    get_redis_client,
    close_redis
)

# Re-export for backward compatibility
__all__ = [
    "RedisClient",
    "RedisPipeline",
    "DummyRedisClient",
    "DummyPubSub",
    "get_redis_client",
    "close_redis"
]