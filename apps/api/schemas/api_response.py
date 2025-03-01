"""
Standardized API response format for Maily API.
"""
from typing import TypeVar, Generic, Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field
from pydantic.generics import GenericModel
from enum import Enum

T = TypeVar('T')  # Generic type for response data

class ResponseStatus(str, Enum):
    """API response status values."""
    SUCCESS = "success"
    ERROR = "error"

class ErrorResponse(BaseModel):
    """Error details for API responses."""
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ApiResponse(GenericModel, Generic[T]):
    """Standard API response wrapper for all Maily API endpoints."""
    status: ResponseStatus = ResponseStatus.SUCCESS
    data: Optional[T] = None
    error: Optional[ErrorResponse] = None
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def success(cls, data: Any = None, metadata: Optional[Dict[str, Any]] = None) -> "ApiResponse":
        """Create a success response.

        Args:
            data: Response payload
            metadata: Optional metadata

        Returns:
            ApiResponse: Formatted success response
        """
        return cls(
            status=ResponseStatus.SUCCESS,
            data=data,
            metadata=metadata
        )

    @classmethod
    def error(
        cls,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "ApiResponse":
        """Create an error response.

        Args:
            error_code: Error code string
            message: Error message
            details: Optional error details
            metadata: Optional metadata

        Returns:
            ApiResponse: Formatted error response
        """
        return cls(
            status=ResponseStatus.ERROR,
            error=ErrorResponse(
                error_code=error_code,
                message=message,
                details=details
            ),
            metadata=metadata
        )

# Common response types
class PaginatedResponseMetadata(BaseModel):
    """Metadata for paginated responses."""
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_more: bool = Field(default=False, description="Whether there are more pages")

class PaginatedResponse(ApiResponse, Generic[T]):
    """Paginated API response for list endpoints."""
    metadata: PaginatedResponseMetadata

    @classmethod
    def paginated(
        cls,
        data: List[T],
        page: int,
        page_size: int,
        total_items: int
    ) -> "PaginatedResponse[T]":
        """Create a paginated response.

        Args:
            data: List of items for the current page
            page: Current page number (1-indexed)
            page_size: Number of items per page
            total_items: Total number of items across all pages

        Returns:
            PaginatedResponse: Formatted paginated response
        """
        total_pages = (total_items + page_size - 1) // page_size if page_size > 0 else 0
        has_more = page < total_pages

        return cls(
            status=ResponseStatus.SUCCESS,
            data=data,
            metadata=PaginatedResponseMetadata(
                page=page,
                page_size=page_size,
                total_items=total_items,
                total_pages=total_pages,
                has_more=has_more
            )
        )
