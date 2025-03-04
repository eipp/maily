"""
Error handling middleware for Python services.

This package provides middleware for handling errors in various Python frameworks,
ensuring consistent error responses across all services.
"""

from .fastapi_error_handler import ErrorHandlingMiddleware, setup_error_handling

__all__ = ["ErrorHandlingMiddleware", "setup_error_handling"]