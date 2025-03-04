"""
Security-related error classes for Maily ecosystem.

This module provides error classes for security-related errors, such as
authentication errors, authorization errors, and other security-related issues.
"""

from typing import Any, Dict, Optional

from .maily_error import MailyError


class SecurityError(MailyError):
    """
    Base class for all security-related errors.
    
    This class should be used for errors related to security, such as
    authentication, authorization, and other security-related issues.
    """
    
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 401,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new SecurityError.
        
        Args:
            code: A unique identifier for this error type
            message: A human-readable error message
            status_code: The HTTP status code that should be returned
            details: Additional details about the error
        """
        super().__init__(code, message, status_code, details)


class AuthenticationError(SecurityError):
    """
    Error raised when authentication fails.
    
    This error should be used when a user fails to authenticate, such as
    providing invalid credentials or an expired token.
    """
    
    def __init__(
        self,
        message: str = "Authentication failed",
        code: str = "AUTHENTICATION_FAILED",
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new AuthenticationError.
        
        Args:
            message: A human-readable error message
            code: A unique identifier for this error type
            details: Additional details about the error
        """
        super().__init__(code, message, 401, details)


class AuthorizationError(SecurityError):
    """
    Error raised when authorization fails.
    
    This error should be used when a user is authenticated but does not have
    permission to access a resource or perform an operation.
    """
    
    def __init__(
        self,
        message: str = "Permission denied",
        resource: Optional[str] = None,
        action: Optional[str] = None,
        code: str = "PERMISSION_DENIED",
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new AuthorizationError.
        
        Args:
            message: A human-readable error message
            resource: The resource that the user tried to access
            action: The action that the user tried to perform
            code: A unique identifier for this error type
            details: Additional details about the error
        """
        error_details = details or {}
        
        if resource:
            error_details["resource"] = resource
            
        if action:
            error_details["action"] = action
            
        super().__init__(code, message, 403, error_details)