"""Open Policy Agent (OPA) middleware for FastAPI."""
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type, Union

from fastapi import Depends, HTTPException, Request, status
from pydantic import BaseModel

from middleware.auth0 import get_current_user
from services.opa_service import opa_service


class PermissionDependency:
    """Dependency for checking permissions with OPA."""

    def __init__(
        self,
        action: str,
        resource: str,
        resource_id_path_param: Optional[str] = None,
        resource_owner_field: Optional[str] = None,
    ):
        """Initialize the permission dependency.

        Args:
            action: The action to check permission for.
            resource: The resource type.
            resource_id_path_param: The path parameter name for the resource ID.
            resource_owner_field: The field name in the resource that identifies the owner.
        """
        self.action = action
        self.resource = resource
        self.resource_id_path_param = resource_id_path_param
        self.resource_owner_field = resource_owner_field

    async def __call__(
        self,
        request: Request,
        user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        """Check if the user has permission to perform the action on the resource.

        Args:
            request: The FastAPI request object.
            user: The current user.

        Returns:
            The user if they have permission.

        Raises:
            HTTPException: If the user doesn't have permission.
        """
        resource_id = None
        context = {}

        # Extract resource ID from path parameters if specified
        if self.resource_id_path_param and self.resource_id_path_param in request.path_params:
            resource_id = request.path_params[self.resource_id_path_param]

        # Add resource owner information to context if available
        if self.resource_owner_field and hasattr(request, "state") and hasattr(request.state, "resource"):
            resource = getattr(request.state, "resource", None)
            if resource and hasattr(resource, self.resource_owner_field):
                context["resource_owner"] = getattr(resource, self.resource_owner_field)

        # Check permission with OPA
        has_permission = await opa_service.check_permission(
            user=user,
            action=self.action,
            resource=self.resource,
            resource_id=resource_id,
            context=context,
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {self.action} on {self.resource}",
            )

        return user


def require_permission(
    action: str,
    resource: str,
    resource_id_path_param: Optional[str] = None,
    resource_owner_field: Optional[str] = None,
):
    """Create a dependency that requires permission to perform an action on a resource.

    Args:
        action: The action to check permission for.
        resource: The resource type.
        resource_id_path_param: The path parameter name for the resource ID.
        resource_owner_field: The field name in the resource that identifies the owner.

    Returns:
        A dependency function that checks permission.
    """
    return PermissionDependency(
        action=action,
        resource=resource,
        resource_id_path_param=resource_id_path_param,
        resource_owner_field=resource_owner_field,
    )


class ResourceFilterDependency:
    """Dependency for filtering resources based on permissions."""

    def __init__(
        self,
        action: str,
        resource: str,
    ):
        """Initialize the resource filter dependency.

        Args:
            action: The action to check permission for.
            resource: The resource type.
        """
        self.action = action
        self.resource = resource

    async def __call__(
        self,
        request: Request,
        user: Dict[str, Any] = Depends(get_current_user),
    ) -> List[str]:
        """Get the resources that the user has permission to access.

        Args:
            request: The FastAPI request object.
            user: The current user.

        Returns:
            A list of resource IDs that the user has permission to access.
        """
        # Get allowed resources from OPA
        allowed_resources = await opa_service.get_allowed_resources(
            user=user,
            action=self.action,
            resource=self.resource,
        )

        return allowed_resources


def filter_resources(
    action: str,
    resource: str,
):
    """Create a dependency that filters resources based on permissions.

    Args:
        action: The action to check permission for.
        resource: The resource type.

    Returns:
        A dependency function that returns allowed resource IDs.
    """
    return ResourceFilterDependency(
        action=action,
        resource=resource,
    )


class BulkPermissionDependency:
    """Dependency for checking multiple permissions at once."""

    def __init__(
        self,
        permissions: List[Dict[str, str]],
    ):
        """Initialize the bulk permission dependency.

        Args:
            permissions: A list of permission requests, each with action, resource, and optional resource_id.
        """
        self.permissions = permissions

    async def __call__(
        self,
        request: Request,
        user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, bool]:
        """Check multiple permissions at once.

        Args:
            request: The FastAPI request object.
            user: The current user.

        Returns:
            A dictionary mapping permission keys to boolean results.
        """
        # Check bulk permissions with OPA
        permission_results = await opa_service.check_bulk_permissions(
            user=user,
            permissions=self.permissions,
        )

        return permission_results


def check_bulk_permissions(
    permissions: List[Dict[str, str]],
):
    """Create a dependency that checks multiple permissions at once.

    Args:
        permissions: A list of permission requests, each with action, resource, and optional resource_id.

    Returns:
        A dependency function that returns permission results.
    """
    return BulkPermissionDependency(
        permissions=permissions,
    )


def permission_required(
    action: str,
    resource: str,
    resource_id_path_param: Optional[str] = None,
    resource_owner_field: Optional[str] = None,
):
    """Decorator for route handlers that require permission.

    Args:
        action: The action to check permission for.
        resource: The resource type.
        resource_id_path_param: The path parameter name for the resource ID.
        resource_owner_field: The field name in the resource that identifies the owner.

    Returns:
        A decorator function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request and user from kwargs
            request = kwargs.get("request")
            user = kwargs.get("user")

            if not request or not user:
                raise ValueError("Request and user must be provided as kwargs")

            resource_id = None
            context = {}

            # Extract resource ID from path parameters if specified
            if resource_id_path_param and resource_id_path_param in kwargs:
                resource_id = kwargs[resource_id_path_param]

            # Add resource owner information to context if available
            if resource_owner_field and hasattr(request, "state") and hasattr(request.state, "resource"):
                resource = getattr(request.state, "resource", None)
                if resource and hasattr(resource, resource_owner_field):
                    context["resource_owner"] = getattr(resource, resource_owner_field)

            # Check permission with OPA
            has_permission = await opa_service.check_permission(
                user=user,
                action=action,
                resource=resource,
                resource_id=resource_id,
                context=context,
            )

            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {action} on {resource}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
