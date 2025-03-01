"""
AI Service Error Module

Defines standardized error classes for AI service interactions to ensure
consistent error handling and reporting across different AI providers.
"""

from typing import Optional, Dict, Any

class AIServiceError(Exception):
    """
    Base exception class for all AI service errors.

    This class serves as the root exception for all errors that may occur
    when interacting with AI services like OpenAI, Anthropic, Google, etc.
    """

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        status_code: Optional[int] = None,
        request_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the AI service error.

        Args:
            message: Human-readable error message
            provider: Name of the AI provider (e.g., "openai", "anthropic")
            status_code: HTTP status code if applicable
            request_id: Provider-specific request ID for tracking
            context: Additional context information
        """
        self.message = message
        self.provider = provider
        self.status_code = status_code
        self.request_id = request_id
        self.context = context or {}

        # Construct detailed error message for better debugging
        detailed_message = f"{message}"
        if provider:
            detailed_message += f" (Provider: {provider})"
        if status_code:
            detailed_message += f" (Status: {status_code})"
        if request_id:
            detailed_message += f" (Request ID: {request_id})"

        super().__init__(detailed_message)


class RateLimitError(AIServiceError):
    """
    Exception raised when an AI service's rate limit is exceeded.

    This indicates that the client should retry after a delay or
    implement backoff strategies.
    """
    pass


class AuthenticationError(AIServiceError):
    """
    Exception raised when authentication with an AI service fails.

    This typically indicates an invalid or expired API key.
    """
    pass


class ValidationError(AIServiceError):
    """
    Exception raised when request parameters are invalid.

    This indicates that the request to the AI service contained
    invalid parameters or violated service constraints.
    """
    pass


class ServerError(AIServiceError):
    """
    Exception raised when the AI service encounters an internal error.

    This typically indicates an issue on the provider's side.
    """
    pass


class NetworkError(AIServiceError):
    """
    Exception raised when network connectivity issues occur.

    This indicates problems establishing a connection to the AI service.
    """
    pass


class TimeoutError(AIServiceError):
    """
    Exception raised when a request to an AI service times out.

    This indicates that the service did not respond within the expected time.
    """
    pass


class ContentFilterError(AIServiceError):
    """
    Exception raised when content is filtered by the AI service.

    This indicates that the input or output content violated the
    service's content policies.
    """
    pass


class UnsupportedModelError(AIServiceError):
    """
    Exception raised when an unsupported model is requested.

    This indicates that the client requested a model that is not
    supported by the provider or adapter.
    """
    pass


class QuotaExceededError(AIServiceError):
    """
    Exception raised when the quota for an AI service is exceeded.

    This indicates that the account has used up its available credit
    or token allocation.
    """
    pass


class ModelOverloadedError(AIServiceError):
    """
    Exception raised when a model is overloaded and unavailable.

    This indicates high demand for the model and the service's
    inability to process the request at the moment.
    """
    pass


# Error mapping dictionaries for each provider
# These can be used to map provider-specific errors to our standardized errors

OPENAI_ERROR_MAPPING = {
    "rate_limit_exceeded": RateLimitError,
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
    "rate_limit_error": RateLimitError,
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
    "RESOURCE_EXHAUSTED": RateLimitError,
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


def map_provider_error(provider: str, error_type: str, message: str, **kwargs) -> AIServiceError:
    """
    Map a provider-specific error to our standardized error classes.

    Args:
        provider: Name of the AI provider (e.g., "openai", "anthropic")
        error_type: Provider-specific error type
        message: Error message
        **kwargs: Additional error context

    Returns:
        An appropriate AIServiceError subclass instance
    """
    mapping = {
        "openai": OPENAI_ERROR_MAPPING,
        "anthropic": ANTHROPIC_ERROR_MAPPING,
        "google": GOOGLE_ERROR_MAPPING
    }.get(provider.lower(), {})

    error_class = mapping.get(error_type, AIServiceError)
    return error_class(message, provider=provider, **kwargs)
