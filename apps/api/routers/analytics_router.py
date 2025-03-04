"""
Analytics router for accessing predictive analytics capabilities.
Provides endpoints for recommendations, predictions, and interaction tracking.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Path, Query, HTTPException, status
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from ..database.dependencies import get_db
from ..services.predictive_analytics_service import PredictiveAnalyticsService, get_predictive_analytics_service
from ..schemas.api_response import ApiResponse
from ..cache.redis_cache import get_redis_cache
from ..logging.logging_config import bind_contextvars
from ..monitoring.metrics import record_metric

# Schema definitions
class RecommendationFeedback(BaseModel):
    """Schema for providing feedback on a recommendation."""
    rating: Optional[int] = Field(None, title="Rating (1-5)", ge=1, le=5)
    comment: Optional[str] = Field(None, title="Feedback comment")
    applied: Optional[bool] = Field(None, title="Whether recommendation was applied")
    useful: Optional[bool] = Field(None, title="Whether recommendation was useful")

    @validator('rating')
    def validate_rating(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Rating must be between 1 and 5')
        return v

class RecommendationInteraction(BaseModel):
    """Schema for recording user interaction with a recommendation."""
    recommendation_id: str = Field(..., title="Recommendation ID")
    action: str = Field(..., title="Action type (view, click, dismiss, apply)")
    campaign_id: Optional[int] = Field(None, title="Associated campaign ID")
    feedback: Optional[RecommendationFeedback] = Field(None, title="User feedback")
    
    @validator('action')
    def validate_action(cls, v):
        valid_actions = ['view', 'click', 'dismiss', 'apply']
        if v not in valid_actions:
            raise ValueError(f"Action must be one of: {', '.join(valid_actions)}")
        return v

class PredictionRequest(BaseModel):
    """Schema for requesting a performance prediction."""
    metric: str = Field(..., title="Metric to predict")
    horizon: str = Field("7d", title="Time horizon for prediction")
    campaign_id: Optional[int] = Field(None, title="Campaign ID to focus prediction")
    segment: Optional[str] = Field(None, title="User segment to focus prediction")

class RecommendationResponse(BaseModel):
    """Schema for recommendation response."""
    id: str
    type: str
    message: str
    suggestion: str
    priority: int
    confidence: float
    confidenceLevel: str
    confidenceExplanation: str
    tags: List[str]
    metadata: Optional[Dict[str, Any]] = None

# Create router
router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Resource not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"}
    }
)

@router.get("/recommendations/campaigns/{campaign_id}", response_model=ApiResponse[List[RecommendationResponse]])
async def get_campaign_recommendations(
    campaign_id: int = Path(..., title="Campaign ID", gt=0),
    include_confidence: bool = Query(True, title="Include confidence details"),
    tags: Optional[str] = Query(None, title="Filter by tags (comma-separated)"),
    service: PredictiveAnalyticsService = Depends(get_predictive_analytics_service),
    db: Session = Depends(get_db),
    user_id: int = 1  # This would normally come from auth middleware
):
    """Get recommendations for a specific campaign."""
    # Add context for logging
    bind_contextvars(
        user_id=str(user_id), 
        campaign_id=str(campaign_id), 
        resource_type="campaign_recommendations"
    )
    
    # Parse tags if provided
    tag_list = tags.split(',') if tags else None
    
    # Get recommendations
    recommendations = await service.get_campaign_recommendations(
        user_id=user_id,
        campaign_ids=[campaign_id],
        tags=tag_list,
        include_confidence_scores=include_confidence
    )
    
    # Track metrics
    record_metric(
        "api.recommendations.fetch", 
        1, 
        {
            "user_id": user_id,
            "campaign_id": campaign_id,
            "count": len(recommendations)
        }
    )
    
    return ApiResponse.success(recommendations)

@router.post("/recommendations/track", response_model=ApiResponse[bool])
async def track_recommendation_interaction(
    data: RecommendationInteraction,
    service: PredictiveAnalyticsService = Depends(get_predictive_analytics_service),
    db: Session = Depends(get_db),
    user_id: int = 1  # This would normally come from auth middleware
):
    """Track user interaction with a recommendation."""
    # Add context for logging
    bind_contextvars(
        user_id=str(user_id), 
        recommendation_id=data.recommendation_id, 
        resource_type="recommendation_interaction"
    )
    
    # Track the interaction
    result = await service.track_recommendation_interaction(
        recommendation_id=data.recommendation_id,
        user_id=user_id,
        action=data.action,
        campaign_id=data.campaign_id,
        feedback=data.feedback.dict() if data.feedback else None
    )
    
    # Track metrics
    record_metric(
        "api.recommendations.interaction", 
        1, 
        {
            "user_id": user_id,
            "action": data.action,
            "has_feedback": data.feedback is not None
        }
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track recommendation interaction"
        )
    
    return ApiResponse.success(result)

@router.post("/predictions", response_model=ApiResponse[Dict[str, Any]])
async def get_performance_prediction(
    data: PredictionRequest,
    service: PredictiveAnalyticsService = Depends(get_predictive_analytics_service),
    db: Session = Depends(get_db),
    user_id: int = 1  # This would normally come from auth middleware
):
    """Get performance prediction for a specific metric."""
    # Add context for logging
    bind_contextvars(
        user_id=str(user_id), 
        metric=data.metric,
        resource_type="performance_prediction"
    )
    
    # Get prediction
    prediction = await service.get_performance_predictions(
        user_id=user_id,
        metric=data.metric,
        horizon=data.horizon,
        campaign_id=data.campaign_id,
        segment=data.segment
    )
    
    # Track metrics
    record_metric(
        "api.predictions.fetch", 
        1, 
        {
            "user_id": user_id,
            "metric": data.metric,
            "horizon": data.horizon
        }
    )
    
    return ApiResponse.success(prediction)

@router.get("/recommendations/campaigns", response_model=ApiResponse[List[RecommendationResponse]])
async def get_multiple_campaign_recommendations(
    campaign_ids: str = Query(..., title="Comma-separated campaign IDs"),
    include_confidence: bool = Query(True, title="Include confidence details"),
    tags: Optional[str] = Query(None, title="Filter by tags (comma-separated)"),
    service: PredictiveAnalyticsService = Depends(get_predictive_analytics_service),
    db: Session = Depends(get_db),
    user_id: int = 1  # This would normally come from auth middleware
):
    """Get recommendations for multiple campaigns."""
    # Add context for logging
    bind_contextvars(
        user_id=str(user_id), 
        campaign_ids=campaign_ids, 
        resource_type="multiple_campaign_recommendations"
    )
    
    # Parse campaign IDs and tags
    try:
        campaign_id_list = [int(id_str) for id_str in campaign_ids.split(',')]
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid campaign IDs format. Expected comma-separated integers."
        )
    
    tag_list = tags.split(',') if tags else None
    
    # Get recommendations
    recommendations = await service.get_campaign_recommendations(
        user_id=user_id,
        campaign_ids=campaign_id_list,
        tags=tag_list,
        include_confidence_scores=include_confidence
    )
    
    # Track metrics
    record_metric(
        "api.recommendations.fetch.multiple", 
        1, 
        {
            "user_id": user_id,
            "campaign_count": len(campaign_id_list),
            "recommendation_count": len(recommendations)
        }
    )
    
    return ApiResponse.success(recommendations)