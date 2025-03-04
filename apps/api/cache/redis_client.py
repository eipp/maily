"""
Redis Client Wrapper

This is a wrapper around the standardized Redis client from packages/database/src/redis-client.
All services should use the standardized client directly when possible.
This wrapper exists only for backward compatibility with existing code.
"""

import sys
import os
import asyncio
from typing import Any, Dict, List, Optional, Union

# Add parent directory to path to enable imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

# Import the standardized Redis client
from packages.database.src.redis-client import (
    RedisClient as StandardRedisClient,
    get_redis_client as get_standard_redis_client,
    DummyRedisClient
)

class RedisClient:
    """
    Wrapper around standardized Redis client for backward compatibility.
    New code should import directly from packages/database/src/redis-client.
    """
    
    def __init__(self, url: str = None, db: int = None, password: str = None, 
                 host: str = None, port: int = None):
        self._client_instance = None
        self._client_params = {
            "url": url,
            "db": db,
            "password": password,
            "host": host,
            "port": port
        }
        
    async def _get_client(self):
        """Get or create the standardized Redis client instance"""
        if self._client_instance is None:
            # Use the standardized client with the same params
            self._client_instance = StandardRedisClient(
                url=self._client_params["url"],
                db=self._client_params["db"],
                password=self._client_params["password"],
                host=self._client_params["host"],
                port=self._client_params["port"]
            )
            await self._client_instance.connect()
        return self._client_instance
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        client = await self._get_client()
        return await client.get(key)
    
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set value in Redis"""
        client = await self._get_client()
        return await client.set(key, value, ex=ex)
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        client = await self._get_client()
        return await client.delete(key)
    
    async def keys(self, pattern: str) -> List[str]:
        """Get keys matching pattern from Redis"""
        client = await self._get_client()
        return await client.keys(pattern)
    
    async def ping(self) -> bool:
        """Ping Redis"""
        client = await self._get_client()
        return await client.ping()
    
    async def hset(self, key: str, field: str, value: str) -> bool:
        """Set hash field in Redis"""
        client = await self._get_client()
        return await client.hset(key, field, value)
    
    async def hget(self, key: str, field: str) -> Optional[str]:
        """Get hash field from Redis"""
        client = await self._get_client()
        return await client.hget(key, field)
    
    async def hgetall(self, key: str) -> Dict[str, str]:
        """Get all hash fields from Redis"""
        client = await self._get_client()
        return await client.hgetall(key)
    
    async def lpush(self, key: str, *values: str) -> bool:
        """Push values to list in Redis"""
        client = await self._get_client()
        return await client.lpush(key, *values)
    
    async def rpush(self, key: str, *values: str) -> bool:
        """Push values to list in Redis"""
        client = await self._get_client()
        return await client.rpush(key, *values)
    
    async def lrange(self, key: str, start: int, end: int) -> List[str]:
        """Get range of values from list in Redis"""
        client = await self._get_client()
        return await client.lrange(key, start, end)
    
    def pipeline(self):
        """Get a Redis pipeline for batch operations"""
        raise NotImplementedError(
            "Please use the standardized Redis client pipeline directly: "
            "from packages.database.src.redis-client import get_redis_client"
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Redis client statistics"""
        if self._client_instance is None:
            return {
                "connected": False,
                "operations_total": 0,
                "operations_success": 0,
                "operations_failed": 0,
                "circuit_breaker": {"state": "unknown"},
                "last_error": "Client not initialized"
            }
        return self._client_instance.get_stats()
    
    async def publish(self, channel: str, message: str) -> bool:
        """Publish message to channel in Redis"""
        client = await self._get_client()
        return await client.publish(channel, message)
    
    async def subscribe(self, channel: str):
        """Subscribe to channel in Redis"""
        client = await self._get_client()
        return await client.subscribe(channel)
    
    async def info(self, section: Optional[str] = None) -> Dict[str, str]:
        """Get Redis server info"""
        client = await self._get_client()
        return await client.info(section)
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self._client_instance:
            await self._client_instance.disconnect()
            self._client_instance = None

# Simplified API for backward compatibility
async def get_redis_client() -> Union[RedisClient, DummyRedisClient]:
    """
    Get a Redis client instance. For backward compatibility.
    New code should import get_redis_client from packages/database/src/redis-client.
    """
    # First try to get the standardized client
    try:
        standard_client = await get_standard_redis_client()
        if isinstance(standard_client, DummyRedisClient):
            # Return a dummy client with our wrapper interface
            return DummyRedisClient()
            
        # Create a wrapper around the standardized client
        wrapper = RedisClient()
        wrapper._client_instance = standard_client
        return wrapper
    except Exception as e:
        import logging
        logging.getLogger("maily.api.cache.redis_client").error(
            f"Failed to get standardized Redis client: {e}. Falling back to new instance."
        )
        # Fall back to creating a new instance
        return RedisClient()