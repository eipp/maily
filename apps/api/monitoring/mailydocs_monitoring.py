"""Monitoring configuration for MailyDocs service."""

import logging
import os
import time
from functools import wraps
from typing import Dict, Any, Callable, Optional

import prometheus_client as prom
from prometheus_client import Counter, Histogram, Gauge

# Set up logger
logger = logging.getLogger("mailydocs")

# Configure Prometheus metrics
DOCUMENT_GENERATION_REQUESTS = Counter(
    'mailydocs_document_generation_requests_total',
    'Total number of document generation requests',
    ['document_type', 'status']
)

DOCUMENT_GENERATION_TIME = Histogram(
    'mailydocs_document_generation_seconds',
    'Time spent generating documents',
    ['document_type'],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0)
)

ACTIVE_GENERATIONS = Gauge(
    'mailydocs_active_generations',
    'Number of active document generations',
    ['document_type']
)

DOCUMENT_SIZE = Histogram(
    'mailydocs_document_size_bytes',
    'Size of generated documents',
    ['document_type'],
    buckets=(
        1024, 5*1024, 10*1024, 50*1024, 100*1024,
        500*1024, 1024*1024, 5*1024*1024, 10*1024*1024, 25*1024*1024
    )
)

BLOCKCHAIN_VERIFICATION_TIME = Histogram(
    'mailydocs_blockchain_verification_seconds',
    'Time spent on blockchain verification',
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)
)

DOCUMENT_ANALYTICS_COUNT = Counter(
    'mailydocs_document_analytics_total',
    'Document analytics events',
    ['event_type']
)

TEMPLATE_USAGE = Counter(
    'mailydocs_template_usage_total',
    'Template usage count',
    ['template_id', 'document_type']
)

ERROR_COUNT = Counter(
    'mailydocs_errors_total',
    'Count of errors in MailyDocs service',
    ['error_type']
)


def initialize_metrics_endpoint(app=None):
    """Initialize metrics endpoint for Prometheus scraping.

    Args:
        app: FastAPI app instance
    """
    if app:
        from prometheus_client import make_asgi_app
        metrics_app = make_asgi_app()
        app.mount("/metrics", metrics_app)
        logger.info("Prometheus metrics endpoint initialized at /metrics")


def monitor_document_generation(document_type: str) -> Callable:
    """Decorator to monitor document generation.

    Args:
        document_type: Type of document being generated

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            ACTIVE_GENERATIONS.labels(document_type=document_type).inc()
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                DOCUMENT_GENERATION_REQUESTS.labels(
                    document_type=document_type, status="success"
                ).inc()
                return result

            except Exception as e:
                DOCUMENT_GENERATION_REQUESTS.labels(
                    document_type=document_type, status="error"
                ).inc()
                ERROR_COUNT.labels(error_type=type(e).__name__).inc()
                logger.error(f"Document generation error ({document_type}): {str(e)}")
                raise

            finally:
                generation_time = time.time() - start_time
                DOCUMENT_GENERATION_TIME.labels(document_type=document_type).observe(generation_time)
                ACTIVE_GENERATIONS.labels(document_type=document_type).dec()

        return wrapper
    return decorator


def track_document_size(document_path: str, document_type: str) -> None:
    """Track document file size.

    Args:
        document_path: Path to document file
        document_type: Type of document
    """
    try:
        if os.path.exists(document_path):
            size_bytes = os.path.getsize(document_path)
            DOCUMENT_SIZE.labels(document_type=document_type).observe(size_bytes)
            logger.debug(f"Document size tracked: {size_bytes} bytes ({document_type})")
    except Exception as e:
        logger.error(f"Error tracking document size: {str(e)}")


def track_template_usage(template_id: str, document_type: str) -> None:
    """Track template usage.

    Args:
        template_id: Template ID
        document_type: Document type
    """
    if template_id:
        TEMPLATE_USAGE.labels(template_id=template_id, document_type=document_type).inc()


def track_document_analytics_event(event_type: str) -> None:
    """Track document analytics event.

    Args:
        event_type: Type of analytics event
    """
    DOCUMENT_ANALYTICS_COUNT.labels(event_type=event_type).inc()


def monitor_blockchain_verification() -> Callable:
    """Decorator to monitor blockchain verification.

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                return result

            finally:
                verification_time = time.time() - start_time
                BLOCKCHAIN_VERIFICATION_TIME.observe(verification_time)

        return wrapper
    return decorator


def log_document_event(event_type: str, document_id: str, **kwargs) -> None:
    """Log document-related events with structured data.

    Args:
        event_type: Type of event
        document_id: Document ID
        **kwargs: Additional fields to log
    """
    log_data = {
        "event": event_type,
        "document_id": document_id,
        **kwargs
    }

    logger.info(f"MailyDocs event: {event_type}", extra={"data": log_data})
