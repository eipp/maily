"""API key routes for managing API keys."""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from database.session import get_db
from middleware.auth_middleware import get_current_user
from services.api_key_service import (
    create_api_key,
    revoke_api_key,
    list_api_keys
)
from packages.error_handling.python.error import ResourceNotFoundError, DatabaseError, UnauthorizedError

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


class ApiKeyCreate(BaseModel):
    """Model for creating a new API key."""
    name: str = Field(..., description="A name for the API key")
    expires_in_days: int = Field(365, description="Number of days until the key expires")


class ApiKeyResponse(BaseModel):
    """Response model for API key endpoints."""
    id: str
    name: str
    created_at: Any
    expires_at: Any
    is_active: bool
    last_used_at: Any = None


class ApiKeyCreateResponse(ApiKeyResponse):
    """Response model for API key creation endpoint."""
    api_key: str


@router.post("", response_model=ApiKeyCreateResponse)
async def create_api_key_endpoint(
    api_key_data: ApiKeyCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new API key for the current user.

    Args:
        api_key_data: The API key data.
        current_user: The current user.
        db: The database session.

    Returns:
        The created API key.
    """
    try:
        api_key = await create_api_key(
            user_id=current_user["id"],
            name=api_key_data.name,
            expires_in_days=api_key_data.expires_in_days,
            db=db
        )
        return api_key
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[ApiKeyResponse])
async def list_api_keys_endpoint(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all API keys for the current user.

    Args:
        current_user: The current user.
        db: The database session.

    Returns:
        A list of API keys.
    """
    try:
        api_keys = await list_api_keys(
            user_id=current_user["id"],
            db=db
        )
        return api_keys
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{api_key_id}")
async def revoke_api_key_endpoint(
    api_key_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Revoke an API key.

    Args:
        api_key_id: The ID of the API key to revoke.
        current_user: The current user.
        db: The database session.

    Returns:
        A success message.
    """
    try:
        await revoke_api_key(
            api_key_id=api_key_id,
            user_id=current_user["id"],
            db=db
        )
        return {"message": "API key revoked successfully"}
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))
