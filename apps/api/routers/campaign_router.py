"""
Campaign router implementing standardized patterns.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ..database.dependencies import get_db
from ..services.campaign_service import CampaignService, get_campaign_service
from ..schemas.api_response import ApiResponse, PaginatedResponse
from ..errors.maily_error import ResourceNotFoundError, ValidationError
from ..logging.logging_config import bind_contextvars

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
