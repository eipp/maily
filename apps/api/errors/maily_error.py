"""
Standardized error hierarchy for all Maily errors.
"""
from typing import Dict, Any, Optional, List, Union, Type
from enum import Enum
from fastapi import status

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

class MailyError(Exception):
    """Base exception for all Maily errors."""
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = ErrorCode.INTERNAL_ERROR

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.message = message
        self.details = details or {}
        self.headers = headers
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary for API responses."""
        error_dict = {
            "error_code": self.error_code,
            "message": self.message
        }

        if self.details:
            error_dict["details"] = self.details

        return error_dict


# HTTP 400 Errors
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


class RateLimitExceededError(BadRequestError):
    """Rate limit exceeded error."""
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    error_code = ErrorCode.RATE_LIMIT_EXCEEDED


# HTTP 401 and 403 Errors
class UnauthorizedError(MailyError):
    """Unauthorized error."""
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = ErrorCode.UNAUTHORIZED


class ForbiddenError(MailyError):
    """Forbidden error."""
    status_code = status.HTTP_403_FORBIDDEN
    error_code = ErrorCode.FORBIDDEN


# HTTP 404 Errors
class ResourceNotFoundError(MailyError):
    """Resource not found error."""
    status_code = status.HTTP_404_NOT_FOUND
    error_code = ErrorCode.NOT_FOUND


class CampaignNotFoundError(ResourceNotFoundError):
    """Campaign not found error."""
    error_code = ErrorCode.CAMPAIGN_ERROR


class TemplateNotFoundError(ResourceNotFoundError):
    """Template not found error."""
    error_code = ErrorCode.TEMPLATE_ERROR


class ContactNotFoundError(ResourceNotFoundError):
    """Contact not found error."""
    error_code = ErrorCode.CONTACT_ERROR


# Domain/Service Specific Errors
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


class FeatureDisabledError(MailyError):
    """Feature disabled error."""
    status_code = status.HTTP_403_FORBIDDEN
    error_code = ErrorCode.FEATURE_DISABLED


# Legacy compatibility
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
