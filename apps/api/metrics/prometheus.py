import time
import functools
import logging
from typing import Callable, Any, Dict, List, Optional
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import FastAPI, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response as StarletteResponse

logger = logging.getLogger("mailydocs.metrics")

# Define metrics
HTTP_REQUEST_COUNTER = Counter(
    "http_requests_total",
    "Total count of HTTP requests",
    ["method", "endpoint", "status_code"]
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

ACTIVE_REQUESTS = Gauge(
    "http_active_requests",
    "Number of active HTTP requests",
    ["method", "endpoint"]
)

# MailyDocs specific metrics
DOCUMENT_GENERATION_REQUESTS = Counter(
    "mailydocs_document_generation_requests_total",
    "Total count of document generation requests",
    ["document_type", "status"]
)

DOCUMENT_GENERATION_TIME = Histogram(
    "mailydocs_document_generation_duration_seconds",
    "Document generation duration in seconds",
    ["document_type"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
)

ACTIVE_GENERATIONS = Gauge(
    "mailydocs_active_document_generations",
    "Number of active document generations",
    ["document_type"]
)

DOCUMENT_SIZE = Histogram(
    "mailydocs_document_size_bytes",
    "Document size in bytes",
    ["document_type"],
    buckets=[1024, 10240, 102400, 1048576, 10485760, 104857600]
)

BLOCKCHAIN_VERIFICATION_TIME = Histogram(
    "mailydocs_blockchain_verification_duration_seconds",
    "Blockchain verification duration in seconds",
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0]
)

DOCUMENT_ANALYTICS_COUNT = Counter(
    "mailydocs_document_analytics_events_total",
    "Total count of document analytics events",
    ["event_type"]
)

TEMPLATE_USAGE = Counter(
    "mailydocs_template_usage_total",
    "Total count of template usage",
    ["template_id", "document_type"]
)

ERROR_COUNT = Counter(
    "mailydocs_errors_total",
    "Total count of errors in MailyDocs service",
    ["error_type"]
)

class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect metrics on HTTP requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        method = request.method
        path = request.url.path

        # Increment active requests gauge
        ACTIVE_REQUESTS.labels(method=method, endpoint=path).inc()

        # Start timer
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Record metrics
            status_code = response.status_code
            duration = time.time() - start_time

            HTTP_REQUEST_COUNTER.labels(
                method=method, endpoint=path, status_code=status_code
            ).inc()

            HTTP_REQUEST_DURATION.labels(
                method=method, endpoint=path
            ).observe(duration)

            return response
        except Exception as e:
            # Record error metrics
            ERROR_COUNT.labels(error_type=type(e).__name__).inc()
            # Re-raise exception
            raise
        finally:
            # Decrement active requests gauge
            ACTIVE_REQUESTS.labels(method=method, endpoint=path).dec()

def initialize_metrics_endpoint(app: FastAPI) -> None:
    """Initialize metrics endpoint for Prometheus scraping."""

    @app.get("/metrics")
    async def metrics() -> Response:
        return Response(
            content=generate_latest(),
            media_type="text/plain"
        )

    # Add Prometheus middleware
    app.add_middleware(PrometheusMiddleware)

    logger.info("Prometheus metrics endpoint initialized")

def monitor_document_generation(document_type: str):
    """Decorator to monitor document generation."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Increment counter and gauge
            DOCUMENT_GENERATION_REQUESTS.labels(document_type=document_type, status="started").inc()
            ACTIVE_GENERATIONS.labels(document_type=document_type).inc()

            # Start timer
            start_time = time.time()

            try:
                # Execute function
                result = await func(*args, **kwargs)

                # Record success metrics
                DOCUMENT_GENERATION_REQUESTS.labels(document_type=document_type, status="success").inc()

                return result
            except Exception as e:
                # Record error metrics
                DOCUMENT_GENERATION_REQUESTS.labels(document_type=document_type, status="error").inc()
                ERROR_COUNT.labels(error_type=type(e).__name__).inc()

                # Re-raise exception
                raise
            finally:
                # Record duration and decrement gauge
                duration = time.time() - start_time
                DOCUMENT_GENERATION_TIME.labels(document_type=document_type).observe(duration)
                ACTIVE_GENERATIONS.labels(document_type=document_type).dec()

        return wrapper
    return decorator

def track_document_size(document_path: str, document_type: str) -> None:
    """Track the size of generated documents."""
    try:
        import os
        if os.path.exists(document_path):
            size = os.path.getsize(document_path)
            DOCUMENT_SIZE.labels(document_type=document_type).observe(size)
    except Exception as e:
        logger.error(f"Failed to track document size: {str(e)}")
        ERROR_COUNT.labels(error_type=type(e).__name__).inc()

def track_template_usage(template_id: str, document_type: str) -> None:
    """Track template usage."""
    TEMPLATE_USAGE.labels(template_id=template_id, document_type=document_type).inc()

def track_document_analytics_event(event_type: str) -> None:
    """Track document analytics events."""
    DOCUMENT_ANALYTICS_COUNT.labels(event_type=event_type).inc()

def monitor_blockchain_verification():
    """Decorator to monitor blockchain verification."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Start timer
            start_time = time.time()

            try:
                # Execute function
                result = await func(*args, **kwargs)
                return result
            finally:
                # Record duration
                duration = time.time() - start_time
                BLOCKCHAIN_VERIFICATION_TIME.observe(duration)

        return wrapper
    return decorator
