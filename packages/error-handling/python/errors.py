"""
Standard error classes for Python services.

This module defines a complete hierarchy of error classes that match
the TypeScript error hierarchy for consistent error handling across services.
"""

import enum
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

class ErrorCode(str, enum.Enum):
    """Standard error codes for the application."""
    
    # General errors
    INTERNAL_ERROR = "internal_error"
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    ALREADY_EXISTS = "already_exists"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    BAD_REQUEST = "bad_request"
    CONFLICT = "conflict"
    TOO_MANY_REQUESTS = "too_many_requests"
    SERVICE_UNAVAILABLE = "service_unavailable"
    
    # Domain-specific errors
    CAMPAIGN_ERROR = "campaign_error"
    TEMPLATE_ERROR = "template_error"
    CONTACT_ERROR = "contact_error"
    AI_ERROR = "ai_error"
    MODEL_ERROR = "model_error"
    INTEGRATION_ERROR = "integration_error"
    BLOCKCHAIN_ERROR = "blockchain_error"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    DATA_PROCESSING_ERROR = "data_processing_error"
    CONFIGURATION_ERROR = "configuration_error"
    QUOTA_EXCEEDED = "quota_exceeded"
    FEATURE_DISABLED = "feature_disabled"
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    CONTENT_FILTER_ERROR = "content_filter_error"

class ErrorDetail:
    """Detailed error information."""
    
    def __init__(
        self,
        code: str,
        message: str,
        field: Optional[str] = None,
        info: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize error detail.
        
        Args:
            code: Error code for the specific detail
            message: Human-readable message for the error detail
            field: Optional field name if the error is related to a specific field
            info: Additional error information
        """
        self.code = code
        self.message = message
        self.field = field
        self.info = info or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "code": self.code,
            "message": self.message,
        }
        
        if self.field:
            result["field"] = self.field
            
        if self.info:
            result["info"] = self.info
            
        return result

class ApplicationError(Exception):
    """Base error class for all application errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Union[ErrorCode, str] = ErrorCode.INTERNAL_ERROR,
        status_code: int = 500,
        details: Optional[Union[List[ErrorDetail], Dict[str, Any]]] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        provider: Optional[str] = None,
    ):
        """
        Initialize application error.
        
        Args:
            message: Error message
            error_code: Error code from ErrorCode enum or string
            status_code: HTTP status code
            details: Error details as list of ErrorDetail objects or dict
            trace_id: Trace ID for error tracking
            request_id: Request ID if available
            provider: Provider information (e.g., API provider)
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.timestamp = int(time.time() * 1000)  # milliseconds since epoch
        self.trace_id = trace_id or self._generate_trace_id()
        self.request_id = request_id
        self.provider = provider
        self.documentation_url_base = "https://docs.maily.com/errors"
        
        # Process details
        if not details:
            self.details = []
        elif isinstance(details, list):
            self.details = details
        else:
            self.details = [
                ErrorDetail(
                    code=f"{self.error_code}.details",
                    message="Error details",
                    info=details
                )
            ]
        
        # Log the error
        self._log_error()
    
    def _log_error(self) -> None:
        """Log the error to the console with appropriate level."""
        context = {
            "errorType": self.__class__.__name__,
            "errorCode": self.error_code,
            "traceId": self.trace_id,
            "statusCode": self.status_code
        }
        
        if self.status_code >= 500:
            logger.error(f"[ERROR] {self.error_code}: {self.message}", extra=context)
        else:
            logger.warning(f"[WARN] {self.error_code}: {self.message}", extra=context)
    
    @staticmethod
    def _generate_trace_id() -> str:
        """Generate a unique trace ID for the error."""
        return f"err_{int(time.time() * 1000)}_{uuid.uuid4().hex[:7]}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "name": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "status_code": self.status_code,
            "details": [detail.to_dict() for detail in self.details],
            "trace_id": self.trace_id,
            "timestamp": self.timestamp,
        }
        
        if self.request_id:
            result["request_id"] = self.request_id
            
        if self.provider:
            result["provider"] = self.provider
            
        return result
    
    def to_response(self) -> Dict[str, Any]:
        """Create a standardized error response object."""
        response = {
            "error": True,
            "error_code": str(self.error_code),
            "message": self.message,
            "status_code": self.status_code,
            "trace_id": self.trace_id,
            "timestamp": self.timestamp,
            "documentation_url": f"{self.documentation_url_base}/{self.error_code}",
        }
        
        if self.request_id:
            response["request_id"] = self.request_id
            
        if self.details:
            response["details"] = [detail.to_dict() for detail in self.details]
            
        return response
    
    @classmethod
    def from_exception(
        cls,
        exception: Exception,
        error_code: Union[ErrorCode, str] = ErrorCode.INTERNAL_ERROR,
        status_code: int = 500,
        details: Optional[Union[List[ErrorDetail], Dict[str, Any]]] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> "ApplicationError":
        """
        Create ApplicationError from another exception.
        
        Args:
            exception: Original exception
            error_code: Error code
            status_code: HTTP status code
            details: Error details
            trace_id: Trace ID
            request_id: Request ID
            provider: Provider information
            
        Returns:
            ApplicationError instance
        """
        if details is None:
            details = {
                "original_error": str(exception),
                "error_type": exception.__class__.__name__,
            }
            
        return cls(
            message=str(exception) or "An unknown error occurred",
            error_code=error_code,
            status_code=status_code,
            details=details,
            trace_id=trace_id,
            request_id=request_id,
            provider=provider,
        )

# HTTP Error Classes

class HttpError(ApplicationError):
    """Base class for all HTTP errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Union[ErrorCode, str] = ErrorCode.BAD_REQUEST,
        status_code: int = 400,
        details: Optional[Union[List[ErrorDetail], Dict[str, Any]]] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        provider: Optional[str] = None,
        exposable: bool = True,
    ):
        """Initialize HTTP error."""
        self.exposable = exposable
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details,
            trace_id=trace_id,
            request_id=request_id,
            provider=provider,
        )

