"""
Standardized error handling middleware for FastAPI applications.

This module provides middleware and exception handlers for consistent
error handling across all FastAPI applications in the Maily ecosystem.
"""
import logging
import time
import uuid
from typing import Callable, Dict, List, Optional, Any, Union

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .error import MailyError, ValidationError, ServerError, ErrorDetail

logger = logging.getLogger(__name__)


async def error_handler_middleware(request: Request, call_next):
    """
    Middleware to catch and handle all errors consistently.
    
    This middleware catches all exceptions in the request-response cycle
    and formats them into standardized error responses.
    
    Args:
        request: The incoming request
        call_next: The next middleware in the chain
        
    Returns:
        Response with standardized error format if an error occurs
    """
    # Generate request ID for tracing
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Add request ID to request state for access in route handlers
    request.state.request_id = request_id
    
    try:
        # Process the request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        # Return the successful response
        return response
    
    except MailyError as e:
        # For our standard errors, use their built-in formatting
        e.request_id = e.request_id or request_id
        
        # Add context about the request
        e.context = e.context or {}
        e.context.update({
            "path": request.url.path,
            "method": request.method,
            "processing_time_ms": (time.time() - start_time) * 1000
        })
        
        # Log at the appropriate level based on status code
        if e.status_code >= 500:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
        else:
            logger.warning(f"Error processing request: {str(e)}")
        
        # Convert to JSON response
        response_data = e.to_response()
        return JSONResponse(
            status_code=e.status_code,
            content=response_data,
            headers=e.headers
        )
    
    except Exception as e:
        # For unexpected exceptions, wrap in a ServerError
        error = ServerError.from_exception(
            e,
            request_id=request_id,
            context={
                "path": request.url.path,
                "method": request.method,
                "processing_time_ms": (time.time() - start_time) * 1000
            }
        )
        
        # Log at error level
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        
        # Convert to JSON response
        response_data = error.to_response()
        return JSONResponse(
            status_code=error.status_code,
            content=response_data
        )


class ErrorHandlingMiddleware:
    """
    Comprehensive error handling middleware for FastAPI.
    
    This class provides a middleware component and exception handlers
    to ensure consistent error handling across FastAPI applications.
    """
    
    def __init__(
        self,
        app: FastAPI,
        include_debug_info: bool = False,
        documentation_url_base: Optional[str] = None,
        on_error_callbacks: Optional[List[Callable[[Request, Exception], None]]] = None
    ):
        """
        Initialize the error handling middleware.
        
        Args:
            app: The FastAPI application to add error handling to
            include_debug_info: Whether to include debug info in error responses
            documentation_url_base: Base URL for error documentation
            on_error_callbacks: Callbacks to execute when errors occur
        """
        self.app = app
        self.include_debug_info = include_debug_info
        self.documentation_url_base = documentation_url_base
        self.on_error_callbacks = on_error_callbacks or []
        
        # Register exception handlers
        self.register_exception_handlers()
        
        # Add middleware
        app.middleware("http")(error_handler_middleware)
    
    def register_exception_handlers(self):
        """Register exception handlers with the FastAPI application."""
        
        # Handler for RequestValidationError (FastAPI validation)
        @self.app.exception_handler(RequestValidationError)
        async def validation_error_handler(request: Request, exc: RequestValidationError):
            # Convert validation errors to our format
            details = []
            for error in exc.errors():
                location = error.get("loc", [])
                field = location[-1] if location else None
                type_str = error.get("type", "")
                msg = error.get("msg", "")
                
                details.append(
                    ErrorDetail(
                        code=f"validation.{type_str}",
                        message=msg,
                        field=str(field) if field is not None else None
                    )
                )
            
            # Create MailyError from validation error
            error = ValidationError(
                message="Request validation failed",
                details=details
            )
            
            # Add request ID and context
            error.request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
            error.context = {
                "path": request.url.path,
                "method": request.method
            }
            
            # Execute error callbacks
            for callback in self.on_error_callbacks:
                try:
                    await callback(request, error)
                except Exception as callback_error:
                    logger.error(f"Error callback failed: {str(callback_error)}")
            
            # Return JSON response
            return JSONResponse(
                status_code=error.status_code,
                content=error.to_response()
            )
        
        # Handler for StarletteHTTPException
        @self.app.exception_handler(StarletteHTTPException)
        async def http_exception_handler(request: Request, exc: StarletteHTTPException):
            # Create MailyError from HTTP exception
            error = MailyError(
                message=str(exc.detail),
                status_code=exc.status_code
            )
            
            # Add request ID and context
            error.request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
            error.context = {
                "path": request.url.path,
                "method": request.method
            }
            
            # Execute error callbacks
            for callback in self.on_error_callbacks:
                try:
                    await callback(request, error)
                except Exception as callback_error:
                    logger.error(f"Error callback failed: {str(callback_error)}")
            
            # Return JSON response
            return JSONResponse(
                status_code=error.status_code,
                content=error.to_response(),
                headers=getattr(exc, "headers", None)
            )
        
        # Handler for MailyError
        @self.app.exception_handler(MailyError)
        async def maily_error_handler(request: Request, exc: MailyError):
            # Add request ID if not already set
            if not exc.request_id:
                exc.request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
            
            # Add context if not already set
            if not exc.context:
                exc.context = {}
            
            exc.context.update({
                "path": request.url.path,
                "method": request.method
            })
            
            # Execute error callbacks
            for callback in self.on_error_callbacks:
                try:
                    await callback(request, exc)
                except Exception as callback_error:
                    logger.error(f"Error callback failed: {str(callback_error)}")
            
            # Return JSON response
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.to_response(),
                headers=exc.headers
            )
        
        # Handler for general exceptions
        @self.app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            # Create ServerError from general exception
            error = ServerError.from_exception(
                exc,
                request_id=getattr(request.state, "request_id", str(uuid.uuid4())),
                context={
                    "path": request.url.path,
                    "method": request.method
                }
            )
            
            # Log the error
            logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
            
            # Execute error callbacks
            for callback in self.on_error_callbacks:
                try:
                    await callback(request, error)
                except Exception as callback_error:
                    logger.error(f"Error callback failed: {str(callback_error)}")
            
            # Return JSON response
            return JSONResponse(
                status_code=error.status_code,
                content=error.to_response()
            )


def setup_error_handling(
    app: FastAPI,
    include_debug_info: bool = False,
    documentation_url_base: Optional[str] = None,
    on_error_callbacks: Optional[List[Callable[[Request, Exception], None]]] = None
) -> ErrorHandlingMiddleware:
    """
    Set up standardized error handling for a FastAPI application.
    
    Args:
        app: The FastAPI application to set up error handling for
        include_debug_info: Whether to include debug info in error responses
        documentation_url_base: Base URL for error documentation
        on_error_callbacks: Callbacks to execute when errors occur
        
    Returns:
        Configured ErrorHandlingMiddleware instance
    """
    return ErrorHandlingMiddleware(
        app=app,
        include_debug_info=include_debug_info,
        documentation_url_base=documentation_url_base,
        on_error_callbacks=on_error_callbacks
    )