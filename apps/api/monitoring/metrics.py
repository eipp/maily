"""Metrics module for collecting and tracking system performance metrics.

This module defines the metrics used to monitor various aspects of the Maily
platform, including request latency, model performance, and cache efficiency.
"""

from prometheus_client import Counter, Histogram, Gauge, Info
from typing import Dict, Optional, Any, Union
import time
import logging

logger = logging.getLogger(__name__)

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

# Recommendation Metrics
RECOMMENDATION_VIEWS = Counter(
    'maily_recommendation_views_total',
    'Total number of recommendation views',
    ['user_id', 'recommendation_type']
)

RECOMMENDATION_CLICKS = Counter(
    'maily_recommendation_clicks_total',
    'Total number of recommendation clicks',
    ['user_id', 'recommendation_type']
)

RECOMMENDATION_APPLIES = Counter(
    'maily_recommendation_applies_total',
    'Total number of recommendation applications',
    ['user_id', 'recommendation_type']
)

RECOMMENDATION_DISMISSES = Counter(
    'maily_recommendation_dismisses_total',
    'Total number of recommendation dismissals',
    ['user_id', 'recommendation_type']
)

RECOMMENDATION_FEEDBACK = Counter(
    'maily_recommendation_feedback_total',
    'Total number of recommendation feedback submissions',
    ['user_id', 'recommendation_type', 'rating']
)

RECOMMENDATION_CONFIDENCE = Histogram(
    'maily_recommendation_confidence',
    'Confidence distribution of recommendations',
    ['recommendation_type'],
    buckets=[0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99]
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
            
    def record_recommendation_interaction(
        self,
        action: str,
        user_id: str,
        recommendation_type: str,
        rating: Optional[int] = None
    ) -> None:
        """Record recommendation interaction metrics.
        
        Args:
            action: Interaction type (view, click, apply, dismiss)
            user_id: User ID
            recommendation_type: Type of recommendation
            rating: Optional rating (1-5)
        """
        try:
            if action == "view":
                RECOMMENDATION_VIEWS.labels(
                    user_id=user_id,
                    recommendation_type=recommendation_type
                ).inc()
            elif action == "click":
                RECOMMENDATION_CLICKS.labels(
                    user_id=user_id,
                    recommendation_type=recommendation_type
                ).inc()
            elif action == "apply":
                RECOMMENDATION_APPLIES.labels(
                    user_id=user_id,
                    recommendation_type=recommendation_type
                ).inc()
            elif action == "dismiss":
                RECOMMENDATION_DISMISSES.labels(
                    user_id=user_id,
                    recommendation_type=recommendation_type
                ).inc()
                
            # Record feedback if rating provided
            if rating is not None:
                RECOMMENDATION_FEEDBACK.labels(
                    user_id=user_id,
                    recommendation_type=recommendation_type,
                    rating=str(rating)
                ).inc()
        except Exception as e:
            logger.error(f"Error recording recommendation interaction: {str(e)}")
            
    def record_recommendation_confidence(
        self,
        recommendation_type: str,
        confidence: float
    ) -> None:
        """Record confidence score for a recommendation.
        
        Args:
            recommendation_type: Type of recommendation
            confidence: Confidence score (0-1)
        """
        try:
            RECOMMENDATION_CONFIDENCE.labels(
                recommendation_type=recommendation_type
            ).observe(confidence)
        except Exception as e:
            logger.error(f"Error recording recommendation confidence: {str(e)}")
            

# Helper function for recording metrics
def record_metric(
    metric_name: str, 
    value: Union[int, float], 
    labels: Dict[str, Any] = None
) -> None:
    """Record a metric value with optional labels.
    
    Args:
        metric_name: Name of the metric to record
        value: Value to record
        labels: Optional dictionary of label values
    """
    try:
        labels = labels or {}
        
        # Common metric types
        if metric_name.startswith("recommendation."):
            # Handle recommendation metrics
            if metric_name == "recommendation.view":
                RECOMMENDATION_VIEWS.labels(
                    user_id=str(labels.get("user_id", "unknown")),
                    recommendation_type=labels.get("type", "unknown")
                ).inc(value)
            elif metric_name == "recommendation.click":
                RECOMMENDATION_CLICKS.labels(
                    user_id=str(labels.get("user_id", "unknown")),
                    recommendation_type=labels.get("type", "unknown")
                ).inc(value)
            elif metric_name == "recommendation.apply":
                RECOMMENDATION_APPLIES.labels(
                    user_id=str(labels.get("user_id", "unknown")),
                    recommendation_type=labels.get("type", "unknown")
                ).inc(value)
            elif metric_name == "recommendation.dismiss":
                RECOMMENDATION_DISMISSES.labels(
                    user_id=str(labels.get("user_id", "unknown")),
                    recommendation_type=labels.get("type", "unknown")
                ).inc(value)
            elif metric_name == "recommendation.confidence":
                RECOMMENDATION_CONFIDENCE.labels(
                    recommendation_type=labels.get("type", "unknown")
                ).observe(value)
        elif metric_name.startswith("cache."):
            # Handle cache metrics
            if metric_name == "cache.hit":
                CACHE_HITS.inc(value)
            elif metric_name == "cache.miss":
                CACHE_MISSES.inc(value)
        
        # Log unhandled metrics for now, can add more handlers as needed
    except Exception as e:
        logger.error(f"Error recording metric {metric_name}: {str(e)}")
