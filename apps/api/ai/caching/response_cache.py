"""
Model Response Cache

This module provides a caching service for AI model responses to enhance
performance and reduce costs by avoiding duplicate requests.
"""

import hashlib
import json
import logging
import time
from typing import Dict, Any, Optional, List, Tuple, Set
import os

from ...cache.tiered_cache_service import CacheService

logger = logging.getLogger(__name__)

# Cache TTL settings (in seconds)
CACHE_TTL = {
    "short": 300,      # 5 minutes
    "medium": 3600,    # 1 hour
    "long": 86400,     # 1 day
    "permanent": 0     # No expiration
}

# Cache key prefix
CACHE_PREFIX = "ai:model_response:"

# Minimum prompt length for caching
MIN_PROMPT_LENGTH = 10

# Maximum temperature for deterministic caching
MAX_DETERMINISTIC_TEMP = 0.3


class CacheableRequest:
    """
    Model for cacheable requests.

    This class models the data for cacheable requests, including methods
    to generate a deterministic cache key.
    """

    def __init__(
        self,
        prompt: str,
        model_name: str,
        temperature: float = 0.0,
        max_tokens: int = 1000,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        stop_sequences: Optional[List[str]] = None,
        user_id: Optional[str] = None,
    ):
        """
        Initialize a cacheable request.

        Args:
            prompt: The prompt to send to the model.
            model_name: The name of the model to use.
            temperature: Controls randomness. Higher values mean more random completions.
            max_tokens: The maximum number of tokens to generate.
            top_p: Controls diversity via nucleus sampling.
            frequency_penalty: Penalizes repeated tokens.
            presence_penalty: Penalizes repeated topics.
            stop_sequences: Sequences where the API will stop generating further tokens.
            user_id: A unique identifier representing the end-user.
        """
        self.prompt = prompt
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.stop_sequences = stop_sequences or []
        self.user_id = user_id

    def get_cache_key(self) -> str:
        """
        Generate a deterministic cache key for this request.

        Returns:
            A cache key string.
        """
        # Create a dictionary of parameters that affect the response
        key_dict = {
            "prompt": self.prompt,
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "stop_sequences": sorted(self.stop_sequences) if self.stop_sequences else [],
        }

        # Convert to a stable JSON string
        key_json = json.dumps(key_dict, sort_keys=True)

        # Hash the JSON string
        key_hash = hashlib.md5(key_json.encode()).hexdigest()

        return f"{CACHE_PREFIX}{key_hash}"


class CacheableResponse:
    """
    Model for cacheable responses.

    This class models the data for cacheable responses.
    """

    def __init__(
        self,
        content: str,
        model_name: str,
        usage: Dict[str, int],
        finish_reason: Optional[str] = None,
        cached_at: Optional[float] = None,
    ):
        """
        Initialize a cacheable response.

        Args:
            content: The generated content.
            model_name: The name of the model used.
            usage: Token usage statistics.
            finish_reason: The reason the model stopped generating.
            cached_at: Timestamp when the response was cached.
        """
        self.content = content
        self.model_name = model_name
        self.usage = usage
        self.finish_reason = finish_reason
        self.cached_at = cached_at or time.time()


