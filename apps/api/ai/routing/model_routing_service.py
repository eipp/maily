"""
Intelligent model routing service for AI requests.
Routes requests to appropriate model adapters based on task characteristics.
"""
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from enum import Enum
import asyncio
import time
import random
import json
import structlog
from datetime import datetime, timedelta

from ..adapters.base import ModelAdapter, ModelResponse
from ..errors import AIGenerationError, InvalidInputError, RoutingError, ModelUnavailableError
from ..fallback import fallback_service, FallbackChain
from ..monitoring.performance_metrics import MetricType, MetricsService

logger = structlog.get_logger(__name__)

class TaskComplexity(int, Enum):
    """Task complexity levels."""
    SIMPLE = 1      # Simple tasks (classification, short answers)
    MEDIUM = 2      # Medium complexity (summarization, short content generation)
    COMPLEX = 3     # Complex tasks (detailed content, reasoning)
    ADVANCED = 4    # Advanced tasks (multi-step reasoning, specialized knowledge)
    EXPERT = 5      # Expert tasks (creative, nuanced, highly specialized)

class ModelTier(str, Enum):
    """Model capability tiers."""
    BASIC = "basic"         # Basic models (GPT-3.5-like capabilities)
    STANDARD = "standard"   # Standard models (GPT-4-like capabilities)
    PREMIUM = "premium"     # Premium models (advanced capabilities)
    SPECIALIZED = "specialized"  # Domain-specific models

class RoutingStrategy(str, Enum):
    """Routing strategy options."""
    COST_EFFICIENT = "cost_efficient"  # Prioritize lower cost
    PERFORMANCE = "performance"        # Prioritize performance
    BALANCED = "balanced"              # Balance cost and performance
    RELIABILITY = "reliability"        # Prioritize reliability/uptime
    SPECIALIZED = "specialized"        # Use specialized models where appropriate

