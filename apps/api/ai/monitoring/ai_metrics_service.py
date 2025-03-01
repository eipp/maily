"""
AI Metrics Service

This module provides a specialized metrics service for AI operations,
tracking performance, costs, and usage patterns.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Tuple
import asyncio
import json
import statistics
from functools import wraps

from ...monitoring.performance_metrics import MetricsService
from ...cache.redis_service import RedisService

logger = logging.getLogger(__name__)


class AIMetricsService:
    """
    Specialized metrics service for AI operations.

    This service tracks performance, costs, and usage patterns for AI operations,
    providing insights into model performance and cost efficiency.
    """

    def __init__(self, metrics_service: MetricsService, redis_service: Optional[RedisService] = None):
        """
        Initialize the AI metrics service.

        Args:
            metrics_service: The base metrics service to use for recording metrics.
            redis_service: Optional Redis service for real-time metrics and alerting.
        """
        self.metrics_service = metrics_service
        self.redis_service = redis_service
        self.model_costs = {
            # OpenAI models (approximate costs per 1K tokens)
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "text-embedding-3-small": {"input": 0.0001, "output": 0.0},
            "text-embedding-3-large": {"input": 0.00013, "output": 0.0},

            # Anthropic models (approximate costs per 1K tokens)
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "claude-3-haiku": {"input": 0.00025, "output": 0.00125},

            # Google models (approximate costs per 1K tokens)
            "gemini-1.5-pro": {"input": 0.00125, "output": 0.00375},
            "gemini-1.5-flash": {"input": 0.0005, "output": 0.0015},
        }

        # Alert thresholds
        self.alert_thresholds = {
            "latency_ms": 5000,  # Alert if latency exceeds 5 seconds
            "error_rate": 0.05,  # Alert if error rate exceeds 5%
            "cost_per_minute": 1.0,  # Alert if cost exceeds $1 per minute
            "token_usage_per_minute": 100000,  # Alert if token usage exceeds 100K per minute
        }

        # Initialize performance tracking
        self._initialize_performance_tracking()

    def _initialize_performance_tracking(self):
        """Initialize performance tracking metrics."""
        self.performance_windows = {
            "1m": 60,    # 1 minute window
            "5m": 300,   # 5 minute window
            "15m": 900,  # 15 minute window
            "1h": 3600,  # 1 hour window
        }

        # Initialize performance metrics
        self.performance_metrics = {
            window: {
                "latency": [],
                "success_count": 0,
                "error_count": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "requests": 0,
                "start_time": time.time(),
            }
            for window in self.performance_windows
        }

    def record_generation(
        self,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        success: bool = True,
        error: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record metrics for a text generation operation.

        Args:
            model_name: The name of the model used.
            prompt_tokens: The number of tokens in the prompt.
            completion_tokens: The number of tokens in the completion.
            latency_ms: The latency of the operation in milliseconds.
            success: Whether the operation was successful.
            error: The error message if the operation failed.
            user_id: The ID of the user who made the request.
            metadata: Additional metadata to include in the metrics.
        """
        metadata = metadata or {}

        # Calculate cost
        cost = self._calculate_cost(model_name, prompt_tokens, completion_tokens)
        total_tokens = prompt_tokens + completion_tokens

        # Record metrics
        self.metrics_service.record_metric(
            metric_type="ai_generation",
            name=f"generation_{model_name.replace('-', '_')}",
            value={
                "model_name": model_name,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "latency_ms": latency_ms,
                "cost_usd": cost,
                "success": success,
                "error": error,
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                **metadata,
            },
            success=success,
            error_message=error,
        )

        # Record additional metrics for aggregation
        self.metrics_service.record_metric(
            metric_type="ai_tokens",
            name="total_tokens",
            value=total_tokens,
        )

        self.metrics_service.record_metric(
            metric_type="ai_cost",
            name="total_cost",
            value=cost,
        )

        self.metrics_service.record_metric(
            metric_type="ai_latency",
            name=f"latency_{model_name.replace('-', '_')}",
            value=latency_ms,
        )

        # Update performance tracking
        self._update_performance_metrics(latency_ms, success, total_tokens, cost)

        # Store real-time metrics in Redis if available
        if self.redis_service:
            self._store_realtime_metrics(model_name, latency_ms, success, total_tokens, cost)

            # Check for alert conditions
            self._check_alert_conditions(model_name, latency_ms, success, error)

    def record_embedding(
        self,
        model_name: str,
        input_tokens: int,
        vector_count: int,
        latency_ms: float,
        success: bool = True,
        error: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record metrics for an embedding operation.

        Args:
            model_name: The name of the model used.
            input_tokens: The number of tokens in the input.
            vector_count: The number of vectors generated.
            latency_ms: The latency of the operation in milliseconds.
            success: Whether the operation was successful.
            error: The error message if the operation failed.
            user_id: The ID of the user who made the request.
            metadata: Additional metadata to include in the metrics.
        """
        metadata = metadata or {}

        # Calculate cost
        cost = self._calculate_cost(model_name, input_tokens, 0)

        # Record metrics
        self.metrics_service.record_metric(
            metric_type="ai_embedding",
            name=f"embedding_{model_name.replace('-', '_')}",
            value={
                "model_name": model_name,
                "input_tokens": input_tokens,
                "vector_count": vector_count,
                "latency_ms": latency_ms,
                "cost_usd": cost,
                "success": success,
                "error": error,
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                **metadata,
            },
            success=success,
            error_message=error,
        )

        # Record additional metrics for aggregation
        self.metrics_service.record_metric(
            metric_type="ai_tokens",
            name="embedding_tokens",
            value=input_tokens,
        )

        self.metrics_service.record_metric(
            metric_type="ai_cost",
            name="embedding_cost",
            value=cost,
        )

        # Update performance tracking
        self._update_performance_metrics(latency_ms, success, input_tokens, cost)

        # Store real-time metrics in Redis if available
        if self.redis_service:
            self._store_realtime_metrics(model_name, latency_ms, success, input_tokens, cost, operation_type="embedding")

            # Check for alert conditions
            self._check_alert_conditions(model_name, latency_ms, success, error, operation_type="embedding")

    def record_cache_metrics(
        self,
        hits: int,
        misses: int,
        hit_ratio: float,
        estimated_savings: float,
    ) -> None:
        """
        Record cache performance metrics.

        Args:
            hits: The number of cache hits.
            misses: The number of cache misses.
            hit_ratio: The cache hit ratio.
            estimated_savings: The estimated cost savings from cache hits.
        """
        self.metrics_service.record_metric(
            metric_type="ai_cache",
            name="cache_performance",
            value={
                "hits": hits,
                "misses": misses,
                "hit_ratio": hit_ratio,
                "estimated_savings": estimated_savings,
                "timestamp": datetime.now().isoformat(),
            },
        )

        # Store cache metrics in Redis if available
        if self.redis_service:
            cache_metrics = {
                "hits": hits,
                "misses": misses,
                "hit_ratio": hit_ratio,
                "estimated_savings": estimated_savings,
                "timestamp": datetime.now().isoformat(),
            }
            self.redis_service.set(
                "maily:ai:cache:metrics",
                json.dumps(cache_metrics),
                ex=3600  # Expire after 1 hour
            )

    def _calculate_cost(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate the cost of a model operation.

        Args:
            model_name: The name of the model used.
            input_tokens: The number of tokens in the input.
            output_tokens: The number of tokens in the output.

        Returns:
            The cost in USD.
        """
        # Get model costs, defaulting to GPT-3.5 Turbo costs if model not found
        model_cost = self.model_costs.get(
            model_name,
            {"input": 0.0015, "output": 0.002}
        )

        # Calculate cost
        input_cost = (input_tokens / 1000) * model_cost["input"]
        output_cost = (output_tokens / 1000) * model_cost["output"]

        return input_cost + output_cost

    def _update_performance_metrics(self, latency_ms: float, success: bool, tokens: int, cost: float) -> None:
        """
        Update performance metrics for all time windows.

        Args:
            latency_ms: The latency of the operation in milliseconds.
            success: Whether the operation was successful.
            tokens: The number of tokens processed.
            cost: The cost of the operation.
        """
        current_time = time.time()

        for window, duration in self.performance_windows.items():
            # Reset window if expired
            if current_time - self.performance_metrics[window]["start_time"] > duration:
                self.performance_metrics[window] = {
                    "latency": [],
                    "success_count": 0,
                    "error_count": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "requests": 0,
                    "start_time": current_time,
                }

            # Update metrics
            metrics = self.performance_metrics[window]
            metrics["latency"].append(latency_ms)
            metrics["success_count"] += 1 if success else 0
            metrics["error_count"] += 0 if success else 1
            metrics["total_tokens"] += tokens
            metrics["total_cost"] += cost
            metrics["requests"] += 1

            # Limit latency array size to prevent memory issues
            if len(metrics["latency"]) > 1000:
                metrics["latency"] = metrics["latency"][-1000:]

    def _store_realtime_metrics(
        self,
        model_name: str,
        latency_ms: float,
        success: bool,
        tokens: int,
        cost: float,
        operation_type: str = "generation"
    ) -> None:
        """
        Store real-time metrics in Redis.

        Args:
            model_name: The name of the model used.
            latency_ms: The latency of the operation in milliseconds.
            success: Whether the operation was successful.
            tokens: The number of tokens processed.
            cost: The cost of the operation.
            operation_type: The type of operation (generation or embedding).
        """
        if not self.redis_service:
            return

        # Store model-specific metrics
        model_key = f"maily:ai:{operation_type}:{model_name.replace('-', '_')}"

        # Update latency histogram
        latency_bucket = self._get_latency_bucket(latency_ms)
        self.redis_service.hincrby(f"{model_key}:latency", latency_bucket, 1)

        # Update success/error counts
        self.redis_service.hincrby(f"{model_key}:status", "success" if success else "error", 1)

        # Update token usage
        self.redis_service.hincrby(f"{model_key}:tokens", "total", tokens)

        # Update cost
        self.redis_service.hincrbyfloat(f"{model_key}:cost", "total", cost)

        # Set expiration for all keys
        self.redis_service.expire(f"{model_key}:latency", 86400)  # 24 hours
        self.redis_service.expire(f"{model_key}:status", 86400)
        self.redis_service.expire(f"{model_key}:tokens", 86400)
        self.redis_service.expire(f"{model_key}:cost", 86400)

        # Update global metrics
        global_key = f"maily:ai:{operation_type}:global"
        self.redis_service.hincrby(f"{global_key}:status", "success" if success else "error", 1)
        self.redis_service.hincrby(f"{global_key}:tokens", "total", tokens)
        self.redis_service.hincrbyfloat(f"{global_key}:cost", "total", cost)
        self.redis_service.expire(f"{global_key}:status", 86400)
        self.redis_service.expire(f"{global_key}:tokens", 86400)
        self.redis_service.expire(f"{global_key}:cost", 86400)

        # Update minute-by-minute metrics for time series
        minute_key = f"maily:ai:{operation_type}:minute:{int(time.time() / 60)}"
        self.redis_service.hincrby(minute_key, "requests", 1)
        self.redis_service.hincrby(minute_key, "success", 1 if success else 0)
        self.redis_service.hincrby(minute_key, "errors", 0 if success else 1)
        self.redis_service.hincrby(minute_key, "tokens", tokens)
        self.redis_service.hincrbyfloat(minute_key, "cost", cost)
        self.redis_service.hincrbyfloat(minute_key, "latency_sum", latency_ms)
        self.redis_service.expire(minute_key, 86400)  # 24 hours

    def _get_latency_bucket(self, latency_ms: float) -> str:
        """
        Get the appropriate latency bucket for a latency value.

        Args:
            latency_ms: The latency in milliseconds.

        Returns:
            The latency bucket as a string.
        """
        if latency_ms < 100:
            return "<100ms"
        elif latency_ms < 500:
            return "100-500ms"
        elif latency_ms < 1000:
            return "500-1000ms"
        elif latency_ms < 2000:
            return "1-2s"
        elif latency_ms < 5000:
            return "2-5s"
        else:
            return ">5s"

    def _check_alert_conditions(
        self,
        model_name: str,
        latency_ms: float,
        success: bool,
        error: Optional[str] = None,
        operation_type: str = "generation"
    ) -> None:
        """
        Check for alert conditions and trigger alerts if necessary.

        Args:
            model_name: The name of the model used.
            latency_ms: The latency of the operation in milliseconds.
            success: Whether the operation was successful.
            error: The error message if the operation failed.
            operation_type: The type of operation (generation or embedding).
        """
        if not self.redis_service:
            return

        # Check latency threshold
        if latency_ms > self.alert_thresholds["latency_ms"]:
            self._trigger_alert(
                alert_type="high_latency",
                model_name=model_name,
                operation_type=operation_type,
                details={
                    "latency_ms": latency_ms,
                    "threshold_ms": self.alert_thresholds["latency_ms"],
                }
            )

        # Check error rate threshold for 1-minute window
        metrics_1m = self.performance_metrics["1m"]
        if metrics_1m["requests"] >= 10:  # Only check if we have enough data
            error_rate = metrics_1m["error_count"] / metrics_1m["requests"]
            if error_rate > self.alert_thresholds["error_rate"]:
                self._trigger_alert(
                    alert_type="high_error_rate",
                    model_name=model_name,
                    operation_type=operation_type,
                    details={
                        "error_rate": error_rate,
                        "threshold": self.alert_thresholds["error_rate"],
                        "error_count": metrics_1m["error_count"],
                        "total_requests": metrics_1m["requests"],
                        "latest_error": error,
                    }
                )

        # Check cost per minute threshold
        if metrics_1m["total_cost"] > self.alert_thresholds["cost_per_minute"]:
            self._trigger_alert(
                alert_type="high_cost",
                model_name=model_name,
                operation_type=operation_type,
                details={
                    "cost_per_minute": metrics_1m["total_cost"],
                    "threshold": self.alert_thresholds["cost_per_minute"],
                }
            )

        # Check token usage per minute threshold
        if metrics_1m["total_tokens"] > self.alert_thresholds["token_usage_per_minute"]:
            self._trigger_alert(
                alert_type="high_token_usage",
                model_name=model_name,
                operation_type=operation_type,
                details={
                    "tokens_per_minute": metrics_1m["total_tokens"],
                    "threshold": self.alert_thresholds["token_usage_per_minute"],
                }
            )

    def _trigger_alert(
        self,
        alert_type: str,
        model_name: str,
        operation_type: str,
        details: Dict[str, Any]
    ) -> None:
        """
        Trigger an alert by storing it in Redis and logging it.

        Args:
            alert_type: The type of alert.
            model_name: The name of the model that triggered the alert.
            operation_type: The type of operation (generation or embedding).
            details: Additional details about the alert.
        """
        if not self.redis_service:
            return

        alert_id = f"{int(time.time())}_{alert_type}_{model_name}"
        alert_data = {
            "id": alert_id,
            "type": alert_type,
            "model_name": model_name,
            "operation_type": operation_type,
            "timestamp": datetime.now().isoformat(),
            "details": details,
        }

        # Store alert in Redis
        self.redis_service.set(
            f"maily:ai:alerts:{alert_id}",
            json.dumps(alert_data),
            ex=86400  # Expire after 24 hours
        )

        # Add to recent alerts list
        self.redis_service.lpush("maily:ai:recent_alerts", alert_id)
        self.redis_service.ltrim("maily:ai:recent_alerts", 0, 99)  # Keep last 100 alerts

        # Log the alert
        logger.warning(f"AI Performance Alert: {alert_type} for {model_name} ({operation_type})", extra=details)

    def get_model_performance_summary(self) -> Dict[str, Any]:
        """
        Get a summary of model performance metrics.

        Returns:
            A dictionary containing performance metrics for each model.
        """
        summary = {}

        for window, metrics in self.performance_metrics.items():
            if metrics["requests"] == 0:
                continue

            window_metrics = {
                "requests": metrics["requests"],
                "success_rate": metrics["success_count"] / metrics["requests"] if metrics["requests"] > 0 else 1.0,
                "error_rate": metrics["error_count"] / metrics["requests"] if metrics["requests"] > 0 else 0.0,
                "total_tokens": metrics["total_tokens"],
                "total_cost": metrics["total_cost"],
                "avg_tokens_per_request": metrics["total_tokens"] / metrics["requests"] if metrics["requests"] > 0 else 0,
                "avg_cost_per_request": metrics["total_cost"] / metrics["requests"] if metrics["requests"] > 0 else 0,
            }

            # Calculate latency statistics if we have data
            if metrics["latency"]:
                window_metrics.update({
                    "latency_avg": statistics.mean(metrics["latency"]),
                    "latency_p50": statistics.median(metrics["latency"]),
                    "latency_p90": statistics.quantiles(metrics["latency"], n=10)[8] if len(metrics["latency"]) >= 10 else None,
                    "latency_p95": statistics.quantiles(metrics["latency"], n=20)[18] if len(metrics["latency"]) >= 20 else None,
                    "latency_p99": statistics.quantiles(metrics["latency"], n=100)[98] if len(metrics["latency"]) >= 100 else None,
                })

            summary[window] = window_metrics

        return {
            "summary": summary,
            "timestamp": datetime.now().isoformat(),
        }

    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent alerts from Redis.

        Args:
            limit: Maximum number of alerts to return.

        Returns:
            A list of recent alerts.
        """
        if not self.redis_service:
            return []

        # Get recent alert IDs
        alert_ids = self.redis_service.lrange("maily:ai:recent_alerts", 0, limit - 1)

        # Get alert details
        alerts = []
        for alert_id in alert_ids:
            alert_json = self.redis_service.get(f"maily:ai:alerts:{alert_id}")
            if alert_json:
                try:
                    alerts.append(json.loads(alert_json))
                except json.JSONDecodeError:
                    logger.error(f"Failed to decode alert JSON: {alert_json}")

        return alerts

    def set_alert_threshold(self, metric: str, value: float) -> None:
        """
        Set an alert threshold.

        Args:
            metric: The metric to set the threshold for.
            value: The threshold value.
        """
        if metric in self.alert_thresholds:
            self.alert_thresholds[metric] = value
            logger.info(f"Set alert threshold for {metric} to {value}")
        else:
            logger.warning(f"Unknown alert metric: {metric}")


# Decorator for measuring AI function performance
def measure_ai_performance(metrics_service: AIMetricsService, model_name: str, operation_type: str = "generation"):
    """
    Decorator for measuring AI function performance.

    Args:
        metrics_service: The AI metrics service to use.
        model_name: The name of the model being used.
        operation_type: The type of operation (generation or embedding).

    Returns:
        A decorator function.
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error = None
            tokens_in = 0
            tokens_out = 0

            try:
                # Extract token counts from kwargs if available
                if "prompt_tokens" in kwargs:
                    tokens_in = kwargs["prompt_tokens"]

                result = await func(*args, **kwargs)

                # Try to extract token counts from result if available
                if isinstance(result, dict):
                    if "usage" in result:
                        usage = result["usage"]
                        if "prompt_tokens" in usage:
                            tokens_in = usage["prompt_tokens"]
                        if "completion_tokens" in usage:
                            tokens_out = usage["completion_tokens"]
                    elif "tokens" in result:
                        tokens_in = result.get("input_tokens", 0)
                        tokens_out = result.get("output_tokens", 0)

                return result
            except Exception as e:
                success = False
                error = str(e)
                raise
            finally:
                end_time = time.time()
                latency_ms = (end_time - start_time) * 1000

                if operation_type == "generation":
                    metrics_service.record_generation(
                        model_name=model_name,
                        prompt_tokens=tokens_in,
                        completion_tokens=tokens_out,
                        latency_ms=latency_ms,
                        success=success,
                        error=error,
                    )
                elif operation_type == "embedding":
                    metrics_service.record_embedding(
                        model_name=model_name,
                        input_tokens=tokens_in,
                        vector_count=1,  # Default to 1 if not known
                        latency_ms=latency_ms,
                        success=success,
                        error=error,
                    )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error = None
            tokens_in = 0
            tokens_out = 0

            try:
                # Extract token counts from kwargs if available
                if "prompt_tokens" in kwargs:
                    tokens_in = kwargs["prompt_tokens"]

                result = func(*args, **kwargs)

                # Try to extract token counts from result if available
                if isinstance(result, dict):
                    if "usage" in result:
                        usage = result["usage"]
                        if "prompt_tokens" in usage:
                            tokens_in = usage["prompt_tokens"]
                        if "completion_tokens" in usage:
                            tokens_out = usage["completion_tokens"]
                    elif "tokens" in result:
                        tokens_in = result.get("input_tokens", 0)
                        tokens_out = result.get("output_tokens", 0)

                return result
            except Exception as e:
                success = False
                error = str(e)
                raise
            finally:
                end_time = time.time()
                latency_ms = (end_time - start_time) * 1000

                if operation_type == "generation":
                    metrics_service.record_generation(
                        model_name=model_name,
                        prompt_tokens=tokens_in,
                        completion_tokens=tokens_out,
                        latency_ms=latency_ms,
                        success=success,
                        error=error,
                    )
                elif operation_type == "embedding":
                    metrics_service.record_embedding(
                        model_name=model_name,
                        input_tokens=tokens_in,
                        vector_count=1,  # Default to 1 if not known
                        latency_ms=latency_ms,
                        success=success,
                        error=error,
                    )

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


# Create a singleton instance of the service
from ...monitoring.performance_metrics import metrics_service
ai_metrics_service = AIMetricsService(metrics_service)
