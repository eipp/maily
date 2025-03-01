"""
Enhanced AI Orchestrator
Provides advanced orchestration capabilities for AI model requests with:
- Multi-model fallback strategies
- Confidence-based routing
- Chain-of-thought validation
- Performance monitoring
- Caching and rate limiting integration
"""
import os
import json
import time
import logging
import asyncio
import uuid
from typing import Dict, List, Optional, Any, Union, Type, Tuple
from pydantic import BaseModel, Field

from apps.api.ai.adapters.base import (
    EnhancedModelAdapter,
    EnhancedModelRequest,
    EnhancedModelResponse,
    ValidationResult,
    ModelProvider,
    ModelCapability,
    ConfidenceLevel
)
from apps.api.ai.adapters.openai_adapter import EnhancedOpenAIAdapter
# Import other adapters as they are implemented
# from apps.api.ai.adapters.enhanced_anthropic_adapter import EnhancedAnthropicAdapter
# from apps.api.ai.adapters.enhanced_google_adapter import EnhancedGoogleAdapter

# Configure logging
logger = logging.getLogger("ai.orchestration")


class RoutingStrategy(str, Enum):
    """Available routing strategies"""
    COST_OPTIMIZED = "cost_optimized"
    PERFORMANCE_OPTIMIZED = "performance_optimized"
    QUALITY_OPTIMIZED = "quality_optimized"
    FALLBACK_CHAIN = "fallback_chain"
    ENSEMBLE = "ensemble"
    ROUND_ROBIN = "round_robin"


class FallbackConfig(BaseModel):
    """Configuration for fallback behavior"""
    enabled: bool = True
    max_attempts: int = 3
    confidence_threshold: float = 0.7
    providers: List[ModelProvider] = []
    models: List[str] = []
    timeout_seconds: float = 30.0
    reasons: List[str] = ["timeout", "error", "low_confidence"]


class CachingConfig(BaseModel):
    """Configuration for response caching"""
    enabled: bool = True
    ttl_seconds: int = 3600  # 1 hour
    include_metadata_in_key: List[str] = []
    respect_no_cache: bool = True


class MetricsConfig(BaseModel):
    """Configuration for metrics collection"""
    enabled: bool = True
    detailed_logging: bool = True
    sample_rate: float = 1.0  # Percentage of requests to track (1.0 = 100%)
    export_metrics: bool = False
    export_destination: Optional[str] = None


class ValidationConfig(BaseModel):
    """Configuration for response validation"""
    enabled: bool = True
    default_validation_type: Optional[str] = None
    min_confidence_threshold: float = 0.7
    validation_timeout_seconds: float = 5.0


class ModelRouteConfig(BaseModel):
    """Configuration for a specific model route"""
    model: str
    provider: ModelProvider
    weight: float = 1.0
    capabilities: List[ModelCapability] = []
    timeout_seconds: float = 30.0
    concurrency_limit: Optional[int] = None
    cost_per_1k_tokens: Optional[float] = None


