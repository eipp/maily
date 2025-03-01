"""
Standardized response utility module.

This module provides utility functions for creating standardized API responses
with consistent formatting across all endpoints.
"""

from fastapi import status
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional, List, Union


def standard_response(
    data: Any,
    status_code: int = status.HTTP_200_OK,
    message: Optional[str] = None
) -> JSONResponse:
    """
    Create standardized response with consistent format.

    Args:
        data: Response data
        status_code: HTTP status code
        message: Optional message

    Returns:
        Standardized JSON response
    """
    response = {
        "data": data,
        "status": "success" if status_code < 400 else "error"
    }

    if message:
        response["message"] = message

    return JSONResponse(
        status_code=status_code,
        content=response
    )


def error_response(
    detail: Union[str, List[Dict[str, Any]]],
    status_code: int = status.HTTP_400_BAD_REQUEST,
    error_code: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None
) -> JSONResponse:
    """
    Create standardized error response.

    Args:
        detail: Error detail or validation errors
        status_code: HTTP status code
        error_code: Optional error code
        headers: Optional HTTP headers

    Returns:
        Standardized JSON error response
    """
    error = {
        "detail": detail
    }

    if error_code:
        error["code"] = error_code

    response = {
        "status": "error",
        "error": error
    }

    return JSONResponse(
        status_code=status_code,
        content=response,
        headers=headers or {}
    )


def paginated_response(
    items: List[Any],
    page: int,
    limit: int,
    total: int,
    status_code: int = status.HTTP_200_OK,
    message: Optional[str] = None
) -> JSONResponse:
    """
    Create standardized paginated response.

    Args:
        items: List of items
        page: Current page number
        limit: Items per page
        total: Total number of items
        status_code: HTTP status code
        message: Optional message

    Returns:
        Standardized JSON response with pagination
    """
    # Calculate total pages
    total_pages = (total + limit - 1) // limit if limit > 0 else 0

    response = {
        "data": items,
        "status": "success",
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": total_pages
        }
    }

    if message:
        response["message"] = message

    return JSONResponse(
        status_code=status_code,
        content=response
    )


def validation_error_response(
    errors: List[Dict[str, Any]],
    status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY
) -> JSONResponse:
    """
    Create standardized validation error response.

    Args:
        errors: List of validation errors
        status_code: HTTP status code

    Returns:
        Standardized JSON error response
    """
    return error_response(
        detail=errors,
        status_code=status_code,
        error_code="validation_error"
    )


def not_found_response(
    resource_type: str,
    resource_id: str
) -> JSONResponse:
    """
    Create standardized not found error response.

    Args:
        resource_type: Type of resource (e.g., "Campaign")
        resource_id: ID of the resource

    Returns:
        Standardized JSON error response
    """
    return error_response(
        detail=f"{resource_type} with ID {resource_id} not found",
        status_code=status.HTTP_404_NOT_FOUND,
        error_code="not_found"
    )


def unauthorized_response(
    detail: str = "Authentication required"
) -> JSONResponse:
    """
    Create standardized unauthorized error response.

    Args:
        detail: Error detail

    Returns:
        Standardized JSON error response
    """
    return error_response(
        detail=detail,
        status_code=status.HTTP_401_UNAUTHORIZED,
        error_code="unauthorized",
        headers={"WWW-Authenticate": "Bearer"}
    )


def forbidden_response(
    detail: str = "You do not have permission to perform this action"
) -> JSONResponse:
    """
    Create standardized forbidden error response.

    Args:
        detail: Error detail

    Returns:
        Standardized JSON error response
    """
    return error_response(
        detail=detail,
        status_code=status.HTTP_403_FORBIDDEN,
        error_code="forbidden"
    )


def too_many_requests_response(
    detail: str = "Rate limit exceeded",
    retry_after: int = 60
) -> JSONResponse:
    """
    Create standardized rate limit error response.

    Args:
        detail: Error detail
        retry_after: Seconds until rate limit resets

    Returns:
        Standardized JSON error response
    """
    return error_response(
        detail=detail,
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        error_code="rate_limit_exceeded",
        headers={"Retry-After": str(retry_after)}
    )


def internal_error_response(
    detail: str = "An internal server error occurred"
) -> JSONResponse:
    """
    Create standardized internal server error response.

    Args:
        detail: Error detail

    Returns:
        Standardized JSON error response
    """
    return error_response(
        detail=detail,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="internal_error"
    )
