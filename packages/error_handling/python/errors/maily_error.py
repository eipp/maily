"""
Base error class for all Maily-specific errors.

This module defines the MailyError class, which is the base class for all errors
in the Maily ecosystem. All other error classes should inherit from this class.
"""

from typing import Any, Dict, Optional


class MailyError(Exception):
    """
    Base class for all Maily-specific errors.
    
    This class should be extended by more specific error classes rather than
    being used directly.
    
    Attributes:
        code (str): A unique code that identifies the error type
        message (str): A human-readable description of the error
        status_code (int): The HTTP status code that should be returned to the client
        details (Dict[str, Any], optional): Additional error details
    """
    
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new MailyError.
        
        Args:
            code: A unique identifier for this error type
            message: A human-readable error message
            status_code: The HTTP status code that should be returned
            details: Additional details about the error
        """
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        
        # Pass the message to the base Exception class
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the error to a dictionary representation.
        
        This is useful for serializing the error to JSON in API responses.
        
        Returns:
            A dictionary containing the error details
        """
        result = {
            "error": {
                "code": self.code,
                "message": self.message,
                "status_code": self.status_code,
            }
        }
        
        if self.details:
            result["error"]["details"] = self.details
            
        return result