"""
Standardized Redis client for use across all services.
This module provides a unified interface for Redis operations with built-in
resilience, telemetry, and consistent error handling.
"""

import asyncio
import json
import logging
import os
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, cast

import httpx
import redis
from redis.asyncio import Redis as AsyncRedis
from redis.asyncio.client import PubSub
from redis.exceptions import ConnectionError, RedisError, TimeoutError

from packages.error_handling.python.errors import DatabaseError, InfrastructureError, MailyError

# Type variables for better typing support
T = TypeVar('T')
RedisValue = Union[str, bytes, int, float]

# Configure logger
logger = logging.getLogger(__name__)

# Default TTL in seconds (12 hours)
DEFAULT_TTL = 43200


def handle_redis_errors(func):
    """Decorator to standardize Redis error handling across all methods."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ConnectionError as e:
            error_msg = f"Redis connection error: {str(e)}"
            logger.error(error_msg)
            raise InfrastructureError(
                code="REDIS_CONNECTION_ERROR",
                message=error_msg,
                status_code=503,
            ) from e
        except TimeoutError as e:
            error_msg = f"Redis timeout error: {str(e)}"
            logger.error(error_msg)
            raise InfrastructureError(
                code="REDIS_TIMEOUT_ERROR",
                message=error_msg,
                status_code=504,
            ) from e
        except RedisError as e:
            error_msg = f"Redis error: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(
                code="REDIS_ERROR",
                message=error_msg,
                status_code=500,
            ) from e
        except Exception as e:
            error_msg = f"Unexpected error in Redis operation: {str(e)}"
            logger.error(error_msg)
            raise InfrastructureError(
                code="UNEXPECTED_REDIS_ERROR",
                message=error_msg,
                status_code=500,
            ) from e
    return wrapper


class RedisClient:
    """Standardized Redis client with connection pooling, resilience, and metrics."""

    _instance = None
    _connection_pool = None
    
    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern to ensure only one Redis client instance."""
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        password: Optional[str] = None,
        db: int = 0,
        ssl: bool = False,
        **kwargs
    ):
        """Initialize the Redis client with connection pooling."""
        if self._initialized:
            return
            
        self.host = host or os.environ.get("REDIS_HOST", "localhost")
        self.port = port or int(os.environ.get("REDIS_PORT", 6379))
        self.password = password or os.environ.get("REDIS_PASSWORD", None)
        self.db = db
        self.ssl = ssl or os.environ.get("REDIS_SSL", "false").lower() == "true"
        
        connection_kwargs = {
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "ssl": self.ssl,
            **kwargs
        }
        
        if self.password:
            connection_kwargs["password"] = self.password
            
        # Initialize connection pool for better performance
        if RedisClient._connection_pool is None:
            RedisClient._connection_pool = redis.asyncio.ConnectionPool(**connection_kwargs)
            
        self.redis = AsyncRedis(connection_pool=RedisClient._connection_pool)
        self._pub_sub = None
        
        # Add service-specific prefixes for keys if needed
        self.key_prefix = kwargs.get("key_prefix", "")
        self._initialized = True
        
        logger.info(f"Redis client initialized: host={self.host}, port={self.port}, db={self.db}, ssl={self.ssl}")
    
    def get_prefixed_key(self, key: str) -> str:
        """Apply service-specific prefix to Redis keys."""
        return f"{self.key_prefix}{key}" if self.key_prefix else key
    
    @handle_redis_errors
    async def get(self, key: str) -> Optional[str]:
        """Get a value from Redis."""
        prefixed_key = self.get_prefixed_key(key)
        value = await self.redis.get(prefixed_key)
        return value.decode("utf-8") if value else None
    
    @handle_redis_errors
    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a JSON value from Redis and deserialize it."""
        value = await self.get(key)
        return json.loads(value) if value else None
    
    @handle_redis_errors
    async def set(
        self, key: str, value: RedisValue, ttl: Optional[int] = DEFAULT_TTL
    ) -> bool:
        """Set a value in Redis with optional TTL."""
        prefixed_key = self.get_prefixed_key(key)
        return await self.redis.set(prefixed_key, value, ex=ttl)
    
    @handle_redis_errors
    async def set_json(
        self, key: str, value: Dict[str, Any], ttl: Optional[int] = DEFAULT_TTL
    ) -> bool:
        """Serialize and set a JSON value in Redis with optional TTL."""
        serialized = json.dumps(value)
        return await self.set(key, serialized, ttl)
    
    @handle_redis_errors
    async def delete(self, key: str) -> bool:
        """Delete a key from Redis."""
        prefixed_key = self.get_prefixed_key(key)
        result = await self.redis.delete(prefixed_key)
        return result > 0
    
    @handle_redis_errors
    async def exists(self, key: str) -> bool:
        """Check if a key exists in Redis."""
        prefixed_key = self.get_prefixed_key(key)
        return await self.redis.exists(prefixed_key) > 0
    
    @handle_redis_errors
    async def expire(self, key: str, ttl: int) -> bool:
        """Set the TTL for a key in Redis."""
        prefixed_key = self.get_prefixed_key(key)
        return await self.redis.expire(prefixed_key, ttl)
    
    @handle_redis_errors
    async def ttl(self, key: str) -> int:
        """Get the TTL for a key in Redis."""
        prefixed_key = self.get_prefixed_key(key)
        return await self.redis.ttl(prefixed_key)
    
    @handle_redis_errors
    async def keys(self, pattern: str) -> List[str]:
        """Find keys matching a pattern."""
        prefixed_pattern = self.get_prefixed_key(pattern)
        keys = await self.redis.keys(prefixed_pattern)
        return [k.decode("utf-8") for k in keys]
    
    @handle_redis_errors
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment a key's value by the given amount."""
        prefixed_key = self.get_prefixed_key(key)
        return await self.redis.incrby(prefixed_key, amount)
    
    @handle_redis_errors
    async def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement a key's value by the given amount."""
        prefixed_key = self.get_prefixed_key(key)
        return await self.redis.decrby(prefixed_key, amount)
    
    @handle_redis_errors
    async def hset(self, key: str, field: str, value: RedisValue) -> bool:
        """Set a hash field in Redis."""
        prefixed_key = self.get_prefixed_key(key)
        result = await self.redis.hset(prefixed_key, field, value)
        return result > 0
    
    @handle_redis_errors
    async def hget(self, key: str, field: str) -> Optional[str]:
        """Get a hash field from Redis."""
        prefixed_key = self.get_prefixed_key(key)
        value = await self.redis.hget(prefixed_key, field)
        return value.decode("utf-8") if value else None
    
    @handle_redis_errors
    async def hmset(self, key: str, mapping: Dict[str, RedisValue]) -> bool:
        """Set multiple hash fields in Redis."""
        prefixed_key = self.get_prefixed_key(key)
        return await self.redis.hmset(prefixed_key, mapping)
    
    @handle_redis_errors
    async def hmget(self, key: str, fields: List[str]) -> List[Optional[str]]:
        """Get multiple hash fields from Redis."""
        prefixed_key = self.get_prefixed_key(key)
        values = await self.redis.hmget(prefixed_key, fields)
        return [(v.decode("utf-8") if v else None) for v in values]
    
    @handle_redis_errors
    async def hgetall(self, key: str) -> Dict[str, str]:
        """Get all fields and values from a hash in Redis."""
        prefixed_key = self.get_prefixed_key(key)
        result = await self.redis.hgetall(prefixed_key)
        return {k.decode("utf-8"): v.decode("utf-8") for k, v in result.items()}
    
    @handle_redis_errors
    async def hdel(self, key: str, *fields: str) -> int:
        """Delete fields from a hash in Redis."""
        prefixed_key = self.get_prefixed_key(key)
        return await self.redis.hdel(prefixed_key, *fields)
    
    @handle_redis_errors
    async def sadd(self, key: str, *values: RedisValue) -> int:
        """Add values to a set in Redis."""
        prefixed_key = self.get_prefixed_key(key)
        return await self.redis.sadd(prefixed_key, *values)
    
    @handle_redis_errors
    async def smembers(self, key: str) -> List[str]:
        """Get all members of a set in Redis."""
        prefixed_key = self.get_prefixed_key(key)
        result = await self.redis.smembers(prefixed_key)
        return [v.decode("utf-8") for v in result]
    
    @handle_redis_errors
    async def srem(self, key: str, *values: RedisValue) -> int:
        """Remove values from a set in Redis."""
        prefixed_key = self.get_prefixed_key(key)
        return await self.redis.srem(prefixed_key, *values)
    
    @handle_redis_errors
    async def lpush(self, key: str, *values: RedisValue) -> int:
        """Push values onto the beginning of a list in Redis."""
        prefixed_key = self.get_prefixed_key(key)
        return await self.redis.lpush(prefixed_key, *values)
    
    @handle_redis_errors
    async def rpush(self, key: str, *values: RedisValue) -> int:
        """Push values onto the end of a list in Redis."""
        prefixed_key = self.get_prefixed_key(key)
        return await self.redis.rpush(prefixed_key, *values)
    
    @handle_redis_errors
    async def lpop(self, key: str) -> Optional[str]:
        """Pop a value from the beginning of a list in Redis."""
        prefixed_key = self.get_prefixed_key(key)
        value = await self.redis.lpop(prefixed_key)
        return value.decode("utf-8") if value else None
    
    @handle_redis_errors
    async def rpop(self, key: str) -> Optional[str]:
        """Pop a value from the end of a list in Redis."""
        prefixed_key = self.get_prefixed_key(key)
        value = await self.redis.rpop(prefixed_key)
        return value.decode("utf-8") if value else None
    
    @handle_redis_errors
    async def lrange(self, key: str, start: int, end: int) -> List[str]:
        """Get a range of values from a list in Redis."""
        prefixed_key = self.get_prefixed_key(key)
        result = await self.redis.lrange(prefixed_key, start, end)
        return [v.decode("utf-8") for v in result]
    
    @handle_redis_errors
    async def publish(self, channel: str, message: str) -> int:
        """Publish a message to a channel in Redis."""
        return await self.redis.publish(channel, message)
    
    @handle_redis_errors
    async def get_pubsub(self) -> PubSub:
        """Get a PubSub instance for subscribing to channels."""
        if not self._pub_sub:
            self._pub_sub = self.redis.pubsub()
        return self._pub_sub
    
    @handle_redis_errors
    async def flush_db(self) -> bool:
        """Flush the current database. USE WITH CAUTION!"""
        return await self.redis.flushdb()
    
    @handle_redis_errors
    async def pipeline_execute(self, commands: List[Callable]) -> List[Any]:
        """Execute a pipeline of Redis commands for better performance."""
        pipeline = self.redis.pipeline()
        
        for cmd in commands:
            # Apply the command to the pipeline
            cmd(pipeline)
            
        results = await pipeline.execute()
        return results
    
    async def close(self) -> None:
        """Close the Redis connection."""
        if self._pub_sub:
            await self._pub_sub.close()
            self._pub_sub = None
            
        await self.redis.close()


# Create singleton instance
redis_client = RedisClient()


# Convenience functions for global access
async def get(key: str) -> Optional[str]:
    """Get a value from Redis."""
    return await redis_client.get(key)


async def set(key: str, value: RedisValue, ttl: Optional[int] = DEFAULT_TTL) -> bool:
    """Set a value in Redis with optional TTL."""
    return await redis_client.set(key, value, ttl)


async def delete(key: str) -> bool:
    """Delete a key from Redis."""
    return await redis_client.delete(key)


async def get_json(key: str) -> Optional[Dict[str, Any]]:
    """Get a JSON value from Redis and deserialize it."""
    return await redis_client.get_json(key)


async def set_json(key: str, value: Dict[str, Any], ttl: Optional[int] = DEFAULT_TTL) -> bool:
    """Serialize and set a JSON value in Redis with optional TTL."""
    return await redis_client.set_json(key, value, ttl)