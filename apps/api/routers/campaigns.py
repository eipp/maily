"""Campaign routes for the Maily API.

This module provides routes for creating, updating, and managing email
campaigns, including content generation and scheduling.
"""

import json
import logging
from typing import Dict, List, Optional

import redis
from fastapi import APIRouter, Depends, HTTPException, Request, status, BackgroundTasks
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..models.campaign import Campaign
from ..models.user import User
from ..services.database import get_db
from ..services.user_service import get_current_user
from ..services.octotools_service import OctoToolsService
from ..cache.redis import redis_client
from ..utils.response import BaseResponse
from ..services.campaign_service import CampaignService
from ..services.email_service import EmailService
from .schemas import CampaignResponse, ErrorResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize Redis client
redis_client = redis.Redis.from_url("redis://localhost:6379/0")

# Create router
router = APIRouter(prefix="/campaigns", tags=["campaigns"])

# Create octotools service instance
octotools_service = OctoToolsService()


class CampaignRequest(BaseModel):
    """Schema for campaign creation request using OctoTools.

    Attributes:
        objective: Campaign objective
        audience: Target audience
        brand_voice: Brand voice/tone
        key_points: Key points to include
        attachments: Optional attachments to include
    """

    objective: str = Field(..., description="Campaign objective (e.g., product announcement, newsletter)")
    audience: str = Field(..., description="Target audience description")
    brand_voice: str = Field("professional", description="Brand voice/tone (e.g., professional, friendly, technical)")
    key_points: List[str] = Field(..., description="Key points to include in the email")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="Optional attachments to include")
    personalization: Optional[Dict[str, Any]] = Field(None, description="Optional personalization variables")


class CampaignResponse(BaseResponse):
    campaign_id: Optional[int] = None
    result: Optional[Dict] = None
    metadata: Optional[Dict] = None


class CampaignCreate(BaseModel):
    """Campaign creation model."""

    name: str = Field(..., description="Campaign name")
    subject: str = Field(..., description="Email subject")
    content: str = Field(..., description="Email content")
    schedule_time: Optional[str] = Field(None, description="Schedule time (ISO format)")


class CampaignUpdate(BaseModel):
    """Campaign update model."""

    name: Optional[str] = Field(None, description="Campaign name")
    subject: Optional[str] = Field(None, description="Email subject")
    content: Optional[str] = Field(None, description="Email content")
    status: Optional[str] = Field(None, description="Campaign status")
    schedule_time: Optional[str] = Field(None, description="Schedule time (ISO format)")


class CampaignSendRequest(BaseModel):
    """Campaign send request model."""

    recipients: List[str] = Field(..., description="List of recipient email addresses")


class CampaignSendResponse(BaseModel):
    """Campaign send response model."""

    status: str
    campaign_id: int
    sent_to: List[str]


