
"""
API Error Handling Framework

Provides a standardized framework for error handling across the API,
ensuring consistent error responses, logging, and monitoring.
"""

import sys
import time
import traceback
import logging
import uuid
from typing import Any, Dict, List, Optional, Type, Union, Callable
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

# Error response model
class ErrorDetail(BaseModel):
    """Detailed information about a specific error."""
    code: str
    message: str
    field: Optional[str] = None
    info: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standardized error response model."""
    error: bool = True
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str
    status_code: int
    error_type: str
    timestamp: float = Field(default_factory=time.time)
    details: Optional[List[ErrorDetail]] = None
    trace_id: Optional[str] = None
    documentation_url: Optional[str] = None


# Base error class
class APIError(Exception):
    """Base class for all API errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_type: str = "internal_server_error"
    message: str = "An unexpected error occurred"

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[List[Dict[str, Any]]] = None,
        status_code: Optional[int] = None,
        error_type: Optional[str] = None
    ):
        """
        Initialize the API error.

        Args:
            message: Human-readable error message
            details: List of error details
            status_code: HTTP status code
            error_type: Error type identifier
        """
        self.message = message or self.message
        self.details = details or []
        self.status_code = status_code or self.status_code
        self.error_type = error_type or self.error_type
        super().__init__(self.message)


# Specific error classes
class BadRequestError(APIError):
    """Error for invalid requests."""
    status_code = status.HTTP_400_BAD_REQUEST
    error_type = "bad_request"
    message = "The request was invalid"


class UnauthorizedError(APIError):
    """Error for authentication failures."""
    status_code = status.HTTP_401_UNAUTHORIZED
    error_type = "unauthorized"
    message = "Authentication is required"


class ForbiddenError(APIError):
    """Error for authorization failures."""
    status_code = status.HTTP_403_FORBIDDEN
    error_type = "forbidden"
    message = "You do not have permission to perform this action"


class NotFoundError(APIError):
    """Error for resources that don't exist."""
    status_code = status.HTTP_404_NOT_FOUND
    error_type = "not_found"
    message = "The requested resource was not found"


class ConflictError(APIError):
    """Error for resource conflicts."""
    status_code = status.HTTP_409_CONFLICT
    error_type = "conflict"
    message = "The request conflicts with the current state"


class TooManyRequestsError(APIError):
    """Error for rate limiting."""
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    error_type = "too_many_requests"
    message = "Too many requests, please try again later"


class InternalServerError(APIError):
    """Error for unexpected server errors."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_type = "internal_server_error"
    message = "An unexpected error occurred"


class ServiceUnavailableError(APIError):
    """Error for unavailable services."""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_type = "service_unavailable"
    message = "The service is currently unavailable"


class DatabaseError(APIError):
    """Error for database issues."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_type = "database_error"
    message = "A database error occurred"


class ValidationError(BadRequestError):
    """Error for validation failures."""
    error_type = "validation_error"
    message = "Validation error"


# Mapping from HTTP status codes to error classes
STATUS_CODE_TO_ERROR = {
    400: BadRequestError,
    401: UnauthorizedError,
    403: ForbiddenError,
    404: NotFoundError,
    409: ConflictError,
    429: TooManyRequestsError,
    500: InternalServerError,
    503: ServiceUnavailableError
}


