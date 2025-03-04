"""
Redis Client Import Module

This module provides compatibility imports for the standardized Redis client.
This approach avoids issues with Python's import system and dashes in directory names.
"""

import warnings

# Show deprecation warning
warnings.warn(
    "Please use 'from packages.database.src.redis.redis_client import *' for imports.",
    DeprecationWarning, stacklevel=2
)

# Import from the standardized location via the compatibility module
from packages.database.src.redis.redis_client import (
    RedisClient,
    RedisPipeline,
    DummyRedisClient,
    DummyPubSub,
    get_redis_client,
    close_redis
)

# Re-export for compatibility
__all__ = [
    "RedisClient",
    "RedisPipeline",
    "DummyRedisClient",
    "DummyPubSub",
    "get_redis_client",
    "close_redis"
]