class BadRequestError(HttpError):
    """400 Bad Request error."""
    
    def __init__(
        self,
        message: str = "Bad Request",
        details: Optional[Union[List[ErrorDetail], Dict[str, Any]]] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        provider: Optional[str] = None,
    ):
        """Initialize Bad Request error."""
        super().__init__(
            message=message,
            error_code=ErrorCode.BAD_REQUEST,
            status_code=400,
            details=details,
            trace_id=trace_id,
            request_id=request_id,
            provider=provider,
        )

class ValidationError(BadRequestError):
    """422 Validation error."""
    
    def __init__(
        self,
        message: str = "Validation Error",
        details: Optional[Union[List[ErrorDetail], Dict[str, Any]]] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        provider: Optional[str] = None,
    ):
        """Initialize Validation error."""
        super().__init__(
            message=message,
            details=details,
            trace_id=trace_id,
            request_id=request_id,
            provider=provider,
        )
        self.error_code = ErrorCode.VALIDATION_ERROR
        self.status_code = 422

class DuplicateResourceError(BadRequestError):
    """409 Duplicate Resource error."""
    
    def __init__(
        self,
        message: str = "Resource already exists",
        details: Optional[Union[List[ErrorDetail], Dict[str, Any]]] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        provider: Optional[str] = None,
    ):
        """Initialize Duplicate Resource error."""
        super().__init__(
            message=message,
            details=details,
            trace_id=trace_id,
            request_id=request_id,
            provider=provider,
        )
        self.error_code = ErrorCode.ALREADY_EXISTS
        self.status_code = 409

