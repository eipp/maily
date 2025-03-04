"""
Standardized error classes for Python services in the Maily ecosystem.

This module provides a consistent error hierarchy for use across all Python services,
ensuring consistent error handling, logging, and API responses.
"""

from .maily_error import MailyError
from .application_errors import ApplicationError, ValidationError, NotFoundError, ConflictError
from .infrastructure_errors import InfrastructureError, DatabaseError, NetworkError
from .security_errors import SecurityError, AuthenticationError, AuthorizationError
from .integration_errors import IntegrationError, ExternalServiceError, ThrottlingError

__all__ = [
    "MailyError",
    "ApplicationError",
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    "InfrastructureError",
    "DatabaseError",
    "NetworkError",
    "SecurityError",
    "AuthenticationError", 
    "AuthorizationError",
    "IntegrationError",
    "ExternalServiceError",
    "ThrottlingError",
]