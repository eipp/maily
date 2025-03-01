"""Metrics module for collecting and tracking system performance metrics.

This module defines the metrics used to monitor various aspects of the Maily
platform, including request latency, model performance, and cache efficiency.
"""

from prometheus_client import Counter, Histogram, Gauge, Info
from typing import Dict, Optional
import time

# Request metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests processed",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request processing duration in seconds",
    ["method", "endpoint"],
)

# Model metrics
MODEL_LATENCY = Histogram(
    "maily_model_latency_seconds",
    "Model inference latency in seconds",
    ["model_name", "operation"],
)

MODEL_ERRORS = Counter(
    "maily_model_errors_total",
    "Total number of model inference errors",
    ["model_name", "error_type"],
)

# Cache metrics
CACHE_HITS = Counter(
    "maily_cache_hits_total",
    "Total number of successful cache retrievals",
)

CACHE_MISSES = Counter(
    "maily_cache_misses_total",
    "Total number of failed cache retrievals",
)

# Campaign Metrics
CAMPAIGN_SENDS = Counter(
    'maily_campaign_sends_total',
    'Total number of emails sent per campaign',
    ['campaign_id', 'template_id']
)

CAMPAIGN_OPENS = Counter(
    'maily_campaign_opens_total',
    'Total number of email opens per campaign',
    ['campaign_id']
)

CAMPAIGN_CLICKS = Counter(
    'maily_campaign_clicks_total',
    'Total number of email clicks per campaign',
    ['campaign_id', 'link_id']
)

CAMPAIGN_BOUNCES = Counter(
    'maily_campaign_bounces_total',
    'Total number of email bounces per campaign',
    ['campaign_id', 'bounce_type']
)

CAMPAIGN_UNSUBSCRIBES = Counter(
    'maily_campaign_unsubscribes_total',
    'Total number of unsubscribes per campaign',
    ['campaign_id']
)

# AI Model Metrics
AI_REQUEST_DURATION = Histogram(
    'maily_ai_request_duration_seconds',
    'Time spent processing AI requests',
    ['model_name', 'operation'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

AI_TOKEN_USAGE = Counter(
    'maily_ai_token_usage_total',
    'Total number of tokens used by AI models',
    ['model_name', 'operation']
)

AI_ERROR_COUNT = Counter(
    'maily_ai_errors_total',
    'Total number of AI model errors',
    ['model_name', 'error_type']
)

# System Metrics
ACTIVE_USERS = Gauge(
    'maily_active_users',
    'Number of currently active users'
)

API_REQUEST_DURATION = Histogram(
    'maily_api_request_duration_seconds',
    'Time spent processing API requests',
    ['endpoint', 'method', 'status_code'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

QUEUE_SIZE = Gauge(
    'maily_queue_size',
    'Current size of the email sending queue',
    ['priority']
)

SYSTEM_INFO = Info(
    'maily_system_info',
    'System information'
)

# Database Metrics
DB_CONNECTION_POOL = Gauge(
    'maily_db_connection_pool_size',
    'Current size of the database connection pool',
    ['pool_name']
)

DB_QUERY_DURATION = Histogram(
    'maily_db_query_duration_seconds',
    'Time spent executing database queries',
    ['query_type'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5]
)

# Cache Metrics
CACHE_HIT_RATIO = Gauge(
    'maily_cache_hit_ratio',
    'Cache hit ratio',
    ['cache_name']
)

CACHE_SIZE = Gauge(
    'maily_cache_size_bytes',
    'Current size of the cache in bytes',
    ['cache_name']
)

# Compliance Metrics
CONSENT_CHANGES = Counter(
    'maily_consent_changes_total',
    'Total number of consent preference changes',
    ['change_type']
)

GDPR_REQUESTS = Counter(
    'maily_gdpr_requests_total',
    'Total number of GDPR-related requests',
    ['request_type']
)

class MetricsManager:
    """Manager class for handling metrics collection."""

    def __init__(self):
        self._start_times: Dict[str, float] = {}

    def start_request_timer(self, request_id: str) -> None:
        """Start timing a request."""
        self._start_times[request_id] = time.time()

    def stop_request_timer(
        self,
        request_id: str,
        endpoint: str,
        method: str,
        status_code: int
    ) -> Optional[float]:
        """Stop timing a request and record the duration."""
        start_time = self._start_times.pop(request_id, None)
        if start_time is None:
            return None

        duration = time.time() - start_time
        API_REQUEST_DURATION.labels(
            endpoint=endpoint,
            method=method,
            status_code=status_code
        ).observe(duration)

        return duration

    def record_ai_operation(
        self,
        model_name: str,
        operation: str,
        duration: float,
        tokens: int
    ) -> None:
        """Record metrics for an AI operation."""
        AI_REQUEST_DURATION.labels(
            model_name=model_name,
            operation=operation
        ).observe(duration)

        AI_TOKEN_USAGE.labels(
            model_name=model_name,
            operation=operation
        ).inc(tokens)

    def record_campaign_event(
        self,
        event_type: str,
        campaign_id: str,
        **kwargs
    ) -> None:
        """Record a campaign-related event."""
        if event_type == "send":
            CAMPAIGN_SENDS.labels(
                campaign_id=campaign_id,
                template_id=kwargs.get("template_id", "unknown")
            ).inc()
        elif event_type == "open":
            CAMPAIGN_OPENS.labels(campaign_id=campaign_id).inc()
        elif event_type == "click":
            CAMPAIGN_CLICKS.labels(
                campaign_id=campaign_id,
                link_id=kwargs.get("link_id", "unknown")
            ).inc()
        elif event_type == "bounce":
            CAMPAIGN_BOUNCES.labels(
                campaign_id=campaign_id,
                bounce_type=kwargs.get("bounce_type", "unknown")
            ).inc()
        elif event_type == "unsubscribe":
            CAMPAIGN_UNSUBSCRIBES.labels(campaign_id=campaign_id).inc()

    def update_system_info(self, info: Dict[str, str]) -> None:
        """Update system information metrics."""
        SYSTEM_INFO.info(info)

    def record_db_query(self, query_type: str, duration: float) -> None:
        """Record database query metrics."""
        DB_QUERY_DURATION.labels(query_type=query_type).observe(duration)

    def update_cache_metrics(
        self,
        cache_name: str,
        hit_ratio: float,
        size_bytes: int
    ) -> None:
        """Update cache-related metrics."""
        CACHE_HIT_RATIO.labels(cache_name=cache_name).set(hit_ratio)
        CACHE_SIZE.labels(cache_name=cache_name).set(size_bytes)

    def record_compliance_event(
        self,
        event_type: str,
        request_type: Optional[str] = None
    ) -> None:
        """Record compliance-related events."""
        if event_type == "consent_change":
            CONSENT_CHANGES.labels(
                change_type=request_type or "unknown"
            ).inc()
        elif event_type == "gdpr_request":
            GDPR_REQUESTS.labels(
                request_type=request_type or "unknown"
            ).inc()
