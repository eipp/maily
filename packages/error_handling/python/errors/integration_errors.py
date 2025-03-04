"""
Integration-related error classes for Maily ecosystem.

This module provides error classes for integration-related errors, such as
external service errors, throttling errors, and other issues related to
integrating with external systems.
"""

from typing import Any, Dict, Optional

from .maily_error import MailyError


class IntegrationError(MailyError):
    """
    Base class for all integration-related errors.
    
    This class should be used for errors related to external integrations, such as
    API clients, external services, and other third-party systems.
    """
    
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 502,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new IntegrationError.
        
        Args:
            code: A unique identifier for this error type
            message: A human-readable error message
            status_code: The HTTP status code that should be returned
            details: Additional details about the error
        """
        super().__init__(code, message, status_code, details)


class ExternalServiceError(IntegrationError):
    """
    Error raised when an external service fails.
    
    This error should be used when an external service returns an error or
    fails to respond as expected.
    """
    
    def __init__(
        self,
        service_name: str,
        message: str,
        status_code: int = 502,
        code: str = "EXTERNAL_SERVICE_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new ExternalServiceError.
        
        Args:
            service_name: The name of the external service that failed
            message: A human-readable error message
            status_code: The HTTP status code that should be returned
            code: A unique identifier for this error type
            details: Additional details about the error
        """
        error_details = details or {}
        error_details["service_name"] = service_name
            
        super().__init__(code, message, status_code, error_details)


class ThrottlingError(IntegrationError):
    """
    Error raised when a service is throttled by an external API.
    
    This error should be used when an external service throttles our requests
    due to rate limiting or other constraints.
    """
    
    def __init__(
        self,
        service_name: str,
        message: Optional[str] = None,
        retry_after: Optional[int] = None,
        code: str = "THROTTLING_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new ThrottlingError.
        
        Args:
            service_name: The name of the service that is throttling requests
            message: A human-readable error message
            retry_after: The number of seconds to wait before retrying
            code: A unique identifier for this error type
            details: Additional details about the error
        """
        error_message = message or f"Request throttled by {service_name}"
        error_details = details or {}
        error_details["service_name"] = service_name
        
        if retry_after:
            error_details["retry_after"] = retry_after
            
        super().__init__(code, error_message, 429, error_details)