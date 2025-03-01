import json
import asyncio
from typing import Dict, List, Any, Callable, Optional, Set
from loguru import logger

from .redis_client import get_redis_client

class RedisPubSub:
    """
    Redis Pub/Sub service for real-time messaging.
    Handles channel subscription, message publishing, and callback registration.
    """

    def __init__(self):
        self.redis = None
        self.pubsub = None
        self.tasks: Dict[str, asyncio.Task] = {}
        self.callbacks: Dict[str, Set[Callable]] = {}
        self.lock = asyncio.Lock()
        self._running = False
        self._initialized = False

    async def _ensure_initialized(self):
        """Ensure Redis client is initialized"""
        if not self._initialized:
            self.redis = await get_redis_client()
            self.pubsub = self.redis.pubsub()
            self._initialized = True

    async def subscribe(self, channel: str, callback: Callable):
        """Subscribe to a channel and register a callback"""
        await self._ensure_initialized()

        async with self.lock:
            # Add callback for channel
            if channel not in self.callbacks:
                self.callbacks[channel] = set()

                # First callback for this channel, subscribe in Redis
                await self.pubsub.subscribe(channel)

                # Start listener task if not already running
                if channel not in self.tasks or self.tasks[channel].done():
                    self.tasks[channel] = asyncio.create_task(
                        self._message_listener(channel)
                    )

            # Add callback
            self.callbacks[channel].add(callback)

        logger.debug(f"Subscribed to channel: {channel}")

    async def unsubscribe(self, channel: str, callback: Callable):
        """Unsubscribe a callback from a channel"""
        if not self._initialized:
            return

        async with self.lock:
            if channel in self.callbacks:
                # Remove callback
                self.callbacks[channel].discard(callback)

                # If no more callbacks, unsubscribe from channel
                if not self.callbacks[channel]:
                    await self.pubsub.unsubscribe(channel)
                    self.callbacks.pop(channel)

                    # Cancel listener task
                    if channel in self.tasks and not self.tasks[channel].done():
                        self.tasks[channel].cancel()
                        try:
                            await self.tasks[channel]
                        except asyncio.CancelledError:
                            pass
                        self.tasks.pop(channel)

        logger.debug(f"Unsubscribed from channel: {channel}")

    async def publish(self, channel: str, message: Any):
        """Publish a message to a channel"""
        await self._ensure_initialized()

        # Convert message to JSON if it's a dict
        message_data = json.dumps(message) if isinstance(message, dict) else message

        # Publish to Redis
        await self.redis.publish(channel, message_data)
        logger.debug(f"Published message to {channel}")

    async def _message_listener(self, channel: str):
        """Listen for messages on a channel and dispatch to callbacks"""
        try:
            logger.debug(f"Started listener for channel: {channel}")

            while True:
                message = await self.pubsub.get_message(ignore_subscribe_messages=True)
                if message is None:
                    await asyncio.sleep(0.01)  # Prevent CPU spinning
                    continue

                # Process message
                if message["type"] == "message":
                    try:
                        # Parse message data
                        data = message["data"]
                        if isinstance(data, bytes):
                            data = data.decode("utf-8")

                        # Try to parse as JSON
                        try:
                            data = json.loads(data)
                        except json.JSONDecodeError:
                            pass  # Keep as string if not valid JSON

                        # Check if message has exclusion metadata
                        exclude_user = None
                        if isinstance(data, dict) and "_exclude_user" in data:
                            exclude_user = data.pop("_exclude_user")

                        # Dispatch to all callbacks
                        async with self.lock:
                            callbacks = list(self.callbacks.get(channel, []))

                        for callback in callbacks:
                            try:
                                await callback(data)
                            except Exception as e:
                                logger.error(f"Error in channel {channel} callback: {e}")

                    except Exception as e:
                        logger.error(f"Error processing message from channel {channel}: {e}")

        except asyncio.CancelledError:
            logger.debug(f"Listener for channel {channel} cancelled")
            raise
        except Exception as e:
            logger.error(f"Channel {channel} listener failed: {e}")

    async def close(self):
        """Close all connections and cancel tasks"""
        if not self._initialized:
            return

        try:
            # Cancel all listener tasks
            for channel, task in list(self.tasks.items()):
                if not task.done():
                    task.cancel()

            # Wait for all tasks to complete
            if self.tasks:
                await asyncio.gather(*list(self.tasks.values()), return_exceptions=True)

            # Close PubSub and Redis connections
            if self.pubsub:
                await self.pubsub.unsubscribe()
                await self.pubsub.close()

            self._initialized = False
            logger.info("Redis PubSub service closed")

        except Exception as e:
            logger.error(f"Error closing Redis PubSub: {e}")