class OrchestratorConfig(BaseModel):
    """Main configuration for the AI orchestrator"""
    default_provider: ModelProvider = ModelProvider.OPENAI
    default_model: str = "gpt-4o"
    routing_strategy: RoutingStrategy = RoutingStrategy.FALLBACK_CHAIN
    fallback: FallbackConfig = Field(default_factory=FallbackConfig)
    caching: CachingConfig = Field(default_factory=CachingConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    model_routes: List[ModelRouteConfig] = []


class EnhancedAIOrchestrator:
    """
    Enhanced AI Orchestrator with advanced capabilities

    Features:
    - Multi-model provider support
    - Fallback strategies based on errors and confidence
    - Chain-of-thought validation
    - Performance metrics and monitoring
    - Automated scaling and routing
    - Integration with monitoring tools
    """

    def __init__(
        self,
        config: Union[OrchestratorConfig, Dict[str, Any]],
        api_keys: Optional[Dict[str, str]] = None,
        cache_client=None,
        metrics_client=None
    ):
        """Initialize the AI orchestrator with configuration"""
        # Convert dict config to OrchestratorConfig if needed
        if isinstance(config, dict):
            self.config = OrchestratorConfig(**config)
        else:
            self.config = config

        # Store API keys, defaulting to environment variables if not provided
        self.api_keys = api_keys or {}
        self._load_api_keys_from_env()

        # Initialize adapters for each provider
        self.adapters: Dict[ModelProvider, EnhancedModelAdapter] = {}
        self._initialize_adapters()

        # Cache and metrics clients
        self.cache_client = cache_client
        self.metrics_client = metrics_client

        # Metrics tracking
        self.request_metrics: List[Dict[str, Any]] = []
        self.max_metrics_history = 1000

        logger.info("EnhancedAIOrchestrator initialized with strategy: %s", self.config.routing_strategy)

    def _load_api_keys_from_env(self):
        """Load API keys from environment variables if not provided"""
        for provider in ModelProvider:
            env_var = f"{provider.upper()}_API_KEY"
            if provider not in self.api_keys and env_var in os.environ:
                self.api_keys[provider] = os.environ[env_var]

    def _initialize_adapters(self):
        """Initialize adapters for each configured provider"""
        # Initialize OpenAI adapter if key is available
        if ModelProvider.OPENAI in self.api_keys:
            self.adapters[ModelProvider.OPENAI] = EnhancedOpenAIAdapter(
                api_key=self.api_keys[ModelProvider.OPENAI],
                default_model=self.config.default_model if self.config.default_provider == ModelProvider.OPENAI else "gpt-4o"
            )
            logger.info("Initialized OpenAI adapter")

        # Initialize other adapters as they are implemented
        # if ModelProvider.ANTHROPIC in self.api_keys:
        #     self.adapters[ModelProvider.ANTHROPIC] = EnhancedAnthropicAdapter(
        #         api_key=self.api_keys[ModelProvider.ANTHROPIC],
        #         default_model="claude-3-opus-20240229"
        #     )
        #     logger.info("Initialized Anthropic adapter")

        # if ModelProvider.GOOGLE in self.api_keys:
        #     self.adapters[ModelProvider.GOOGLE] = EnhancedGoogleAdapter(
        #         api_key=self.api_keys[ModelProvider.GOOGLE],
        #         default_model="gemini-1.5-pro"
        #     )
        #     logger.info("Initialized Google adapter")

    async def _get_cache_key(self, request: EnhancedModelRequest) -> str:
        """Generate a cache key for a request"""
        # Base key components
        key_components = [
            request.model_name,
            request.provider,
            request.prompt,
            str(request.temperature),
            str(request.max_tokens)
        ]

        # Add specified metadata fields to the key if configured
        for field in self.config.caching.include_metadata_in_key:
            if field in request.metadata:
                key_components.append(f"{field}:{request.metadata[field]}")

        # Create a deterministic key
        key = ":".join(key_components)

        # Use a hash of the key to keep it manageable in size
        import hashlib
        return f"ai:response:{hashlib.md5(key.encode()).hexdigest()}"

    async def _check_cache(self, request: EnhancedModelRequest) -> Optional[EnhancedModelResponse]:
        """Check if a response exists in cache"""
        if not self.config.caching.enabled or not self.cache_client:
            return None

        # Skip cache if explicitly requested
        if request.metadata.get("no_cache") and self.config.caching.respect_no_cache:
            return None

        try:
            # Generate cache key
            cache_key = await self._get_cache_key(request)

            # Check cache
            cached_data = await self.cache_client.get(cache_key)
            if cached_data:
                # Deserialize response
                response_dict = json.loads(cached_data)
                response = EnhancedModelResponse(**response_dict)

                # Update cached response
                response.metadata["cached"] = True
                response.metadata["cache_time"] = time.time()

                logger.info(f"Cache hit for model {request.model_name}")
                return response

        except Exception as e:
            logger.warning(f"Error checking cache: {str(e)}")

        return None

    async def _store_in_cache(self, request: EnhancedModelRequest, response: EnhancedModelResponse):
        """Store a response in cache"""
        if not self.config.caching.enabled or not self.cache_client:
            return

        # Skip caching if explicitly requested
        if request.metadata.get("no_cache") and self.config.caching.respect_no_cache:
            return

        # Skip caching low confidence or invalid responses
        if (response.validation.confidence_score < self.config.validation.min_confidence_threshold or
            not response.validation.is_valid):
            return

        try:
            # Generate cache key
            cache_key = await self._get_cache_key(request)

            # Store in cache
            response_dict = response.dict()
            await self.cache_client.set(
                cache_key,
                json.dumps(response_dict),
                expire=self.config.caching.ttl_seconds
            )

            logger.debug(f"Stored response in cache for model {request.model_name}")

        except Exception as e:
            logger.warning(f"Error storing in cache: {str(e)}")

    async def _track_request_metrics(
        self,
        request: EnhancedModelRequest,
        response: EnhancedModelResponse,
        start_time: float,
        adapter_metrics: Optional[Dict[str, Any]] = None
    ):
        """Track request metrics"""
        if not self.config.metrics.enabled:
            return

        try:
            # Calculate metrics
            latency = (time.time() - start_time) * 1000  # ms

            # Create metrics object
            metrics = {
                "request_id": request.trace_id or str(uuid.uuid4()),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "model": request.model_name,
                "provider": request.provider,
                "latency_ms": latency,
                "input_tokens": response.prompt_tokens or 0,
                "output_tokens": response.completion_tokens or 0,
                "total_tokens": response.total_tokens or 0,
                "success": response.validation.is_valid,
                "confidence_score": response.validation.confidence_score,
                "confidence_level": response.validation.confidence_level,
                "cost_estimate_usd": response.cost_estimate_usd,
                "user_id": request.user_id,
                "validation_type": request.validation_type
            }

            # Add adapter-specific metrics if available
            if adapter_metrics:
                metrics.update(adapter_metrics)

            # Add to metrics history (limited size)
            self.request_metrics.append(metrics)
            if len(self.request_metrics) > self.max_metrics_history:
                self.request_metrics.pop(0)

            # Send to metrics client if available
            if self.metrics_client and self.config.metrics.export_metrics:
                await self.metrics_client.send_metrics("ai_request", metrics)

            # Detailed logging if enabled
            if self.config.metrics.detailed_logging:
                log_msg = (
                    f"AI Request: {request.model_name} ({request.provider}) - "
                    f"{latency:.2f}ms - {metrics['total_tokens']} tokens - "
                    f"${metrics['cost_estimate_usd']:.6f} - "
                    f"Confidence: {metrics['confidence_score']:.2f}"
                )
                logger.info(log_msg)

        except Exception as e:
            logger.warning(f"Error tracking metrics: {str(e)}")

    async def _should_fallback(
        self,
        response: EnhancedModelResponse,
        attempt: int
    ) -> Tuple[bool, str]:
        """Determine if a fallback should be triggered"""
        if not self.config.fallback.enabled:
            return False, ""

        # Check max attempts
        if attempt >= self.config.fallback.max_attempts:
            return False, "max_attempts_reached"

        # Check for errors
        if "error" in response.metadata:
            return True, "error"

        # Check confidence threshold
        if (response.validation.confidence_score < self.config.fallback.confidence_threshold and
            "low_confidence" in self.config.fallback.reasons):
            return True, "low_confidence"

        return False, ""

    async def _get_fallback_provider_and_model(
        self,
        current_provider: ModelProvider,
        current_model: str,
        fallback_reason: str
    ) -> Tuple[ModelProvider, str]:
        """Get the next provider and model to try for fallback"""
        # If specific fallback providers are configured, use those
        if self.config.fallback.providers:
            for provider in self.config.fallback.providers:
                if provider != current_provider and provider in self.adapters:
                    # Use the default model for this provider
                    adapter = self.adapters[provider]
                    return provider, adapter.default_model

        # If specific fallback models are configured, use those
        if self.config.fallback.models:
            for model in self.config.fallback.models:
                # Skip the current model
                if model == current_model:
                    continue

                # Find a provider that supports this model
                for provider, adapter in self.adapters.items():
                    # Check if this provider supports the model
                    model_info = await adapter.get_model_info()
                    if model in model_info.get("available_models", []):
                        return provider, model

        # Default fallback: OpenAI GPT-3.5 for cost/reliability reasons
        if (ModelProvider.OPENAI in self.adapters and
            current_provider != ModelProvider.OPENAI and
            current_model != "gpt-3.5-turbo"):
            return ModelProvider.OPENAI, "gpt-3.5-turbo"

        # If no suitable fallback, just use default
        return self.config.default_provider, self.config.default_model

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        provider: Optional[ModelProvider] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system_message: Optional[str] = None,
        validation_type: Optional[str] = None,
        expected_format: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> EnhancedModelResponse:
        """
        High-level method to generate a response with the AI orchestrator.

        This is the main entry point for most use cases, providing a simple interface
        while leveraging all the advanced capabilities internally.
        """
        # Create request object with defaults if not provided
        request = EnhancedModelRequest(
            prompt=prompt,
            model_name=model or self.config.default_model,
            provider=provider or self.config.default_provider,
            temperature=temperature,
            max_tokens=max_tokens,
            validation_type=validation_type or self.config.validation.default_validation_type,
            expected_format=expected_format,
            trace_id=trace_id or str(uuid.uuid4()),
            user_id=user_id,
            tools=tools or [],
            metadata=metadata or {}
        )

        # Add system message to metadata if provided
        if system_message:
            request.metadata["system_message"] = system_message

        # Use the full generation method
        return await self.generate_with_request(request)

    async def generate_with_request(
        self,
        request: EnhancedModelRequest
    ) -> EnhancedModelResponse:
        """
        Generate a response using the full request object.

        This method handles:
        - Caching
        - Provider selection
        - Fallback strategies
        - Validation
        - Metrics tracking
        """
        start_time = time.time()

        # Check cache first
        cached_response = await self._check_cache(request)
        if cached_response:
            return cached_response

        # Determine initial provider and model
        provider = request.provider or self.config.default_provider
        model = request.model_name or self.config.default_model

        # Try to generate response with fallback
        attempts = 0
        max_attempts = self.config.fallback.max_attempts

        while attempts < max_attempts:
            attempts += 1

            try:
                # Check if adapter exists for this provider
                if provider not in self.adapters:
                    logger.warning(f"No adapter available for provider {provider}, falling back to default")
                    provider = self.config.default_provider
                    model = self.config.default_model

                # Update request with current provider and model
                current_request = request.copy()
                current_request.provider = provider
                current_request.model_name = model

                # Get adapter
                adapter = self.adapters[provider]

                # Generate response
                response = await adapter.enhanced_generate(current_request)

                # Check if fallback should be triggered
                should_fallback, reason = await self._should_fallback(response, attempts)
                if should_fallback:
                    logger.info(f"Fallback triggered: {reason}, attempt {attempts}/{max_attempts}")
                    provider, model = await self._get_fallback_provider_and_model(provider, model, reason)
                    continue

                # If we reach here, the response is acceptable

                # Store in cache if enabled
                await self._store_in_cache(request, response)

                # Track metrics
                await self._track_request_metrics(request, response, start_time)

                # Add attempt information to metadata
                response.metadata["attempts"] = attempts
                if attempts > 1:
                    response.metadata["fallback_used"] = True

                return response

            except Exception as e:
                logger.error(f"Error generating response: {str(e)}")

                # Create error response
                error_response = EnhancedModelResponse(
                    content=f"Error: {str(e)}",
                    model_name=model,
                    usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                    finish_reason="error",
                    metadata={
                        "error": str(e),
                        "attempts": attempts
                    },
                    provider=provider,
                    trace_id=request.trace_id,
                    processing_time_ms=(time.time() - start_time) * 1000,
                    validation=ValidationResult(
                        is_valid=False,
                        errors=[str(e)],
                        confidence_score=0.0,
                        confidence_level=ConfidenceLevel.UNCERTAIN
                    )
                )

                # Check if fallback should be tried
                if self.config.fallback.enabled and "error" in self.config.fallback.reasons and attempts < max_attempts:
                    logger.info(f"Fallback triggered due to error: {str(e)}, attempt {attempts}/{max_attempts}")
                    provider, model = await self._get_fallback_provider_and_model(provider, model, "error")
                    continue

                # Track error metrics
                await self._track_request_metrics(request, error_response, start_time)

                return error_response

        # If we reach here, all attempts failed
        logger.error(f"All {max_attempts} generation attempts failed")

        # Create final error response
        final_error_response = EnhancedModelResponse(
            content="Error: Unable to generate response after multiple attempts",
            model_name=model,
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            finish_reason="error",
            metadata={
                "error": "All generation attempts failed",
                "attempts": attempts,
                "max_attempts": max_attempts
            },
            provider=provider,
            trace_id=request.trace_id,
            processing_time_ms=(time.time() - start_time) * 1000,
            validation=ValidationResult(
                is_valid=False,
                errors=["All generation attempts failed"],
                confidence_score=0.0,
                confidence_level=ConfidenceLevel.UNCERTAIN
            )
        )

        # Track error metrics
        await self._track_request_metrics(request, final_error_response, start_time)

        return final_error_response

    async def get_metrics(
        self,
        limit: int = 100,
        provider: Optional[ModelProvider] = None,
        model: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get request metrics with optional filtering"""
        # Filter metrics based on criteria
        filtered_metrics = self.request_metrics

        # Filter by provider
        if provider:
            filtered_metrics = [m for m in filtered_metrics if m.get("provider") == provider]

        # Filter by model
        if model:
            filtered_metrics = [m for m in filtered_metrics if m.get("model") == model]

        # Filter by time range
        if start_time:
            filtered_metrics = [m for m in filtered_metrics if m.get("timestamp", "") >= start_time]

        if end_time:
            filtered_metrics = [m for m in filtered_metrics if m.get("timestamp", "") <= end_time]

        # Return limited number of metrics
        return filtered_metrics[-limit:]

    async def get_aggregate_metrics(self) -> Dict[str, Any]:
        """Get aggregate metrics for AI requests"""
        metrics = self.request_metrics

        if not metrics:
            return {
                "count": 0,
                "success_rate": 0,
                "avg_latency_ms": 0,
                "total_tokens": 0,
                "total_cost_usd": 0,
                "avg_confidence": 0
            }

        # Calculate aggregates
        total_requests = len(metrics)
        successful_requests = sum(1 for m in metrics if m.get("success", False))
        success_rate = successful_requests / total_requests if total_requests > 0 else 0

        # Latency stats
        latencies = [m.get("latency_ms", 0) for m in metrics]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0

        # Token usage
        total_tokens = sum(m.get("total_tokens", 0) for m in metrics)
        total_cost = sum(m.get("cost_estimate_usd", 0) for m in metrics)

        # Confidence stats
        confidence_scores = [m.get("confidence_score", 0) for m in metrics if "confidence_score" in m]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0

        # Provider distribution
        provider_counts = {}
        for m in metrics:
            provider = m.get("provider")
            if provider:
                provider_counts[provider] = provider_counts.get(provider, 0) + 1

        # Model distribution
        model_counts = {}
        for m in metrics:
            model = m.get("model")
            if model:
                model_counts[model] = model_counts.get(model, 0) + 1

        return {
            "count": total_requests,
            "success_rate": success_rate,
            "avg_latency_ms": avg_latency,
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost,
            "avg_confidence": avg_confidence,
            "provider_distribution": provider_counts,
            "model_distribution": model_counts
        }
