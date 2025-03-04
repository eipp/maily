"""
Campaign router implementing standardized patterns.
Includes endpoints for campaign management and recommendation handling.
"""
from typing import List, Dict, Any, Optional, Union
from fastapi import APIRouter, Depends, Path, Query, status, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator

from ..database.dependencies import get_db
from ..services.campaign_service import CampaignService, get_campaign_service
from ..schemas.api_response import ApiResponse, PaginatedResponse
from ..errors.maily_error import ResourceNotFoundError, ValidationError
from ..logging.logging_config import bind_contextvars
from ..monitoring.metrics import record_metric

# Define API schemas
class CampaignBase(BaseModel):
    """Base schema for campaign data."""
    name: str = Field(..., title="Campaign name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, title="Campaign description")
    subject: Optional[str] = Field(None, title="Email subject line")
    template_id: Optional[int] = Field(None, title="Template ID")
    content_data: Optional[Dict[str, Any]] = Field(None, title="Campaign content data")

class CampaignCreate(CampaignBase):
    """Schema for creating campaigns."""
    pass

class CampaignUpdate(BaseModel):
    """Schema for updating campaigns."""
    name: Optional[str] = Field(None, title="Campaign name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, title="Campaign description")
    subject: Optional[str] = Field(None, title="Email subject line")
    status: Optional[str] = Field(None, title="Campaign status")
    template_id: Optional[int] = Field(None, title="Template ID")
    content_data: Optional[Dict[str, Any]] = Field(None, title="Campaign content data")

class CampaignStatusUpdate(BaseModel):
    """Schema for updating campaign status."""
    status: str = Field(..., title="New campaign status")

class CampaignResponse(CampaignBase):
    """Schema for campaign response."""
    id: int
    user_id: int
    status: str
    created_at: str
    updated_at: str
    schedule_time: Optional[str] = None
    sent_time: Optional[str] = None
    certificate_id: Optional[str] = None
    verified_at: Optional[str] = None

    class Config:
        orm_mode = True

# Create router
router = APIRouter(
    prefix="/campaigns",
    tags=["campaigns"],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Campaign not found"},
        status.HTTP_403_FORBIDDEN: {"description": "Permission denied"}
    }
)

@router.post("", response_model=ApiResponse[CampaignResponse], status_code=status.HTTP_201_CREATED)
async def create_campaign(
    data: CampaignCreate,
    service: CampaignService = Depends(get_campaign_service),
    db: Session = Depends(get_db),
    user_id: int = 1  # This would normally come from auth middleware
):
    """Create a new campaign."""
    # Add context for logging
    bind_contextvars(user_id=str(user_id), resource_type="campaign")

    # Create the campaign
    campaign = service.create_campaign(user_id, data.dict())

    # Convert to response model
    response = CampaignResponse.from_orm(campaign)

    return ApiResponse.success(response)

@router.get("/{campaign_id}", response_model=ApiResponse[CampaignResponse])
async def get_campaign(
    campaign_id: int = Path(..., title="Campaign ID", gt=0),
    service: CampaignService = Depends(get_campaign_service),
    db: Session = Depends(get_db),
    user_id: int = 1  # This would normally come from auth middleware
):
    """Get a campaign by ID."""
    # Add context for logging
    bind_contextvars(user_id=str(user_id), campaign_id=str(campaign_id), resource_type="campaign")

    # Get the campaign
    campaign = service.get_campaign(campaign_id, user_id)

    # Convert to response model
    response = CampaignResponse.from_orm(campaign)

    return ApiResponse.success(response)

@router.get("", response_model=PaginatedResponse[List[CampaignResponse]])
async def get_campaigns(
    status: Optional[str] = Query(None, title="Filter by status"),
    limit: int = Query(50, title="Page size", ge=1, le=100),
    offset: int = Query(0, title="Page offset", ge=0),
    sort_by: str = Query("created_at", title="Sort field"),
    sort_order: str = Query("desc", title="Sort order"),
    service: CampaignService = Depends(get_campaign_service),
    db: Session = Depends(get_db),
    user_id: int = 1  # This would normally come from auth middleware
):
    """Get campaigns with pagination and filtering."""
    # Add context for logging
    bind_contextvars(user_id=str(user_id), resource_type="campaign")

    # Get campaigns with pagination
    campaigns, total = service.get_campaigns(
        user_id=user_id,
        status=status,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order
    )

    # Convert to response models
    response = [CampaignResponse.from_orm(c) for c in campaigns]

    # Create paginated response
    return PaginatedResponse.paginated(
        data=response,
        page=(offset // limit) + 1,
        page_size=limit,
        total_items=total
    )

@router.put("/{campaign_id}", response_model=ApiResponse[CampaignResponse])
async def update_campaign(
    data: CampaignUpdate,
    campaign_id: int = Path(..., title="Campaign ID", gt=0),
    service: CampaignService = Depends(get_campaign_service),
    db: Session = Depends(get_db),
    user_id: int = 1  # This would normally come from auth middleware
):
    """Update a campaign."""
    # Add context for logging
    bind_contextvars(user_id=str(user_id), campaign_id=str(campaign_id), resource_type="campaign")

    # Update the campaign
    campaign = service.update_campaign(campaign_id, user_id, data.dict(exclude_unset=True))

    # Convert to response model
    response = CampaignResponse.from_orm(campaign)

    return ApiResponse.success(response)

@router.patch("/{campaign_id}/status", response_model=ApiResponse[CampaignResponse])
async def update_campaign_status(
    data: CampaignStatusUpdate,
    campaign_id: int = Path(..., title="Campaign ID", gt=0),
    service: CampaignService = Depends(get_campaign_service),
    db: Session = Depends(get_db),
    user_id: int = 1  # This would normally come from auth middleware
):
    """Update campaign status."""
    # Add context for logging
    bind_contextvars(user_id=str(user_id), campaign_id=str(campaign_id), resource_type="campaign")

    # Update the status
    campaign = service.update_campaign_status(campaign_id, user_id, data.status)

    # Convert to response model
    response = CampaignResponse.from_orm(campaign)

    return ApiResponse.success(response)

@router.delete("/{campaign_id}", response_model=ApiResponse[bool])
async def delete_campaign(
    campaign_id: int = Path(..., title="Campaign ID", gt=0),
    service: CampaignService = Depends(get_campaign_service),
    db: Session = Depends(get_db),
    user_id: int = 1  # This would normally come from auth middleware
):
    """Delete a campaign."""
    # Add context for logging
    bind_contextvars(user_id=str(user_id), campaign_id=str(campaign_id), resource_type="campaign")

    # Delete the campaign
    result = service.delete_campaign(campaign_id, user_id)

    return ApiResponse.success(result)


# Recommendation schemas
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

class ConfidenceScoreResponse(BaseModel):
    """Schema for confidence score response."""
    score: float = Field(..., title="Confidence score (0-1)")
    level: str = Field(..., title="Confidence level category")
    explanation: str = Field(..., title="Human-readable explanation")
    factors: List[Dict[str, Any]] = Field(..., title="Factors affecting confidence")

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

# Recommendation endpoints
@router.get("/{campaign_id}/recommendations", response_model=ApiResponse[List[RecommendationResponse]])
async def get_campaign_recommendations(
    campaign_id: int = Path(..., title="Campaign ID", gt=0),
    include_confidence: bool = Query(True, title="Include confidence details"),
    tags: Optional[str] = Query(None, title="Filter by tags (comma-separated)"),
    service: CampaignService = Depends(get_campaign_service),
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
    recommendations = service.get_campaign_recommendations(
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
    service: CampaignService = Depends(get_campaign_service),
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
    result = service.track_recommendation_interaction(
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