class ModelRoutingService:
    """Service for intelligently routing requests to appropriate model adapters.

    Attributes:
        adapters: Dict of model adapters
        performance_metrics: Performance tracking for models
        routing_strategy: Current routing strategy
        fallback_service: Service for handling model fallbacks
    """

    def __init__(
        self,
        model_adapters: Dict[str, ModelAdapter],
        metrics_service: Optional[MetricsService] = None,
        config: Dict[str, Any] = None
    ):
        """Initialize the routing service.

        Args:
            model_adapters: Dict mapping model IDs to adapters
            metrics_service: Optional metrics service for monitoring
            config: Optional configuration settings
        """
        self.adapters = model_adapters
        self.metrics = metrics_service
        self.config = config or {}

        # Initialize performance metrics
        self.performance_metrics: Dict[str, Dict[str, Any]] = {
            model_id: {
                "success_rate": 1.0,  # Start optimistic
                "average_latency_ms": 0,
                "cost_per_1k_tokens": adapter.get_cost_per_1k_tokens(),
                "last_failure": None,
                "consecutive_failures": 0,
                "total_calls": 0,
                "total_successes": 0,
                "total_failures": 0,
                "capabilities": adapter.get_capabilities(),
                "tier": adapter.get_tier(),
                "status": "available"
            }
            for model_id, adapter in model_adapters.items()
        }

        # Set routing strategy
        self.routing_strategy = RoutingStrategy(
            self.config.get("routing_strategy", RoutingStrategy.BALANCED)
        )

        # Use the fallback service instead of local fallback chains
        self.fallback_service = fallback_service

        # Task type routing preferences
        self.task_type_preferences = self.config.get("task_type_preferences", {})

        # Circuit breaker settings
        self.circuit_breaker_threshold = self.config.get("circuit_breaker_threshold", 3)
        self.circuit_breaker_reset_time = self.config.get("circuit_breaker_reset_time", 300) # 5 minutes

        logger.info("Model routing service initialized",
                    models_count=len(model_adapters),
                    routing_strategy=self.routing_strategy.value)

    async def generate_response(
        self,
        prompt: str,
        task_type: str,
        complexity: Union[TaskComplexity, int] = TaskComplexity.MEDIUM,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        top_p: float = 1.0,
        requirements: Dict[str, Any] = None,
        override_model: Optional[str] = None,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """Generate response using optimal model for task type.

        Args:
            prompt: Input prompt
            task_type: Type of task (affects routing)
            complexity: Task complexity
            max_tokens: Maximum tokens to generate
            temperature: Temperature parameter
            top_p: Top-p parameter
            requirements: Optional specific requirements
            override_model: Optional specific model to use
            timeout: Request timeout in seconds

        Returns:
            Dictionary with response and metadata

        Raises:
            AIGenerationError: If generation fails with all models
            InvalidInputError: If input is invalid
            RoutingError: If no suitable model found
        """
        # Track metrics for the request
        start_time = time.time()
        request_id = f"req_{int(start_time * 1000)}"

        # Log request
        logger.info("Generation request received",
                    request_id=request_id,
                    task_type=task_type,
                    complexity=complexity if isinstance(complexity, int) else complexity.value,
                    max_tokens=max_tokens,
                    prompt_length=len(prompt),
                    override_model=override_model)

        # Record metric
        if self.metrics:
            self.metrics.record_metric(
                metric_type=MetricType.AI_REQUEST,
                name=f"generation_request_{task_type}",
                metadata={
                    "request_id": request_id,
                    "task_type": task_type,
                    "complexity": complexity if isinstance(complexity, int) else complexity.value,
                    "max_tokens": max_tokens,
                    "prompt_length": len(prompt)
                }
            )

        # Use specific model if provided
        if override_model:
            if override_model not in self.adapters:
                raise InvalidInputError(f"Model '{override_model}' not found")

            model_id = override_model
            adapter = self.adapters[model_id]

            # Check if model is available
            if self._is_circuit_open(model_id):
                raise ModelUnavailableError(f"Model '{model_id}' is currently unavailable")

            # Generate with the specified model without fallbacks
            try:
                response = await asyncio.wait_for(
                    adapter.generate(
                        prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        top_p=top_p
                    ),
                    timeout=timeout
                )

                # Update metrics for success
                self._update_metrics(model_id, True, time.time() - start_time)

                result = self._prepare_result(
                    model_id,
                    response,
                    time.time() - start_time,
                    prompt_tokens=len(prompt.split()),
                    completion_tokens=len(response.content.split())
                )

                return result

            except Exception as e:
                # Update metrics for failure
                self._update_metrics(model_id, False, time.time() - start_time)

                # Log error
                logger.error("Generation failed with specified model",
                            request_id=request_id,
                            model_id=model_id,
                            error=str(e),
                            error_type=e.__class__.__name__)

                raise AIGenerationError(f"Failed to generate response with model '{model_id}': {str(e)}")

        # If no specific model, select optimal adapter using routing logic
        try:
            # Convert complexity to enum if needed
            if isinstance(complexity, int):
                complexity = TaskComplexity(complexity)

            # Normalize requirements
            requirements = requirements or {}

            # Get the optimal model and fallbacks
            model_chain = self._select_model_chain(
                task_type,
                complexity,
                requirements
            )

            if not model_chain:
                raise RoutingError("No suitable models available for this request")

            # Try each model in the chain
            for model_id in model_chain:
                # Skip if circuit breaker is open
                if self._is_circuit_open(model_id):
                    logger.warning("Skipping unavailable model",
                                  request_id=request_id,
                                  model_id=model_id)
                    continue

                adapter = self.adapters[model_id]

                try:
                    # Track model attempt
                    model_start_time = time.time()

                    # Generate response with timeout
                    response = await asyncio.wait_for(
                        adapter.generate(
                            prompt,
                            max_tokens=max_tokens,
                            temperature=temperature,
                            top_p=top_p
                        ),
                        timeout=timeout
                    )

                    # Calculate time taken
                    duration = time.time() - model_start_time

                    # Update metrics for success
                    self._update_metrics(model_id, True, duration)

                    # Prepare result with model information
                    result = self._prepare_result(
                        model_id,
                        response,
                        duration,
                        prompt_tokens=len(prompt.split()),
                        completion_tokens=len(response.content.split())
                    )

                    # Log success
                    logger.info("Generation successful",
                               request_id=request_id,
                               model_id=model_id,
                               duration_ms=int(duration * 1000),
                               fallback_position=model_chain.index(model_id))

                    # Record successful completion metric
                    if self.metrics:
                        self.metrics.record_metric(
                            metric_type=MetricType.AI_RESPONSE,
                            name=f"generation_success_{task_type}",
                            duration_ms=duration * 1000,
                            metadata={
                                "request_id": request_id,
                                "model_id": model_id,
                                "task_type": task_type,
                                "complexity": complexity.value,
                                "prompt_tokens": len(prompt.split()),
                                "completion_tokens": len(response.content.split())
                            }
                        )

                    return result

                except Exception as e:
                    # Update metrics for failure
                    self._update_metrics(model_id, False, time.time() - model_start_time)

                    # Log error for this model
                    logger.warning("Model generation failed, trying fallback",
                                  request_id=request_id,
                                  model_id=model_id,
                                  error=str(e),
                                  error_type=e.__class__.__name__)

                    # Continue to next model in chain
                    continue

            # If we get here, all models failed
            error_message = f"All models failed for task type {task_type}"

            logger.error("All models failed",
                        request_id=request_id,
                        task_type=task_type,
                        complexity=complexity.value)

            # Record error metric
            if self.metrics:
                self.metrics.record_metric(
                    metric_type=MetricType.AI_ERROR,
                    name=f"generation_all_failed_{task_type}",
                    duration_ms=(time.time() - start_time) * 1000,
                    metadata={
                        "request_id": request_id,
                        "task_type": task_type,
                        "complexity": complexity.value,
                        "error": error_message
                    },
                    success=False,
                    error=error_message
                )

            raise AIGenerationError(error_message)

        except AIGenerationError:
            # Re-raise existing generation errors
            raise

        except Exception as e:
            # Handle any other errors
            error_message = f"Unexpected error in model routing: {str(e)}"

            logger.error("Routing error",
                        request_id=request_id,
                        error=str(e),
                        error_type=e.__class__.__name__,
                        exc_info=True)

            # Record error metric
            if self.metrics:
                self.metrics.record_metric(
                    metric_type=MetricType.AI_ERROR,
                    name="generation_routing_error",
                    duration_ms=(time.time() - start_time) * 1000,
                    metadata={
                        "request_id": request_id,
                        "task_type": task_type,
                        "complexity": complexity.value if isinstance(complexity, TaskComplexity) else complexity,
                        "error": str(e),
                        "error_type": e.__class__.__name__
                    },
                    success=False,
                    error=str(e)
                )

            raise RoutingError(error_message)

    async def generate_with_retry(
        self,
        prompt: str,
        task_type: str,
        max_retries: int = 3,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate response with automatic retries.

        Args:
            prompt: Input prompt
            task_type: Type of task
            max_retries: Maximum retry attempts
            **kwargs: Additional parameters for generate_response

        Returns:
            Generation result

        Raises:
            AIGenerationError: If all retries fail
        """
        attempts = 0
        last_error = None

        while attempts <= max_retries:
            try:
                return await self.generate_response(prompt, task_type, **kwargs)
            except (AIGenerationError, RoutingError) as e:
                last_error = e
                attempts += 1

                if attempts <= max_retries:
                    # Exponential backoff with jitter
                    backoff_time = (2 ** attempts) + (random.random() * 0.5)

                    logger.warning("Retrying generation",
                                  task_type=task_type,
                                  attempt=attempts,
                                  max_retries=max_retries,
                                  backoff_seconds=backoff_time,
                                  error=str(e))

                    await asyncio.sleep(backoff_time)

        # All retries failed
        logger.error("All retry attempts failed",
                    task_type=task_type,
                    attempts=attempts,
                    error=str(last_error))

        raise AIGenerationError(f"Failed after {max_retries} retries: {str(last_error)}")

    async def batch_generate(
        self,
        prompts: List[str],
        task_type: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Generate multiple responses in parallel.

        Args:
            prompts: List of prompts
            task_type: Type of task
            **kwargs: Additional parameters for generate_response

        Returns:
            List of generation results
        """
        # Create tasks for all prompts
        tasks = [
            self.generate_response(prompt, task_type, **kwargs)
            for prompt in prompts
        ]

        # Run all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results, converting exceptions to error objects
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Convert exception to error response
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "error_type": result.__class__.__name__,
                    "prompt_index": i
                })
            else:
                # Add prompt index to successful result
                result["prompt_index"] = i
                processed_results.append(result)

        return processed_results

    def get_model_status(self, model_id: Optional[str] = None) -> Dict[str, Any]:
        """Get status information for models.

        Args:
            model_id: Optional specific model ID

        Returns:
            Status information
        """
        if model_id:
            if model_id not in self.performance_metrics:
                return {"error": f"Model {model_id} not found"}

            return {
                "model_id": model_id,
                **self.performance_metrics[model_id]
            }
        else:
            # Return status for all models
            return {
                "models": {
                    model_id: {
                        "success_rate": metrics["success_rate"],
                        "average_latency_ms": metrics["average_latency_ms"],
                        "status": metrics["status"],
                        "tier": metrics["tier"],
                        "total_calls": metrics["total_calls"]
                    }
                    for model_id, metrics in self.performance_metrics.items()
                },
                "routing_strategy": self.routing_strategy.value,
                "available_models_count": sum(
                    1 for metrics in self.performance_metrics.values()
                    if metrics["status"] == "available"
                )
            }

    def set_routing_strategy(self, strategy: Union[str, RoutingStrategy]) -> None:
        """Set the routing strategy.

        Args:
            strategy: Routing strategy to use
        """
        if isinstance(strategy, str):
            strategy = RoutingStrategy(strategy)

        self.routing_strategy = strategy
        logger.info("Routing strategy updated", strategy=strategy.value)

    def reset_circuit_breaker(self, model_id: str) -> bool:
        """Reset circuit breaker for a model.

        Args:
            model_id: Model identifier

        Returns:
            True if reset succeeded, False otherwise
        """
        if model_id not in self.performance_metrics:
            return False

        metrics = self.performance_metrics[model_id]

        if metrics["status"] == "unavailable":
            metrics["status"] = "available"
            metrics["consecutive_failures"] = 0

            logger.info("Circuit breaker reset", model_id=model_id)
            return True

        return False

    def _select_model_chain(
        self,
        task_type: str,
        complexity: TaskComplexity,
        requirements: Dict[str, Any]
    ) -> List[str]:
        """Select optimal model chain for task.

        Args:
            task_type: Type of task
            complexity: Task complexity
            requirements: Specific requirements

        Returns:
            List of model IDs in priority order
        """
        # Check if task type has preferred models
        preferred_models = self.task_type_preferences.get(task_type, [])

        # Filter models by requirements
        viable_models = []

        for model_id, adapter in self.adapters.items():
            # Skip models with open circuit breakers
            if self._is_circuit_open(model_id):
                continue

            # Check if model is suitable for complexity
            if isinstance(complexity, TaskComplexity):
                complexity_supported = self._complexity_supported(model_id, complexity)
                if not complexity_supported:
                    continue

            # Check specific requirements
            if requirements:
                capabilities = self.performance_metrics[model_id]["capabilities"]

                # Check required capabilities
                if "required_capabilities" in requirements:
                    required = set(requirements["required_capabilities"])
                    if not required.issubset(set(capabilities)):
                        continue

                # Check model family if specified
                if "model_family" in requirements and requirements["model_family"] not in model_id:
                    continue

            # Model passes all filters
            viable_models.append(model_id)

        if not viable_models:
            return []

        # Score models based on routing strategy
        model_scores = {}

        for model_id in viable_models:
            metrics = self.performance_metrics[model_id]

            # Base score components
            success_score = metrics["success_rate"] * 100
            latency_score = 100 / (1 + (metrics["average_latency_ms"] / 1000))
            cost_score = 100 / (1 + (metrics["cost_per_1k_tokens"] * 10))

            # Bonus for preferred models
            preferred_bonus = 20 if model_id in preferred_models else 0

            # Apply strategy weights
            if self.routing_strategy == RoutingStrategy.COST_EFFICIENT:
                # Prioritize cost efficiency
                score = (
                    0.6 * cost_score +        # 60% weight on cost
                    0.25 * success_score +    # 25% weight on success rate
                    0.1 * latency_score +     # 10% weight on latency
                    0.05 * preferred_bonus    # 5% weight on preference
                )

            elif self.routing_strategy == RoutingStrategy.PERFORMANCE:
                # Prioritize performance
                score = (
                    0.5 * success_score +     # 50% weight on success rate
                    0.3 * latency_score +     # 30% weight on latency
                    0.1 * cost_score +        # 10% weight on cost
                    0.1 * preferred_bonus     # 10% weight on preference
                )

            elif self.routing_strategy == RoutingStrategy.RELIABILITY:
                # Prioritize reliability
                score = (
                    0.7 * success_score +     # 70% weight on success rate
                    0.1 * latency_score +     # 10% weight on latency
                    0.1 * cost_score +        # 10% weight on cost
                    0.1 * preferred_bonus     # 10% weight on preference
                )

            elif self.routing_strategy == RoutingStrategy.SPECIALIZED:
                # Prioritize specialized models for specific tasks
                specialized_score = 50 if model_id in preferred_models else 0

                score = (
                    0.4 * specialized_score +  # 40% weight on specialization
                    0.3 * success_score +      # 30% weight on success rate
                    0.2 * latency_score +      # 20% weight on latency
                    0.1 * cost_score           # 10% weight on cost
                )

            else:  # BALANCED
                # Balanced approach
                score = (
                    0.3 * success_score +     # 30% weight on success rate
                    0.3 * latency_score +     # 30% weight on latency
                    0.3 * cost_score +        # 30% weight on cost
                    0.1 * preferred_bonus     # 10% weight on preference
                )

            model_scores[model_id] = score

        # Sort models by score
        sorted_models = sorted(viable_models, key=lambda m: model_scores[m], reverse=True)

        # If we have a primary model, use its fallback chain but filter to viable models
        if sorted_models:
            primary_model = sorted_models[0]
            full_chain = self.fallback_service.get_fallback_chain(primary_model)
            return [model for model in full_chain if model in viable_models]

        return []

    def _complexity_supported(self, model_id: str, complexity: TaskComplexity) -> bool:
        """Check if model supports complexity level.

        Args:
            model_id: Model identifier
            complexity: Task complexity

        Returns:
            True if model supports complexity, False otherwise
        """
        if model_id not in self.performance_metrics:
            return False

        tier = self.performance_metrics[model_id]["tier"]

        # Basic models support simple tasks
        if tier == ModelTier.BASIC.value:
            return complexity <= TaskComplexity.MEDIUM

        # Standard models support medium complexity
        elif tier == ModelTier.STANDARD.value:
            return complexity <= TaskComplexity.COMPLEX

        # Premium models support all complexity levels
        elif tier == ModelTier.PREMIUM.value:
            return True

        # Specialized models vary - assume they support complex tasks
        elif tier == ModelTier.SPECIALIZED.value:
            return complexity <= TaskComplexity.EXPERT

        return False

    def _is_circuit_open(self, model_id: str) -> bool:
        """Check if circuit breaker is open for model.

        Args:
            model_id: Model identifier

        Returns:
            True if circuit is open (model unavailable), False otherwise
        """
        if model_id not in self.performance_metrics:
            return True

        metrics = self.performance_metrics[model_id]

        # Check if model is marked unavailable
        if metrics["status"] == "unavailable":
            # Check if it's time to try resetting
            if metrics["last_failure"]:
                last_failure_time = datetime.fromisoformat(metrics["last_failure"])
                seconds_since_failure = (datetime.now() - last_failure_time).total_seconds()

                # Auto-reset after specified time
                if seconds_since_failure > self.circuit_breaker_reset_time:
                    metrics["status"] = "available"
                    metrics["consecutive_failures"] = 0
                    return False

            return True

        return False

    def _update_metrics(
        self,
        model_id: str,
        success: bool,
        duration: float
    ) -> None:
        """Update performance metrics for a model.

        Args:
            model_id: Model identifier
            success: Whether the call succeeded
            duration: Request duration in seconds
        """
        if model_id not in self.performance_metrics:
            return

        metrics = self.performance_metrics[model_id]

        # Update call counts
        metrics["total_calls"] += 1

        if success:
            metrics["total_successes"] += 1
            metrics["consecutive_failures"] = 0
        else:
            metrics["total_failures"] += 1
            metrics["consecutive_failures"] += 1
            metrics["last_failure"] = datetime.now().isoformat()

            # Check circuit breaker
            if metrics["consecutive_failures"] >= self.circuit_breaker_threshold:
                metrics["status"] = "unavailable"

                logger.warning("Circuit breaker tripped",
                              model_id=model_id,
                              consecutive_failures=metrics["consecutive_failures"],
                              threshold=self.circuit_breaker_threshold)

        # Update success rate (exponential moving average)
        success_value = 1.0 if success else 0.0
        if metrics["total_calls"] == 1:
            metrics["success_rate"] = success_value
        else:
            metrics["success_rate"] = (0.9 * metrics["success_rate"]) + (0.1 * success_value)

        # Update latency (exponential moving average)
        duration_ms = duration * 1000
        if metrics["average_latency_ms"] == 0:
            metrics["average_latency_ms"] = duration_ms
        else:
            metrics["average_latency_ms"] = (0.9 * metrics["average_latency_ms"]) + (0.1 * duration_ms)

    def _prepare_result(
        self,
        model_id: str,
        response: ModelResponse,
        duration: float,
        prompt_tokens: int,
        completion_tokens: int
    ) -> Dict[str, Any]:
        """Prepare standardized result with metadata.

        Args:
            model_id: Model identifier
            response: Model response
            duration: Request duration in seconds
            prompt_tokens: Estimated prompt tokens
            completion_tokens: Estimated completion tokens

        Returns:
            Standardized result dictionary
        """
        # Get adapter and metrics
        adapter = self.adapters[model_id]
        metrics = self.performance_metrics[model_id]

        # Calculate estimated cost
        cost_per_1k = metrics["cost_per_1k_tokens"]
        estimated_cost = (
            (prompt_tokens * adapter.get_prompt_token_cost()) +
            (completion_tokens * adapter.get_completion_token_cost())
        ) / 1000

        # Prepare result
        return {
            "success": True,
            "model": model_id,
            "content": response.content,
            "model_tier": metrics["tier"],
            "raw_response": response.raw_response,
            "meta": {
                "duration_ms": int(duration * 1000),
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "estimated_cost": estimated_cost,
                "timestamp": datetime.now().isoformat()
            }
        }
