import redis.asyncio as aioredis
from loguru import logger
import asyncio
from typing import Optional

from ..config.settings import get_settings

_redis_client: Optional[aioredis.Redis] = None
_redis_lock = asyncio.Lock()

async def get_redis_client() -> aioredis.Redis:
    """
    Get a Redis client instance.
    Creates a singleton client if it doesn't exist yet.
    """
    global _redis_client

    if _redis_client is not None:
        return _redis_client

    async with _redis_lock:
        # Check again in case another coroutine created it while we were waiting
        if _redis_client is not None:
            return _redis_client

        settings = get_settings()

        try:
            # Build Redis URL
            redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
            if settings.REDIS_PASSWORD:
                redis_url = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"

            # Create client
            _redis_client = aioredis.from_url(
                redis_url,
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0,
                health_check_interval=30
            )

            # Test connection
            await _redis_client.ping()

            logger.info("Redis client initialized successfully")
            return _redis_client

        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            # Return a dummy client for development/testing environments
            if settings.ENVIRONMENT.lower() in ["development", "test"]:
                logger.warning("Using dummy Redis client for development/testing")
                return DummyRedisClient()
            raise

class DummyRedisClient:
    """Dummy Redis client for development/testing without Redis"""

    async def get(self, key):
        return None

    async def set(self, key, value, expire=None):
        return True

    async def delete(self, key):
        return 0

    async def exists(self, key):
        return 0

    async def close(self):
        return True

    async def ping(self):
        return True

    async def publish(self, channel, message):
        return 0

    def pubsub(self):
        return DummyPubSub()

class DummyPubSub:
    """Dummy PubSub implementation"""

    async def subscribe(self, channel):
        return None

    async def unsubscribe(self, channel=None):
        return None

    async def get_message(self, ignore_subscribe_messages=True):
        await asyncio.sleep(0.1)  # Simulate delay
        return None

    async def close(self):
        return None
