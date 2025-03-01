"""
Centralized error handling system for Maily API.

This module implements a comprehensive error handling system with:
- Standardized error formats with correlation IDs
- Error logging with structured metadata
- Exception categorization and mapping
- Automatic retry capabilities for transient errors
- Error reporting to monitoring systems
"""

import os
import sys
import uuid
import traceback
import logging
import json
from typing import Dict, Any, Optional, List, Type, Callable, TypeVar, Union
from functools import wraps
from datetime import datetime

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from prometheus_client import Counter

# Configure logging
logger = logging.getLogger(__name__)

# Error metrics
ERROR_COUNTER = Counter(
    'api_error_total',
    'Total number of API errors',
    ['error_type', 'error_code', 'endpoint']
)

# Error environment configuration
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
SENTRY_DSN = os.environ.get("SENTRY_DSN")
ERROR_MONITORING_ENABLED = os.environ.get("ERROR_MONITORING_ENABLED", "false").lower() == "true"

# Initialize error monitoring with Sentry if enabled
if ERROR_MONITORING_ENABLED and SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=ENVIRONMENT,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,
    )

# Error severity levels
class ErrorSeverity:
    """Error severity levels"""
    CRITICAL = "critical"  # System is unusable, immediate action required
    ERROR = "error"        # Error that prevents operation from completing
    WARNING = "warning"    # Something unexpected happened but operation completed
    INFO = "info"          # Informational message about an error condition


# Standard error response model
class ErrorResponse(BaseModel):
    """Standardized error response format."""
    status: str = Field("error", description="Error status indicator")
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    correlation_id: str = Field(..., description="Unique error correlation ID")
    timestamp: str = Field(..., description="ISO 8601 timestamp of when the error occurred")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    debug_info: Optional[Dict[str, Any]] = Field(None, description="Debug information (development only)")


# Base exception class for all Maily errors
class MailyError(Exception):
    """Base class for all Maily exceptions."""

    def __init__(
        self,
        message: str,
        code: str = "internal_error",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
        severity: str = ErrorSeverity.ERROR,
        is_retryable: bool = False,
    ):
        """
        Initialize error with standard attributes.

        Args:
            message: Human-readable error message
            code: Error code
            status_code: HTTP status code
            details: Additional error details
            severity: Error severity level
            is_retryable: Whether the error can be retried
        """
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        self.severity = severity
        self.is_retryable = is_retryable
        self.correlation_id = str(uuid.uuid4())
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON response."""
        result = {
            "status": "error",
            "code": self.code,
            "message": self.message,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
        }

        if self.details:
            result["details"] = self.details

        # Only include debug info in development environment
        if ENVIRONMENT in ["development", "test"]:
            result["debug_info"] = {
                "exception_type": self.__class__.__name__,
                "status_code": self.status_code,
                "severity": self.severity,
                "is_retryable": self.is_retryable,
                "traceback": traceback.format_exc(),
            }

        return result


# Specific error classes
class ValidationError(MailyError):
    """Validation error for invalid input data."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="validation_error",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
            severity=ErrorSeverity.WARNING,
            is_retryable=False,
        )


class NotFoundError(MailyError):
    """Error for resources that cannot be found."""

    def __init__(self, message: str, resource_type: str, resource_id: str):
        super().__init__(
            message=message,
            code="not_found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource_type": resource_type, "resource_id": resource_id},
            severity=ErrorSeverity.WARNING,
            is_retryable=False,
        )


class AuthenticationError(MailyError):
    """Authentication error for invalid credentials."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="authentication_error",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
            severity=ErrorSeverity.WARNING,
            is_retryable=False,
        )


class AuthorizationError(MailyError):
    """Authorization error for insufficient permissions."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="authorization_error",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
            severity=ErrorSeverity.WARNING,
            is_retryable=False,
        )


class RateLimitError(MailyError):
    """Rate limit exceeded error."""

    def __init__(self, message: str, retry_after: int):
        super().__init__(
            message=message,
            code="rate_limit_exceeded",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={"retry_after": retry_after},
            severity=ErrorSeverity.WARNING,
            is_retryable=True,
        )


class ServiceUnavailableError(MailyError):
    """Service unavailable error for temporary outages."""

    def __init__(self, message: str, retry_after: Optional[int] = None):
        details = {}
        if retry_after is not None:
            details["retry_after"] = retry_after

        super().__init__(
            message=message,
            code="service_unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details,
            severity=ErrorSeverity.ERROR,
            is_retryable=True,
        )


