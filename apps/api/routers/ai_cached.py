"""
API router for AI endpoints with caching support.
"""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.services.ai_service import AIService, get_ai_service
from apps.api.schemas.ai import AIModelRequest, AIModelResponse
from apps.api.core.auth import get_current_user
from apps.api.schemas.users import User


router = APIRouter(prefix="/ai/cached", tags=["AI Cached"])


@router.post("/generate", response_model=AIModelResponse)
async def generate_response(
    request: AIModelRequest,
    ai_service: AIService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a response from an AI model.

    This endpoint uses caching for improved performance with deterministic requests.
    Responses are cached based on the prompt, model, and parameters for faster retrieval.
    """
    return await ai_service.generate_response(request)


@router.get("/models", response_model=List[Dict[str, Any]])
async def get_models(
    ai_service: AIService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user)
):
    """Get a list of available AI models."""
    return await ai_service.get_model_list()


@router.get("/cache/stats", response_model=Dict[str, Any])
async def get_cache_stats(
    ai_service: AIService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get cache statistics.

    Returns information about cache size, hits, misses, and hit rate.
    """
    return await ai_service.get_cache_stats()


@router.post("/cache/invalidate", response_model=Dict[str, int])
async def invalidate_cache(
    model_name: str = None,
    ai_service: AIService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user)
):
    """
    Invalidate cache entries.

    If model_name is provided, only invalidates entries for that model.
    Otherwise, invalidates all entries.

    Returns:
        A dictionary with the count of invalidated entries
    """
    count = await ai_service.invalidate_cache(model_name)
    return {"invalidated_entries": count}
