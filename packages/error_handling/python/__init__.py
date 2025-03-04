"""
Python error handling package for the Maily ecosystem.

This package provides standardized error classes and middleware for
handling errors in Python services. It ensures consistent error reporting
and handling across all Python services in the Maily ecosystem.
"""

from .errors import (
    MailyError,
    ApplicationError,
    ValidationError,
    NotFoundError,
    ConflictError,
    InfrastructureError,
    DatabaseError,
    NetworkError,
    SecurityError,
    AuthenticationError,
    AuthorizationError,
    IntegrationError,
    ExternalServiceError,
    ThrottlingError,
)