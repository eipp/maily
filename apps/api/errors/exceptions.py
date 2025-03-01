from typing import Optional, Dict, Any

class BaseMailyError(Exception):
    """Base exception class for Maily application."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class AuthenticationError(BaseMailyError):
    """Exception raised for authentication errors."""
    pass

class AuthorizationError(BaseMailyError):
    """Exception raised for authorization errors."""
    pass

class UnauthorizedError(BaseMailyError):
    """Exception raised when a user doesn't have permission for an action."""
    pass

class ValidationError(BaseMailyError):
    """Exception raised for validation errors."""
    pass

class ResourceNotFoundError(BaseMailyError):
    """Exception raised when a resource is not found."""
    pass

class ConsentNotFoundError(ResourceNotFoundError):
    """Exception raised when a consent record is not found."""
    pass

class TemplateNotFoundError(ResourceNotFoundError):
    """Exception raised when a template is not found."""
    pass

class DuplicateResourceError(BaseMailyError):
    """Exception raised when trying to create a duplicate resource."""
    pass

class RateLimitExceededError(BaseMailyError):
    """Exception raised when rate limits are exceeded."""
    pass

class AIModelError(BaseMailyError):
    """Exception raised for AI model related errors."""
    pass

class DatabaseError(BaseMailyError):
    """Exception raised for database related errors."""
    pass

class ExternalServiceError(BaseMailyError):
    """Exception raised for external service related errors."""
    pass

class ConfigurationError(BaseMailyError):
    """Exception raised for configuration related errors."""
    pass
