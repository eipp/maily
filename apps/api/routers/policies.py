"""Policy management router for OPA."""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel

from middleware.auth0 import admin_with_mfa
from services.opa_service import opa_service

router = APIRouter(prefix="/policies", tags=["policies"])


class PolicyResponse(BaseModel):
    """Policy response model."""

    name: str
    content: str


class PolicyRequest(BaseModel):
    """Policy request model."""

    name: str
    content: str


@router.get("/{policy_name}", response_model=PolicyResponse)
async def get_policy(
    policy_name: str = Path(..., description="The name of the policy"),
    _: Dict[str, Any] = Depends(admin_with_mfa),
):
    """Get a policy by name.

    Args:
        policy_name: The name of the policy.
        _: The current admin user with MFA.

    Returns:
        The policy.
    """
    content = await opa_service.get_policy(policy_name)
    return PolicyResponse(name=policy_name, content=content)


@router.put("/{policy_name}", status_code=status.HTTP_204_NO_CONTENT)
async def upload_policy(
    policy: PolicyRequest,
    policy_name: str = Path(..., description="The name of the policy"),
    _: Dict[str, Any] = Depends(admin_with_mfa),
):
    """Upload a policy.

    Args:
        policy: The policy request.
        policy_name: The name of the policy.
        _: The current admin user with MFA.
    """
    if policy.name != policy_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Policy name in path must match policy name in request body",
        )

    await opa_service.upload_policy(policy_name, policy.content)


@router.delete("/{policy_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(
    policy_name: str = Path(..., description="The name of the policy"),
    _: Dict[str, Any] = Depends(admin_with_mfa),
):
    """Delete a policy.

    Args:
        policy_name: The name of the policy.
        _: The current admin user with MFA.
    """
    await opa_service.delete_policy(policy_name)


@router.post("/check", response_model=Dict[str, bool])
async def check_permissions(
    permissions: List[Dict[str, Any]],
    user: Dict[str, Any] = Depends(admin_with_mfa),
):
    """Check multiple permissions at once.

    Args:
        permissions: A list of permission requests, each with action, resource, and optional resource_id.
        user: The current admin user with MFA.

    Returns:
        A dictionary mapping permission keys to boolean results.
    """
    return await opa_service.check_bulk_permissions(user, permissions)
