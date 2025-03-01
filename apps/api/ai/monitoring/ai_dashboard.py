"""
AI Performance Dashboard

This module provides FastAPI endpoints for visualizing AI performance metrics.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from .ai_metrics_service import AIMetricsService
from ...cache.redis_service import RedisService
from ...auth.auth_service import get_current_user, User

logger = logging.getLogger(__name__)

# Models for API responses
class PerformanceMetric(BaseModel):
    timestamp: str
    value: float

class LatencyPercentiles(BaseModel):
    p50: float
    p90: float
    p95: float
    p99: Optional[float] = None
    avg: float

class ModelPerformance(BaseModel):
    model_name: str
    requests: int
    success_rate: float
    error_rate: float
    total_tokens: int
    total_cost: float
    avg_tokens_per_request: float
    avg_cost_per_request: float
    latency: LatencyPercentiles

class AlertDetails(BaseModel):
    id: str
    type: str
    model_name: str
    operation_type: str
    timestamp: str
    details: Dict[str, Any]

class CacheMetrics(BaseModel):
    hits: int
    misses: int
    hit_ratio: float
    estimated_savings: float
    timestamp: str

# Create router
router = APIRouter(
    prefix="/ai/monitoring",
    tags=["ai-monitoring"],
    responses={404: {"description": "Not found"}},
)

# Dependency for getting services
def get_ai_metrics_service():
    # This would typically be injected via dependency injection
    from ...monitoring.performance_metrics import MetricsService
    from ...cache.redis_service import get_redis_service

    metrics_service = MetricsService()
    redis_service = get_redis_service()

    return AIMetricsService(metrics_service, redis_service)

@router.get("/performance/summary", response_model=Dict[str, Any])
async def get_performance_summary(
    metrics_service: AIMetricsService = Depends(get_ai_metrics_service),
    current_user: User = Depends(get_current_user),
):
    """
    Get a summary of AI model performance metrics.
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    return metrics_service.get_model_performance_summary()

@router.get("/performance/models", response_model=List[str])
async def get_active_models(
    redis_service: RedisService = Depends(lambda: get_ai_metrics_service().redis_service),
    current_user: User = Depends(get_current_user),
):
    """
    Get a list of active AI models.
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    if not redis_service:
        return []

    # Get all keys matching the pattern for model metrics
    keys = redis_service.keys("maily:ai:*:*:status")

    # Extract model names from keys
    models = set()
    for key in keys:
        parts = key.split(":")
        if len(parts) >= 4:
            operation_type = parts[2]
            model_name = parts[3]
            models.add(f"{operation_type}:{model_name}")

    return sorted(list(models))

@router.get("/performance/latency/{model_key}", response_model=Dict[str, int])
async def get_model_latency_distribution(
    model_key: str,
    redis_service: RedisService = Depends(lambda: get_ai_metrics_service().redis_service),
    current_user: User = Depends(get_current_user),
):
    """
    Get latency distribution for a specific model.

    Args:
        model_key: The model key in format "operation_type:model_name"
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    if not redis_service:
        raise HTTPException(status_code=503, detail="Redis service not available")

    # Split model key into operation type and model name
    parts = model_key.split(":")
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="Invalid model key format")

    operation_type, model_name = parts

    # Get latency distribution
    key = f"maily:ai:{operation_type}:{model_name}:latency"
    distribution = redis_service.hgetall(key)

    # Convert string values to integers
    return {bucket: int(count) for bucket, count in distribution.items()}

@router.get("/performance/timeseries/{metric_type}", response_model=List[Dict[str, Any]])
async def get_performance_timeseries(
    metric_type: str,
    operation_type: str = Query("generation"),
    model_name: Optional[str] = Query(None),
    window: int = Query(60, description="Time window in minutes"),
    redis_service: RedisService = Depends(lambda: get_ai_metrics_service().redis_service),
    current_user: User = Depends(get_current_user),
):
    """
    Get time series data for a specific metric.

    Args:
        metric_type: The type of metric (requests, latency, tokens, cost)
        operation_type: The operation type (generation or embedding)
        model_name: Optional model name filter
        window: Time window in minutes
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    if not redis_service:
        raise HTTPException(status_code=503, detail="Redis service not available")

    # Validate metric type
    valid_metrics = ["requests", "latency", "tokens", "cost", "errors", "success_rate"]
    if metric_type not in valid_metrics:
        raise HTTPException(status_code=400, detail=f"Invalid metric type. Must be one of: {', '.join(valid_metrics)}")

    # Calculate time range
    current_minute = int(datetime.now().timestamp() / 60)
    start_minute = current_minute - window

    # Collect time series data
    time_series = []
    for minute in range(start_minute, current_minute + 1):
        # Get data for this minute
        key = f"maily:ai:{operation_type}:minute:{minute}"
        data = redis_service.hgetall(key)

        if not data:
            continue

        # Calculate derived metrics if needed
        if metric_type == "success_rate" and "requests" in data and int(data["requests"]) > 0:
            success_rate = int(data.get("success", 0)) / int(data["requests"])
            value = success_rate
        elif metric_type == "latency" and "latency_sum" in data and "requests" in data and int(data["requests"]) > 0:
            avg_latency = float(data["latency_sum"]) / int(data["requests"])
            value = avg_latency
        else:
            value = float(data.get(metric_type, 0))

        time_series.append({
            "timestamp": datetime.fromtimestamp(minute * 60).isoformat(),
            "value": value
        })

    return time_series

@router.get("/alerts/recent", response_model=List[AlertDetails])
async def get_recent_alerts(
    limit: int = Query(10, ge=1, le=100),
    metrics_service: AIMetricsService = Depends(get_ai_metrics_service),
    current_user: User = Depends(get_current_user),
):
    """
    Get recent alerts.

    Args:
        limit: Maximum number of alerts to return
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    return metrics_service.get_recent_alerts(limit=limit)

@router.get("/cache/metrics", response_model=CacheMetrics)
async def get_cache_metrics(
    redis_service: RedisService = Depends(lambda: get_ai_metrics_service().redis_service),
    current_user: User = Depends(get_current_user),
):
    """
    Get cache performance metrics.
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    if not redis_service:
        raise HTTPException(status_code=503, detail="Redis service not available")

    # Get cache metrics from Redis
    cache_metrics_json = redis_service.get("maily:ai:cache:metrics")
    if not cache_metrics_json:
        raise HTTPException(status_code=404, detail="Cache metrics not found")

    try:
        cache_metrics = json.loads(cache_metrics_json)
        return CacheMetrics(**cache_metrics)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to decode cache metrics")

@router.post("/alerts/thresholds/{metric}")
async def update_alert_threshold(
    metric: str,
    value: float,
    metrics_service: AIMetricsService = Depends(get_ai_metrics_service),
    current_user: User = Depends(get_current_user),
):
    """
    Update an alert threshold.

    Args:
        metric: The metric to update the threshold for
        value: The new threshold value
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    if metric not in metrics_service.alert_thresholds:
        raise HTTPException(status_code=400, detail=f"Invalid metric. Must be one of: {', '.join(metrics_service.alert_thresholds.keys())}")

    metrics_service.set_alert_threshold(metric, value)

    return {"status": "success", "message": f"Updated threshold for {metric} to {value}"}

# Register the router in the main app
def register_ai_dashboard(app):
    app.include_router(router)
