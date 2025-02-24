import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict
from loguru import logger
from ..services import process_campaign_task, save_campaign_result
from ..models import MODEL_REGISTRY
from .auth import get_api_key
from .schemas import BaseResponse, ErrorResponse
from ..cache import redis_client

router = APIRouter()

class CampaignRequest(BaseModel):
    task: str
    model_name: Optional[str] = "gpt-4"
    cache_ttl: Optional[int] = 3600  # Cache TTL in seconds

class CampaignResponse(BaseResponse):
    campaign_id: Optional[int] = None
    result: Optional[Dict] = None
    metadata: Optional[Dict] = None

@router.post("/create_campaign", response_model=CampaignResponse, tags=["Campaigns"], summary="Create new campaign")
async def create_campaign(request: CampaignRequest, api_key: str = Depends(get_api_key)):
    try:
        # Check cache first
        cache_key = f"campaign:{request.task}"
        if redis_client:
            try:
                cached_result = redis_client.get(cache_key)
                if cached_result:
                    cached_data = json.loads(cached_result)
                    return CampaignResponse(
                        status="success",
                        result=cached_data,
                        metadata={"source": "cache"}
                    )
            except Exception as e:
                logger.error(f"Cache error: {e}")

        # Get model adapter
        if request.model_name not in MODEL_REGISTRY:
            raise HTTPException(status_code=400, detail=f"Model {request.model_name} not supported")
        
        model_adapter = MODEL_REGISTRY[request.model_name](api_key)
        
        # Process campaign
        result = process_campaign_task(request.task, model_adapter, user_id=1)  # TODO: Get user_id from auth
        
        # Save result
        campaign_id = None  # TODO: Save to database and get ID
        save_campaign_result(campaign_id, result)
        
        # Cache successful results
        if result["status"] == "success" and redis_client:
            try:
                redis_client.setex(cache_key, request.cache_ttl, json.dumps(result))
            except Exception as e:
                logger.error(f"Failed to cache result: {e}")
        
        return CampaignResponse(
            status="success",
            campaign_id=campaign_id,
            result=result["result"],
            metadata=result["metadata"]
        )
        
    except Exception as e:
        logger.error(f"Campaign creation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        ) 