"""Standardized auth router for user management and authentication."""
from typing import Any, Dict, List, Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status, Request
from pydantic import BaseModel, Field, EmailStr

from middleware.standardized_auth import require_auth, require_admin, optional_auth
from services.api_key_service import create_api_key, list_api_keys, revoke_api_key
from services.auth0_service import auth0_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


class ApiKeyCreateRequest(BaseModel):
    """API key creation request model."""
    name: str = Field(..., description="A friendly name for the API key")
    scopes: Optional[List[str]] = Field(None, description="List of scopes for the API key")
    expires_in_days: Optional[int] = Field(90, description="Number of days until the key expires")


class ApiKeyResponse(BaseModel):
    """API key response model."""
    id: str
    name: str
    api_key: Optional[str] = None
    scopes: List[str]
    created_at: Any
    expires_at: Any
    is_active: bool
    last_used_at: Optional[Any] = None


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: EmailStr
    name: Optional[str] = None
    is_admin: bool = False
    auth_method: Optional[str] = None


class RoleResponse(BaseModel):
    """Role response model."""
    id: str
    name: str
    description: Optional[str] = None


class RoleRequest(BaseModel):
    """Role request model."""
    name: str
    description: Optional[str] = None


class RoleAssignmentRequest(BaseModel):
    """Role assignment request model."""
    role_ids: List[str]


@router.get("/users/me", response_model=UserResponse)
async def get_current_user_info(user: Dict[str, Any] = Depends(require_auth)):
    """Get the current user's information.

    Args:
        user: The current user.

    Returns:
        The user information.
    """
    return user


@router.get("/api-keys", response_model=List[ApiKeyResponse])
async def get_api_keys(user: Dict[str, Any] = Depends(require_auth)):
    """List all API keys for the authenticated user.

    Args:
        user: The authenticated user.

    Returns:
        List of API keys.
    """
    try:
        return await list_api_keys(user["id"])
    except Exception as e:
        logger.error(f"Error listing API keys: {str(e)}")
        raise HTTPException(status_code=500, detail="Error listing API keys")


@router.post("/api-keys", response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key_endpoint(
    api_key_data: ApiKeyCreateRequest,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Create a new API key for the authenticated user.

    Args:
        api_key_data: API key creation data.
        user: The authenticated user.

    Returns:
        The created API key.
    """
    try:
        return await create_api_key(
            user_id=user["id"],
            name=api_key_data.name,
            scopes=api_key_data.scopes,
            expires_in_days=api_key_data.expires_in_days
        )
    except Exception as e:
        logger.error(f"Error creating API key: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating API key")


@router.delete("/api-keys/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key_endpoint(
    api_key_id: str = Path(..., description="The ID of the API key to revoke"),
    user: Dict[str, Any] = Depends(require_auth)
):
    """Revoke an API key.

    Args:
        api_key_id: The ID of the API key to revoke.
        user: The authenticated user.
    """
    try:
        await revoke_api_key(api_key_id, user["id"])
    except Exception as e:
        logger.error(f"Error revoking API key: {str(e)}")
        raise HTTPException(status_code=500, detail="Error revoking API key")


# User management endpoints
@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str = Path(..., description="The Auth0 user ID"),
    admin: Dict[str, Any] = Depends(require_admin),
):
    """Get a user by ID.

    Args:
        user_id: The Auth0 user ID.
        admin: The current admin user.

    Returns:
        The user information.
    """
    try:
        return await auth0_service.get_user(user_id)
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        raise HTTPException(status_code=404, detail="User not found")


@router.get("/users/{user_id}/roles", response_model=List[RoleResponse])
async def get_user_roles(
    user_id: str = Path(..., description="The Auth0 user ID"),
    admin: Dict[str, Any] = Depends(require_admin),
):
    """Get a user's roles.

    Args:
        user_id: The Auth0 user ID.
        admin: The current admin user.

    Returns:
        The user's roles.
    """
    try:
        return await auth0_service.get_user_roles(user_id)
    except Exception as e:
        logger.error(f"Error getting user roles: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting user roles")


@router.post("/users/{user_id}/roles", status_code=status.HTTP_204_NO_CONTENT)
async def assign_roles_to_user(
    role_assignment: RoleAssignmentRequest,
    user_id: str = Path(..., description="The Auth0 user ID"),
    admin: Dict[str, Any] = Depends(require_admin),
):
    """Assign roles to a user.

    Args:
        role_assignment: The role assignment request.
        user_id: The Auth0 user ID.
        admin: The current admin user.
    """
    try:
        await auth0_service.assign_roles_to_user(user_id, role_assignment.role_ids)
    except Exception as e:
        logger.error(f"Error assigning roles to user: {str(e)}")
        raise HTTPException(status_code=500, detail="Error assigning roles to user")


@router.delete("/users/{user_id}/roles", status_code=status.HTTP_204_NO_CONTENT)
async def remove_roles_from_user(
    role_assignment: RoleAssignmentRequest,
    user_id: str = Path(..., description="The Auth0 user ID"),
    admin: Dict[str, Any] = Depends(require_admin),
):
    """Remove roles from a user.

    Args:
        role_assignment: The role assignment request.
        user_id: The Auth0 user ID.
        admin: The current admin user.
    """
    try:
        await auth0_service.remove_roles_from_user(user_id, role_assignment.role_ids)
    except Exception as e:
        logger.error(f"Error removing roles from user: {str(e)}")
        raise HTTPException(status_code=500, detail="Error removing roles from user")


@router.get("/roles", response_model=List[RoleResponse])
async def get_roles(admin: Dict[str, Any] = Depends(require_admin)):
    """Get all roles.

    Args:
        admin: The current admin user.

    Returns:
        The roles.
    """
    try:
        return await auth0_service.get_roles()
    except Exception as e:
        logger.error(f"Error getting roles: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting roles")


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role: RoleRequest,
    admin: Dict[str, Any] = Depends(require_admin),
):
    """Create a role.

    Args:
        role: The role request.
        admin: The current admin user.

    Returns:
        The created role.
    """
    try:
        return await auth0_service.create_role(role.name, role.description)
    except Exception as e:
        logger.error(f"Error creating role: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating role")


# Admin endpoints
@router.get("/admin/users", response_model=List[UserResponse])
async def list_users(admin: Dict[str, Any] = Depends(require_admin)):
    """List all users (admin only).

    Args:
        admin: The admin user.

    Returns:
        List of users.
    """
    try:
        return await auth0_service.list_users()
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(status_code=500, detail="Error listing users")
