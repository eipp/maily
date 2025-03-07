"""
Optimized Campaign service using standardized patterns.
Includes integration with recommendation system.
"""
from typing import List, Dict, Any, Optional, Union, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func
import structlog
import httpx
import json
import time
from datetime import datetime
from fastapi import Depends

from ..models.campaign_optimized import Campaign, CampaignStatus
from ..database.transaction import transaction, transactional
from ..errors.maily_error import ResourceNotFoundError, ValidationError
from packages.database.src.redis import redis_client
from ..config.settings import get_settings
from ..monitoring.metrics import record_metric

logger = structlog.get_logger("justmaily.services.campaign")

class CampaignService:
    """Service for managing campaign operations with optimized queries and recommendation integration."""

    def __init__(self, db: Session, cache_service: CacheService):
        """Initialize the campaign service.

        Args:
            db: SQLAlchemy database session
            cache_service: Redis cache service
        """
        self.db = db
        self.cache = cache_service
        self.settings = get_settings()
        self.analytics_base_url = self.settings.ANALYTICS_SERVICE_URL

    @transactional
    def create_campaign(self, user_id: int, data: Dict[str, Any]) -> Campaign:
        """Create a new campaign.

        Args:
            user_id: ID of the user creating the campaign
            data: Campaign data dictionary

        Returns:
            Created Campaign instance

        Raises:
            ValidationError: If required fields are missing
        """
        # Validate required fields
        if 'name' not in data:
            raise ValidationError("Campaign name is required")

        # Create campaign object
        campaign = Campaign(
            user_id=user_id,
            name=data.get('name'),
            description=data.get('description'),
            subject=data.get('subject'),
            template_id=data.get('template_id'),
            content_data=data.get('content_data', {}),
            status=CampaignStatus.DRAFT.value
        )

        # Add to database (commit happens in the @transactional decorator)
        self.db.add(campaign)
        self.db.flush()  # To get the ID

        # Log campaign creation
        logger.info(
            "Campaign created",
            campaign_id=campaign.id,
            user_id=user_id,
            campaign_name=campaign.name
        )

        # Invalidate cache
        self._invalidate_campaign_cache(user_id)

        return campaign

    def get_campaign(self, campaign_id: int, user_id: Optional[int] = None) -> Campaign:
        """Get a campaign by ID.

        Args:
            campaign_id: ID of the campaign to retrieve
            user_id: Optional user ID for access validation

        Returns:
            Campaign instance

        Raises:
            ResourceNotFoundError: If campaign not found
        """
        # Try to get from cache first
        cache_key = f"campaign:{campaign_id}"
        cached_campaign = self.cache.get(cache_key)

        if cached_campaign:
            logger.debug("Campaign retrieved from cache", campaign_id=campaign_id)
            # Check user access if user_id is provided
            if user_id and cached_campaign.get('user_id') != user_id:
                raise ResourceNotFoundError(f"Campaign {campaign_id} not found")
            return cached_campaign

        # Query with optimized columns selection
        query = self.db.query(Campaign)

        # Add user_id filter if provided
        if user_id:
            query = query.filter(Campaign.user_id == user_id)

        campaign = query.filter(Campaign.id == campaign_id).first()

        if not campaign:
            logger.warning("Campaign not found", campaign_id=campaign_id)
            raise ResourceNotFoundError(f"Campaign {campaign_id} not found")

        # Cache the result
        self.cache.set(cache_key, campaign.to_dict(), "campaign_content")

        return campaign

    def get_campaigns(
        self,
        user_id: int,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        include_recommendations: bool = False
    ) -> Tuple[List[Campaign], int, Optional[List[Dict[str, Any]]]]:
        """Get campaigns with pagination and filtering.

        Args:
            user_id: ID of the user
            status: Optional status filter
            limit: Maximum number of campaigns to return
            offset: Offset for pagination
            sort_by: Field to sort by
            sort_order: Sort order ('asc' or 'desc')
            include_recommendations: Whether to include campaign recommendations

        Returns:
            Tuple of (list of campaigns, total count, optional recommendations)
        """
        # Try to get from cache if no dynamic filters
        if status is None and sort_by == "created_at" and sort_order == "desc" and not include_recommendations:
            cache_key = f"user:{user_id}:campaigns:{limit}:{offset}"
            cached_result = self.cache.get(cache_key)

            if cached_result:
                logger.debug("Campaigns retrieved from cache", user_id=user_id)
                return cached_result["campaigns"], cached_result["total"], None

        # Build base query for both data and count
        base_query = self.db.query(Campaign).filter(Campaign.user_id == user_id)

        # Apply status filter if provided
        if status:
            base_query = base_query.filter(Campaign.status == status)

        # Get total count
        total_count = base_query.count()

        # Apply sorting
        sort_column = getattr(Campaign, sort_by, Campaign.created_at)
        if sort_order.lower() == "desc":
            sort_column = desc(sort_column)
        else:
            sort_column = asc(sort_column)

        # Apply pagination and get results - select only needed columns
        campaigns = base_query.order_by(sort_column).limit(limit).offset(offset).all()

        # Get recommendations if requested
        recommendations = None
        if include_recommendations:
            try:
                # Import here to avoid circular imports
                from ..services.predictive_analytics_service import PredictiveAnalyticsService
                
                # Get instance of predictive analytics service
                predictive_service = PredictiveAnalyticsService(self.db)
                
                # Get campaign IDs
                campaign_ids = [c.id for c in campaigns]
                
                # Get recommendations using the standardized service
                recommendations = predictive_service.get_campaign_recommendations(
                    user_id=user_id,
                    campaign_ids=campaign_ids
                )
                
                logger.info(
                    "Retrieved campaign recommendations", 
                    user_id=user_id,
                    campaign_count=len(campaigns),
                    recommendation_count=len(recommendations) if recommendations else 0
                )
            except Exception as e:
                # Log the error but don't fail the entire request
                logger.error(
                    "Failed to retrieve campaign recommendations",
                    user_id=user_id,
                    error=str(e),
                    exc_info=True
                )
                # Return empty recommendations list
                recommendations = []

        # Cache the result if it's a standard query
        if status is None and sort_by == "created_at" and sort_order == "desc" and not include_recommendations:
            cache_key = f"user:{user_id}:campaigns:{limit}:{offset}"
            self.cache.set(
                cache_key,
                {
                    "campaigns": [c.to_dict() for c in campaigns],
                    "total": total_count
                },
                "campaign_content"
            )

        return campaigns, total_count, recommendations

    @transactional
    def update_campaign(self, campaign_id: int, user_id: int, data: Dict[str, Any]) -> Campaign:
        """Update an existing campaign.

        Args:
            campaign_id: ID of the campaign to update
            user_id: ID of the user making the update
            data: Updated campaign data

        Returns:
            Updated Campaign instance

        Raises:
            ResourceNotFoundError: If campaign not found
            ValidationError: If update is invalid
        """
        # Get the campaign
        campaign = self.get_campaign(campaign_id, user_id)

        # Prevent updates to sent campaigns
        if campaign.status == CampaignStatus.SENT.value:
            raise ValidationError("Cannot update a campaign that has already been sent")

        # Update fields
        for key, value in data.items():
            if hasattr(campaign, key) and key not in ['id', 'user_id', 'created_at', 'updated_at']:
                setattr(campaign, key, value)

        # Log update
        logger.info(
            "Campaign updated",
            campaign_id=campaign.id,
            user_id=user_id
        )

        # Invalidate cache
        self._invalidate_campaign_cache(user_id, campaign_id)

        return campaign

    @transactional
    def delete_campaign(self, campaign_id: int, user_id: int) -> bool:
        """Delete a campaign.

        Args:
            campaign_id: ID of the campaign to delete
            user_id: ID of the user making the deletion

        Returns:
            True if deleted successfully

        Raises:
            ResourceNotFoundError: If campaign not found
        """
        # Get the campaign
        campaign = self.get_campaign(campaign_id, user_id)

        # Delete the campaign
        self.db.delete(campaign)

        # Log deletion
        logger.info(
            "Campaign deleted",
            campaign_id=campaign_id,
            user_id=user_id
        )

        # Invalidate cache
        self._invalidate_campaign_cache(user_id, campaign_id)

        return True

    @transactional
    def update_campaign_status(self, campaign_id: int, user_id: int, status: str) -> Campaign:
        """Update campaign status.

        Args:
            campaign_id: ID of the campaign
            user_id: ID of the user
            status: New status

        Returns:
            Updated Campaign instance
        """
        # Validate status
        if status not in [s.value for s in CampaignStatus]:
            raise ValidationError(f"Invalid status: {status}")

        # Get the campaign
        campaign = self.get_campaign(campaign_id, user_id)

        # Update status
        campaign.status = status

        # Log status change
        logger.info(
            "Campaign status updated",
            campaign_id=campaign_id,
            user_id=user_id,
            old_status=campaign.status,
            new_status=status
        )

        # Invalidate cache
        self._invalidate_campaign_cache(user_id, campaign_id)

        return campaign

    def _invalidate_campaign_cache(self, user_id: int, campaign_id: Optional[int] = None):
        """Invalidate campaign cache entries.

        Args:
            user_id: User ID for campaigns
            campaign_id: Optional specific campaign ID
        """
        # Invalidate specific campaign if ID provided
        if campaign_id:
            self.cache.invalidate(f"campaign:{campaign_id}")

        # Invalidate user's campaign lists
        self.cache.invalidate(f"user:{user_id}:campaigns:*")


    # Note: These recommendation-related methods are deprecated.
    # Use the dedicated predictive_analytics_service for these functionalities.
    # These are retained for backward compatibility but will be removed in future.
    def get_campaign_recommendations(
        self, 
        user_id: int, 
        campaign_ids: List[int], 
        tags: List[str] = None,
        include_confidence_scores: bool = True
    ) -> List[Dict[str, Any]]:
        """[DEPRECATED] Get campaign recommendations from the analytics service.
           Use predictive_analytics_service.get_campaign_recommendations() instead.

        Args:
            user_id: ID of the user
            campaign_ids: List of campaign IDs to get recommendations for
            tags: Optional list of recommendation tags to filter by
            include_confidence_scores: Whether to include confidence scores in the response

        Returns:
            List of recommendations for the campaigns with confidence scores
        """
        logger.warning(
            "Using deprecated method get_campaign_recommendations in campaign_service. "
            "Use predictive_analytics_service.get_campaign_recommendations() instead.",
            user_id=user_id
        )
        
        # Return an empty array with a deprecation notice in the first item
        return [{
            "id": "deprecated_method",
            "type": "deprecation_notice",
            "message": "This method is deprecated. Use the dedicated predictive analytics service.",
            "suggestion": "Update your code to use predictive_analytics_service",
            "priority": 1,
            "confidence": 1.0,
            "confidenceLevel": "very_high",
            "confidenceExplanation": "This is a deprecation notice, not an actual recommendation.",
            "tags": ["deprecation"],
            "metadata": {
                "deprecated": True,
                "useInstead": "predictive_analytics_service.get_campaign_recommendations()"
            }
        }]
            
    def track_recommendation_interaction(
        self, 
        recommendation_id: str, 
        user_id: int, 
        action: str, 
        campaign_id: int = None,
        feedback: dict = None
    ) -> bool:
        """[DEPRECATED] Track user interaction with a recommendation.
           Use predictive_analytics_service.track_recommendation_interaction() instead.

        Args:
            recommendation_id: ID of the recommendation
            user_id: ID of the user
            action: Action taken (view, click, dismiss, apply)
            campaign_id: Optional campaign ID associated with the recommendation
            feedback: Optional user feedback about the recommendation (like rating or comment)

        Returns:
            True if tracking was successful, False otherwise
        """
        logger.warning(
            "Using deprecated method track_recommendation_interaction in campaign_service. "
            "Use predictive_analytics_service.track_recommendation_interaction() instead.",
            user_id=user_id,
            recommendation_id=recommendation_id
        )
        
        # Always return True to avoid breaking existing code
        return True


def get_campaign_service(
    db: Session,
    cache_service: CacheService = Depends(get_cache_service)
) -> CampaignService:
    """Dependency for getting campaign service.

    Args:
        db: Database session
        cache_service: Cache service

    Returns:
        Initialized CampaignService
    """
    return CampaignService(db, cache_service)
