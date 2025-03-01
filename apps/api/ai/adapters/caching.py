"""
Caching utilities for AI adapters to improve performance.
"""
import time
import json
import hashlib
import logging
from typing import Dict, Any, Optional, Union, List, Tuple, Callable
from functools import wraps
import asyncio

from apps.api.ai.adapters.base import ModelRequest, ModelResponse

logger = logging.getLogger(__name__)

class AdapterCache:
    """
    Cache implementation for AI adapter responses.

    This class provides caching functionality for AI model responses,
    with support for TTL (time-to-live) and cache invalidation.
    """

    def __init__(self, ttl_seconds: int = 3600, max_size: int = 1000):
        """
        Initialize the cache.

        Args:
            ttl_seconds: Time-to-live in seconds for cache entries
            max_size: Maximum number of entries in the cache
        """
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
        self.lock = asyncio.Lock()

    def _generate_key(self, request: ModelRequest) -> str:
        """
        Generate a cache key from a model request.

        Args:
            request: The model request

        Returns:
            A string key for the cache
        """
        # Create a dictionary of the request attributes to hash
        key_dict = {
            "prompt": request.prompt,
            "model_name": request.model_name,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "frequency_penalty": request.frequency_penalty,
            "presence_penalty": request.presence_penalty,
            "stop_sequences": request.stop_sequences
        }

        # Convert to a stable string representation and hash
        key_str = json.dumps(key_dict, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    async def get(self, request: ModelRequest) -> Optional[ModelResponse]:
        """
        Get a cached response for a request.

        Args:
            request: The model request

        Returns:
            The cached response, or None if not found or expired
        """
        key = self._generate_key(request)

        async with self.lock:
            if key in self.cache:
                value, timestamp = self.cache[key]

                # Check if the entry has expired
                if time.time() - timestamp <= self.ttl_seconds:
                    self.hits += 1
                    logger.debug(f"Cache hit for key: {key[:8]}...")
                    return value

                # Remove expired entry
                del self.cache[key]

            self.misses += 1
            logger.debug(f"Cache miss for key: {key[:8]}...")
            return None

    async def set(self, request: ModelRequest, response: ModelResponse) -> None:
        """
        Store a response in the cache.

        Args:
            request: The model request
            response: The model response to cache
        """
        key = self._generate_key(request)

        async with self.lock:
            # Evict entries if cache is full
            if len(self.cache) >= self.max_size:
                # Remove the oldest entry (simple LRU strategy)
                oldest_key = min(self.cache.items(), key=lambda x: x[1][1])[0]
                del self.cache[oldest_key]

            self.cache[key] = (response, time.time())
            logger.debug(f"Cached response for key: {key[:8]}...")

    async def invalidate(self, key_pattern: str = None) -> int:
        """
        Invalidate cache entries matching a pattern.

        Args:
            key_pattern: Optional pattern to match against keys

        Returns:
            Number of entries invalidated
        """
        count = 0

        async with self.lock:
            if key_pattern:
                keys_to_remove = [k for k in self.cache.keys() if key_pattern in k]
                for key in keys_to_remove:
                    del self.cache[key]
                    count += 1
            else:
                count = len(self.cache)
                self.cache.clear()

        logger.info(f"Invalidated {count} cache entries")
        return count

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests) * 100 if total_requests > 0 else 0

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_percent": hit_rate,
            "total_requests": total_requests
        }


def cached_response(cache: AdapterCache):
    """
    Decorator for caching adapter responses.

    Args:
        cache: The cache instance to use

    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, request: ModelRequest, *args, **kwargs):
            # Skip cache for non-deterministic requests (temperature > 0)
            if request.temperature > 0:
                return await func(self, request, *args, **kwargs)

            # Check cache
            cached_response = await cache.get(request)
            if cached_response:
                # Add cache metadata
                cached_response.metadata["cached"] = True
                return cached_response

            # Get fresh response
            response = await func(self, request, *args, **kwargs)

            # Cache the response
            await cache.set(request, response)

            return response
        return wrapper
    return decorator
