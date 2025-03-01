from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from api.services.auth_service import get_current_user
from api.services.platform_auth_service import platform_auth_service
from api.services.platform_service import platform_service
from api.models.user import User

router = APIRouter()

class PlatformConnectionRequest(BaseModel):
    platform: str

class PlatformConnectionResponse(BaseModel):
    auth_url: str
    platform: str

class PlatformSyncRequest(BaseModel):
    platform: str
    sync_all: Optional[bool] = False

@router.post("/connect", response_model=PlatformConnectionResponse)
async def connect_platform(
    request: PlatformConnectionRequest,
    current_user: User = Depends(get_current_user)
):
    """Start the process of connecting to a platform."""
    try:
        auth_url = platform_auth_service.get_auth_url(
            platform=request.platform,
            user_id=current_user.id
        )

        return {
            "auth_url": auth_url,
            "platform": request.platform
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/callback/{platform}")
async def platform_callback(
    platform: str,
    code: str = Query(...),
    state: str = Query(...)
):
    """Handle the callback from a platform after authentication."""
    try:
        result = await platform_auth_service.handle_auth_callback(
            platform=platform,
            code=code,
            state=state
        )

        # Register platform-specific tools
        await platform_service.register_platform_tools(
            user_id=result["user_id"],
            platform=platform
        )

        # Return success with redirect URL
        return {
            "status": "success",
            "redirect_url": "/dashboard/platforms?connection=success"
        }
    except Exception as e:
        # Return error with redirect URL
        return {
            "status": "error",
            "message": str(e),
            "redirect_url": "/dashboard/platforms?connection=failed"
        }

@router.get("/connected")
async def get_connected_platforms(
    current_user: User = Depends(get_current_user)
):
    """Get all platforms connected by the current user."""
    try:
        platforms = await platform_service.get_user_connected_platforms(
            user_id=current_user.id
        )

        return {"platforms": platforms}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync")
async def sync_platform_data(
    request: PlatformSyncRequest,
    current_user: User = Depends(get_current_user)
):
    """Synchronize data from a platform."""
    try:
        result = await platform_service.sync_platform_data(
            user_id=current_user.id,
            platform=request.platform,
            sync_all=request.sync_all
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{platform}")
async def disconnect_platform(
    platform: str,
    current_user: User = Depends(get_current_user)
):
    """Disconnect a platform."""
    try:
        result = await platform_service.disconnect_platform(
            user_id=current_user.id,
            platform=platform
        )

        return {"status": "success", "platform": platform}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{platform}/status")
async def get_platform_status(
    platform: str,
    current_user: User = Depends(get_current_user)
):
    """Get the status of a platform connection."""
    try:
        status = await platform_service.get_platform_status(
            user_id=current_user.id,
            platform=platform
        )

        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
