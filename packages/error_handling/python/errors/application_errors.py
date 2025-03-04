"""
Application-level error classes for Maily ecosystem.

This module provides error classes for application-level errors, such as
validation errors, not found errors, and other business logic errors.
"""

from typing import Any, Dict, Optional

from .maily_error import MailyError


class ApplicationError(MailyError):
    """
    Base class for all application-level errors.
    
    This class should be used for errors related to business logic, input validation,
    and other application-level concerns.
    """
    
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new ApplicationError.
        
        Args:
            code: A unique identifier for this error type
            message: A human-readable error message
            status_code: The HTTP status code that should be returned
            details: Additional details about the error
        """
        super().__init__(code, message, status_code, details)


class ValidationError(ApplicationError):
    """
    Error raised when input validation fails.
    
    This error should be used when a user provides invalid input data.
    """
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        code: str = "VALIDATION_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new ValidationError.
        
        Args:
            message: A human-readable error message
            field: The name of the field that failed validation
            code: A unique identifier for this error type
            details: Additional details about the error
        """
        error_details = details or {}
        if field:
            error_details["field"] = field
            
        super().__init__(code, message, 400, error_details)


class NotFoundError(ApplicationError):
    """
    Error raised when a requested resource is not found.
    
    This error should be used when a user requests a resource that doesn't exist.
    """
    
    def __init__(
        self,
        resource_type: str,
        resource_id: Optional[str] = None,
        message: Optional[str] = None,
        code: str = "RESOURCE_NOT_FOUND",
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new NotFoundError.
        
        Args:
            resource_type: The type of resource that wasn't found
            resource_id: The ID of the resource that wasn't found
            message: A human-readable error message
            code: A unique identifier for this error type
            details: Additional details about the error
        """
        error_details = details or {}
        error_details["resource_type"] = resource_type
        
        if resource_id:
            error_details["resource_id"] = resource_id
            
        error_message = message or f"{resource_type} not found"
        if resource_id:
            error_message = f"{resource_type} with ID '{resource_id}' not found"
            
        super().__init__(code, error_message, 404, error_details)


class ConflictError(ApplicationError):
    """
    Error raised when a conflict occurs in the application.
    
    This error should be used for situations like uniqueness constraint violations
    or concurrent modification conflicts.
    """
    
    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        code: str = "RESOURCE_CONFLICT",
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new ConflictError.
        
        Args:
            message: A human-readable error message
            resource_type: The type of resource that has a conflict
            resource_id: The ID of the resource that has a conflict
            code: A unique identifier for this error type
            details: Additional details about the error
        """
        error_details = details or {}
        
        if resource_type:
            error_details["resource_type"] = resource_type
            
        if resource_id:
            error_details["resource_id"] = resource_id
            
        super().__init__(code, message, 409, error_details)