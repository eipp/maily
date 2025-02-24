from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from ..models.privacy import (
    ConsentPreferences,
    DataDeletionRequest,
    DataExportRequest,
    ConsentLog
)
from ..services.privacy import PrivacyService
from ..auth import get_current_user
from ..config import Settings

router = APIRouter(prefix="/privacy", tags=["Privacy"])
settings = Settings()
privacy_service = PrivacyService(settings)

class ConsentUpdateRequest(BaseModel):
    essential: bool = True  # Essential cookies cannot be disabled
    functional: bool
    analytics: bool
    marketing: bool
    notification_preferences: Optional[dict]

@router.get("/consent", response_model=ConsentPreferences)
async def get_consent_preferences(
    current_user = Depends(get_current_user)
):
    """
    Get the current user's consent preferences.
    
    Returns:
        ConsentPreferences: The user's current privacy and cookie preferences
    """
    try:
        return await privacy_service.get_consent_preferences(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/consent", response_model=ConsentPreferences)
async def update_consent_preferences(
    preferences: ConsentUpdateRequest,
    current_user = Depends(get_current_user)
):
    """
    Update the user's consent preferences.
    
    Args:
        preferences: New consent preferences
        current_user: Authenticated user
        
    Returns:
        ConsentPreferences: Updated preferences
    """
    try:
        return await privacy_service.update_consent_preferences(
            user_id=current_user.id,
            preferences=preferences
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/data/delete", response_model=DataDeletionRequest)
async def request_data_deletion(
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """
    Request deletion of all user data.
    Initiates a background task to delete user data after a cooling period.
    
    Args:
        background_tasks: FastAPI background tasks handler
        current_user: Authenticated user
        
    Returns:
        DataDeletionRequest: Deletion request details including status
    """
    try:
        # Create deletion request with cooling period
        deletion_request = await privacy_service.create_deletion_request(
            user_id=current_user.id,
            execution_date=datetime.utcnow() + timedelta(days=30)  # 30-day cooling period
        )
        
        # Schedule deletion task
        background_tasks.add_task(
            privacy_service.execute_deletion_request,
            request_id=deletion_request.id
        )
        
        return deletion_request
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/delete/{request_id}", response_model=DataDeletionRequest)
async def get_deletion_status(
    request_id: str,
    current_user = Depends(get_current_user)
):
    """
    Check the status of a data deletion request.
    
    Args:
        request_id: ID of the deletion request
        current_user: Authenticated user
        
    Returns:
        DataDeletionRequest: Current status of the deletion request
    """
    try:
        request = await privacy_service.get_deletion_request(request_id)
        if request.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this request")
        return request
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/data/export", response_model=DataExportRequest)
async def request_data_export(
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """
    Request export of all user data in a machine-readable format.
    
    Args:
        background_tasks: FastAPI background tasks handler
        current_user: Authenticated user
        
    Returns:
        DataExportRequest: Export request details including download URL when ready
    """
    try:
        # Create export request
        export_request = await privacy_service.create_export_request(
            user_id=current_user.id
        )
        
        # Schedule export task
        background_tasks.add_task(
            privacy_service.generate_data_export,
            request_id=export_request.id
        )
        
        return export_request
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/export/{request_id}", response_model=DataExportRequest)
async def get_export_status(
    request_id: str,
    current_user = Depends(get_current_user)
):
    """
    Check the status of a data export request and get download URL if ready.
    
    Args:
        request_id: ID of the export request
        current_user: Authenticated user
        
    Returns:
        DataExportRequest: Current status and download URL if ready
    """
    try:
        request = await privacy_service.get_export_request(request_id)
        if request.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this request")
        return request
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/consent/log", response_model=List[ConsentLog])
async def get_consent_history(
    current_user = Depends(get_current_user)
):
    """
    Get the history of consent preference changes.
    
    Args:
        current_user: Authenticated user
        
    Returns:
        List[ConsentLog]: History of consent changes with timestamps
    """
    try:
        return await privacy_service.get_consent_logs(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/data/anonymize")
async def anonymize_account(
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """
    Anonymize the user's account instead of deleting it.
    Replaces personal data with anonymous identifiers while preserving analytics data.
    
    Args:
        background_tasks: FastAPI background tasks handler
        current_user: Authenticated user
        
    Returns:
        dict: Confirmation of anonymization request
    """
    try:
        # Schedule anonymization
        background_tasks.add_task(
            privacy_service.anonymize_user_data,
            user_id=current_user.id
        )
        
        return {
            "message": "Account anonymization scheduled",
            "status": "pending"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/data/cookies")
async def delete_cookies(
    current_user = Depends(get_current_user)
):
    """
    Delete all non-essential cookies for the user.
    
    Args:
        current_user: Authenticated user
        
    Returns:
        dict: Confirmation of cookie deletion
    """
    try:
        await privacy_service.delete_user_cookies(current_user.id)
        return {
            "message": "Non-essential cookies deleted",
            "status": "completed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 