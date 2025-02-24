class MailyError(Exception):
    """Base class for all Maily application errors."""
    def __init__(self, message: str, error_code: str, status_code: int = 500):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)

class DatabaseError(MailyError):
    """Exception raised for database-related errors."""
    def __init__(self, message: str):
        super().__init__(message, "DATABASE_ERROR", 503)

class AuthenticationError(MailyError):
    """Exception raised for authentication-related errors."""
    def __init__(self, message: str):
        super().__init__(message, "AUTHENTICATION_ERROR", 401)

class RateLimitError(MailyError):
    """Exception raised when rate limits are exceeded."""
    def __init__(self, message: str):
        super().__init__(message, "RATE_LIMIT_ERROR", 429)

class ValidationError(MailyError):
    """Exception raised for validation errors."""
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR", 400)

class NotFoundError(MailyError):
    """Exception raised when a resource is not found."""
    def __init__(self, message: str):
        super().__init__(message, "NOT_FOUND_ERROR", 404)

class ConfigurationError(MailyError):
    """Exception raised for configuration-related errors."""
    def __init__(self, message: str):
        super().__init__(message, "CONFIGURATION_ERROR", 500) 