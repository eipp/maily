"""
Redis Client Utility for AI Service

This module provides a Redis client for the AI service.
"""

import logging
import os
from typing import Any, Optional, List, Dict, Union
import redis.asyncio as redis
import json

logger = logging.getLogger("ai_service.utils.redis_client")

class RedisClient:
    """Redis client for AI service"""
    
    def __init__(self, url: str = None):
        """Initialize Redis client"""
        self.url = url or os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self.client = None
        
    async def connect(self):
        """Connect to Redis"""
        if self.client is None:
            try:
                self.client = redis.from_url(
                    self.url,
                    encoding="utf-8",
                    decode_responses=True
                )
                logger.info(f"Connected to Redis at {self.url}")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.client:
            await self.client.close()
            self.client = None
            logger.info("Disconnected from Redis")
    
    async def _ensure_connected(self):
        """Ensure Redis client is connected"""
        if self.client is None:
            await self.connect()
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        await self._ensure_connected()
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error(f"Failed to get key {key}: {e}")
            return None
    
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set value in Redis"""
        await self._ensure_connected()
        try:
            await self.client.set(key, value, ex=ex)
            return True
        except Exception as e:
            logger.error(f"Failed to set key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        await self._ensure_connected()
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete key {key}: {e}")
            return False
    
    async def keys(self, pattern: str) -> List[str]:
        """Get keys matching pattern from Redis"""
        await self._ensure_connected()
        try:
            return await self.client.keys(pattern)
        except Exception as e:
            logger.error(f"Failed to get keys matching {pattern}: {e}")
            return []
    
    async def ping(self) -> bool:
        """Ping Redis"""
        await self._ensure_connected()
        try:
            return await self.client.ping()
        except Exception as e:
            logger.error(f"Failed to ping Redis: {e}")
            return False
    
    async def hset(self, key: str, field: str, value: str) -> bool:
        """Set hash field in Redis"""
        await self._ensure_connected()
        try:
            await self.client.hset(key, field, value)
            return True
        except Exception as e:
            logger.error(f"Failed to set hash field {field} in key {key}: {e}")
            return False
    
    async def hget(self, key: str, field: str) -> Optional[str]:
        """Get hash field from Redis"""
        await self._ensure_connected()
        try:
            return await self.client.hget(key, field)
        except Exception as e:
            logger.error(f"Failed to get hash field {field} from key {key}: {e}")
            return None
    
    async def hgetall(self, key: str) -> Dict[str, str]:
        """Get all hash fields from Redis"""
        await self._ensure_connected()
        try:
            return await self.client.hgetall(key)
        except Exception as e:
            logger.error(f"Failed to get all hash fields from key {key}: {e}")
            return {}
    
    async def lpush(self, key: str, *values: str) -> bool:
        """Push values to list in Redis"""
        await self._ensure_connected()
        try:
            await self.client.lpush(key, *values)
            return True
        except Exception as e:
            logger.error(f"Failed to push values to list {key}: {e}")
            return False
    
    async def rpush(self, key: str, *values: str) -> bool:
        """Push values to list in Redis"""
        await self._ensure_connected()
        try:
            await self.client.rpush(key, *values)
            return True
        except Exception as e:
            logger.error(f"Failed to push values to list {key}: {e}")
            return False
    
    async def lrange(self, key: str, start: int, end: int) -> List[str]:
        """Get range of values from list in Redis"""
        await self._ensure_connected()
        try:
            return await self.client.lrange(key, start, end)
        except Exception as e:
            logger.error(f"Failed to get range from list {key}: {e}")
            return []
    
    async def publish(self, channel: str, message: str) -> bool:
        """Publish message to channel in Redis"""
        await self._ensure_connected()
        try:
            await self.client.publish(channel, message)
            return True
        except Exception as e:
            logger.error(f"Failed to publish message to channel {channel}: {e}")
            return False
    
    async def subscribe(self, channel: str):
        """Subscribe to channel in Redis"""
        await self._ensure_connected()
        try:
            pubsub = self.client.pubsub()
            await pubsub.subscribe(channel)
            return pubsub
        except Exception as e:
            logger.error(f"Failed to subscribe to channel {channel}: {e}")
            return None

# Singleton instance
_redis_client_instance = None

def get_redis_client() -> RedisClient:
    """Get the singleton instance of RedisClient"""
    global _redis_client_instance
    if _redis_client_instance is None:
        _redis_client_instance = RedisClient()
    return _redis_client_instance

async def init_redis():
    """Initialize Redis connection"""
    client = get_redis_client()
    await client.connect()
    return client

async def close_redis():
    """Close Redis connection"""
    global _redis_client_instance
    if _redis_client_instance is not None:
        await _redis_client_instance.disconnect()
        _redis_client_instance = None
