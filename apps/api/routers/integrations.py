from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from typing import Dict, Any, List, Optional
import logging
from pydantic import BaseModel

from ..services.nango_integration_service import NangoIntegrationService
from ..services.platform_integration_orchestrator import PlatformIntegrationOrchestrator
from ..octotools_integration.octotools_service import OctoToolsService
from ..services.identity_resolution_service import IdentityResolutionService
from ..dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/integrations",
    tags=["integrations"],
    responses={404: {"description": "Not found"}},
)

# Dependency to get the platform integration orchestrator
async def get_platform_integration_orchestrator():
    nango_service = NangoIntegrationService()
    octotools_service = OctoToolsService()
    identity_resolution_service = IdentityResolutionService()

    orchestrator = PlatformIntegrationOrchestrator(
        octotools_service=octotools_service,
        nango_service=nango_service,
        identity_resolution_service=identity_resolution_service
    )

    try:
        yield orchestrator
    finally:
        await nango_service.close()

# Request models
class ConnectPlatformRequest(BaseModel):
    platform: str

class TriggerSyncRequest(BaseModel):
    platform: str
    sync_type: str

# Response models
class ConnectPlatformResponse(BaseModel):
    auth_url: str
    platform: str
    connection_id: str

class PlatformConnectionResponse(BaseModel):
    connections: List[Dict[str, Any]]

class TriggerSyncResponse(BaseModel):
    success: bool
    platform: str
    sync_type: str
    sync_name: str
    user_id: str
    connection_id: str
    result: Dict[str, Any]

class DisconnectPlatformResponse(BaseModel):
    success: bool
    platform: str
    user_id: str
    connection_id: str
    result: Dict[str, Any]

class PlatformDataResponse(BaseModel):
    records: List[Dict[str, Any]]
    next_cursor: Optional[str] = None
    has_more: bool

@router.post("/connect", response_model=ConnectPlatformResponse)
async def connect_platform(
    request: ConnectPlatformRequest,
    user = Depends(get_current_user),
    orchestrator: PlatformIntegrationOrchestrator = Depends(get_platform_integration_orchestrator)
):
    """
    Start the platform connection flow.

    This endpoint generates an authorization URL for the specified platform.
    The user should be redirected to this URL to authorize the connection.
    """
    try:
        result = await orchestrator.connect_platform(user["id"], request.platform)
        return result
    except Exception as e:
        logger.error(f"Error connecting platform: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error connecting platform: {str(e)}"
        )

@router.get("/callback")
async def platform_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    orchestrator: PlatformIntegrationOrchestrator = Depends(get_platform_integration_orchestrator)
):
    """
    Handle the OAuth callback from Nango.

    This endpoint is called by the OAuth provider after the user authorizes the connection.
    It completes the OAuth flow and triggers initial data synchronization.
    """
    try:
        # Use the simplified Nango callback handler
        result = await orchestrator.process_nango_callback(code, state)

        # Redirect to the frontend with success parameters
        frontend_url = f"{request.base_url.scheme}://{request.base_url.netloc}"
        redirect_url = f"{frontend_url}/dashboard/integrations?status=success&platform={result.get('platform', '')}"

        return RedirectResponse(url=redirect_url)
    except Exception as e:
        logger.error(f"Error processing callback: {str(e)}")

        # Redirect to the frontend with error parameters
        frontend_url = f"{request.base_url.scheme}://{request.base_url.netloc}"
        redirect_url = f"{frontend_url}/dashboard/integrations?status=error&message={str(e)}"

        return RedirectResponse(url=redirect_url)

@router.get("/connections", response_model=PlatformConnectionResponse)
async def list_connections(
    user = Depends(get_current_user),
    orchestrator: PlatformIntegrationOrchestrator = Depends(get_platform_integration_orchestrator)
):
    """
    List all platform connections for the current user.

    This endpoint returns a list of all connected platforms for the current user,
    along with their sync status.
    """
    try:
        connections = await orchestrator.list_user_connections(user["id"])
        return {"connections": connections}
    except Exception as e:
        logger.error(f"Error listing connections: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing connections: {str(e)}"
        )

@router.post("/sync", response_model=TriggerSyncResponse)
async def trigger_sync(
    request: TriggerSyncRequest,
    user = Depends(get_current_user),
    orchestrator: PlatformIntegrationOrchestrator = Depends(get_platform_integration_orchestrator)
):
    """
    Trigger a sync for a specific platform and sync type.

    This endpoint triggers a synchronization for the specified platform and sync type.
    """
    try:
        result = await orchestrator.trigger_platform_sync(
            user["id"],
            request.platform,
            request.sync_type
        )
        return result
    except Exception as e:
        logger.error(f"Error triggering sync: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error triggering sync: {str(e)}"
        )

@router.delete("/{platform}", response_model=DisconnectPlatformResponse)
async def disconnect_platform(
    platform: str,
    user = Depends(get_current_user),
    orchestrator: PlatformIntegrationOrchestrator = Depends(get_platform_integration_orchestrator)
):
    """
    Disconnect a platform for the current user.

    This endpoint disconnects the specified platform for the current user,
    removing all associated data and tools.
    """
    try:
        result = await orchestrator.disconnect_platform(user["id"], platform)
        return result
    except Exception as e:
        logger.error(f"Error disconnecting platform: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error disconnecting platform: {str(e)}"
        )

@router.get("/{platform}/{sync_type}/data", response_model=PlatformDataResponse)
async def get_platform_data(
    platform: str,
    sync_type: str,
    limit: int = Query(100, ge=1, le=1000),
    cursor: Optional[str] = Query(None),
    user = Depends(get_current_user),
    orchestrator: PlatformIntegrationOrchestrator = Depends(get_platform_integration_orchestrator)
):
    """
    Get synchronized data for a specific platform and sync type.

    This endpoint returns the synchronized data for the specified platform and sync type.
    """
    try:
        result = await orchestrator.get_platform_data(
            user["id"],
            platform,
            sync_type,
            limit=limit,
            cursor=cursor
        )

        return {
            "records": result.get("records", []),
            "next_cursor": result.get("next_cursor"),
            "has_more": result.get("has_more", False)
        }
    except Exception as e:
        logger.error(f"Error getting platform data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting platform data: {str(e)}"
        )
