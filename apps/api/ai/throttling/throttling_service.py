"""
AI Throttling Service

This module provides a service for throttling AI operations to prevent
overloading AI services and manage costs effectively.
"""

import asyncio
import logging
import time
import random
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Set, Union, Callable
import os
import threading
from concurrent.futures import ThreadPoolExecutor
import uuid
from collections import deque

from ..monitoring.ai_metrics_service import AIMetricsService
from ...utils.cache_manager import CacheManager

logger = logging.getLogger(__name__)

# Default throttling limits (requests per minute)
DEFAULT_LIMITS = {
    # OpenAI models
    "gpt-4": 100,
    "gpt-4-turbo": 80,
    "gpt-4-vision": 60,
    "gpt-3.5-turbo": 200,

    # Anthropic models
    "claude-3-opus": 60,
    "claude-3-sonnet": 100,
    "claude-3-haiku": 150,

    # Google models
    "gemini-pro": 120,
    "gemini-ultra": 60,

    # Default for any other model
    "default": 100
}

# Throttling periods in seconds
THROTTLING_PERIODS = {
    "short": 60,      # 1 minute
    "medium": 300,    # 5 minutes
    "long": 3600,     # 1 hour
    "daily": 86400    # 24 hours
}

# Burst allowance for short periods
BURST_ALLOWANCE = 5

# Retry settings
MAX_RETRY_ATTEMPTS = 3
RETRY_BACKOFF_FACTOR = 1.5
MAX_RETRY_DELAY = 30.0

# Cost tracking
COST_TRACKING_ENABLED = os.environ.get("ENABLE_COST_TRACKING", "true").lower() == "true"
BUDGET_ALERT_THRESHOLDS = [50, 75, 90, 95, 100]

# Model costs ($ per 1K tokens)
MODEL_COSTS = {
    # OpenAI models
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4-vision": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},

    # Anthropic models
    "claude-3-opus": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-haiku": {"input": 0.00025, "output": 0.00125},

    # Google models
    "gemini-pro": {"input": 0.00125, "output": 0.00375},
    "gemini-ultra": {"input": 0.0025, "output": 0.0075},

    # Default for any other model
    "default": {"input": 0.01, "output": 0.03}
}

# Priority levels with multipliers for throttling limits
PRIORITY_MULTIPLIERS = {
    "low": 0.5,       # 50% of normal limit
    "normal": 1.0,    # Normal limit
    "high": 1.5,      # 150% of normal limit
    "critical": 2.0   # 200% of normal limit
}

