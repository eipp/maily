"""
Metrics Manager for Maily Application

This module provides a centralized metrics collection system using Prometheus for
monitoring application performance, resource usage, and business metrics. It offers:

1. Standard system metrics collection (CPU, memory, disk usage)
2. Application-specific metrics (endpoint latency, request counts)
3. Business metrics (emails sent, campaign performance)
4. Configurable aggregation and exporters
5. Real-time alerting thresholds
6. Integration with Grafana dashboards
"""

import os
import time
import socket
import threading
from functools import wraps
from typing import Dict, List, Optional, Callable, Any, Union, Set
from enum import Enum
import logging
import psutil

from fastapi import Request, Response
from prometheus_client import (
    Counter, Gauge, Histogram, Summary,
    REGISTRY, CollectorRegistry, push_to_gateway,
    start_http_server, multiprocess, generate_latest
)
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily
from prometheus_client.utils import INF

# Configure logging
logger = logging.getLogger(__name__)

# Metric configuration
DEFAULT_BUCKETS = (
    0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, INF
)

# Environment-specific settings
ENABLE_METRICS = os.getenv("ENABLE_METRICS", "true").lower() == "true"
METRICS_PORT = int(os.getenv("METRICS_PORT", "9090"))
PUSH_GATEWAY_URL = os.getenv("PUSH_GATEWAY_URL", "")
PUSH_INTERVAL = int(os.getenv("METRICS_PUSH_INTERVAL", "15"))  # seconds
HOSTNAME = socket.gethostname()
ENV = os.getenv("ENVIRONMENT", "development")