class DatabaseError(MailyError):
    """Database error."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        details = {}
        if original_error is not None and ENVIRONMENT in ["development", "test"]:
            details["original_error"] = str(original_error)

        super().__init__(
            message=message,
            code="database_error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            severity=ErrorSeverity.ERROR,
            is_retryable=True,
        )


class ThirdPartyError(MailyError):
    """Error from third-party service integration."""

    def __init__(
        self,
        message: str,
        service_name: str,
        original_error: Optional[Exception] = None,
        status_code: int = status.HTTP_502_BAD_GATEWAY,
    ):
        details = {"service": service_name}
        if original_error is not None and ENVIRONMENT in ["development", "test"]:
            details["original_error"] = str(original_error)

        super().__init__(
            message=message,
            code="third_party_error",
            status_code=status_code,
            details=details,
            severity=ErrorSeverity.ERROR,
            is_retryable=True,
        )


class AIModelError(MailyError):
    """Error from AI model integration."""

    def __init__(
        self,
        message: str,
        model_name: str,
        original_error: Optional[Exception] = None,
        status_code: int = status.HTTP_502_BAD_GATEWAY,
    ):
        details = {"model": model_name}
        if original_error is not None and ENVIRONMENT in ["development", "test"]:
            details["original_error"] = str(original_error)

        super().__init__(
            message=message,
            code="ai_model_error",
            status_code=status_code,
            details=details,
            severity=ErrorSeverity.ERROR,
            is_retryable=True,
        )


# Error handling middleware
class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized error handling."""

    async def dispatch(self, request: Request, call_next):
        """
        Process requests and handle any exceptions.

        Args:
            request: FastAPI request object
            call_next: Next middleware or endpoint handler

        Returns:
            FastAPI response object
        """
        try:
            # Add correlation ID to request state
            request.state.correlation_id = str(uuid.uuid4())

            # Process request
            response = await call_next(request)
            return response

        except MailyError as e:
            # Handle known application errors
            return self._handle_maily_error(e, request)

        except RequestValidationError as e:
            # Handle request validation errors
            validation_error = ValidationError(
                message="Invalid request data",
                details={"validation_errors": [str(err) for err in e.errors()]},
            )
            return self._handle_maily_error(validation_error, request)

        except HTTPException as e:
            # Handle FastAPI HTTP exceptions
            # Map to appropriate MailyError subclass based on status code
            if e.status_code == status.HTTP_404_NOT_FOUND:
                error = NotFoundError(
                    message=e.detail,
                    resource_type="endpoint",
                    resource_id=request.url.path,
                )
            elif e.status_code == status.HTTP_401_UNAUTHORIZED:
                error = AuthenticationError(message=e.detail)
            elif e.status_code == status.HTTP_403_FORBIDDEN:
                error = AuthorizationError(message=e.detail)
            elif e.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                retry_after = 60  # Default retry-after
                if "retry-after" in e.headers:
                    retry_after = int(e.headers["retry-after"])
                error = RateLimitError(message=e.detail, retry_after=retry_after)
            else:
                # Generic MailyError for other HTTP exceptions
                error = MailyError(
                    message=e.detail,
                    code="http_error",
                    status_code=e.status_code,
                )

            return self._handle_maily_error(error, request)

        except Exception as e:
            # Handle unexpected exceptions
            logger.exception("Unhandled exception occurred")

            # Create internal server error
            error = MailyError(
                message="An unexpected error occurred",
                code="internal_server_error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                details={"exception": str(e)} if ENVIRONMENT in ["development", "test"] else None,
                severity=ErrorSeverity.CRITICAL,
            )

            # Report to error monitoring service
            if ERROR_MONITORING_ENABLED and SENTRY_DSN:
                sentry_sdk.capture_exception(e)

            return self._handle_maily_error(error, request)

    def _handle_maily_error(self, error: MailyError, request: Request) -> JSONResponse:
        """
        Handle MailyError instances.

        Args:
            error: MailyError instance
            request: FastAPI request object

        Returns:
            JSONResponse with standardized error format
        """
        # Set correlation ID from request if available
        if hasattr(request.state, "correlation_id"):
            error.correlation_id = request.state.correlation_id

        # Record error metrics
        endpoint = request.url.path
        ERROR_COUNTER.labels(
            error_type=error.__class__.__name__,
            error_code=error.code,
            endpoint=endpoint,
        ).inc()

        # Log error with structured metadata
        log_data = {
            "correlation_id": error.correlation_id,
            "error_code": error.code,
            "endpoint": endpoint,
            "method": request.method,
            "status_code": error.status_code,
            "severity": error.severity,
            "user_agent": request.headers.get("user-agent", "unknown"),
            "ip_address": request.client.host if request.client else "unknown",
        }

        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"{error.message}", extra=log_data)
        elif error.severity == ErrorSeverity.ERROR:
            logger.error(f"{error.message}", extra=log_data)
        elif error.severity == ErrorSeverity.WARNING:
            logger.warning(f"{error.message}", extra=log_data)
        else:
            logger.info(f"{error.message}", extra=log_data)

        # Create response with standardized error format
        error_dict = error.to_dict()

        # Set response headers
        headers = {
            "X-Correlation-ID": error.correlation_id,
        }

        # Add retry-after header for retryable errors
        if error.is_retryable and "retry_after" in error.details:
            headers["Retry-After"] = str(error.details["retry_after"])

        return JSONResponse(
            status_code=error.status_code,
            content=error_dict,
            headers=headers,
        )


# Function to register error handling with FastAPI
def setup_error_handling(app: FastAPI):
    """
    Set up error handling for FastAPI application.

    Args:
        app: FastAPI application instance
    """
    # Add error handling middleware
    app.add_middleware(ErrorHandlingMiddleware)

    # Register exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        # Let middleware handle this
        raise exc

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        # Let middleware handle this
        raise exc

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request, exc):
        # Let middleware handle this
        raise exc


# Decorator for automatic error handling in API endpoints
T = TypeVar("T")
def handle_errors(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for handling errors in API endpoints.

    Args:
        func: API endpoint function

    Returns:
        Wrapped function that catches and standardizes errors
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except MailyError:
            # Let middleware handle these
            raise
        except Exception as e:
            logger.exception(f"Unhandled exception in {func.__name__}")

            # Default to internal server error
            error = MailyError(
                message="An unexpected error occurred",
                code="internal_server_error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                details={"function": func.__name__},
                severity=ErrorSeverity.ERROR,
            )

            # Report to error monitoring service
            if ERROR_MONITORING_ENABLED and SENTRY_DSN:
                sentry_sdk.capture_exception(e)

            raise error

    return wrapper
