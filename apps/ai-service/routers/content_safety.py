"""
Content safety router for the AI service.

This module provides API endpoints for content safety checks and filtering.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

from ai_service.services.content_safety_service import get_content_safety_service, ContentSafetyService
from ai_service.models.content_safety import ContentSafetyLevel, ContentSafetyAction

router = APIRouter()
logger = logging.getLogger("ai_service.routers.content_safety")

class ContentFilterRequest(BaseModel):
    """Model for content filter requests."""
    content: str
    strict_mode: bool = Field(default=False, description="Enable stricter content filtering")

class ContentFilterResponse(BaseModel):
    """Model for content filter responses."""
    filtered_content: str
    was_filtered: bool
    safety_details: Dict[str, Any] = {}

class ContentCheckRequest(BaseModel):
    """Model for content safety check requests."""
    content: str

class ContentCheckResponse(BaseModel):
    """Model for content safety check responses."""
    safety_level: str
    categories: List[Dict[str, Any]] = []
    recommended_action: str

@router.post("/filter", response_model=ContentFilterResponse)
async def filter_content(
    request: ContentFilterRequest,
    content_safety_service: ContentSafetyService = Depends(get_content_safety_service),
):
    """
    Filter content for safety issues.
    
    This endpoint checks content for safety issues and filters it if necessary.
    """
    try:
        logger.info(f"Processing content filter request (strict_mode={request.strict_mode})")
        
        filtered_content, result = await content_safety_service.filter_content(request.content)
        was_filtered = filtered_content != request.content
        
        # Convert safety results to a dict
        safety_details = {
            "safety_level": result.safety_level.value,
            "categories": [c.dict() for c in result.categories if c.flagged],
            "action": result.recommended_action.value
        }
        
        return ContentFilterResponse(
            filtered_content=filtered_content,
            was_filtered=was_filtered,
            safety_details=safety_details,
        )
    
    except Exception as e:
        logger.error(f"Content filtering failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content filtering failed: {str(e)}",
        )

@router.post("/check", response_model=ContentCheckResponse)
async def check_content_safety(
    request: ContentCheckRequest,
    content_safety_service: ContentSafetyService = Depends(get_content_safety_service),
):
    """
    Check content for safety issues without filtering.
    
    This endpoint checks content for safety issues and returns detailed information
    about any detected issues, but does not modify the content.
    """
    try:
        logger.info("Processing content safety check request")
        
        result = await content_safety_service.check_content_safety(request.content)
        
        return ContentCheckResponse(
            safety_level=result.safety_level.value,
            categories=[c.dict() for c in result.categories if c.flagged],
            recommended_action=result.recommended_action.value,
        )
    
    except Exception as e:
        logger.error(f"Content safety check failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content safety check failed: {str(e)}",
        )

@router.get("/stats", response_model=Dict[str, Any])
async def get_safety_stats(
    content_safety_service: ContentSafetyService = Depends(get_content_safety_service),
):
    """
    Get content safety statistics.
    
    This endpoint returns statistics about content safety checks, including
    counts of different safety levels and actions taken.
    """
    try:
        logger.info("Processing content safety stats request")
        
        stats = await content_safety_service.get_safety_stats()
        
        return stats
    
    except Exception as e:
        logger.error(f"Failed to get content safety stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get content safety stats: {str(e)}",
        )