class MetricType(Enum):
    """Enum for different types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class MetricsManager:
    """
    Singleton class for managing application metrics.
    Provides methods for registering, collecting, and exporting metrics.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MetricsManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Metrics collections
        self._counters: Dict[str, Counter] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._histograms: Dict[str, Histogram] = {}
        self._summaries: Dict[str, Summary] = {}

        # Business metric aggregations (for custom reporting)
        self._business_metrics: Dict[str, Dict[str, Any]] = {}

        # Setup thread for pushing metrics if gateway configured
        self._push_thread = None
        self._stop_push_thread = threading.Event()

        # Initialize standard metrics
        if ENABLE_METRICS:
            self._init_standard_metrics()

            # Start metrics HTTP server
            start_http_server(METRICS_PORT)
            logger.info(f"Metrics server started on port {METRICS_PORT}")

            # Start push thread if gateway configured
            if PUSH_GATEWAY_URL:
                self._start_push_thread()

        self._initialized = True

    def _init_standard_metrics(self):
        """Initialize standard application metrics"""
        # System metrics
        self.register_gauge(
            "system_cpu_usage",
            "CPU usage percentage",
            ["hostname", "env"]
        )

        self.register_gauge(
            "system_memory_usage_bytes",
            "Memory usage in bytes",
            ["hostname", "env", "type"]
        )

        self.register_gauge(
            "system_disk_usage_bytes",
            "Disk usage in bytes",
            ["hostname", "env", "path", "type"]
        )

        # Application metrics
        self.register_counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status"]
        )

        self.register_histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint"],
            buckets=DEFAULT_BUCKETS
        )

        self.register_gauge(
            "http_requests_in_progress",
            "HTTP requests currently in progress",
            ["method", "endpoint"]
        )

        # Database metrics
        self.register_histogram(
            "database_query_duration_seconds",
            "Database query duration in seconds",
            ["operation", "table"],
            buckets=DEFAULT_BUCKETS
        )

        self.register_counter(
            "database_errors_total",
            "Total database errors",
            ["operation", "error_type"]
        )

        # Redis cache metrics
        self.register_counter(
            "cache_operations_total",
            "Total cache operations",
            ["operation", "result"]
        )

        self.register_histogram(
            "cache_operation_duration_seconds",
            "Cache operation duration in seconds",
            ["operation"],
            buckets=DEFAULT_BUCKETS
        )

        self.register_gauge(
            "cache_size_keys",
            "Number of keys in cache",
            ["prefix"]
        )

        # Email metrics
        self.register_counter(
            "emails_sent_total",
            "Total emails sent",
            ["campaign_id", "template_id", "status"]
        )

        self.register_gauge(
            "email_queue_size",
            "Number of emails in sending queue",
            ["priority"]
        )

        self.register_histogram(
            "email_send_duration_seconds",
            "Email sending duration in seconds",
            buckets=DEFAULT_BUCKETS
        )

        # AI processing metrics
        self.register_counter(
            "ai_requests_total",
            "Total AI processing requests",
            ["model", "operation", "status"]
        )

        self.register_histogram(
            "ai_processing_duration_seconds",
            "AI processing duration in seconds",
            ["model", "operation"],
            buckets=DEFAULT_BUCKETS
        )

        self.register_counter(
            "ai_token_usage_total",
            "Total AI token usage",
            ["model", "operation", "type"]
        )

    def _start_push_thread(self):
        """Start a thread to periodically push metrics to Prometheus gateway"""
        def push_metrics():
            registry = REGISTRY
            while not self._stop_push_thread.is_set():
                try:
                    push_to_gateway(
                        PUSH_GATEWAY_URL,
                        job=f"maily_{ENV}",
                        registry=registry,
                        grouping_key={"instance": HOSTNAME}
                    )
                except Exception as e:
                    logger.error(f"Failed to push metrics to gateway: {e}")

                # Collect system metrics
                self._collect_system_metrics()

                # Wait for next push interval or until stopped
                self._stop_push_thread.wait(timeout=PUSH_INTERVAL)

        self._push_thread = threading.Thread(target=push_metrics, daemon=True)
        self._push_thread.start()
        logger.info(f"Started metrics push thread, pushing to {PUSH_GATEWAY_URL} every {PUSH_INTERVAL}s")

    def _collect_system_metrics(self):
        """Collect system metrics like CPU, memory, and disk usage"""
        if not ENABLE_METRICS:
            return

        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.5)
            self._gauges["system_cpu_usage"].labels(
                hostname=HOSTNAME,
                env=ENV
            ).set(cpu_percent)

            # Memory usage
            memory = psutil.virtual_memory()
            self._gauges["system_memory_usage_bytes"].labels(
                hostname=HOSTNAME,
                env=ENV,
                type="total"
            ).set(memory.total)
            self._gauges["system_memory_usage_bytes"].labels(
                hostname=HOSTNAME,
                env=ENV,
                type="used"
            ).set(memory.used)
            self._gauges["system_memory_usage_bytes"].labels(
                hostname=HOSTNAME,
                env=ENV,
                type="available"
            ).set(memory.available)

            # Disk usage
            disk = psutil.disk_usage('/')
            self._gauges["system_disk_usage_bytes"].labels(
                hostname=HOSTNAME,
                env=ENV,
                path="/",
                type="total"
            ).set(disk.total)
            self._gauges["system_disk_usage_bytes"].labels(
                hostname=HOSTNAME,
                env=ENV,
                path="/",
                type="used"
            ).set(disk.used)
            self._gauges["system_disk_usage_bytes"].labels(
                hostname=HOSTNAME,
                env=ENV,
                path="/",
                type="free"
            ).set(disk.free)
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

    def register_counter(self, name: str, description: str, labels: List[str] = None) -> Counter:
        """
        Register a counter metric

        Args:
            name: Metric name
            description: Metric description
            labels: Label names for the metric

        Returns:
            The registered counter
        """
        if not ENABLE_METRICS:
            return None

        if name in self._counters:
            return self._counters[name]

        counter = Counter(name, description, labels or [])
        self._counters[name] = counter
        return counter

    def register_gauge(self, name: str, description: str, labels: List[str] = None) -> Gauge:
        """
        Register a gauge metric

        Args:
            name: Metric name
            description: Metric description
            labels: Label names for the metric

        Returns:
            The registered gauge
        """
        if not ENABLE_METRICS:
            return None

        if name in self._gauges:
            return self._gauges[name]

        gauge = Gauge(name, description, labels or [])
        self._gauges[name] = gauge
        return gauge

    def register_histogram(
        self,
        name: str,
        description: str,
        labels: List[str] = None,
        buckets: tuple = DEFAULT_BUCKETS
    ) -> Histogram:
        """
        Register a histogram metric

        Args:
            name: Metric name
            description: Metric description
            labels: Label names for the metric
            buckets: Histogram buckets

        Returns:
            The registered histogram
        """
        if not ENABLE_METRICS:
            return None

        if name in self._histograms:
            return self._histograms[name]

        histogram = Histogram(name, description, labels or [], buckets=buckets)
        self._histograms[name] = histogram
        return histogram

    def register_summary(
        self,
        name: str,
        description: str,
        labels: List[str] = None,
        quantiles: tuple = (.5, .9, .95, .99)
    ) -> Summary:
        """
        Register a summary metric

        Args:
            name: Metric name
            description: Metric description
            labels: Label names for the metric
            quantiles: Summary quantiles

        Returns:
            The registered summary
        """
        if not ENABLE_METRICS:
            return None

        if name in self._summaries:
            return self._summaries[name]

        summary = Summary(name, description, labels or [], quantiles=quantiles)
        self._summaries[name] = summary
        return summary

    def increment_counter(self, name: str, amount: float = 1, **labels) -> None:
        """
        Increment a counter metric

        Args:
            name: Metric name
            amount: Amount to increment
            **labels: Label values
        """
        if not ENABLE_METRICS or name not in self._counters:
            return

        if labels:
            self._counters[name].labels(**labels).inc(amount)
        else:
            self._counters[name].inc(amount)

    def set_gauge(self, name: str, value: float, **labels) -> None:
        """
        Set a gauge metric value

        Args:
            name: Metric name
            value: Value to set
            **labels: Label values
        """
        if not ENABLE_METRICS or name not in self._gauges:
            return

        if labels:
            self._gauges[name].labels(**labels).set(value)
        else:
            self._gauges[name].set(value)

    def observe_histogram(self, name: str, value: float, **labels) -> None:
        """
        Observe a value in a histogram

        Args:
            name: Metric name
            value: Value to observe
            **labels: Label values
        """
        if not ENABLE_METRICS or name not in self._histograms:
            return

        if labels:
            self._histograms[name].labels(**labels).observe(value)
        else:
            self._histograms[name].observe(value)

    def observe_summary(self, name: str, value: float, **labels) -> None:
        """
        Observe a value in a summary

        Args:
            name: Metric name
            value: Value to observe
            **labels: Label values
        """
        if not ENABLE_METRICS or name not in self._summaries:
            return

        if labels:
            self._summaries[name].labels(**labels).observe(value)
        else:
            self._summaries[name].observe(value)

    def track_business_metric(self, category: str, name: str, value: Any) -> None:
        """
        Track a business metric for aggregation and reporting

        Args:
            category: Metric category
            name: Metric name
            value: Metric value
        """
        if category not in self._business_metrics:
            self._business_metrics[category] = {}

        self._business_metrics[category][name] = value

    def get_business_metrics(self, category: str = None) -> Dict[str, Any]:
        """
        Get business metrics

        Args:
            category: Metric category (optional)

        Returns:
            Dict of business metrics
        """
        if category is not None:
            return self._business_metrics.get(category, {})
        return self._business_metrics

    def timed(self, histogram_name: str, **labels):
        """
        Decorator to time a function and record duration in a histogram

        Args:
            histogram_name: Name of the histogram to use
            **labels: Label values

        Returns:
            Decorated function
        """
        def decorator(func):
            @wraps(func)
            def wrapped(*args, **kwargs):
                start_time = time.time()
                try:
                    return func(*args, **kwargs)
                finally:
                    duration = time.time() - start_time
                    self.observe_histogram(histogram_name, duration, **labels)
            return wrapped
        return decorator

    def counted(self, counter_name: str, **labels):
        """
        Decorator to count function calls

        Args:
            counter_name: Name of the counter to use
            **labels: Label values

        Returns:
            Decorated function
        """
        def decorator(func):
            @wraps(func)
            def wrapped(*args, **kwargs):
                try:
                    result = func(*args, **kwargs)
                    current_labels = {**labels, "status": "success"}
                    self.increment_counter(counter_name, 1, **current_labels)
                    return result
                except Exception as e:
                    current_labels = {**labels, "status": "error"}
                    self.increment_counter(counter_name, 1, **current_labels)
                    raise
            return wrapped
        return decorator

    def shutdown(self):
        """Shutdown the metrics manager and stop the push thread"""
        if self._push_thread and self._push_thread.is_alive():
            self._stop_push_thread.set()
            self._push_thread.join(timeout=5)