# Error handler class
class ErrorHandler:
    """
    Centralized error handler for API errors.

    This class provides methods for registering error handlers with a FastAPI app
    and converting various types of errors to standardized error responses.
    """

    def __init__(
        self,
        app: FastAPI,
        include_exception_handlers: bool = True,
        include_debug_info: bool = False,
        error_documentation_base_url: Optional[str] = None,
        on_error_callbacks: List[Callable[[Request, Exception], None]] = None
    ):
        """
        Initialize the error handler.

        Args:
            app: FastAPI application to register handlers with
            include_exception_handlers: Whether to register exception handlers
            include_debug_info: Whether to include debug info in responses
            error_documentation_base_url: Base URL for error documentation
            on_error_callbacks: Callbacks to execute when errors occur
        """
        self.app = app
        self.include_debug_info = include_debug_info
        self.error_documentation_base_url = error_documentation_base_url
        self.on_error_callbacks = on_error_callbacks or []

        if include_exception_handlers:
            self.register_exception_handlers()

    def register_exception_handlers(self):
        """Register exception handlers with the FastAPI app."""
        # Register handler for APIError (and subclasses)
        self.app.exception_handler(APIError)(self.api_error_handler)

        # Register handler for RequestValidationError
        self.app.exception_handler(RequestValidationError)(self.validation_error_handler)

        # Register handler for StarletteHTTPException
        self.app.exception_handler(StarletteHTTPException)(self.http_exception_handler)

        # Register handler for generic exceptions
        self.app.exception_handler(Exception)(self.generic_exception_handler)

    async def api_error_handler(self, request: Request, exc: APIError) -> JSONResponse:
        """
        Handler for APIError exceptions.

        Args:
            request: The request that caused the exception
            exc: The APIError exception

        Returns:
            Standardized JSON response
        """
        return await self._create_error_response(request, exc)

    async def validation_error_handler(self, request: Request, exc: RequestValidationError) -> JSONResponse:
        """
        Handler for RequestValidationError exceptions.

        Args:
            request: The request that caused the exception
            exc: The RequestValidationError exception

        Returns:
            Standardized JSON response
        """
        # Convert validation errors to our format
        details = []
        for error in exc.errors():
            location = error.get("loc", [])
            field = location[-1] if location else None
            type_str = error.get("type", "")
            msg = error.get("msg", "")

            details.append(
                ErrorDetail(
                    code=f"validation.{type_str}",
                    message=msg,
                    field=str(field) if field is not None else None
                )
            )

        error = ValidationError(
            message="Request validation failed",
            details=[detail.dict() for detail in details]
        )

        return await self._create_error_response(request, error)

    async def http_exception_handler(self, request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """
        Handler for HTTPException exceptions.

        Args:
            request: The request that caused the exception
            exc: The HTTPException exception

        Returns:
            Standardized JSON response
        """
        # Map status code to appropriate error class
        error_class = STATUS_CODE_TO_ERROR.get(exc.status_code, APIError)

        error = error_class(
            message=str(exc.detail),
            status_code=exc.status_code
        )

        return await self._create_error_response(request, error)

    async def generic_exception_handler(self, request: Request, exc: Exception) -> JSONResponse:
        """
        Handler for generic exceptions.

        Args:
            request: The request that caused the exception
            exc: The exception

        Returns:
            Standardized JSON response
        """
        # Log the full exception for unexpected errors
        logger.exception(f"Unhandled exception: {str(exc)}")

        error = InternalServerError(
            message="An unexpected error occurred"
        )

        return await self._create_error_response(request, error, exc)

    async def _create_error_response(
        self,
        request: Request,
        error: APIError,
        original_exception: Optional[Exception] = None
    ) -> JSONResponse:
        """
        Create a standardized error response.

        Args:
            request: The request that caused the error
            error: The APIError
            original_exception: The original exception if different from error

        Returns:
            Standardized JSON response
        """
        # Generate a trace ID
        trace_id = str(uuid.uuid4())

        # Execute error callbacks
        for callback in self.on_error_callbacks:
            try:
                callback(request, original_exception or error)
            except Exception as callback_exc:
                logger.error(f"Error callback failed: {str(callback_exc)}")

        # Create error details
        details = None
        if error.details:
            details = [
                ErrorDetail(**detail) if isinstance(detail, dict) else detail
                for detail in error.details
            ]

        # Create error response
        error_response = ErrorResponse(
            message=error.message,
            status_code=error.status_code,
            error_type=error.error_type,
            trace_id=trace_id,
            details=details
        )

        # Add documentation URL if available
        if self.error_documentation_base_url and error.error_type:
            error_response.documentation_url = f"{self.error_documentation_base_url}/{error.error_type}"

        # Add debug info if enabled
        if self.include_debug_info and original_exception:
            exc_info = sys.exc_info()
            if exc_info[2]:
                error_response.details = error_response.details or []
                error_stack = traceback.format_exception(*exc_info)
                error_response.details.append(
                    ErrorDetail(
                        code="debug.stack_trace",
                        message="Server error stack trace",
                        info={"stack": error_stack}
                    )
                )

        # Log the error
        log_extra = {
            "trace_id": trace_id,
            "status_code": error.status_code,
            "error_type": error.error_type,
            "path": request.url.path,
            "method": request.method
        }

        if error.status_code >= 500:
            logger.error(
                f"{error.error_type}: {error.message}",
                extra=log_extra
            )
        else:
            logger.warning(
                f"{error.error_type}: {error.message}",
                extra=log_extra
            )

        # Return JSON response
        return JSONResponse(
            status_code=error.status_code,
            content=error_response.dict(exclude_none=True)
        )


# Convenience function to register error handlers
def setup_error_handling(
    app: FastAPI,
    include_debug_info: bool = False,
    error_documentation_base_url: Optional[str] = None,
    on_error_callbacks: List[Callable[[Request, Exception], None]] = None
) -> ErrorHandler:
    """
    Set up error handling for a FastAPI application.

    Args:
        app: FastAPI application
        include_debug_info: Whether to include debug info in responses
        error_documentation_base_url: Base URL for error documentation
        on_error_callbacks: Callbacks to execute when errors occur

    Returns:
        The configured ErrorHandler instance
    """
    return ErrorHandler(
        app=app,
        include_debug_info=include_debug_info,
        error_documentation_base_url=error_documentation_base_url,
        on_error_callbacks=on_error_callbacks
    )
