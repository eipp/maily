"""
Infrastructure-level error classes for Maily ecosystem.

This module provides error classes for infrastructure-level errors, such as
database errors, network errors, and other system-level errors.
"""

from typing import Any, Dict, Optional

from .maily_error import MailyError


class InfrastructureError(MailyError):
    """
    Base class for all infrastructure-level errors.
    
    This class should be used for errors related to infrastructure components,
    such as databases, caches, message queues, etc.
    """
    
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new InfrastructureError.
        
        Args:
            code: A unique identifier for this error type
            message: A human-readable error message
            status_code: The HTTP status code that should be returned
            details: Additional details about the error
        """
        super().__init__(code, message, status_code, details)


class DatabaseError(InfrastructureError):
    """
    Error raised when a database operation fails.
    
    This error should be used for database-related errors, such as connection
    failures, query failures, or constraint violations.
    """
    
    def __init__(
        self,
        code: str = "DATABASE_ERROR",
        message: str = "A database error occurred",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        operation: Optional[str] = None
    ):
        """
        Initialize a new DatabaseError.
        
        Args:
            code: A unique identifier for this error type
            message: A human-readable error message
            status_code: The HTTP status code that should be returned
            details: Additional details about the error
            operation: The database operation that failed
        """
        error_details = details or {}
        
        if operation:
            error_details["operation"] = operation
            
        super().__init__(code, message, status_code, error_details)


class NetworkError(InfrastructureError):
    """
    Error raised when a network operation fails.
    
    This error should be used for network-related errors, such as connection
    failures, timeouts, or other network issues.
    """
    
    def __init__(
        self,
        code: str = "NETWORK_ERROR",
        message: str = "A network error occurred",
        status_code: int = 503,
        details: Optional[Dict[str, Any]] = None,
        service: Optional[str] = None
    ):
        """
        Initialize a new NetworkError.
        
        Args:
            code: A unique identifier for this error type
            message: A human-readable error message
            status_code: The HTTP status code that should be returned
            details: Additional details about the error
            service: The service that experienced the network error
        """
        error_details = details or {}
        
        if service:
            error_details["service"] = service
            
        super().__init__(code, message, status_code, error_details)