"""
Standardized error hierarchy for all Maily errors.

This module provides a unified error handling system that consolidates
all error types across the application into a single hierarchy.
"""
import logging
import sys
import time
import traceback
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Type

from fastapi import status

logger = logging.getLogger(__name__)

class ErrorCode(str, Enum):
    """Standard error codes for Maily application."""
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
    """Detailed information about a specific error."""
    
    def __init__(
        self,
        code: str,
        message: str,
        field: Optional[str] = None,
        info: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.field = field
        self.info = info or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the error detail to a dictionary."""
        result = {
            "code": self.code,
            "message": self.message
        }
        
        if self.field:
            result["field"] = self.field
            
        if self.info:
            result["info"] = self.info
            
        return result

class MailyError(Exception):
    """Base exception for all Maily errors."""
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = ErrorCode.INTERNAL_ERROR
    documentation_url_base: str = "https://docs.maily.com/errors"

    def __init__(
        self,
        message: str,
        details: Optional[Union[List[Dict[str, Any]], List[ErrorDetail], Dict[str, Any]]] = None,
        headers: Optional[Dict[str, str]] = None,
        trace_id: Optional[str] = None,
        provider: Optional[str] = None,
        request_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.trace_id = trace_id or str(uuid.uuid4())
        self.timestamp = time.time()
        self.headers = headers
        self.provider = provider
        self.request_id = request_id
        self.context = context or {}
        
        # Process details, which can be various formats
        if details is None:
            self.details = []
        elif isinstance(details, dict):
            self.details = [ErrorDetail(
                code=f"{self.error_code}.details",
                message="Error details",
                info=details
            )]
        elif isinstance(details, list) and all(isinstance(d, dict) for d in details):
            self.details = [ErrorDetail(**d) for d in details]
        elif isinstance(details, list) and all(isinstance(d, ErrorDetail) for d in details):
            self.details = details
        else:
            self.details = [ErrorDetail(
                code=f"{self.error_code}.details",
                message="Error details",
                info={"details": details}
            )]
        
        # Construct detailed message
        detailed_message = message
        if provider:
            detailed_message += f" (Provider: {provider})"
        if request_id:
            detailed_message += f" (Request ID: {request_id})"
        
        super().__init__(detailed_message)
        
        # Log the error
        self._log_error()

    def _log_error(self):
        """Log the error with appropriate severity level."""
        log_context = {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "trace_id": self.trace_id
        }
        
        if self.provider:
            log_context["provider"] = self.provider
        
        if self.request_id:
            log_context["request_id"] = self.request_id
            
        if self.context:
            log_context.update(self.context)
        
        if self.status_code >= 500:
            logger.error(f"{self.error_code}: {self.message}", extra=log_context)
        else:
            logger.warning(f"{self.error_code}: {self.message}", extra=log_context)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary for API responses."""
        error_dict = {
            "error": True,
            "error_code": self.error_code,
            "message": self.message,
            "status_code": self.status_code,
            "trace_id": self.trace_id,
            "timestamp": self.timestamp
        }
        
        if self.request_id:
            error_dict["request_id"] = self.request_id
            
        if self.details:
            error_dict["details"] = [detail.to_dict() for detail in self.details]
            
        # Add documentation URL
        error_dict["documentation_url"] = f"{self.documentation_url_base}/{self.error_code}"
        
        return error_dict
    
    def to_response(self) -> Dict[str, Any]:
        """Convert the error to a response dictionary."""
        return self.to_dict()
    
    @classmethod
    def from_exception(cls, exc: Exception, **kwargs) -> 'MailyError':
        """Create a MailyError from another exception."""
        return cls(str(exc), **kwargs)


###################
# HTTP 400 Errors #
###################

class BadRequestError(MailyError):
    """Bad request error."""
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = ErrorCode.BAD_REQUEST


class ValidationError(BadRequestError):
    """Validation error."""
    error_code = ErrorCode.VALIDATION_ERROR


class DuplicateResourceError(BadRequestError):
    """Resource already exists error."""
    status_code = status.HTTP_409_CONFLICT
    error_code = ErrorCode.ALREADY_EXISTS


class ConflictError(BadRequestError):
    """Resource conflict error."""
    status_code = status.HTTP_409_CONFLICT
    error_code = ErrorCode.CONFLICT


class RateLimitExceededError(BadRequestError):
    """Rate limit exceeded error."""
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    error_code = ErrorCode.RATE_LIMIT_EXCEEDED


class TooManyRequestsError(BadRequestError):
    """Too many requests error."""
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    error_code = ErrorCode.TOO_MANY_REQUESTS


#########################
# HTTP 401 & 403 Errors #
#########################

class UnauthorizedError(MailyError):
    """Unauthorized error."""
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = ErrorCode.UNAUTHORIZED


class ForbiddenError(MailyError):
    """Forbidden error."""
    status_code = status.HTTP_403_FORBIDDEN
    error_code = ErrorCode.FORBIDDEN


class FeatureDisabledError(ForbiddenError):
    """Feature disabled error."""
    error_code = ErrorCode.FEATURE_DISABLED


##################
# HTTP 404 Error #
##################

class ResourceNotFoundError(MailyError):
    """Resource not found error."""
    status_code = status.HTTP_404_NOT_FOUND
    error_code = ErrorCode.NOT_FOUND


#######################
# HTTP 5xx-type Error #
#######################

class ServerError(MailyError):
    """Server error."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = ErrorCode.INTERNAL_ERROR


class ServiceUnavailableError(ServerError):
    """Service unavailable error."""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = ErrorCode.SERVICE_UNAVAILABLE


###############################
# Domain/Service-specific Errors #
###############################

class AIError(MailyError):
    """AI related error."""
    error_code = ErrorCode.AI_ERROR


class AIModelError(AIError):
    """AI model related error."""
    error_code = ErrorCode.MODEL_ERROR


class IntegrationError(MailyError):
    """Integration related error."""
    error_code = ErrorCode.INTEGRATION_ERROR


class DatabaseError(MailyError):
    """Database related error."""
    error_code = ErrorCode.DATA_PROCESSING_ERROR


class BlockchainError(MailyError):
    """Blockchain related error."""
    error_code = ErrorCode.BLOCKCHAIN_ERROR


class ConfigurationError(MailyError):
    """Configuration related error."""
    error_code = ErrorCode.CONFIGURATION_ERROR


class QuotaExceededError(MailyError):
    """Quota exceeded error."""
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    error_code = ErrorCode.QUOTA_EXCEEDED


class NetworkError(MailyError):
    """Network connectivity error."""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = ErrorCode.NETWORK_ERROR


class TimeoutError(MailyError):
    """Request timeout error."""
    status_code = status.HTTP_504_GATEWAY_TIMEOUT
    error_code = ErrorCode.TIMEOUT_ERROR


class ContentFilterError(MailyError):
    """Content filtering error."""
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = ErrorCode.CONTENT_FILTER_ERROR


############################
# AI Service-specific Errors #
############################

class ModelUnavailableError(AIError):
    """Model unavailable error."""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = ErrorCode.SERVICE_UNAVAILABLE


class ModelOverloadedError(ModelUnavailableError):
    """Model overloaded error."""
    pass


class UnsupportedModelError(AIError):
    """Unsupported model error."""
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = ErrorCode.BAD_REQUEST


#####################
# Resource-specific Errors #
#####################

class CampaignNotFoundError(ResourceNotFoundError):
    """Campaign not found error."""
    error_code = ErrorCode.CAMPAIGN_ERROR


class TemplateNotFoundError(ResourceNotFoundError):
    """Template not found error."""
    error_code = ErrorCode.TEMPLATE_ERROR


class ContactNotFoundError(ResourceNotFoundError):
    """Contact not found error."""
    error_code = ErrorCode.CONTACT_ERROR


#####################
# Legacy Compatibility #
#####################

class AuthenticationError(UnauthorizedError):
    """Legacy exception for authentication errors."""
    pass


class AuthorizationError(ForbiddenError):
    """Legacy exception for authorization errors."""
    pass


class ConsentNotFoundError(ResourceNotFoundError):
    """Legacy exception for consent not found errors."""
    pass


class ExternalServiceError(IntegrationError):
    """Legacy exception for external service errors."""
    pass


# Provider-specific error mappings
OPENAI_ERROR_MAPPING = {
    "rate_limit_exceeded": RateLimitExceededError,
    "invalid_api_key": AuthenticationError,
    "invalid_request_error": ValidationError,
    "server_error": ServerError,
    "connection_error": NetworkError,
    "timeout": TimeoutError,
    "content_filter": ContentFilterError,
    "model_not_found": UnsupportedModelError,
    "insufficient_quota": QuotaExceededError,
    "overloaded": ModelOverloadedError,
}

ANTHROPIC_ERROR_MAPPING = {
    "rate_limit_error": RateLimitExceededError,
    "authentication_error": AuthenticationError,
    "invalid_request_error": ValidationError,
    "internal_server_error": ServerError,
    "connection_error": NetworkError,
    "timeout_error": TimeoutError,
    "content_policy_violation": ContentFilterError,
    "model_not_available": UnsupportedModelError,
    "quota_exceeded": QuotaExceededError,
    "capacity_exceeded": ModelOverloadedError,
}

GOOGLE_ERROR_MAPPING = {
    "RESOURCE_EXHAUSTED": RateLimitExceededError,
    "UNAUTHENTICATED": AuthenticationError,
    "INVALID_ARGUMENT": ValidationError,
    "INTERNAL": ServerError,
    "UNAVAILABLE": NetworkError,
    "DEADLINE_EXCEEDED": TimeoutError,
    "PERMISSION_DENIED": ContentFilterError,
    "NOT_FOUND": UnsupportedModelError,
    "OUT_OF_RANGE": QuotaExceededError,
    "FAILED_PRECONDITION": ModelOverloadedError,
}


def map_provider_error(provider: str, error_type: str, message: str, **kwargs) -> MailyError:
    """
    Map a provider-specific error to our standardized error classes.

    Args:
        provider: Name of the AI provider (e.g., "openai", "anthropic")
        error_type: Provider-specific error type
        message: Error message
        **kwargs: Additional error context

    Returns:
        An appropriate MailyError subclass instance
    """
    mapping = {
        "openai": OPENAI_ERROR_MAPPING,
        "anthropic": ANTHROPIC_ERROR_MAPPING,
        "google": GOOGLE_ERROR_MAPPING
    }.get(provider.lower(), {})

    error_class = mapping.get(error_type, ServerError)
    return error_class(message, provider=provider, **kwargs)


def handle_common_exceptions(func):
    """
    Decorator for handling common exceptions in service methods.
    
    Args:
        func: The function to wrap
    
    Returns:
        Wrapped function with exception handling
    """
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except MailyError:
            # Re-raise Maily errors as they're already properly formatted
            raise
        except Exception as e:
            # Get information about the function being called
            module = func.__module__
            function_name = func.__name__
            
            # Log the error
            logger.exception(
                f"Unhandled exception in {module}.{function_name}",
                extra={
                    "function": function_name,
                    "module": module,
                }
            )
            
            # Convert to a MailyError
            raise ServerError.from_exception(
                e, 
                context={
                    "function": function_name,
                    "module": module,
                }
            )
    
    return wrapper