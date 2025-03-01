"""
Model Fallback Service

This module provides a service for handling model failures gracefully,
automatically falling back to alternative models when primary models fail.
"""

import logging
import time
import asyncio
import random
from typing import Dict, List, Optional, Any, Tuple, Set
import os

from ..adapters.base import ModelRequest, ModelResponse
from ..monitoring.ai_metrics_service import AIMetricsService

logger = logging.getLogger(__name__)

# Default blacklist duration in seconds
DEFAULT_BLACKLIST_DURATION = 300  # 5 minutes

# Maximum retry attempts for any model
MAX_RETRY_ATTEMPTS = 3

# Backoff settings
INITIAL_RETRY_DELAY_MS = 500
BACKOFF_FACTOR = 2
MAX_RETRY_DELAY_MS = 10000

# Error categories
TRANSIENT_ERRORS = [
    "rate_limit_exceeded",
    "server_overloaded",
    "timeout",
    "connection_error",
    "service_unavailable",
]

PERMANENT_ERRORS = [
    "invalid_api_key",
    "access_denied",
    "model_not_found",
    "content_filter",
]


class FallbackChain:
    """
    Represents a chain of fallback models to try when the primary model fails.

    A fallback chain defines a sequence of models to try in order when the
    primary model fails, along with retry settings and timeout configurations.
    """

    def __init__(
        self,
        primary_model: str,
        fallback_models: List[str],
        max_retries: int = 2,
        retry_delay_ms: int = 500,
        timeout_ms: int = 10000,
        error_mapping: Optional[Dict[str, List[str]]] = None,
    ):
        """
        Initialize a fallback chain.

        Args:
            primary_model: The primary model to try first.
            fallback_models: A list of fallback models to try in order.
            max_retries: The maximum number of retries for each model.
            retry_delay_ms: The delay between retries in milliseconds.
            timeout_ms: The timeout for each model request in milliseconds.
            error_mapping: Optional mapping of error types to fallback models.
        """
        self.primary_model = primary_model
        self.fallback_models = fallback_models
        self.max_retries = max_retries
        self.retry_delay_ms = retry_delay_ms
        self.timeout_ms = timeout_ms
        self.error_mapping = error_mapping or {}

        # Track usage statistics
        self.stats = {
            "primary_success": 0,
            "primary_failure": 0,
            "fallback_success": 0,
            "fallback_failure": 0,
            "total_requests": 0,
            "error_types": {},
            "model_usage": {primary_model: 0},
        }

        # Initialize model usage stats for fallback models
        for model in fallback_models:
            self.stats["model_usage"][model] = 0

    def get_model_sequence(self) -> List[str]:
        """
        Get the sequence of models to try.

        Returns:
            A list of model names to try in order.
        """
        return [self.primary_model] + self.fallback_models

    def get_fallback_for_error(self, error_type: str) -> List[str]:
        """
        Get the fallback models to try for a specific error type.

        Args:
            error_type: The type of error that occurred.

        Returns:
            A list of model names to try for this error type.
        """
        # If we have a specific fallback chain for this error, use it
        if error_type in self.error_mapping:
            return self.error_mapping[error_type]

        # Otherwise, use the default fallback chain
        return self.fallback_models

    def update_stats(
        self,
        primary_succeeded: bool,
        fallback_succeeded: bool,
        error_type: Optional[str] = None,
        used_model: Optional[str] = None
    ) -> None:
        """
        Update usage statistics.

        Args:
            primary_succeeded: Whether the primary model succeeded.
            fallback_succeeded: Whether a fallback model succeeded.
            error_type: The type of error that occurred, if any.
            used_model: The model that was ultimately used.
        """
        self.stats["total_requests"] += 1

        if primary_succeeded:
            self.stats["primary_success"] += 1
            self.stats["model_usage"][self.primary_model] += 1
        else:
            self.stats["primary_failure"] += 1

            # Track error type
            if error_type:
                if error_type not in self.stats["error_types"]:
                    self.stats["error_types"][error_type] = 0
                self.stats["error_types"][error_type] += 1

            if fallback_succeeded:
                self.stats["fallback_success"] += 1
                if used_model and used_model in self.stats["model_usage"]:
                    self.stats["model_usage"][used_model] += 1
            else:
                self.stats["fallback_failure"] += 1

    def get_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics.

        Returns:
            A dictionary of usage statistics.
        """
        total_requests = self.stats["total_requests"]
        primary_failures = self.stats["primary_failure"]

        return {
            **self.stats,
            "primary_success_rate": self.stats["primary_success"] / total_requests
                if total_requests > 0 else 0,
            "fallback_success_rate": self.stats["fallback_success"] / primary_failures
                if primary_failures > 0 else 0,
            "overall_success_rate": (self.stats["primary_success"] + self.stats["fallback_success"]) / total_requests
                if total_requests > 0 else 0,
            "most_common_errors": sorted(
                self.stats["error_types"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5] if self.stats["error_types"] else [],
        }


class ModelFallbackService:
    """
    Service for handling model failures gracefully.

    This service automatically falls back to alternative models when primary
    models fail, providing a more reliable AI service.
    """

    def __init__(self, metrics_service: Optional[AIMetricsService] = None):
        """
        Initialize the model fallback service.

        Args:
            metrics_service: Optional metrics service for tracking fallback metrics.
        """
        # Define default fallback chains for different model categories
        self.fallback_chains = {
            # High-capability models
            "gpt-4": FallbackChain(
                primary_model="gpt-4",
                fallback_models=["claude-3-opus", "gemini-1.5-pro", "gpt-3.5-turbo"],
                error_mapping={
                    "rate_limit_exceeded": ["claude-3-opus", "gemini-1.5-pro"],
                    "content_filter": ["claude-3-opus", "gemini-1.5-pro"],
                    "timeout": ["gpt-3.5-turbo", "claude-3-haiku"],
                }
            ),
            "claude-3-opus": FallbackChain(
                primary_model="claude-3-opus",
                fallback_models=["gpt-4", "gemini-1.5-pro", "claude-3-sonnet"],
                error_mapping={
                    "rate_limit_exceeded": ["gpt-4", "gemini-1.5-pro"],
                    "content_filter": ["gpt-4", "gemini-1.5-pro"],
                    "timeout": ["claude-3-sonnet", "gpt-3.5-turbo"],
                }
            ),
            "gemini-1.5-pro": FallbackChain(
                primary_model="gemini-1.5-pro",
                fallback_models=["gpt-4", "claude-3-opus", "gemini-1.5-flash"],
                error_mapping={
                    "rate_limit_exceeded": ["gpt-4", "claude-3-opus"],
                    "content_filter": ["gpt-4", "claude-3-opus"],
                    "timeout": ["gemini-1.5-flash", "gpt-3.5-turbo"],
                }
            ),

            # Mid-tier models
            "gpt-3.5-turbo": FallbackChain(
                primary_model="gpt-3.5-turbo",
                fallback_models=["claude-3-haiku", "gemini-1.5-flash"],
                error_mapping={
                    "rate_limit_exceeded": ["claude-3-haiku", "gemini-1.5-flash"],
                    "content_filter": ["claude-3-haiku", "gemini-1.5-flash"],
                }
            ),
            "claude-3-sonnet": FallbackChain(
                primary_model="claude-3-sonnet",
                fallback_models=["gpt-3.5-turbo", "gemini-1.5-flash"],
                error_mapping={
                    "rate_limit_exceeded": ["gpt-3.5-turbo", "gemini-1.5-flash"],
                    "content_filter": ["gpt-3.5-turbo", "gemini-1.5-flash"],
                }
            ),
            "gemini-1.5-flash": FallbackChain(
                primary_model="gemini-1.5-flash",
                fallback_models=["gpt-3.5-turbo", "claude-3-haiku"],
                error_mapping={
                    "rate_limit_exceeded": ["gpt-3.5-turbo", "claude-3-haiku"],
                    "content_filter": ["gpt-3.5-turbo", "claude-3-haiku"],
                }
            ),

            # Fast models
            "claude-3-haiku": FallbackChain(
                primary_model="claude-3-haiku",
                fallback_models=["gpt-3.5-turbo", "gemini-1.5-flash"],
                error_mapping={
                    "rate_limit_exceeded": ["gpt-3.5-turbo", "gemini-1.5-flash"],
                    "content_filter": ["gpt-3.5-turbo", "gemini-1.5-flash"],
                }
            ),

            # Embedding models
            "text-embedding-3-small": FallbackChain(
                primary_model="text-embedding-3-small",
                fallback_models=["text-embedding-3-large"],
            ),
            "text-embedding-3-large": FallbackChain(
                primary_model="text-embedding-3-large",
                fallback_models=["text-embedding-3-small"],
            ),
        }

        # Track blacklisted models (temporarily unavailable)
        self.blacklisted_models: Dict[str, float] = {}

        # Load blacklist duration from environment or use default
        self.blacklist_duration_sec = int(os.environ.get(
            "MODEL_BLACKLIST_DURATION",
            str(DEFAULT_BLACKLIST_DURATION)
        ))

        # Health check settings
        self.health_check_interval_sec = int(os.environ.get("FALLBACK_HEALTH_CHECK_INTERVAL", "60"))
        self.health_check_enabled = os.environ.get("ENABLE_FALLBACK_HEALTH_CHECKS", "true").lower() == "true"

        # Circuit breaker settings
        self.circuit_breaker_threshold = float(os.environ.get("CIRCUIT_BREAKER_THRESHOLD", "0.5"))
        self.circuit_breaker_window = int(os.environ.get("CIRCUIT_BREAKER_WINDOW", "10"))
        self.circuit_breaker_counts: Dict[str, List[bool]] = {}

        # Metrics service for tracking
        self.metrics_service = metrics_service

        # Start health check loop if enabled
        if self.health_check_enabled:
            asyncio.create_task(self._health_check_loop())

    def get_fallback_chain(self, model_name: str) -> Optional[FallbackChain]:
        """
        Get the fallback chain for a model.

        Args:
            model_name: The name of the model.

        Returns:
            A FallbackChain object, or None if no fallback chain is defined.
        """
        return self.fallback_chains.get(model_name)

    def register_fallback_chain(self, fallback_chain: FallbackChain) -> None:
        """
        Register a fallback chain.

        Args:
            fallback_chain: The fallback chain to register.
        """
        self.fallback_chains[fallback_chain.primary_model] = fallback_chain

    def blacklist_model(self, model_name: str, duration_sec: Optional[int] = None) -> None:
        """
        Temporarily blacklist a model.

        Args:
            model_name: The name of the model to blacklist.
            duration_sec: Optional custom blacklist duration in seconds.
        """
        duration = duration_sec or self.blacklist_duration_sec
        self.blacklisted_models[model_name] = time.time()
        logger.warning(f"Model {model_name} has been blacklisted for {duration} seconds")

        # Record circuit breaker event
        self._record_circuit_breaker_event(model_name, False)

    def is_model_blacklisted(self, model_name: str) -> bool:
        """
        Check if a model is blacklisted.

        Args:
            model_name: The name of the model to check.

        Returns:
            True if the model is blacklisted, False otherwise.
        """
        if model_name not in self.blacklisted_models:
            return False

        blacklist_time = self.blacklisted_models[model_name]
        current_time = time.time()

        # Check if blacklist has expired
        if current_time - blacklist_time > self.blacklist_duration_sec:
            # Remove from blacklist
            del self.blacklisted_models[model_name]
            return False

        return True

    def get_available_models(self, models: List[str]) -> List[str]:
        """
        Filter out blacklisted models.

        Args:
            models: A list of model names.

        Returns:
            A list of available model names.
        """
        return [model for model in models if not self.is_model_blacklisted(model)]

    def get_fallback_stats(self) -> Dict[str, Any]:
        """
        Get fallback statistics for all models.

        Returns:
            A dictionary of fallback statistics.
        """
        return {
            model: chain.get_stats()
            for model, chain in self.fallback_chains.items()
        }

    def categorize_error(self, error: Any) -> str:
        """
        Categorize an error to determine the appropriate fallback strategy.

        Args:
            error: The error object or message.

        Returns:
            A string categorizing the error.
        """
        error_str = str(error).lower()

        # Check for rate limiting errors
        if any(phrase in error_str for phrase in [
            "rate limit", "rate_limit", "too many requests", "429"
        ]):
            return "rate_limit_exceeded"

        # Check for timeout errors
        if any(phrase in error_str for phrase in [
            "timeout", "timed out", "deadline exceeded"
        ]):
            return "timeout"

        # Check for server overload
        if any(phrase in error_str for phrase in [
            "server overloaded", "overloaded", "capacity", "busy"
        ]):
            return "server_overloaded"

        # Check for connection errors
        if any(phrase in error_str for phrase in [
            "connection", "network", "unreachable"
        ]):
            return "connection_error"

        # Check for service unavailable
        if any(phrase in error_str for phrase in [
            "unavailable", "503", "service unavailable"
        ]):
            return "service_unavailable"

        # Check for authentication errors
        if any(phrase in error_str for phrase in [
            "api key", "authentication", "auth", "unauthorized", "401"
        ]):
            return "invalid_api_key"

        # Check for access denied
        if any(phrase in error_str for phrase in [
            "access denied", "permission", "forbidden", "403"
        ]):
            return "access_denied"

        # Check for model not found
        if any(phrase in error_str for phrase in [
            "model not found", "not found", "404", "no such model"
        ]):
            return "model_not_found"

        # Check for content filter
        if any(phrase in error_str for phrase in [
            "content filter", "content policy", "moderation", "inappropriate"
        ]):
            return "content_filter"

        # Default to unknown error
        return "unknown_error"

    def is_transient_error(self, error_type: str) -> bool:
        """
        Determine if an error is transient (can be retried).

        Args:
            error_type: The type of error.

        Returns:
            True if the error is transient, False otherwise.
        """
        return error_type in TRANSIENT_ERRORS

    def calculate_backoff_delay(self, attempt: int, base_delay_ms: int = INITIAL_RETRY_DELAY_MS) -> int:
        """
        Calculate exponential backoff delay with jitter.

        Args:
            attempt: The current attempt number (0-based).
            base_delay_ms: The base delay in milliseconds.

        Returns:
            The delay in milliseconds.
        """
        # Calculate exponential backoff
        delay = base_delay_ms * (BACKOFF_FACTOR ** attempt)

        # Add jitter (±20%)
        jitter = delay * 0.2
        delay = delay + random.uniform(-jitter, jitter)

        # Cap at maximum delay
        return min(int(delay), MAX_RETRY_DELAY_MS)

    def _record_circuit_breaker_event(self, model_name: str, success: bool) -> None:
        """
        Record a success/failure event for the circuit breaker.

        Args:
            model_name: The name of the model.
            success: Whether the request was successful.
        """
        if model_name not in self.circuit_breaker_counts:
            self.circuit_breaker_counts[model_name] = []

        # Add the result
        self.circuit_breaker_counts[model_name].append(success)

        # Trim to window size
        if len(self.circuit_breaker_counts[model_name]) > self.circuit_breaker_window:
            self.circuit_breaker_counts[model_name] = self.circuit_breaker_counts[model_name][-self.circuit_breaker_window:]

    def should_trip_circuit_breaker(self, model_name: str) -> bool:
        """
        Check if the circuit breaker should trip for a model.

        Args:
            model_name: The name of the model.

        Returns:
            True if the circuit breaker should trip, False otherwise.
        """
        if model_name not in self.circuit_breaker_counts:
            return False

        # Need enough samples
        if len(self.circuit_breaker_counts[model_name]) < 5:
            return False

        # Calculate failure rate
        failure_rate = 1 - (sum(self.circuit_breaker_counts[model_name]) / len(self.circuit_breaker_counts[model_name]))

        # Trip if failure rate exceeds threshold
        return failure_rate >= self.circuit_breaker_threshold

    async def _health_check_loop(self) -> None:
        """Run periodic health checks on blacklisted models."""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval_sec)

                # Check if any blacklisted models have recovered
                current_time = time.time()
                for model_name, blacklist_time in list(self.blacklisted_models.items()):
                    # If blacklist has expired, remove from blacklist
                    if current_time - blacklist_time > self.blacklist_duration_sec:
                        del self.blacklisted_models[model_name]
                        logger.info(f"Model {model_name} removed from blacklist (duration expired)")

                # Log current blacklist status
                if self.blacklisted_models:
                    logger.info(f"Currently blacklisted models: {list(self.blacklisted_models.keys())}")
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")


# Create a singleton instance of the service
fallback_service = ModelFallbackService()
