"""
FastAPI middleware for standardized error handling.

This module provides middleware for handling errors in FastAPI applications,
ensuring consistent error responses across all services.
"""

import logging
import traceback
import uuid
from typing import Any, Callable, Dict, Optional

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..errors import MailyError

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling errors in FastAPI applications.
    
    This middleware catches all exceptions, logs them, and returns standardized
    error responses. It ensures consistent error handling across all services.
    """
    
    def __init__(
        self,
        app: FastAPI,
        include_exception: bool = False,
        include_traceback: bool = False,
    ):
        """
        Initialize the error handling middleware.
        
        Args:
            app: The FastAPI application
            include_exception: Whether to include the exception in the response
            include_traceback: Whether to include the traceback in the response
        """
        super().__init__(app)
        self.include_exception = include_exception
        self.include_traceback = include_traceback
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and handle any errors.
        
        Args:
            request: The incoming request
            call_next: The next middleware in the chain
            
        Returns:
            The response from the application or an error response
        """
        try:
            return await call_next(request)
        except Exception as exc:
            return await self._handle_exception(request, exc)
    
    async def _handle_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """
        Handle an exception and return a standardized error response.
        
        Args:
            request: The incoming request
            exc: The exception that was raised
            
        Returns:
            A JSON response with standardized error information
        """
        trace_id = str(uuid.uuid4())
        
        if isinstance(exc, MailyError):
            # Handle Maily-specific errors
            response_data = exc.to_dict()
            status_code = exc.status_code
            log_level = logging.ERROR if status_code >= 500 else logging.WARNING
        else:
            # Handle unexpected errors
            status_code = 500
            log_level = logging.ERROR
            response_data = {
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "status_code": status_code,
                }
            }
        
        # Add trace ID to all error responses
        response_data["error"]["trace_id"] = trace_id
        
        # Include exception details in development environment
        if self.include_exception:
            response_data["error"]["exception"] = str(exc)
            
        if self.include_traceback:
            response_data["error"]["traceback"] = traceback.format_exc()
        
        # Log the error with contextual information
        log_message = f"Error processing request: {request.method} {request.url.path}"
        log_data = {
            "trace_id": trace_id,
            "status_code": status_code,
            "method": request.method,
            "path": request.url.path,
            "client_host": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }
        
        if isinstance(exc, MailyError):
            log_data["error_code"] = exc.code
            log_data["error_message"] = exc.message
            
            if exc.details:
                log_data["error_details"] = exc.details
        else:
            log_data["error_message"] = str(exc)
            log_data["traceback"] = traceback.format_exc()
        
        logger.log(log_level, log_message, extra=log_data)
        
        return JSONResponse(
            status_code=status_code,
            content=response_data,
        )


def setup_error_handling(
    app: FastAPI,
    include_exception: bool = False,
    include_traceback: bool = False,
) -> None:
    """
    Set up error handling for a FastAPI application.
    
    This function adds the error handling middleware to the application and
    sets up exception handlers for common exceptions.
    
    Args:
        app: The FastAPI application
        include_exception: Whether to include the exception in the response
        include_traceback: Whether to include the traceback in the response
    """
    # Add the error handling middleware
    app.add_middleware(
        ErrorHandlingMiddleware,
        include_exception=include_exception,
        include_traceback=include_traceback,
    )