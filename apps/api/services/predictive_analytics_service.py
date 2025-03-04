"""
Predictive Analytics Service for integrating with the Analytics Service.
Provides access to predictive features, recommendations, and confidence scoring.
"""
from typing import List, Dict, Any, Optional, Union
import httpx
import structlog
from datetime import datetime
import json
import time

from ..config.settings import get_settings
from ..cache.redis_cache import RedisCache
from ..monitoring.metrics import record_metric

logger = structlog.get_logger("justmaily.services.predictive_analytics")

class PredictiveAnalyticsService:
    """Service for accessing predictive analytics capabilities from the analytics service."""

    def __init__(self, redis_cache: RedisCache):
        """Initialize the predictive analytics service.

        Args:
            redis_cache: Redis cache client for optimizing API calls
        """
        self.cache = redis_cache
        self.settings = get_settings()
        self.analytics_base_url = self.settings.ANALYTICS_SERVICE_URL
        self.cache_ttl = 300  # 5 minutes cache by default

    async def get_campaign_recommendations(
        self, 
        user_id: int, 
        campaign_ids: List[int],
        include_confidence_scores: bool = True,
        tags: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Get campaign recommendations from the analytics service.

        Args:
            user_id: User ID
            campaign_ids: List of campaign IDs to get recommendations for
            include_confidence_scores: Whether to include confidence scores
            tags: Optional list of tags to filter recommendations by

        Returns:
            List of recommendations with confidence scores
        """
        try:
            # Start performance tracking
            start_time = time.time()
            
            # Generate cache key
            cache_key = f"predictive:recommendations:user:{user_id}:campaigns:{','.join(map(str, campaign_ids))}"
            if tags:
                cache_key += f":tags:{','.join(tags)}"
                
            # Check cache first
            cached_recommendations = await self.cache.get(cache_key)
            if cached_recommendations:
                logger.debug("Campaign recommendations retrieved from cache", user_id=user_id)
                # Track cache hit for metrics
                record_metric("recommendation.cache.hit", 1, {"user_id": user_id})
                return json.loads(cached_recommendations)
            
            # Track cache miss for metrics
            record_metric("recommendation.cache.miss", 1, {"user_id": user_id})
            
            # Prepare request parameters
            params = {
                "campaignIds": campaign_ids,
                "userId": user_id,
                "includeConfidence": str(include_confidence_scores).lower()
            }
            
            if tags:
                params["tags"] = tags
                
            # Make request to analytics service
            url = f"{self.analytics_base_url}/api/predictive/recommendations/campaigns"
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                recommendations = response.json()
                
                # Process recommendations to include enhanced confidence information
                if include_confidence_scores and recommendations:
                    for rec in recommendations:
                        # Ensure confidence score exists
                        if "confidence" not in rec:
                            rec["confidence"] = 0.75  # Default confidence
                            
                        # Add confidence level category for UI display
                        confidence = float(rec["confidence"])
                        if confidence >= 0.9:
                            rec["confidenceLevel"] = "very_high"
                        elif confidence >= 0.75:
                            rec["confidenceLevel"] = "high"
                        elif confidence >= 0.5:
                            rec["confidenceLevel"] = "medium"
                        elif confidence >= 0.25:
                            rec["confidenceLevel"] = "low"
                        else:
                            rec["confidenceLevel"] = "very_low"
                        
                        # Add explanation of confidence score if not present
                        if "confidenceExplanation" not in rec:
                            rec["confidenceExplanation"] = self._generate_confidence_explanation(
                                rec["type"], confidence, rec.get("metadata", {})
                            )
                        
                        # Track confidence score for metrics
                        record_metric(
                            "recommendation.confidence", 
                            confidence, 
                            {"type": rec["type"]}
                        )
                
                # Cache the results
                await self.cache.set(cache_key, json.dumps(recommendations), self.cache_ttl)
                
                # Record performance metrics
                duration = time.time() - start_time
                record_metric(
                    "recommendation.fetch.duration", 
                    duration, 
                    {
                        "user_id": user_id,
                        "recommendation_count": len(recommendations)
                    }
                )
                
                # Track recommendation count for analytics
                record_metric(
                    "recommendation.count", 
                    len(recommendations), 
                    {
                        "user_id": user_id,
                        "campaign_count": len(campaign_ids)
                    }
                )
                
                return recommendations
        except Exception as e:
            logger.error(
                "Failed to get campaign recommendations",
                user_id=user_id,
                campaign_ids=campaign_ids,
                error=str(e)
            )
            # Record error metric
            record_metric(
                "recommendation.error", 
                1, 
                {
                    "user_id": user_id, 
                    "error_type": type(e).__name__
                }
            )
            return []
            
    def _generate_confidence_explanation(
        self, 
        recommendation_type: str, 
        confidence: float,
        metadata: Dict[str, Any]
    ) -> str:
        """Generate a human-readable explanation of the confidence score.
        
        Args:
            recommendation_type: Type of recommendation
            confidence: Confidence score (0-1)
            metadata: Additional metadata about the recommendation
            
        Returns:
            Human-readable explanation of confidence score
        """
        if recommendation_type == "threshold":
            return f"Based on {metadata.get('sample_size', 'historical')} data points with {int(confidence * 100)}% statistical confidence."
        elif recommendation_type == "trend":
            return f"Trend analysis with {int(confidence * 100)}% confidence based on correlation coefficient of {metadata.get('correlation', 0.7):.2f}."
        elif recommendation_type == "anomaly":
            return f"Anomaly detection with {int(confidence * 100)}% confidence (z-score: {metadata.get('z_score', 2.5):.2f})."
        elif recommendation_type == "comparison":
            return f"Comparative analysis with {int(confidence * 100)}% confidence across {metadata.get('comparison_count', 5)} similar campaigns."
        else:
            return f"Confidence score: {int(confidence * 100)}% based on predictive modeling."
    
    async def track_recommendation_interaction(
        self, 
        recommendation_id: str, 
        user_id: int, 
        action: str, 
        campaign_id: Optional[int] = None,
        feedback: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Track user interaction with a recommendation.

        Args:
            recommendation_id: ID of the recommendation
            user_id: ID of the user
            action: Action taken (view, click, dismiss, apply)
            campaign_id: Optional campaign ID associated with the recommendation
            feedback: Optional user feedback about the recommendation

        Returns:
            True if tracking was successful, False otherwise
        """
        try:
            # Start performance tracking
            start_time = time.time()
            
            # Make request to analytics service
            url = f"{self.analytics_base_url}/api/predictive/recommendations/track"
            
            data = {
                "recommendationId": recommendation_id,
                "userId": user_id,
                "action": action,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "api_service"
            }
            
            if campaign_id:
                data["campaignId"] = campaign_id
                
            if feedback:
                data["feedback"] = feedback
                
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(url, json=data)
                response.raise_for_status()
                
                # Cache interaction to prevent duplicates and for offline processing
                cache_key = f"recommendation:interaction:{recommendation_id}:{user_id}:{action}"
                await self.cache.set(cache_key, json.dumps(data), 86400)  # Cache for 1 day
                
                # Track metrics for the interaction
                record_metric(
                    f"recommendation.{action}",
                    1,
                    {
                        "user_id": user_id,
                        "type": data.get("type", "unknown")
                    }
                )
                
                # If feedback with rating provided, track that too
                if feedback and "rating" in feedback:
                    record_metric(
                        "recommendation.feedback",
                        1,
                        {
                            "user_id": user_id,
                            "type": data.get("type", "unknown"),
                            "rating": feedback["rating"]
                        }
                    )
                
                # Log tracking duration for performance monitoring
                duration = time.time() - start_time
                logger.info(
                    "Recommendation interaction tracked",
                    recommendation_id=recommendation_id,
                    user_id=user_id,
                    action=action,
                    duration_ms=int(duration * 1000)
                )
                
                return True
        except Exception as e:
            logger.error(
                "Failed to track recommendation interaction",
                recommendation_id=recommendation_id,
                user_id=user_id,
                action=action,
                error=str(e)
            )
            return False
            
    async def get_performance_predictions(
        self,
        user_id: int,
        metric: str,
        horizon: str = "7d",
        campaign_id: Optional[int] = None,
        segment: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get performance predictions for specific metrics.
        
        Args:
            user_id: User ID
            metric: Metric to predict (e.g., "open_rate", "click_rate")
            horizon: Time horizon for prediction (e.g., "7d", "30d")
            campaign_id: Optional campaign ID to focus prediction
            segment: Optional user segment to focus prediction
            
        Returns:
            Dictionary with prediction data including confidence scores
        """
        try:
            # Generate cache key
            cache_key = f"predictive:predictions:user:{user_id}:metric:{metric}:horizon:{horizon}"
            if campaign_id:
                cache_key += f":campaign:{campaign_id}"
            if segment:
                cache_key += f":segment:{segment}"
                
            # Check cache first
            cached_prediction = await self.cache.get(cache_key)
            if cached_prediction:
                logger.debug("Performance prediction retrieved from cache", user_id=user_id, metric=metric)
                return json.loads(cached_prediction)
            
            # Make request to analytics service
            url = f"{self.analytics_base_url}/api/predictive/predictions"
            
            params = {
                "userId": user_id,
                "metric": metric,
                "horizon": horizon
            }
            
            if campaign_id:
                params["campaignId"] = campaign_id
                
            if segment:
                params["segment"] = segment
                
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                prediction = response.json()
                
                # Cache the results
                await self.cache.set(cache_key, json.dumps(prediction), self.cache_ttl)
                
                return prediction
        except Exception as e:
            logger.error(
                "Failed to get performance prediction",
                user_id=user_id,
                metric=metric,
                horizon=horizon,
                error=str(e)
            )
            return {
                "success": False,
                "error": str(e),
                "predictions": []
            }

# Dependency injection function            
async def get_predictive_analytics_service(
    redis_cache: RedisCache
) -> PredictiveAnalyticsService:
    """Dependency for getting predictive analytics service.

    Args:
        redis_cache: Redis cache client

    Returns:
        Initialized PredictiveAnalyticsService
    """
    return PredictiveAnalyticsService(redis_cache)