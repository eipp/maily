"""
AI Model Adapter Factory

Provides a centralized factory for creating and managing model adapters,
supporting dynamic registration, metrics, and caching.
"""

import logging
import time
from typing import Dict, List, Optional, Type, Any, Union
import os
import threading
from pydantic import BaseModel, Field

from .base import BaseModelAdapter, ModelRequest, ModelResponse
from .openai_adapter import OpenAIAdapter
from .anthropic_adapter import AnthropicAdapter
from .google_adapter import GoogleAIAdapter
from .deepseek_adapter import DeepSeekAdapter
from apps.api.errors.ai_service_errors import UnsupportedModelError, AIServiceError

logger = logging.getLogger(__name__)

# Constants for provider identification
PROVIDER_MODEL_PREFIXES = {
    "openai": ["gpt-", "text-embedding-", "text-davinci-", "dall-e"],
    "anthropic": ["claude-"],
    "google": ["gemini-"],
}

# Default timeout for adapter operations
DEFAULT_ADAPTER_TIMEOUT = int(os.environ.get("DEFAULT_ADAPTER_TIMEOUT", "60"))

class AdapterMetrics(BaseModel):
    """
    Metrics for tracking adapter usage and performance.
    """
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_latency: float = 0
    last_error: Optional[str] = None
    last_error_time: Optional[float] = None
    last_success_time: Optional[float] = None
    created_at: float = Field(default_factory=time.time)

    def record_success(self, latency: float):
        """Record a successful call."""
        self.total_calls += 1
        self.successful_calls += 1
        self.total_latency += latency
        self.last_success_time = time.time()

    def record_failure(self, error: str):
        """Record a failed call."""
        self.total_calls += 1
        self.failed_calls += 1
        self.last_error = error
        self.last_error_time = time.time()

    @property
    def success_rate(self) -> float:
        """Calculate the success rate."""
        if self.total_calls == 0:
            return 0.0
        return self.successful_calls / self.total_calls

    @property
    def average_latency(self) -> float:
        """Calculate the average latency."""
        if self.successful_calls == 0:
            return 0.0
        return self.total_latency / self.successful_calls