@router.post("/generate", response_model=Dict[str, Any], summary="Generate campaign content with AI")
async def generate_campaign_content(
    request: CampaignRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate email campaign content using OctoTools.

    This endpoint uses AI to generate email content based on the provided parameters.
    """
    try:
        # Check cache first
        cache_key = f"campaign_content:{request.objective}:{request.audience}"
        if redis_client:
            try:
                cached_result = redis_client.get(cache_key)
                if cached_result:
                    cached_data = json.loads(cached_result)
                    return {
                        "status": "success",
                        "content": cached_data,
                        "metadata": {"source": "cache"}
                    }
            except Exception as e:
                logger.error(f"Cache error: {e}")

        # Prepare campaign data
        campaign_data = {
            "objective": request.objective,
            "audience": request.audience,
            "brand_voice": request.brand_voice,
            "key_points": request.key_points,
            "personalization": request.personalization,
            "attachments": request.attachments,
            "user_id": current_user.id
        }

        # Generate content using OctoTools
        result = await octotools_service.create_email_campaign(campaign_data)

        # Cache successful results
        if result["status"] == "success" and redis_client:
            try:
                redis_client.setex(
                    cache_key, 3600, json.dumps(result["content"])
                )
            except Exception as e:
                logger.error(f"Failed to cache result: {e}")

        return result

    except Exception as e:
        logger.error(f"Campaign content generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign: CampaignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new campaign."""
    try:
        # Create campaign service
        campaign_service = CampaignService(db)

        # Create campaign data
        campaign_data = campaign.dict()

        # Create campaign
        new_campaign = campaign_service.create_campaign(current_user.id, campaign_data)

        # Return response
        return CampaignResponse(
            id=new_campaign.id,
            name=new_campaign.name,
            subject=new_campaign.subject,
            content=new_campaign.content,
            status=new_campaign.status,
            user_id=new_campaign.user_id,
            created_at=new_campaign.created_at.isoformat(),
            updated_at=new_campaign.updated_at.isoformat(),
            schedule_time=new_campaign.schedule_time.isoformat() if new_campaign.schedule_time else None,
            open_rate=new_campaign.open_rate,
            click_rate=new_campaign.click_rate,
            metadata=new_campaign.metadata,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating campaign: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=List[CampaignResponse])
async def get_campaigns(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all campaigns for the current user."""
    try:
        # Create campaign service
        campaign_service = CampaignService(db)

        # Get campaigns
        campaigns = campaign_service.get_user_campaigns(current_user.id)

        # Return response
        return [
            CampaignResponse(
                id=campaign.id,
                name=campaign.name,
                subject=campaign.subject,
                content=campaign.content,
                status=campaign.status,
                user_id=campaign.user_id,
                created_at=campaign.created_at.isoformat(),
                updated_at=campaign.updated_at.isoformat(),
                schedule_time=campaign.schedule_time.isoformat() if campaign.schedule_time else None,
                open_rate=campaign.open_rate,
                click_rate=campaign.click_rate,
                metadata=campaign.metadata,
            )
            for campaign in campaigns
        ]
    except Exception as e:
        logger.error(f"Error getting campaigns: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a campaign by ID."""
    try:
        # Create campaign service
        campaign_service = CampaignService(db)

        # Get campaign
        campaign = campaign_service.get_campaign(campaign_id)

        # Check if campaign exists
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Check if campaign belongs to user
        if campaign.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this campaign")

        # Return response
        return CampaignResponse(
            id=campaign.id,
            name=campaign.name,
            subject=campaign.subject,
            content=campaign.content,
            status=campaign.status,
            user_id=campaign.user_id,
            created_at=campaign.created_at.isoformat(),
            updated_at=campaign.updated_at.isoformat(),
            schedule_time=campaign.schedule_time.isoformat() if campaign.schedule_time else None,
            open_rate=campaign.open_rate,
            click_rate=campaign.click_rate,
            metadata=campaign.metadata,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting campaign: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: int,
    campaign: CampaignUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a campaign."""
    try:
        # Create campaign service
        campaign_service = CampaignService(db)

        # Get campaign
        existing_campaign = campaign_service.get_campaign(campaign_id)

        # Check if campaign exists
        if not existing_campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Check if campaign belongs to user
        if existing_campaign.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this campaign")

        # Update campaign
        updated_campaign = campaign_service.update_campaign(
            campaign_id, campaign.dict(exclude_unset=True)
        )

        # Return response
        return CampaignResponse(
            id=updated_campaign.id,
            name=updated_campaign.name,
            subject=updated_campaign.subject,
            content=updated_campaign.content,
            status=updated_campaign.status,
            user_id=updated_campaign.user_id,
            created_at=updated_campaign.created_at.isoformat(),
            updated_at=updated_campaign.updated_at.isoformat(),
            schedule_time=updated_campaign.schedule_time.isoformat() if updated_campaign.schedule_time else None,
            open_rate=updated_campaign.open_rate,
            click_rate=updated_campaign.click_rate,
            metadata=updated_campaign.metadata,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating campaign: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a campaign."""
    try:
        # Create campaign service
        campaign_service = CampaignService(db)

        # Get campaign
        campaign = campaign_service.get_campaign(campaign_id)

        # Check if campaign exists
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Check if campaign belongs to user
        if campaign.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this campaign")

        # Delete campaign
        campaign_service.delete_campaign(campaign_id)

        # Return no content
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting campaign: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{campaign_id}/send", response_model=CampaignSendResponse)
async def send_campaign(
    campaign_id: int,
    request: CampaignSendRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a campaign to recipients."""
    try:
        # Create campaign service
        campaign_service = CampaignService(db, email_service=EmailService())

        # Get campaign
        campaign = campaign_service.get_campaign(campaign_id)

        # Check if campaign exists
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Check if campaign belongs to user
        if campaign.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to send this campaign")

        # Prepare campaign data for OctoTools
        campaign_data = {
            "from_email": campaign.sender_email,
            "recipients": request.recipients,
            "subject": campaign.subject,
            "content": campaign.content,
            "provider": campaign.metadata.get("provider", "resend") if campaign.metadata else "resend",
            "metadata": {
                "campaign_id": campaign_id,
                "user_id": current_user.id
            }
        }

        # Send campaign using OctoTools
        send_result = await octotools_service._send_campaign(
            content={
                "subject": campaign.subject,
                "html_body": campaign.content,
                "plain_text": campaign.metadata.get("plain_text", "") if campaign.metadata else ""
            },
            attachments=[],
            campaign_data=campaign_data
        )

        # Update campaign status
        campaign_service.update_campaign_status(campaign_id, "SENT")

        # Return response
        return CampaignSendResponse(
            status="success",
            campaign_id=campaign_id,
            sent_to=request.recipients,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending campaign: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{campaign_id}/analytics", response_model=Dict)
async def get_campaign_analytics(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get analytics for a campaign."""
    try:
        # Check cache first
        cache_key = f"analytics:{campaign_id}"
        cached_result = redis_client.get(cache_key)

        if cached_result:
            return json.loads(cached_result)

        # Create campaign service
        campaign_service = CampaignService(db, email_service=EmailService())

        # Get campaign
        campaign = campaign_service.get_campaign(campaign_id)

        # Check if campaign exists
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Check if campaign belongs to user
        if campaign.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this campaign's analytics")

        try:
            # Try to use OctoTools for analytics if implemented
            analytics = await octotools_service.analyze_campaign(str(campaign_id))
        except NotImplementedError:
            # Fall back to the old implementation if OctoTools analytics is not implemented
            analytics = campaign_service.get_campaign_analytics(campaign_id)

        # Cache result for 5 minutes
        redis_client.setex(cache_key, 300, json.dumps(analytics))

        # Return analytics
        return analytics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting campaign analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
