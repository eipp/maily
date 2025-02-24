"""Custom error classes for the Maily application."""

class MailyError(Exception):
    """Base error class for Maily application."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class AuthError(MailyError):
    """Authentication related errors."""
    def __init__(self, message: str, status_code: int = 401):
        super().__init__(message, status_code)

class ValidationError(MailyError):
    """Data validation errors."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message, status_code)

class DatabaseError(MailyError):
    """Database operation errors."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message, status_code)

class AIError(MailyError):
    """AI model related errors."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message, status_code)

class RateLimitError(MailyError):
    """Rate limiting errors."""
    def __init__(self, message: str, status_code: int = 429):
        super().__init__(message, status_code) 