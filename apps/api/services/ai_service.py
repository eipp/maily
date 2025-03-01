"""
AI service that handles interactions with AI models.
Implements caching for improved performance.
"""
from typing import Dict, Any, Optional, List
import logging
from fastapi import Depends, HTTPException

from apps.api.services.base_service import BaseService, handle_common_exceptions
from apps.api.ai.adapters.base import ModelRequest, ModelResponse
from apps.api.ai.adapters.factory import get_adapter
from apps.api.ai.adapters.caching import AdapterCache, cached_response
from apps.api.db.session import get_db
from apps.api.core.config import get_settings
from apps.api.schemas.ai import AIModelRequest, AIModelResponse


class AIService(BaseService):
    """
    Service for handling AI model interactions with caching support.

    This service provides methods for generating AI responses, managing
    model configurations, and optimizing performance through caching.
    """

    def __init__(self, db=None, settings=None):
        """Initialize the AI service with optional DB session and settings."""
        super().__init__(db, settings)
        self.cache = AdapterCache(
            ttl_seconds=self.settings.AI_CACHE_TTL_SECONDS,
            max_size=self.settings.AI_CACHE_MAX_SIZE
        )
        self.logger = logging.getLogger("ai_service")

    async def initialize(self):
        """Initialize the service."""
        await super().initialize()
        self.logger.info("AI service initialized with caching enabled")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.cache.get_stats()

    async def invalidate_cache(self, model_name: Optional[str] = None) -> int:
        """
        Invalidate cache entries.

        Args:
            model_name: Optional model name to invalidate only entries for that model

        Returns:
            Number of invalidated entries
        """
        key_pattern = None
        if model_name:
            key_pattern = f"model_name:{model_name}"

        count = await self.cache.invalidate(key_pattern)
        self.logger.info(f"Invalidated {count} cache entries")
        return count

    @handle_common_exceptions
    async def generate_response(
        self,
        request: AIModelRequest
    ) -> AIModelResponse:
        """
        Generate a response from an AI model with caching support.

        Args:
            request: The AI model request

        Returns:
            The AI model response
        """
        adapter = get_adapter(request.model_name)

        model_request = ModelRequest(
            prompt=request.prompt,
            model_name=request.model_name,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            frequency_penalty=request.frequency_penalty,
            presence_penalty=request.presence_penalty,
            stop_sequences=request.stop_sequences
        )

        # The cached_response decorator is applied at the adapter level
        response = await adapter.generate(model_request)

        # Log success with latency
        latency = response.metadata.get("latency", 0)
        is_cached = response.metadata.get("cached", False)
        cache_status = "cache hit" if is_cached else "cache miss"

        self.log_success(
            operation="generate_response",
            latency=latency,
            context={
                "model": request.model_name,
                "cache_status": cache_status,
                "tokens": response.usage.get("total_tokens", 0)
            }
        )

        return AIModelResponse(
            content=response.content,
            model=response.model_name,
            usage=response.usage,
            finish_reason=response.finish_reason,
            cached=is_cached
        )

    @handle_common_exceptions
    async def get_model_list(self) -> List[Dict[str, Any]]:
        """
        Get a list of available AI models.

        Returns:
            List of model information dictionaries
        """
        # This could be cached as well if the list doesn't change often
        models = [
            {
                "id": "gpt-3.5-turbo",
                "name": "GPT-3.5 Turbo",
                "provider": "openai",
                "max_tokens": 4096,
                "supports_streaming": True
            },
            {
                "id": "gpt-4",
                "name": "GPT-4",
                "provider": "openai",
                "max_tokens": 8192,
                "supports_streaming": True
            },
            # Add more models as needed
        ]

        return models


# Factory function for dependency injection
def get_ai_service(
    db=Depends(get_db),
    settings=Depends(get_settings)
) -> AIService:
    """Create and return an AIService instance."""
    return AIService(db, settings)