class ModelAdapterFactory:
    """
    Factory class for creating and managing model adapters.

    This class provides a centralized way to create and access model adapters,
    ensuring that only one instance of each adapter type is created.
    It also provides metrics, caching, and dynamic registration capabilities.
    """

    def __init__(self):
        """Initialize the factory with empty adapter registry."""
        self._adapters: Dict[str, BaseModelAdapter] = {}
        self._adapter_classes: Dict[str, Type[BaseModelAdapter]] = {
            "openai": OpenAIAdapter,
            "anthropic": AnthropicAdapter,
            "google": GoogleAIAdapter,
        }
        self._metrics: Dict[str, AdapterMetrics] = {}
        self._lock = threading.RLock()  # Thread-safe lock for adapter creation
        self._fallback_order = ["openai", "anthropic", "google"]  # Default fallback order

        logger.info("ModelAdapterFactory initialized with providers: " +
                   ", ".join(self._adapter_classes.keys()))

    def register_adapter_class(self, provider: str, adapter_class: Type[BaseModelAdapter]) -> None:
        """
        Register a new adapter class for a provider.

        Args:
            provider: The name of the provider (e.g., "openai", "anthropic").
            adapter_class: The adapter class to register.

        Raises:
            ValueError: If the provider name is invalid or already registered
        """
        provider = provider.lower()

        if not provider or not isinstance(provider, str):
            raise ValueError(f"Invalid provider name: {provider}")

        with self._lock:
            if provider in self._adapter_classes:
                logger.warning(f"Overriding existing adapter class for provider: {provider}")

            self._adapter_classes[provider] = adapter_class
            logger.info(f"Registered adapter class for provider: {provider}")

    def get_adapter(
        self,
        provider: str,
        api_key: Optional[str] = None,
        timeout: int = DEFAULT_ADAPTER_TIMEOUT
    ) -> BaseModelAdapter:
        """
        Get an adapter instance for the specified provider.

        If an adapter for the provider already exists, return it.
        Otherwise, create a new adapter instance.

        Args:
            provider: The name of the provider (e.g., "openai", "anthropic").
            api_key: Optional API key for the provider.
            timeout: Optional timeout for adapter operations in seconds.

        Returns:
            An adapter instance for the specified provider.

        Raises:
            ValueError: If the provider is not supported.
        """
        provider = provider.lower()

        # Check if we have a registered adapter class for this provider
        if provider not in self._adapter_classes:
            available_providers = ", ".join(self._adapter_classes.keys())
            raise ValueError(
                f"Unsupported provider: {provider}. "
                f"Available providers: {available_providers}"
            )

        # Create a unique key for this adapter configuration
        adapter_key = f"{provider}:{api_key or 'default'}"

        with self._lock:
            # Check if we already have an adapter for this provider/api_key
            if adapter_key in self._adapters:
                return self._adapters[adapter_key]

            # Create a new adapter instance
            adapter_class = self._adapter_classes[provider]

            try:
                logger.info(f"Creating new adapter for provider: {provider}")
                adapter = adapter_class(api_key=api_key, timeout=timeout)

                # Store the adapter for future use
                self._adapters[adapter_key] = adapter

                # Initialize metrics
                self._metrics[adapter_key] = AdapterMetrics()

                return adapter
            except Exception as e:
                logger.error(f"Failed to create adapter for provider {provider}: {str(e)}")
                raise

    def get_adapter_for_model(
        self,
        model_name: str,
        api_key: Optional[str] = None,
        timeout: int = DEFAULT_ADAPTER_TIMEOUT,
        fallback: bool = False
    ) -> BaseModelAdapter:
        """
        Get an adapter instance for the specified model.

        This method determines the provider based on the model name and returns
        the appropriate adapter.

        Args:
            model_name: The name of the model (e.g., "gpt-4", "claude-3-opus").
            api_key: Optional API key for the provider.
            timeout: Optional timeout for adapter operations in seconds.
            fallback: Whether to try fallback providers if primary provider is unavailable.

        Returns:
            An adapter instance for the specified model.

        Raises:
            UnsupportedModelError: If the model is not supported by any provider.
        """
        # Determine the provider based on the model name
        provider = self._detect_provider_for_model(model_name)

        if provider:
            try:
                return self.get_adapter(provider, api_key, timeout)
            except Exception as e:
                if not fallback:
                    # If fallback is disabled, raise the exception
                    raise

                logger.warning(
                    f"Primary provider {provider} for model {model_name} unavailable: {str(e)}. "
                    f"Trying fallbacks."
                )
                # Continue to fallback logic

        # If provider is not detected or fallback is enabled and primary provider failed
        if fallback:
            errors = []

            # Try each provider in fallback order
            for fallback_provider in self._fallback_order:
                # Skip the already-tried primary provider
                if fallback_provider == provider:
                    continue

                try:
                    logger.info(f"Trying fallback provider {fallback_provider} for model {model_name}")
                    return self.get_adapter(fallback_provider, api_key, timeout)
                except Exception as e:
                    error_msg = f"Fallback provider {fallback_provider} unavailable: {str(e)}"
                    logger.warning(error_msg)
                    errors.append(error_msg)

            # If we get here, all fallbacks failed
            error_details = "; ".join(errors)
            raise AIServiceError(
                f"All providers failed for model {model_name}. Details: {error_details}"
            )

        # If no provider is detected and fallback is disabled
        raise UnsupportedModelError(
            f"Unsupported model: {model_name}. Cannot detect provider."
        )

    def _detect_provider_for_model(self, model_name: str) -> Optional[str]:
        """
        Detect the provider for a given model name.

        Args:
            model_name: The name of the model.

        Returns:
            The name of the provider, or None if not detected.
        """
        model_name = model_name.lower()

        # Check each provider's model prefixes
        for provider, prefixes in PROVIDER_MODEL_PREFIXES.items():
            for prefix in prefixes:
                if model_name.startswith(prefix):
                    return provider

        return None

    def set_fallback_order(self, providers: List[str]) -> None:
        """
        Set the order of fallback providers.

        Args:
            providers: List of provider names in fallback order.

        Raises:
            ValueError: If any provider in the list is not supported.
        """
        # Validate all providers
        for provider in providers:
            if provider.lower() not in self._adapter_classes:
                raise ValueError(f"Unsupported provider in fallback list: {provider}")

        # Set fallback order with normalized provider names
        self._fallback_order = [p.lower() for p in providers]
        logger.info(f"Set fallback order: {', '.join(self._fallback_order)}")

    async def generate_with_fallbacks(
        self,
        request: ModelRequest,
        fallback_models: Optional[List[str]] = None
    ) -> ModelResponse:
        """
        Generate a response, falling back to alternative models if needed.

        Args:
            request: The model request.
            fallback_models: Optional list of fallback models to try if the primary model fails.

        Returns:
            The generated response.

        Raises:
            AIServiceError: If all models fail.
        """
        models_to_try = [request.model_name]
        if fallback_models:
            models_to_try.extend(fallback_models)

        last_error = None

        for model in models_to_try:
            try:
                # Create a new request with the current model
                current_request = ModelRequest(
                    **request.dict(exclude={"model_name"}),
                    model_name=model
                )

                # Get the adapter for this model
                adapter = self.get_adapter_for_model(model, fallback=True)

                # Generate the response
                start_time = time.time()
                response = await adapter.generate(current_request)
                latency = time.time() - start_time

                # Update metrics
                self._record_success(adapter, "generate", latency)

                # Add fallback information to metadata if this wasn't the primary model
                if model != request.model_name:
                    response.metadata.update({
                        "fallback_from": request.model_name,
                        "fallback_to": model,
                        "fallback_reason": str(last_error) if last_error else "Unknown"
                    })

                return response

            except Exception as e:
                last_error = e
                logger.warning(f"Model {model} failed: {str(e)}. Trying next fallback.")

                # Update metrics
                try:
                    adapter = self.get_adapter_for_model(model, fallback=False)
                    self._record_failure(adapter, "generate", str(e))
                except Exception:
                    # If we can't get the adapter, we can't record metrics
                    pass

        # If we get here, all models failed
        raise AIServiceError(
            f"All models failed. Last error: {str(last_error) if last_error else 'Unknown'}"
        )

    def _record_success(self, adapter: BaseModelAdapter, operation: str, latency: float) -> None:
        """Record a successful adapter operation in metrics."""
        adapter_key = self._get_adapter_key(adapter)
        if adapter_key in self._metrics:
            self._metrics[adapter_key].record_success(latency)

    def _record_failure(self, adapter: BaseModelAdapter, operation: str, error: str) -> None:
        """Record a failed adapter operation in metrics."""
        adapter_key = self._get_adapter_key(adapter)
        if adapter_key in self._metrics:
            self._metrics[adapter_key].record_failure(error)

    def _get_adapter_key(self, adapter: BaseModelAdapter) -> str:
        """Get the key for an adapter in the metrics dictionary."""
        for key, stored_adapter in self._adapters.items():
            if stored_adapter is adapter:
                return key
        return "unknown"

    def list_providers(self) -> List[str]:
        """
        List all registered providers.

        Returns:
            A list of provider names.
        """
        return list(self._adapter_classes.keys())

    def list_adapters(self) -> List[str]:
        """
        List all active adapters.

        Returns:
            A list of provider names for which adapters have been created.
        """
        return [key.split(":")[0] for key in self._adapters.keys()]

    def get_metrics(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Get metrics for adapters.

        Args:
            provider: Optional provider name to filter metrics by.

        Returns:
            Dictionary of metrics by adapter.
        """
        result = {}

        for key, metrics in self._metrics.items():
            adapter_provider = key.split(":")[0]

            if provider and adapter_provider != provider.lower():
                continue

            result[key] = metrics.dict()

        return result

    async def check_all_health(self) -> Dict[str, Any]:
        """
        Check the health of all active adapters.

        Returns:
            Dictionary of health status by provider.
        """
        result = {}

        for key, adapter in self._adapters.items():
            provider = key.split(":")[0]

            try:
                health = await adapter.check_health()
                result[provider] = health
            except Exception as e:
                result[provider] = {
                    "status": "unhealthy",
                    "error": str(e)
                }

        return result

    def clear_cache(self) -> None:
        """Clear any cached data in the factory and adapters."""
        for adapter in self._adapters.values():
            if hasattr(adapter, "model_info_cache"):
                adapter.model_info_cache = {}

        logger.info("Cleared adapter caches")


# Create a singleton instance of the factory
model_adapter_factory = ModelAdapterFactory()

def create_model_adapter(provider: str, config: Dict[str, Any]) -> BaseModelAdapter:
    """Create a model adapter based on the provider."""
    if provider == "openai":
        return OpenAIAdapter(
            api_key=config.get("api_key"),
            timeout=config.get("timeout", 60)
        )
    elif provider == "anthropic":
        return AnthropicAdapter(
            api_key=config.get("api_key"),
            timeout=config.get("timeout", 60)
        )
    elif provider == "google":
        return GoogleAIAdapter(
            api_key=config.get("api_key"),
            timeout=config.get("timeout", 60)
        )
    elif provider == "deepseek":
        return DeepSeekAdapter(
            api_key=config.get("api_key"),
            base_url=config.get("base_url", "https://api.deepseek.com"),
            timeout=config.get("timeout", 60)
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")