class ModelResponseCache:
    """
    Cache service for AI model responses.

    This service provides caching for AI model responses to enhance
    performance and reduce costs by avoiding duplicate requests.
    """

    def __init__(self, cache_service: CacheService):
        """
        Initialize the model response cache.

        Args:
            cache_service: The cache service to use.
        """
        self.cache_service = cache_service

        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "errors": 0,
        }

        # Cache configuration
        self.ttl_config = self._load_ttl_config()
        self.enable_semantic_caching = os.environ.get("ENABLE_SEMANTIC_CACHING", "false").lower() == "true"
        self.semantic_similarity_threshold = float(os.environ.get("SEMANTIC_SIMILARITY_THRESHOLD", "0.95"))

        # Semantic cache index (prompt hash -> embedding)
        self.semantic_index = {}

        # Cache hit tracking for analytics
        self.recent_hits = []
        self.max_recent_hits = 1000

        logger.info(f"Model response cache initialized with TTL config: {self.ttl_config}")
        if self.enable_semantic_caching:
            logger.info(f"Semantic caching enabled with threshold: {self.semantic_similarity_threshold}")

    def _load_ttl_config(self) -> Dict[str, int]:
        """
        Load TTL configuration from environment variables.

        Returns:
            Dictionary of TTL configurations.
        """
        ttl_config = CACHE_TTL.copy()

        # Override from environment if available
        env_ttl_short = os.environ.get("CACHE_TTL_SHORT")
        if env_ttl_short:
            ttl_config["short"] = int(env_ttl_short)

        env_ttl_medium = os.environ.get("CACHE_TTL_MEDIUM")
        if env_ttl_medium:
            ttl_config["medium"] = int(env_ttl_medium)

        env_ttl_long = os.environ.get("CACHE_TTL_LONG")
        if env_ttl_long:
            ttl_config["long"] = int(env_ttl_long)

        return ttl_config

    async def get(self, request: CacheableRequest) -> Optional[CacheableResponse]:
        """
        Get a cached response for a request.

        Args:
            request: The request to get a cached response for.

        Returns:
            A cached response, or None if no cached response is found.
        """
        try:
            # Get cache key
            cache_key = request.get_cache_key()

            # Try to get from cache
            cached_data = await self.cache_service.get(cache_key)

            if cached_data:
                # Update stats
                self.stats["hits"] += 1

                # Track hit for analytics
                self._track_hit(request)

                # Deserialize response
                response_dict = json.loads(cached_data)

                return CacheableResponse(
                    content=response_dict["content"],
                    model_name=response_dict["model_name"],
                    usage=response_dict["usage"],
                    finish_reason=response_dict.get("finish_reason"),
                    cached_at=response_dict.get("cached_at"),
                )
            else:
                # Try semantic cache if enabled
                if self.enable_semantic_caching and self.should_cache(request):
                    semantic_response = await self._get_from_semantic_cache(request)
                    if semantic_response:
                        return semantic_response

                # Update stats
                self.stats["misses"] += 1

                return None
        except Exception as e:
            logger.error(f"Error getting cached response: {e}")
            self.stats["errors"] += 1
            return None

    async def set(self, request: CacheableRequest, response: CacheableResponse) -> bool:
        """
        Cache a response for a request.

        Args:
            request: The request to cache a response for.
            response: The response to cache.

        Returns:
            True if the response was cached, False otherwise.
        """
        try:
            # Check if we should cache this request
            if not self.should_cache(request):
                return False

            # Get cache key
            cache_key = request.get_cache_key()

            # Serialize response
            response_dict = {
                "content": response.content,
                "model_name": response.model_name,
                "usage": response.usage,
                "finish_reason": response.finish_reason,
                "cached_at": response.cached_at,
            }

            # Determine TTL based on model and usage
            ttl = self._determine_ttl(request, response)

            # Set in cache
            success = await self.cache_service.set(
                cache_key,
                json.dumps(response_dict),
                ttl=ttl
            )

            if success:
                # Update stats
                self.stats["sets"] += 1

                # Add to semantic cache if enabled
                if self.enable_semantic_caching:
                    await self._add_to_semantic_cache(request, response)

            return success
        except Exception as e:
            logger.error(f"Error caching response: {e}")
            self.stats["errors"] += 1
            return False

    def should_cache(self, request: CacheableRequest) -> bool:
        """
        Determine if a request should be cached.

        Args:
            request: The request to check.

        Returns:
            True if the request should be cached, False otherwise.
        """
        # Don't cache if prompt is too short
        if len(request.prompt) < MIN_PROMPT_LENGTH:
            return False

        # Don't cache non-deterministic requests (high temperature)
        if request.temperature > MAX_DETERMINISTIC_TEMP:
            return False

        # Don't cache if model is not suitable for caching
        non_cacheable_models = ["gpt-4-vision", "claude-3-opus-vision"]
        if any(model in request.model_name for model in non_cacheable_models):
            return False

        return True

    def _determine_ttl(self, request: CacheableRequest, response: CacheableResponse) -> int:
        """
        Determine the TTL for a cached response.

        Args:
            request: The request.
            response: The response.

        Returns:
            TTL in seconds.
        """
        # Factual queries with deterministic responses can be cached longer
        if request.temperature < 0.1:
            # Check if response is large (likely more valuable)
            if response.usage.get("completion_tokens", 0) > 500:
                return self.ttl_config["long"]
            else:
                return self.ttl_config["medium"]

        # Default to short TTL for most responses
        return self.ttl_config["short"]

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary of cache statistics.
        """
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_ratio = self.stats["hits"] / total_requests if total_requests > 0 else 0

        return {
            **self.stats,
            "hit_ratio": hit_ratio,
            "total_requests": total_requests,
            "semantic_index_size": len(self.semantic_index) if self.enable_semantic_caching else 0,
        }

    def _track_hit(self, request: CacheableRequest) -> None:
        """
        Track a cache hit for analytics.

        Args:
            request: The request that hit the cache.
        """
        # Add to recent hits
        self.recent_hits.append({
            "model": request.model_name,
            "timestamp": time.time(),
            "prompt_length": len(request.prompt),
        })

        # Trim if needed
        if len(self.recent_hits) > self.max_recent_hits:
            self.recent_hits = self.recent_hits[-self.max_recent_hits:]

    async def _get_from_semantic_cache(self, request: CacheableRequest) -> Optional[CacheableResponse]:
        """
        Try to get a response from the semantic cache.

        Args:
            request: The request to get a response for.

        Returns:
            A cached response, or None if no similar request is found.
        """
        # This would use embeddings to find similar prompts
        # For now, we'll use a simple implementation based on prompt similarity

        # In a real implementation, this would:
        # 1. Generate an embedding for the prompt
        # 2. Find the most similar prompt in the semantic index
        # 3. If similarity is above threshold, return the cached response

        # Placeholder for semantic caching - would be implemented with a vector DB
        return None

    async def _add_to_semantic_cache(self, request: CacheableRequest, response: CacheableResponse) -> None:
        """
        Add a response to the semantic cache.

        Args:
            request: The request.
            response: The response.
        """
        # This would add the prompt embedding to the semantic index
        # For now, we'll use a simple implementation

        # In a real implementation, this would:
        # 1. Generate an embedding for the prompt
        # 2. Store the embedding in the semantic index

        # Placeholder for semantic caching - would be implemented with a vector DB
        pass

    async def invalidate(self, pattern: str) -> int:
        """
        Invalidate cached responses matching a pattern.

        Args:
            pattern: The pattern to match.

        Returns:
            Number of invalidated responses.
        """
        try:
            # Add prefix if not already present
            if not pattern.startswith(CACHE_PREFIX):
                pattern = f"{CACHE_PREFIX}{pattern}"

            # Delete from cache
            count = await self.cache_service.delete_by_prefix(pattern)

            logger.info(f"Invalidated {count} cached responses matching pattern: {pattern}")

            return count
        except Exception as e:
            logger.error(f"Error invalidating cached responses: {e}")
            self.stats["errors"] += 1
            return 0

    async def clear(self) -> bool:
        """
        Clear all cached responses.

        Returns:
            True if the cache was cleared, False otherwise.
        """
        try:
            # Delete all cached responses
            count = await self.cache_service.delete_by_prefix(CACHE_PREFIX)

            # Reset stats
            self.stats = {
                "hits": 0,
                "misses": 0,
                "sets": 0,
                "errors": 0,
            }

            # Clear semantic index
            self.semantic_index = {}

            logger.info(f"Cleared {count} cached responses")

            return True
        except Exception as e:
            logger.error(f"Error clearing cached responses: {e}")
            self.stats["errors"] += 1
            return False