# Create middleware for FastAPI
class MetricsMiddleware:
    """Middleware for collecting API request metrics"""

    def __init__(self, app):
        self.app = app
        self.metrics = MetricsManager()

    async def __call__(self, request: Request, call_next) -> Response:
        method = request.method
        endpoint = request.url.path

        # Track in-progress requests
        self.metrics.increment_counter(
            "http_requests_in_progress",
            1,
            method=method,
            endpoint=endpoint
        )

        # Time the request
        start_time = time.time()
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        except Exception as exc:
            status = 500
            raise
        finally:
            # Record request duration
            duration = time.time() - start_time

            # Update metrics
            self.metrics.increment_counter(
                "http_requests_total",
                1,
                method=method,
                endpoint=endpoint,
                status=str(status)
            )

            self.metrics.observe_histogram(
                "http_request_duration_seconds",
                duration,
                method=method,
                endpoint=endpoint
            )

            # Decrement in-progress counter
            self.metrics.increment_counter(
                "http_requests_in_progress",
                -1,
                method=method,
                endpoint=endpoint
            )


# Module-level singleton for easy access
metrics_manager = MetricsManager()


# Helper decorators for common use cases
def time_function(name=None, labels=None):
    """
    Decorator to time a function execution

    Args:
        name: Custom metric name, defaults to function name
        labels: Dict of label values

    Returns:
        Decorated function
    """
    def decorator(func):
        metric_name = name or f"function_duration_seconds_{func.__name__}"

        @wraps(func)
        def wrapped(*args, **kwargs):
            start_time = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.time() - start_time
                current_labels = labels or {}
                metrics_manager.observe_histogram(metric_name, duration, **current_labels)

        return wrapped

    # If used without parameters, name is actually the function
    if callable(name):
        func = name
        name = f"function_duration_seconds_{func.__name__}"
        return decorator(func)

    return decorator