class ConflictError(BadRequestError):
    """409 Conflict error."""
    
    def __init__(
        self,
        message: str = "The request conflicts with the current state",
        details: Optional[Union[List[ErrorDetail], Dict[str, Any]]] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        provider: Optional[str] = None,
    ):
        """Initialize Conflict error."""
        super().__init__(
            message=message,
            details=details,
            trace_id=trace_id,
            request_id=request_id,
            provider=provider,
        )
        self.error_code = ErrorCode.CONFLICT
        self.status_code = 409

class RateLimitExceededError(BadRequestError):
    """429 Rate Limit Exceeded error."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        details: Optional[Union[List[ErrorDetail], Dict[str, Any]]] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        provider: Optional[str] = None,
    ):
        """Initialize Rate Limit Exceeded error."""
        super().__init__(
            message=message,
            details=details,
            trace_id=trace_id,
            request_id=request_id,
            provider=provider,
        )
        self.error_code = ErrorCode.RATE_LIMIT_EXCEEDED
        self.status_code = 429

class TooManyRequestsError(BadRequestError):
    """429 Too Many Requests error."""
    
    def __init__(
        self,
        message: str = "Too many requests, please try again later",
        details: Optional[Union[List[ErrorDetail], Dict[str, Any]]] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        provider: Optional[str] = None,
    ):
        """Initialize Too Many Requests error."""
        super().__init__(
            message=message,
            details=details,
            trace_id=trace_id,
            request_id=request_id,
            provider=provider,
        )
        self.error_code = ErrorCode.TOO_MANY_REQUESTS
        self.status_code = 429

class UnauthorizedError(HttpError):
    """401 Unauthorized error."""
    
    def __init__(
        self,
        message: str = "Authentication is required",
        details: Optional[Union[List[ErrorDetail], Dict[str, Any]]] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        provider: Optional[str] = None,
    ):
        """Initialize Unauthorized error."""
        super().__init__(
            message=message,
            error_code=ErrorCode.UNAUTHORIZED,
            status_code=401,
            details=details,
            trace_id=trace_id,
            request_id=request_id,
            provider=provider,
        )

class ForbiddenError(HttpError):
    """403 Forbidden error."""
    
    def __init__(
        self,
        message: str = "You do not have permission to perform this action",
        details: Optional[Union[List[ErrorDetail], Dict[str, Any]]] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        provider: Optional[str] = None,
    ):
        """Initialize Forbidden error."""
        super().__init__(
            message=message,
            error_code=ErrorCode.FORBIDDEN,
            status_code=403,
            details=details,
            trace_id=trace_id,
            request_id=request_id,
            provider=provider,
        )

class FeatureDisabledError(ForbiddenError):
    """403 Feature Disabled error."""
    
    def __init__(
        self,
        message: str = "This feature is currently disabled",
        details: Optional[Union[List[ErrorDetail], Dict[str, Any]]] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        provider: Optional[str] = None,
    ):
        """Initialize Feature Disabled error."""
        super().__init__(
            message=message,
            details=details,
            trace_id=trace_id,
            request_id=request_id,
            provider=provider,
        )
        self.error_code = ErrorCode.FEATURE_DISABLED

class NotFoundError(HttpError):
    """404 Not Found error."""
    
    def __init__(
        self,
        message: str = "The requested resource was not found",
        details: Optional[Union[List[ErrorDetail], Dict[str, Any]]] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        provider: Optional[str] = None,
    ):
        """Initialize Not Found error."""
        super().__init__(
            message=message,
            error_code=ErrorCode.NOT_FOUND,
            status_code=404,
            details=details,
            trace_id=trace_id,
            request_id=request_id,
            provider=provider,
        )

class ServerError(HttpError):
    """500 Server error."""
    
    def __init__(
        self,
        message: str = "An unexpected error occurred",
        details: Optional[Union[List[ErrorDetail], Dict[str, Any]]] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        provider: Optional[str] = None,
    ):
        """Initialize Server error."""
        super().__init__(
            message=message,
            error_code=ErrorCode.INTERNAL_ERROR,
            status_code=500,
            details=details,
            trace_id=trace_id,
            request_id=request_id,
            provider=provider,
            exposable=False,  # Server errors are not exposable by default
        )

class ServiceUnavailableError(ServerError):
    """503 Service Unavailable error."""
    
    def __init__(
        self,
        message: str = "The service is currently unavailable",
        details: Optional[Union[List[ErrorDetail], Dict[str, Any]]] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        provider: Optional[str] = None,
    ):
        """Initialize Service Unavailable error."""
        super().__init__(
            message=message,
            details=details,
            trace_id=trace_id,
            request_id=request_id,
            provider=provider,
        )
        self.error_code = ErrorCode.SERVICE_UNAVAILABLE
        self.status_code = 503

# Domain-specific errors

class AIError(ApplicationError):
    """AI service error."""
    
    def __init__(
        self,
        message: str = "AI service error",
        details: Optional[Union[List[ErrorDetail], Dict[str, Any]]] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        provider: Optional[str] = None,
        status_code: int = 500,
    ):
        """Initialize AI error."""
        super().__init__(
            message=message,
            error_code=ErrorCode.AI_ERROR,
            status_code=status_code,
            details=details,
            trace_id=trace_id,
            request_id=request_id,
            provider=provider,
        )

class ModelError(AIError):
    """Model error."""
    
    def __init__(
        self,
        message: str = "Model error",
        details: Optional[Union[List[ErrorDetail], Dict[str, Any]]] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        provider: Optional[str] = None,
        status_code: int = 500,
    ):
        """Initialize Model error."""
        super().__init__(
            message=message,
            details=details,
            trace_id=trace_id,
            request_id=request_id,
            provider=provider,
            status_code=status_code,
        )
        self.error_code = ErrorCode.MODEL_ERROR

class ContentFilterError(AIError):
    """Content filter error."""
    
    def __init__(
        self,
        message: str = "Content filtered",
        details: Optional[Union[List[ErrorDetail], Dict[str, Any]]] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        provider: Optional[str] = None,
    ):
        """Initialize Content Filter error."""
        super().__init__(
            message=message,
            details=details,
            trace_id=trace_id,
            request_id=request_id,
            provider=provider,
            status_code=400,  # Content filter errors are client errors
        )
        self.error_code = ErrorCode.CONTENT_FILTER_ERROR

class CampaignError(ApplicationError):
    """Campaign error."""
    
    def __init__(
        self,
        message: str = "Campaign error",
        details: Optional[Union[List[ErrorDetail], Dict[str, Any]]] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        provider: Optional[str] = None,
        status_code: int = 400,
    ):
        """Initialize Campaign error."""
        super().__init__(
            message=message,
            error_code=ErrorCode.CAMPAIGN_ERROR,
            status_code=status_code,
            details=details,
            trace_id=trace_id,
            request_id=request_id,
            provider=provider,
        )

class TemplateError(ApplicationError):
    """Template error."""
    
    def __init__(
        self,
        message: str = "Template error",
        details: Optional[Union[List[ErrorDetail], Dict[str, Any]]] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        provider: Optional[str] = None,
        status_code: int = 400,
    ):
        """Initialize Template error."""
        super().__init__(
            message=message,
            error_code=ErrorCode.TEMPLATE_ERROR,
            status_code=status_code,
            details=details,
            trace_id=trace_id,
            request_id=request_id,
            provider=provider,
        )

class ContactError(ApplicationError):
    """Contact error."""
    
    def __init__(
        self,
        message: str = "Contact error",
        details: Optional[Union[List[ErrorDetail], Dict[str, Any]]] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        provider: Optional[str] = None,
        status_code: int = 400,
    ):
        """Initialize Contact error."""
        super().__init__(
            message=message,
            error_code=ErrorCode.CONTACT_ERROR,
            status_code=status_code,
            details=details,
            trace_id=trace_id,
            request_id=request_id,
            provider=provider,
        )

class IntegrationError(ApplicationError):
    """Integration error."""
    
    def __init__(
        self,
        message: str = "Integration error",
        details: Optional[Union[List[ErrorDetail], Dict[str, Any]]] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        provider: Optional[str] = None,
        status_code: int = 500,
    ):
        """Initialize Integration error."""
        super().__init__(
            message=message,
            error_code=ErrorCode.INTEGRATION_ERROR,
            status_code=status_code,
            details=details,
            trace_id=trace_id,
            request_id=request_id,
            provider=provider,
        )

class BlockchainError(ApplicationError):
    """Blockchain error."""
    
    def __init__(
        self,
        message: str = "Blockchain error",
        details: Optional[Union[List[ErrorDetail], Dict[str, Any]]] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        provider: Optional[str] = None,
        status_code: int = 500,
    ):
        """Initialize Blockchain error."""
        super().__init__(
            message=message,
            error_code=ErrorCode.BLOCKCHAIN_ERROR,
            status_code=status_code,
            details=details,
            trace_id=trace_id,
            request_id=request_id,
            provider=provider,
        )

class DataProcessingError(ApplicationError):
    """Data processing error."""
    
    def __init__(
        self,
        message: str = "Data processing error",
        details: Optional[Union[List[ErrorDetail], Dict[str, Any]]] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        provider: Optional[str] = None,
        status_code: int = 500,
    ):
        """Initialize Data Processing error."""
        super().__init__(
            message=message,
            error_code=ErrorCode.DATA_PROCESSING_ERROR,
            status_code=status_code,
            details=details,
            trace_id=trace_id,
            request_id=request_id,
            provider=provider,
        )

class ConfigurationError(ApplicationError):
    """Configuration error."""
    
    def __init__(
        self,
        message: str = "Configuration error",
        details: Optional[Union[List[ErrorDetail], Dict[str, Any]]] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        provider: Optional[str] = None,
        status_code: int = 500,
    ):
        """Initialize Configuration error."""
        super().__init__(
            message=message,
            error_code=ErrorCode.CONFIGURATION_ERROR,
            status_code=status_code,
            details=details,
            trace_id=trace_id,
            request_id=request_id,
            provider=provider,
        )

class QuotaExceededError(ApplicationError):
    """Quota exceeded error."""
    
    def __init__(
        self,
        message: str = "Quota exceeded",
        details: Optional[Union[List[ErrorDetail], Dict[str, Any]]] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        provider: Optional[str] = None,
    ):
        """Initialize Quota Exceeded error."""
        super().__init__(
            message=message,
            error_code=ErrorCode.QUOTA_EXCEEDED,
            status_code=403,
            details=details,
            trace_id=trace_id,
            request_id=request_id,
            provider=provider,
        )

class NetworkError(ApplicationError):
    """Network error."""
    
    def __init__(
        self,
        message: str = "Network error",
        details: Optional[Union[List[ErrorDetail], Dict[str, Any]]] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        provider: Optional[str] = None,
        status_code: int = 500,
    ):
        """Initialize Network error."""
        super().__init__(
            message=message,
            error_code=ErrorCode.NETWORK_ERROR,
            status_code=status_code,
            details=details,
            trace_id=trace_id,
            request_id=request_id,
            provider=provider,
        )

class TimeoutError(NetworkError):
    """Timeout error."""
    
    def __init__(
        self,
        message: str = "Operation timed out",
        details: Optional[Union[List[ErrorDetail], Dict[str, Any]]] = None,
        trace_id: Optional[str] = None,
        request_id: Optional[str] = None,
        provider: Optional[str] = None,
    ):
        """Initialize Timeout error."""
        super().__init__(
            message=message,
            details=details,
            trace_id=trace_id,
            request_id=request_id,
            provider=provider,
            status_code=504,
        )
        self.error_code = ErrorCode.TIMEOUT_ERROR