class ThrottlingService:
    """
    Service for throttling AI operations.

    This service provides mechanisms to prevent overloading AI services
    and manage costs effectively by limiting the rate of requests.
    """

    def __init__(self, metrics_service: Optional[AIMetricsService] = None):
        """Initialize the throttling service."""
        self.cache_manager = CacheManager()

        # Load limits from environment or use defaults
        self.limits = self._load_limits_from_env() or DEFAULT_LIMITS

        # Track current request rates
        self.current_rates = {}

        # Track throttled requests
        self.throttled_count = 0
        self.last_throttled = {}

        # Adaptive throttling settings
        self.adaptive_enabled = os.environ.get("ENABLE_ADAPTIVE_THROTTLING", "true").lower() == "true"
        self.adaptive_window = int(os.environ.get("ADAPTIVE_THROTTLING_WINDOW", "300"))  # 5 minutes
        self.adaptive_samples = []

        # Cost tracking
        self.cost_tracking_enabled = COST_TRACKING_ENABLED
        self.daily_budget = float(os.environ.get("DAILY_AI_BUDGET", "0.0"))
        self.current_spend = 0.0
        self.spend_by_model = {}
        self.spend_by_user = {}
        self.budget_alerts_sent = set()

        # Per-user quotas
        self.user_quotas_enabled = os.environ.get("ENABLE_USER_QUOTAS", "false").lower() == "true"
        self.user_quotas = self._load_user_quotas()
        self.user_usage = {}

        # Token bucket settings
        self.token_bucket_enabled = os.environ.get("ENABLE_TOKEN_BUCKET", "true").lower() == "true"
        self.token_buckets = {}

        # Circuit breaker settings
        self.circuit_breaker_enabled = os.environ.get("ENABLE_CIRCUIT_BREAKER", "true").lower() == "true"
        self.circuit_breaker_threshold = float(os.environ.get("CIRCUIT_BREAKER_THRESHOLD", "0.5"))
        self.circuit_breaker_window = int(os.environ.get("CIRCUIT_BREAKER_WINDOW", "20"))
        self.circuit_breaker_counts = {}
        self.circuit_breaker_status = {}

        # Metrics service for tracking
        self.metrics_service = metrics_service

        # Concurrency control
        self.max_concurrent_requests = int(os.environ.get("MAX_CONCURRENT_REQUESTS", "100"))
        self.current_concurrent_requests = 0
        self.request_semaphore = asyncio.Semaphore(self.max_concurrent_requests)

        # Locks for thread safety
        self._rates_lock = threading.RLock()
        self._cost_lock = threading.RLock()
        self._samples_lock = threading.RLock()

        # Start background tasks
        if self.adaptive_enabled:
            asyncio.create_task(self._adaptive_adjustment_task())

        if self.cost_tracking_enabled:
            asyncio.create_task(self._cost_tracking_task())

        logger.info(f"Throttling service initialized with limits: {self.limits}")
        if self.daily_budget > 0:
            logger.info(f"Daily AI budget set to ${self.daily_budget:.2f}")

    def _load_limits_from_env(self) -> Optional[Dict[str, int]]:
        """
        Load throttling limits from environment variables.

        Returns:
            Dictionary of model limits or None if not configured.
        """
        limits_str = os.environ.get("AI_THROTTLING_LIMITS")
        if not limits_str:
            return None

        try:
            # Format: model1:limit1,model2:limit2
            limits = {}
            for limit_pair in limits_str.split(","):
                model, limit = limit_pair.split(":")
                limits[model.strip()] = int(limit.strip())
            return limits
        except Exception as e:
            logger.error(f"Error parsing throttling limits from environment: {e}")
            return None

    def _load_user_quotas(self) -> Dict[str, Dict[str, Any]]:
        """
        Load user quotas from environment or configuration.

        Returns:
            Dictionary of user quotas.
        """
        if not self.user_quotas_enabled:
            return {}

        quotas_file = os.environ.get("USER_QUOTAS_FILE")
        if quotas_file and os.path.exists(quotas_file):
            try:
                with open(quotas_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading user quotas from file: {e}")

        # Default quotas
        return {
            "default": {
                "daily_request_limit": 1000,
                "daily_token_limit": 100000,
                "cost_limit": 1.0
            }
        }

    async def check_throttle(
        self,
        model: str,
        user_id: Optional[str] = None,
        priority: str = "normal",
        tokens: Optional[int] = None,
        request_id: Optional[str] = None
    ) -> Tuple[bool, Optional[float], Optional[str]]:
        """
        Check if a request should be throttled.

        Args:
            model: The AI model being used
            user_id: Optional user ID for per-user throttling
            priority: Priority level (low, normal, high, critical)
            tokens: Optional token count for token-based throttling
            request_id: Optional request ID for tracking

        Returns:
            Tuple of (should_throttle, retry_after, reason)
        """
        start_time = time.time()

        # Generate request ID if not provided
        if not request_id:
            request_id = str(uuid.uuid4())

        # Check if circuit breaker is tripped
        if self.circuit_breaker_enabled and self._check_circuit_breaker(model):
            reason = f"Circuit breaker tripped for {model}"
            retry_after = self._calculate_retry_after(model)
            logger.warning(f"Request {request_id} throttled: {reason}")
            self._update_metrics(model, True, reason, user_id)
            return True, retry_after, reason

        # Check budget if cost tracking is enabled
        if self.cost_tracking_enabled and self.daily_budget > 0:
            with self._cost_lock:
                if self.current_spend >= self.daily_budget:
                    reason = f"Daily budget of ${self.daily_budget:.2f} exceeded"
                    retry_after = self._get_time_until_budget_reset()
                    logger.warning(f"Request {request_id} throttled: {reason}")
                    self._update_metrics(model, True, reason, user_id)
                    return True, retry_after, reason

        # Check user quotas if enabled
        if self.user_quotas_enabled and user_id:
            throttled, retry_after, reason = self._check_user_quota(user_id, model, tokens)
            if throttled:
                logger.warning(f"Request {request_id} throttled: {reason}")
                self._update_metrics(model, True, reason, user_id)
                return True, retry_after, reason

        # Apply priority multiplier to limits
        priority_multiplier = PRIORITY_MULTIPLIERS.get(priority, 1.0)

        # Get the appropriate limit for the model
        model_limit = self.limits.get(model, self.limits.get("default", DEFAULT_LIMITS["default"]))
        adjusted_limit = int(model_limit * priority_multiplier)

        # Check token bucket if enabled
        if self.token_bucket_enabled:
            throttled, retry_after, reason = self._check_token_bucket(model, user_id, priority)
            if throttled:
                logger.warning(f"Request {request_id} throttled: {reason}")
                self._update_metrics(model, True, reason, user_id)
                return True, retry_after, reason

        # Check concurrency limits
        if not self.request_semaphore.locked() and self.current_concurrent_requests >= self.max_concurrent_requests:
            reason = f"Maximum concurrent requests ({self.max_concurrent_requests}) reached"
            retry_after = 1.0 + random.random()  # Add jitter
            logger.warning(f"Request {request_id} throttled: {reason}")
            self._update_metrics(model, True, reason, user_id)
            return True, retry_after, reason

        # Traditional rate-based throttling
        with self._rates_lock:
            # Initialize rates for this model if not exists
            if model not in self.current_rates:
                self.current_rates[model] = {
                    "short": deque(maxlen=THROTTLING_PERIODS["short"]),
                    "medium": deque(maxlen=THROTTLING_PERIODS["medium"]),
                    "long": deque(maxlen=THROTTLING_PERIODS["long"]),
                    "daily": deque(maxlen=THROTTLING_PERIODS["daily"])
                }

            # Get current time
            now = time.time()

            # Clean up old timestamps
            for period in ["short", "medium", "long", "daily"]:
                while (self.current_rates[model][period] and
                       now - self.current_rates[model][period][0] >
                       THROTTLING_PERIODS[period]):
                    self.current_rates[model][period].popleft()

            # Check if we're over the limit for any period
            short_count = len(self.current_rates[model]["short"])
            medium_count = len(self.current_rates[model]["medium"])
            long_count = len(self.current_rates[model]["long"])

            # Allow short bursts over the limit
            short_limit = adjusted_limit + BURST_ALLOWANCE

            if short_count >= short_limit:
                # We're over the short period limit
                reason = f"Rate limit exceeded for {model}: {short_count}/{adjusted_limit} requests in {THROTTLING_PERIODS['short']}s"
                retry_after = self._calculate_retry_after(model)
                logger.warning(f"Request {request_id} throttled: {reason}")
                self._update_metrics(model, True, reason, user_id)
                return True, retry_after, reason

            if medium_count >= adjusted_limit * (THROTTLING_PERIODS["medium"] / 60):
                # We're over the medium period limit
                reason = f"Rate limit exceeded for {model}: {medium_count}/{adjusted_limit * (THROTTLING_PERIODS['medium'] / 60)} requests in {THROTTLING_PERIODS['medium']}s"
                retry_after = self._calculate_retry_after(model)
                logger.warning(f"Request {request_id} throttled: {reason}")
                self._update_metrics(model, True, reason, user_id)
                return True, retry_after, reason

            if long_count >= adjusted_limit * (THROTTLING_PERIODS["long"] / 60):
                # We're over the long period limit
                reason = f"Rate limit exceeded for {model}: {long_count}/{adjusted_limit * (THROTTLING_PERIODS['long'] / 60)} requests in {THROTTLING_PERIODS['long']}s"
                retry_after = self._calculate_retry_after(model)
                logger.warning(f"Request {request_id} throttled: {reason}")
                self._update_metrics(model, True, reason, user_id)
                return True, retry_after, reason

            # If we get here, we're not throttled
            # Add the current timestamp to all periods
            for period in ["short", "medium", "long", "daily"]:
                self.current_rates[model][period].append(now)

        # Update metrics for non-throttled request
        self._update_metrics(model, False, None, user_id)

        # Track request for adaptive throttling
        if self.adaptive_enabled:
            with self._samples_lock:
                self.adaptive_samples.append({
                    "model": model,
                    "timestamp": now,
                    "throttled": False,
                    "user_id": user_id,
                    "priority": priority
                })

        # Track latency
        latency = time.time() - start_time
        if self.metrics_service:
            self.metrics_service.record_metric(
                "throttling_check_latency",
                latency,
                {"model": model, "throttled": "false"}
            )

        return False, None, None

    def _calculate_retry_after(self, model_name: str, remaining: int = 0) -> int:
        """
        Calculate how long to wait before retrying.

        Args:
            model_name: The name of the model.
            remaining: Remaining requests allowed.

        Returns:
            Seconds to wait before retrying.
        """
        # Base retry time is proportional to how far over the limit we are
        limit = self.limits.get(model_name, self.limits["default"])

        if remaining <= 0:
            # We're at or over the limit
            base_retry = THROTTLING_PERIODS["short"]
        else:
            # We're approaching the limit
            ratio = remaining / limit
            base_retry = int(THROTTLING_PERIODS["short"] * (1 - ratio))

        # Add jitter to prevent thundering herd
        jitter = int(base_retry * 0.2 * (0.5 + 0.5 * (hash(model_name) % 100) / 100))

        return max(1, base_retry + jitter)

    def _update_metrics(self, model_name: str, allowed: bool, reason: Optional[str] = None, user_id: Optional[str] = None) -> None:
        """
        Update throttling metrics.

        Args:
            model_name: The name of the model.
            allowed: Whether the request was allowed.
            reason: Optional reason for throttling.
            user_id: Optional user ID for per-user throttling.
        """
        # Update current rates
        now = time.time()
        if model_name not in self.current_rates:
            self.current_rates[model_name] = {"count": 0, "last_reset": now, "throttled": 0}

        # Reset counter if it's been more than a minute
        if now - self.current_rates[model_name]["last_reset"] > 60:
            self.current_rates[model_name] = {"count": 0, "last_reset": now, "throttled": 0}

        # Update counters
        self.current_rates[model_name]["count"] += 1
        if not allowed:
            self.current_rates[model_name]["throttled"] += 1

        # Add sample for adaptive throttling
        if self.adaptive_enabled:
            self.adaptive_samples.append({
                "model": model_name,
                "timestamp": now,
                "allowed": allowed,
                "reason": reason,
                "user_id": user_id
            })

            # Clean up old samples
            self.adaptive_samples = [
                sample for sample in self.adaptive_samples
                if now - sample["timestamp"] < self.adaptive_window
            ]

    def get_stats(self) -> Dict[str, Any]:
        """
        Get throttling statistics.

        Returns:
            Dictionary of throttling statistics.
        """
        with self._rates_lock:
            # Calculate current rates for each model
            current_rates = {}
            for model, periods in self.current_rates.items():
                current_rates[model] = {
                    "short_period": len(periods["short"]),
                    "medium_period": len(periods["medium"]),
                    "long_period": len(periods["long"]),
                    "daily_period": len(periods["daily"])
                }

            # Get circuit breaker status if enabled
            circuit_breaker_status = {}
            if self.circuit_breaker_enabled:
                for model, status in self.circuit_breaker_status.items():
                    circuit_breaker_status[model] = {
                        "tripped": status["tripped"],
                        "trip_until": status["trip_until"],
                        "error_rate": (self.circuit_breaker_counts.get(model, {}).get("error", 0) /
                                      max(1, self.circuit_breaker_counts.get(model, {}).get("error", 0) +
                                          self.circuit_breaker_counts.get(model, {}).get("success", 0)))
                    }

            # Get cost tracking stats if enabled
            cost_stats = {}
            if self.cost_tracking_enabled:
                with self._cost_lock:
                    cost_stats = {
                        "current_spend": self.current_spend,
                        "daily_budget": self.daily_budget,
                        "budget_percentage": (self.current_spend / self.daily_budget * 100) if self.daily_budget > 0 else 0,
                        "spend_by_model": self.spend_by_model,
                        "top_users": dict(sorted(self.spend_by_user.items(), key=lambda x: x[1], reverse=True)[:10])
                    }

            # Get token bucket stats if enabled
            token_bucket_stats = {}
            if self.token_bucket_enabled:
                for key, bucket in self.token_buckets.items():
                    token_bucket_stats[key] = {
                        "tokens": bucket["tokens"],
                        "capacity": bucket["capacity"],
                        "percentage_full": (bucket["tokens"] / bucket["capacity"]) * 100
                    }

            return {
                "limits": self.limits,
                "current_rates": current_rates,
                "throttled_count": self.throttled_count,
                "last_throttled": self.last_throttled,
                "adaptive_enabled": self.adaptive_enabled,
                "circuit_breaker_status": circuit_breaker_status,
                "cost_tracking": cost_stats,
                "token_buckets": token_bucket_stats,
                "concurrent_requests": self.current_concurrent_requests,
                "max_concurrent_requests": self.max_concurrent_requests
            }

    async def __aenter__(self):
        """
        Async context manager entry for throttling.

        This allows using the throttling service with an async context manager:

        async with throttling_service(model="gpt-4", user_id="user123") as allowed:
            if allowed:
                # Make AI request
                pass
        """
        self.current_concurrent_requests += 1
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit for throttling."""
        self.current_concurrent_requests -= 1

    class ThrottlingContext:
        """Context manager for throttling requests."""

        def __init__(self, service: 'ThrottlingService', model: str, user_id: Optional[str] = None,
                     priority: str = "normal", tokens: Optional[int] = None):
            """Initialize the throttling context."""
            self.service = service
            self.model = model
            self.user_id = user_id
            self.priority = priority
            self.tokens = tokens
            self.allowed = False
            self.retry_after = None
            self.reason = None
            self.start_time = None
            self.request_id = str(uuid.uuid4())

        async def __aenter__(self):
            """Async context manager entry."""
            self.start_time = time.time()
            self.service.current_concurrent_requests += 1

            # Check if request should be throttled
            self.allowed, self.retry_after, self.reason = await self.service.check_throttle(
                model=self.model,
                user_id=self.user_id,
                priority=self.priority,
                tokens=self.tokens,
                request_id=self.request_id
            )

            return self.allowed

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            """Async context manager exit."""
            self.service.current_concurrent_requests -= 1

            # Record circuit breaker result if enabled
            if self.service.circuit_breaker_enabled and self.allowed:
                self.service.record_circuit_breaker_result(
                    model=self.model,
                    success=(exc_type is None)
                )

            # Record metrics
            if self.service.metrics_service and self.allowed:
                latency = time.time() - self.start_time
                self.service.metrics_service.record_metric(
                    "ai_request_latency",
                    latency,
                    {"model": self.model, "success": str(exc_type is None)}
                )

    def throttle(self, model: str, user_id: Optional[str] = None,
                priority: str = "normal", tokens: Optional[int] = None) -> ThrottlingContext:
        """
        Get a throttling context manager.

        Usage:
            async with throttling_service.throttle(model="gpt-4", user_id="user123") as allowed:
                if allowed:
                    # Make AI request
                    pass
                else:
                    # Handle throttling
                    pass

        Args:
            model: The AI model being used
            user_id: Optional user ID for per-user throttling
            priority: Priority level (low, normal, high, critical)
            tokens: Optional token count for token-based throttling

        Returns:
            ThrottlingContext instance
        """
        return self.ThrottlingContext(self, model, user_id, priority, tokens)

    def _check_token_bucket(self, model: str, user_id: Optional[str], priority: str) -> Tuple[bool, Optional[float], Optional[str]]:
        """
        Check if a request should be throttled based on token bucket algorithm.

        Args:
            model: The AI model being used
            user_id: Optional user ID for per-user throttling
            priority: Priority level

        Returns:
            Tuple of (should_throttle, retry_after, reason)
        """
        now = time.time()
        bucket_key = f"{model}:{user_id or 'anonymous'}"

        with self._rates_lock:
            # Initialize bucket if not exists
            if bucket_key not in self.token_buckets:
                model_limit = self.limits.get(model, self.limits.get("default", DEFAULT_LIMITS["default"]))
                self.token_buckets[bucket_key] = {
                    "tokens": model_limit,  # Start with full bucket
                    "capacity": model_limit,
                    "last_refill": now
                }

            bucket = self.token_buckets[bucket_key]

            # Refill tokens based on time elapsed
            time_elapsed = now - bucket["last_refill"]
            refill_amount = time_elapsed * (bucket["capacity"] / 60.0)  # Refill rate per second
            bucket["tokens"] = min(bucket["capacity"], bucket["tokens"] + refill_amount)
            bucket["last_refill"] = now

            # Adjust token cost based on priority
            token_cost = 1.0 / PRIORITY_MULTIPLIERS.get(priority, 1.0)

            # Check if enough tokens in bucket
            if bucket["tokens"] < token_cost:
                # Not enough tokens
                time_to_refill = (token_cost - bucket["tokens"]) / (bucket["capacity"] / 60.0)
                reason = f"Token bucket depleted for {model}"
                return True, time_to_refill, reason

            # Consume tokens
            bucket["tokens"] -= token_cost
            return False, None, None

    def _check_circuit_breaker(self, model: str) -> bool:
        """
        Check if circuit breaker is tripped for a model.

        Args:
            model: The AI model to check

        Returns:
            True if circuit breaker is tripped, False otherwise
        """
        if model not in self.circuit_breaker_status:
            self.circuit_breaker_status[model] = {
                "tripped": False,
                "last_check": time.time(),
                "trip_until": 0
            }

        status = self.circuit_breaker_status[model]
        now = time.time()

        # If circuit breaker is tripped, check if it's time to reset
        if status["tripped"]:
            if now > status["trip_until"]:
                logger.info(f"Circuit breaker reset for {model}")
                status["tripped"] = False
                return False
            return True

        # Check error rate
        if model not in self.circuit_breaker_counts:
            return False

        counts = self.circuit_breaker_counts[model]
        total = counts.get("success", 0) + counts.get("error", 0)

        if total >= self.circuit_breaker_window:
            error_rate = counts.get("error", 0) / total

            if error_rate >= self.circuit_breaker_threshold:
                # Trip the circuit breaker
                trip_duration = min(30 * (2 ** counts.get("trips", 0)), 300)  # Exponential backoff, max 5 minutes
                status["tripped"] = True
                status["trip_until"] = now + trip_duration

                if "trips" not in counts:
                    counts["trips"] = 0
                counts["trips"] += 1

                logger.warning(f"Circuit breaker tripped for {model} with error rate {error_rate:.2f}. Will reset in {trip_duration}s")
                return True

            # Reset counts if we've reached the window size
            counts["success"] = 0
            counts["error"] = 0

        return False

    def _check_user_quota(self, user_id: str, model: str, tokens: Optional[int] = None) -> Tuple[bool, Optional[float], Optional[str]]:
        """
        Check if a user has exceeded their quota.

        Args:
            user_id: The user ID
            model: The AI model being used
            tokens: Optional token count

        Returns:
            Tuple of (should_throttle, retry_after, reason)
        """
        if not self.user_quotas_enabled:
            return False, None, None

        now = time.time()
        today = datetime.datetime.now().date().isoformat()

        # Initialize user usage if not exists
        if user_id not in self.user_usage:
            self.user_usage[user_id] = {
                "daily_requests": {},
                "daily_tokens": {},
                "daily_cost": {}
            }

        usage = self.user_usage[user_id]

        # Initialize today's usage if not exists
        if today not in usage["daily_requests"]:
            usage["daily_requests"][today] = {}
            usage["daily_tokens"][today] = {}
            usage["daily_cost"][today] = {}

        # Initialize model usage if not exists
        if model not in usage["daily_requests"][today]:
            usage["daily_requests"][today][model] = 0
            usage["daily_tokens"][today][model] = 0
            usage["daily_cost"][today][model] = 0.0

        # Get user quota
        quota = self.user_quotas.get(user_id, self.user_quotas.get("default", {
            "daily_request_limit": 1000,
            "daily_token_limit": 100000,
            "cost_limit": 1.0
        }))

        # Check request limit
        total_requests = sum(usage["daily_requests"][today].values())
        if total_requests >= quota["daily_request_limit"]:
            reason = f"User {user_id} exceeded daily request limit of {quota['daily_request_limit']}"
            retry_after = self._get_time_until_tomorrow()
            return True, retry_after, reason

        # Check token limit if tokens provided
        if tokens:
            total_tokens = sum(usage["daily_tokens"][today].values()) + tokens
            if total_tokens > quota["daily_token_limit"]:
                reason = f"User {user_id} exceeded daily token limit of {quota['daily_token_limit']}"
                retry_after = self._get_time_until_tomorrow()
                return True, retry_after, reason

        # Check cost limit if cost tracking enabled
        if self.cost_tracking_enabled:
            total_cost = sum(usage["daily_cost"][today].values())
            if total_cost >= quota["cost_limit"]:
                reason = f"User {user_id} exceeded daily cost limit of ${quota['cost_limit']:.2f}"
                retry_after = self._get_time_until_tomorrow()
                return True, retry_after, reason

        return False, None, None

    def _get_time_until_tomorrow(self) -> float:
        """
        Calculate seconds until midnight (next day).

        Returns:
            Seconds until midnight
        """
        now = datetime.datetime.now()
        tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
        return (tomorrow - now).total_seconds()

    def _get_time_until_budget_reset(self) -> float:
        """
        Calculate seconds until budget reset.

        Returns:
            Seconds until budget reset
        """
        # Default to reset at midnight
        return self._get_time_until_tomorrow()

    async def _adaptive_adjustment_task(self) -> None:
        """Background task to periodically adjust throttling limits based on usage patterns."""
        while True:
            try:
                await asyncio.sleep(self.adaptive_window)
                self._adjust_limits()
            except Exception as e:
                logger.error(f"Error in adaptive throttling adjustment: {e}")

    async def _cost_tracking_task(self) -> None:
        """Background task to periodically check and reset cost tracking."""
        while True:
            try:
                await asyncio.sleep(3600)  # Check every hour

                # Reset daily spend at midnight
                now = datetime.datetime.now()
                if now.hour == 0 and now.minute < 10:  # Reset between 12:00 AM and 12:10 AM
                    with self._cost_lock:
                        logger.info(f"Resetting daily AI spend tracking. Previous total: ${self.current_spend:.2f}")
                        self.current_spend = 0.0
                        self.spend_by_model = {}
                        self.spend_by_user = {}
                        self.budget_alerts_sent.clear()

                # Check budget alerts
                if self.cost_tracking_enabled and self.daily_budget > 0:
                    self._check_budget_alerts()

            except Exception as e:
                logger.error(f"Error in cost tracking task: {e}")

    def _check_budget_alerts(self) -> None:
        """Check and send budget alerts if thresholds are reached."""
        with self._cost_lock:
            spend_percentage = (self.current_spend / self.daily_budget) * 100 if self.daily_budget > 0 else 0

            for threshold in sorted(BUDGET_ALERT_THRESHOLDS):
                if spend_percentage >= threshold and threshold not in self.budget_alerts_sent:
                    logger.warning(f"BUDGET ALERT: AI spend has reached {threshold}% of daily budget (${self.current_spend:.2f}/{self.daily_budget:.2f})")
                    self.budget_alerts_sent.add(threshold)

                    # Send notification to admin/monitoring system
                    self._send_admin_notification(
                        alert_type="budget_threshold",
                        severity="high" if threshold >= 90 else "medium" if threshold >= 75 else "low",
                        message=f"AI Budget Alert: {threshold}% of daily budget reached",
                        details={
                            "threshold": threshold,
                            "current_spend": self.current_spend,
                            "daily_budget": self.daily_budget,
                            "percentage": spend_percentage,
                            "timestamp": datetime.datetime.now().isoformat()
                        }
                    )
                    
    def _send_admin_notification(self, alert_type: str, severity: str, message: str, details: Dict[str, Any]) -> None:
        """Send notification to admin/monitoring system.
        
        Args:
            alert_type: Type of alert (e.g., budget_threshold, error_rate)
            severity: Alert severity (low, medium, high)
            message: Alert message
            details: Additional alert details
        """
        try:
            # Log the notification
            log_method = logger.warning if severity == "high" else logger.info
            log_method(f"Admin notification: {message}")
            
            # Send to monitoring system via metrics service if available
            if self.metrics_service:
                self.metrics_service.record_alert(
                    alert_type=alert_type,
                    severity=severity,
                    message=message,
                    details=details
                )
            
            # Send email notification if configured
            if email_config := os.environ.get("ADMIN_EMAIL_NOTIFICATIONS"):
                self._send_email_notification(email_config, alert_type, severity, message, details)
                
            # Send Slack notification if configured
            if slack_webhook := os.environ.get("ADMIN_SLACK_WEBHOOK"):
                self._send_slack_notification(slack_webhook, alert_type, severity, message, details)
                
            # Store alert in database for admin dashboard
            self._store_alert_in_database(alert_type, severity, message, details)
            
        except Exception as e:
            logger.error(f"Failed to send admin notification: {str(e)}")
            
    def _send_email_notification(self, email_config: str, alert_type: str, severity: str, message: str, details: Dict[str, Any]) -> None:
        """Send email notification to admins.
        
        Args:
            email_config: Email configuration string (comma-separated email addresses)
            alert_type: Type of alert
            severity: Alert severity
            message: Alert message
            details: Additional alert details
        """
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Get SMTP configuration from environment
            smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
            smtp_port = int(os.environ.get("SMTP_PORT", "587"))
            smtp_user = os.environ.get("SMTP_USER", "")
            smtp_password = os.environ.get("SMTP_PASSWORD", "")
            
            if not smtp_user or not smtp_password:
                logger.warning("SMTP credentials not configured, skipping email notification")
                return
                
            # Create email message
            recipients = email_config.split(',')
            
            for recipient in recipients:
                msg = MIMEMultipart()
                msg['From'] = smtp_user
                msg['To'] = recipient.strip()
                msg['Subject'] = f"[{severity.upper()}] AI Budget Alert: {message}"
                
                # Format email body with alert details
                body = f"""
                <html>
                <body>
                    <h2>{message}</h2>
                    <p><strong>Alert Type:</strong> {alert_type}</p>
                    <p><strong>Severity:</strong> {severity}</p>
                    <p><strong>Time:</strong> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <h3>Details:</h3>
                    <ul>
                """
                
                for key, value in details.items():
                    body += f"<li><strong>{key}:</strong> {value}</li>"
                
                body += """
                    </ul>
                    <p>Please check the admin dashboard for more information.</p>
                </body>
                </html>
                """
                
                msg.attach(MIMEText(body, 'html'))
                
                # Connect to SMTP server and send email
                with smtplib.SMTP(smtp_host, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
                    
                logger.info(f"Sent email notification to {recipient}")
                
        except Exception as e:
            logger.error(f"Failed to send email notification: {str(e)}")
            
    def _send_slack_notification(self, webhook_url: str, alert_type: str, severity: str, message: str, details: Dict[str, Any]) -> None:
        """Send Slack notification via webhook.
        
        Args:
            webhook_url: Slack webhook URL
            alert_type: Type of alert
            severity: Alert severity
            message: Alert message
            details: Additional alert details
        """
        try:
            import requests
            
            # Format Slack message
            color = "#ff0000" if severity == "high" else "#ffcc00" if severity == "medium" else "#36a64f"
            
            # Format details as fields
            fields = []
            for key, value in details.items():
                fields.append({
                    "title": key,
                    "value": str(value),
                    "short": len(str(value)) < 20  # Short fields for values less than 20 chars
                })
            
            # Create Slack message payload
            payload = {
                "attachments": [
                    {
                        "fallback": message,
                        "color": color,
                        "pretext": f"*{severity.upper()} Alert*: {alert_type}",
                        "title": message,
                        "fields": fields,
                        "footer": "AI Budget Monitoring System",
                        "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
                        "ts": int(datetime.datetime.now().timestamp())
                    }
                ]
            }
            
            # Send to Slack webhook
            response = requests.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                logger.warning(f"Failed to send Slack notification: {response.status_code} {response.text}")
            else:
                logger.info(f"Sent Slack notification: {message}")
                
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {str(e)}")
            
    def _store_alert_in_database(self, alert_type: str, severity: str, message: str, details: Dict[str, Any]) -> None:
        """Store alert in database for admin dashboard.
        
        Args:
            alert_type: Type of alert
            severity: Alert severity
            message: Alert message
            details: Additional alert details
        """
        try:
            # Create alert data
            alert_id = str(uuid.uuid4())
            timestamp = datetime.datetime.now().isoformat()
            
            alert_data = {
                "id": alert_id,
                "type": alert_type,
                "severity": severity,
                "message": message,
                "details": details,
                "created_at": timestamp,
                "acknowledged": False
            }
            
            # Store in Redis for immediate access by admin dashboard
            if hasattr(self, 'cache_manager') and self.cache_manager:
                alert_key = f"maily:alerts:{alert_id}"
                self.cache_manager.set(alert_key, json.dumps(alert_data), ex=86400*7)  # Expire after 7 days
                
                # Add to recent alerts list
                self.cache_manager.lpush("maily:recent_alerts", alert_id)
                self.cache_manager.ltrim("maily:recent_alerts", 0, 99)  # Keep last 100 alerts
                
            # Store in database if available
            try:
                from ...services.database import get_db_connection
                
                # Get database connection
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Create alerts table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS admin_alerts (
                        id TEXT PRIMARY KEY,
                        type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        message TEXT NOT NULL,
                        details TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        acknowledged BOOLEAN NOT NULL DEFAULT FALSE
                    )
                """)
                
                # Insert alert into database
                cursor.execute(
                    """
                    INSERT INTO admin_alerts (id, type, severity, message, details, created_at, acknowledged)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        alert_id,
                        alert_type,
                        severity,
                        message,
                        json.dumps(details),
                        timestamp,
                        False
                    )
                )
                
                conn.commit()
                logger.info(f"Stored alert in database: {alert_id}")
                
            except ImportError:
                logger.debug("Database module not available, skipping database storage")
            except Exception as db_error:
                logger.error(f"Failed to store alert in database: {str(db_error)}")
                
        except Exception as e:
            logger.error(f"Failed to store alert in database: {str(e)}")

    def update_cost_tracking(self, model: str, input_tokens: int, output_tokens: int, user_id: Optional[str] = None) -> None:
        """
        Update cost tracking for a completed request.

        Args:
            model: The AI model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            user_id: Optional user ID for per-user cost tracking
        """
        if not self.cost_tracking_enabled:
            return

        # Calculate cost based on model pricing
        model_costs = MODEL_COSTS.get(model, MODEL_COSTS.get("default"))
        input_cost = (input_tokens / 1000) * model_costs["input"]
        output_cost = (output_tokens / 1000) * model_costs["output"]
        total_cost = input_cost + output_cost

        with self._cost_lock:
            # Update global spend
            self.current_spend += total_cost

            # Update spend by model
            if model not in self.spend_by_model:
                self.spend_by_model[model] = 0.0
            self.spend_by_model[model] += total_cost

            # Update spend by user
            if user_id:
                if user_id not in self.spend_by_user:
                    self.spend_by_user[user_id] = 0.0
                self.spend_by_user[user_id] += total_cost

                # Update user quota usage
                if self.user_quotas_enabled:
                    today = datetime.datetime.now().date().isoformat()
                    if user_id in self.user_usage and today in self.user_usage[user_id]["daily_cost"]:
                        if model not in self.user_usage[user_id]["daily_cost"][today]:
                            self.user_usage[user_id]["daily_cost"][today][model] = 0.0
                        self.user_usage[user_id]["daily_cost"][today][model] += total_cost

                        if model not in self.user_usage[user_id]["daily_tokens"][today]:
                            self.user_usage[user_id]["daily_tokens"][today][model] = 0
                        self.user_usage[user_id]["daily_tokens"][today][model] += input_tokens + output_tokens

        # Check budget alerts
        if self.daily_budget > 0:
            self._check_budget_alerts()

    def record_circuit_breaker_result(self, model: str, success: bool) -> None:
        """
        Record success or failure for circuit breaker tracking.

        Args:
            model: The AI model used
            success: Whether the request was successful
        """
        if not self.circuit_breaker_enabled:
            return

        if model not in self.circuit_breaker_counts:
            self.circuit_breaker_counts[model] = {
                "success": 0,
                "error": 0,
                "trips": 0
            }

        counts = self.circuit_breaker_counts[model]
        if success:
            counts["success"] = counts.get("success", 0) + 1
        else:
            counts["error"] = counts.get("error", 0) + 1

    def _adjust_limits(self) -> Dict[str, Any]:
        """
        Adaptively adjust throttling limits based on usage patterns.

        Returns:
            Dictionary of adjusted limits.
        """
        if not self.adaptive_enabled or len(self.adaptive_samples) < 100:
            return self.limits

        with self._samples_lock:
            # Group samples by model
            model_samples = {}
            for sample in self.adaptive_samples:
                model = sample["model"]
                if model not in model_samples:
                    model_samples[model] = []
                model_samples[model].append(sample)

            # Clear samples after processing
            self.adaptive_samples = []

        # Calculate throttling rate for each model
        adjustments = {}
        for model, samples in model_samples.items():
            if len(samples) < 20:  # Need enough samples
                continue

            throttle_rate = sum(1 for s in samples if s.get("throttled", False)) / len(samples)

            # Adjust limit based on throttle rate
            current_limit = self.limits.get(model, self.limits.get("default", DEFAULT_LIMITS["default"]))

            if throttle_rate > 0.1:  # More than 10% of requests throttled
                # Decrease limit
                new_limit = max(10, int(current_limit * 0.9))
            elif throttle_rate < 0.01:  # Less than 1% of requests throttled
                # Increase limit
                new_limit = min(1000, int(current_limit * 1.1))
            else:
                # Keep current limit
                new_limit = current_limit

            if new_limit != current_limit:
                adjustments[model] = new_limit

        # Apply adjustments
        with self._rates_lock:
            for model, new_limit in adjustments.items():
                self.limits[model] = new_limit
                logger.info(f"Adjusted throttling limit for {model}: {new_limit}")

        return self.limits

    def reset_stats(self) -> None:
        """Reset throttling statistics."""
        with self._rates_lock:
            self.throttled_count = 0
            self.last_throttled = {}

        with self._samples_lock:
            self.adaptive_samples = []

        if self.circuit_breaker_enabled:
            self.circuit_breaker_counts = {}
            self.circuit_breaker_status = {}

        logger.info("Throttling statistics reset")

    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the throttling service.

        Returns:
            Dictionary with health status information.
        """
        return {
            "status": "healthy",
            "throttled_count": self.throttled_count,
            "concurrent_requests": self.current_concurrent_requests,
            "adaptive_enabled": self.adaptive_enabled,
            "circuit_breaker_enabled": self.circuit_breaker_enabled,
            "token_bucket_enabled": self.token_bucket_enabled,
            "cost_tracking_enabled": self.cost_tracking_enabled,
            "timestamp": datetime.datetime.now().isoformat()
        }


# Create a singleton instance of the service
throttling_service = ThrottlingService()

# Example usage:
"""
# Basic throttling check
allowed, retry_after, reason = await throttling_service.check_throttle(
    model="gpt-4",
    user_id="user123",
    priority="normal"
)

if not allowed:
    logger.warning(f"Request throttled: {reason}. Retry after {retry_after} seconds.")
    # Handle throttling (e.g., return error, queue request, etc.)
else:
    # Proceed with AI request
    pass

# Using the context manager (recommended)
async with throttling_service.throttle(
    model="gpt-4",
    user_id="user123",
    priority="high",
    tokens=1500
) as allowed:
    if allowed:
        # Make AI request
        response = await ai_service.generate_response(...)

        # Update cost tracking
        throttling_service.update_cost_tracking(
            model="gpt-4",
            input_tokens=1500,
            output_tokens=500,
            user_id="user123"
        )
    else:
        # Handle throttling
        retry_after = throttling_service.throttle.retry_after
        reason = throttling_service.throttle.reason
        logger.warning(f"Request throttled: {reason}. Retry after {retry_after} seconds.")

# Get throttling statistics
stats = throttling_service.get_stats()
logger.info(f"Throttling stats: {stats}")

# Health check
health = throttling_service.health_check()
logger.info(f"Throttling health: {health}")
"""