def count_calls(name=None, labels=None):
    """
    Decorator to count function calls

    Args:
        name: Custom metric name, defaults to function name
        labels: Dict of label values

    Returns:
        Decorated function
    """
    def decorator(func):
        metric_name = name or f"function_calls_total_{func.__name__}"

        @wraps(func)
        def wrapped(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                current_labels = {**(labels or {}), "status": "success"}
                metrics_manager.increment_counter(metric_name, 1, **current_labels)
                return result
            except Exception as e:
                current_labels = {**(labels or {}), "status": "error", "error_type": type(e).__name__}
                metrics_manager.increment_counter(metric_name, 1, **current_labels)
                raise

        return wrapped

    # If used without parameters, name is actually the function
    if callable(name):
        func = name
        name = f"function_calls_total_{func.__name__}"
        return decorator(func)

    return decorator


def track_database(operation=None, table=None):
    """
    Decorator to track database operations

    Args:
        operation: Database operation (e.g., select, insert)
        table: Database table

    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                metrics_manager.observe_histogram(
                    "database_query_duration_seconds",
                    time.time() - start_time,
                    operation=operation or "unknown",
                    table=table or "unknown"
                )
                return result
            except Exception as e:
                metrics_manager.increment_counter(
                    "database_errors_total",
                    1,
                    operation=operation or "unknown",
                    error_type=type(e).__name__
                )
                raise

        return wrapped
    return decorator


def setup_metrics(app):
    """
    Setup metrics for a FastAPI app

    Args:
        app: FastAPI app
    """
    from fastapi.middleware.gzip import GZipMiddleware
    from fastapi import APIRouter

    # Add metrics middleware
    app.add_middleware(MetricsMiddleware)

    # Add gzip compression for metrics endpoint
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Create metrics endpoint
    router = APIRouter()

    @router.get("/metrics")
    async def metrics():
        from fastapi.responses import Response
        return Response(content=generate_latest(), media_type="text/plain")

    app.include_router(router, tags=["Monitoring"])

    # Initialize metrics
    metrics_manager._collect_system_metrics()

    # Register shutdown event
    @app.on_event("shutdown")
    def shutdown_metrics():
        metrics_manager.shutdown()

    return app
