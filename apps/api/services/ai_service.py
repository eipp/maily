"""
AI service that handles interactions with AI models.
Implements caching for improved performance.
"""
from typing import Dict, Any, Optional, List
import logging
import os
import httpx
import json
from fastapi import Depends, HTTPException

from apps.api.services.base_service import BaseService, handle_common_exceptions
from apps.api.ai.adapters.base import ModelRequest, ModelResponse
from apps.api.ai.adapters.factory import get_adapter
from apps.api.ai.adapters.caching import AdapterCache, cached_response
from apps.api.utils.resilience import circuit_breaker, CircuitBreakerOpenError
from apps.api.db.session import get_db
from apps.api.core.config import get_settings
from apps.api.schemas.ai import AIModelRequest, AIModelResponse


class AIService(BaseService):
    """
    Service for handling AI model interactions with caching support.

    This service provides methods for generating AI responses, managing
    model configurations, and optimizing performance through caching.
    It also integrates with the content safety service to ensure generated
    content meets safety standards.
    """

    def __init__(self, db=None, settings=None):
        """Initialize the AI service with optional DB session and settings."""
        super().__init__(db, settings)
        self.cache = AdapterCache(
            ttl_seconds=self.settings.AI_CACHE_TTL_SECONDS,
            max_size=self.settings.AI_CACHE_MAX_SIZE
        )
        self.logger = logging.getLogger("ai_service")
        
        # Initialize HTTP client for content safety service
        self.content_safety_url = os.getenv("CONTENT_SAFETY_URL", "http://ai-service:8000/content-safety")
        self.content_safety_enabled = os.getenv("CONTENT_SAFETY_ENABLED", "true").lower() == "true"
        self.content_safety_timeout = int(os.getenv("CONTENT_SAFETY_TIMEOUT", "3"))
        self.http_client = httpx.AsyncClient(timeout=self.content_safety_timeout)

    async def initialize(self):
        """Initialize the service."""
        await super().initialize()
        self.logger.info(f"AI service initialized with caching enabled, content safety: {self.content_safety_enabled}")
        
    async def close(self):
        """Clean up resources."""
        await self.http_client.aclose()
        self.logger.info("AI service resources cleaned up")

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
        
    @circuit_breaker(
        name="content_safety",
        failure_threshold=3,
        recovery_timeout=60.0,
        fallback_function=lambda content, *args, **kwargs: (content, False, {"fallback": True})
    )
    async def check_content_safety(self, content: str) -> tuple[str, bool, Dict[str, Any]]:
        """
        Check content for safety issues and filter if necessary.
        
        Args:
            content: The content to check
            
        Returns:
            Tuple of (filtered_content, was_filtered, safety_details)
        """
        if not self.content_safety_enabled:
            return content, False, {"enabled": False}
            
        try:
            response = await self.http_client.post(
                self.content_safety_url + "/filter",
                json={"content": content},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                filtered_content = result.get("filtered_content", content)
                was_filtered = result.get("was_filtered", False)
                safety_details = result.get("safety_details", {})
                
                if was_filtered:
                    self.logger.warning(
                        f"Content filtered for safety reasons: {json.dumps(safety_details)}"
                    )
                
                return filtered_content, was_filtered, safety_details
            else:
                self.logger.error(f"Content safety service error: {response.status_code} {response.text}")
                return content, False, {"error": f"Status code: {response.status_code}"}
                
        except Exception as e:
            self.logger.error(f"Content safety check failed: {str(e)}")
            return content, False, {"error": str(e)}

    @handle_common_exceptions
    async def generate_response(
        self,
        request: AIModelRequest
    ) -> AIModelResponse:
        """
        Generate a response from an AI model with caching support
        and content safety filtering.

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

        # Apply content safety filtering
        original_content = response.content
        filtered_content, was_filtered, safety_details = await self.check_content_safety(original_content)
        
        # Update response with filtered content if necessary
        if was_filtered:
            response.content = filtered_content
            
            # Add safety details to metadata
            if not response.metadata:
                response.metadata = {}
            response.metadata["safety_filtered"] = True
            response.metadata["safety_details"] = safety_details
            
            self.logger.info(
                f"Content safety filter applied to response from {request.model_name}",
                extra={
                    "safety_details": safety_details,
                    "model": request.model_name
                }
            )

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
                "tokens": response.usage.get("total_tokens", 0),
                "safety_filtered": was_filtered
            }
        )

        return AIModelResponse(
            content=response.content,
            model=response.model_name,
            usage=response.usage,
            finish_reason=response.finish_reason,
            cached=is_cached,
            metadata={
                "safety_filtered": was_filtered,
                "safety_details": safety_details if was_filtered else {}
            }
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
