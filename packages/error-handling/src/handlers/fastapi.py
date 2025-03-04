"""
FastAPI error handling middleware

This module provides middleware and exception handlers for FastAPI applications,
standardizing error responses across services.
"""

from typing import Any, Callable, Dict, List, Optional, Type, Union
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from pydantic import ValidationError

import logging
import traceback
import inspect
import json
import uuid
from datetime import datetime

logger = logging.getLogger("maily.error_handling")

# Default error codes
HTTP_ERROR_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMIT_EXCEEDED",
    500: "INTERNAL_SERVER_ERROR",
    502: "BAD_GATEWAY",
    503: "SERVICE_UNAVAILABLE",
    504: "GATEWAY_TIMEOUT"
}

class ApplicationError(Exception):
    """Base class for application errors"""
    
    def __init__(
        self, 
        message: str, 
        code: str = "INTERNAL_ERROR", 
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        self.trace_id = trace_id or f"err_{uuid.uuid4().hex}"
        super().__init__(message)
    
    def to_response(self) -> Dict[str, Any]:
        """Convert error to standardized response format"""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
                "trace_id": self.trace_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }

def setup_error_handlers(app: FastAPI) -> None:
    """Set up error handlers for a FastAPI application"""
    
    @app.exception_handler(ApplicationError)
    async def handle_application_error(request: Request, exc: ApplicationError) -> JSONResponse:
        """Handle ApplicationError instances"""
        # Log error with trace ID
        log_error(request, exc, exc.trace_id)
        
        # Return standardized response
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_response()
        )
    
    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle FastAPI validation errors"""
        # Format validation errors
        validation_errors = format_validation_errors(exc.errors())
        
        # Generate trace ID
        trace_id = f"err_{uuid.uuid4().hex}"
        
        # Convert to response format
        content = {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {"validation_errors": validation_errors},
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        # Log error with trace ID
        log_error(request, exc, trace_id, validation_errors)
        
        return JSONResponse(
            status_code=422,
            content=content
        )
    
    @app.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle FastAPI/Starlette HTTP exceptions"""
        # Get error code for status
        error_code = HTTP_ERROR_CODES.get(exc.status_code, "ERROR")
        
        # Generate trace ID
        trace_id = f"err_{uuid.uuid4().hex}"
        
        # Convert to response format
        content = {
            "error": {
                "code": error_code,
                "message": exc.detail,
                "details": getattr(exc, "details", {}),
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        # Log error with trace ID
        log_error(request, exc, trace_id)
        
        return JSONResponse(
            status_code=exc.status_code,
            content=content
        )
    
    @app.exception_handler(Exception)
    async def handle_unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
        """Handle any unhandled exceptions"""
        # Generate trace ID
        trace_id = f"err_{uuid.uuid4().hex}"
        
        # Convert to response format
        content = {
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "trace_id": trace_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        # Log error with stack trace
        log_error(request, exc, trace_id, include_stack=True)
        
        return JSONResponse(
            status_code=500,
            content=content
        )

def log_error(
    request: Request, 
    exc: Exception, 
    trace_id: str, 
    details: Optional[Dict[str, Any]] = None,
    include_stack: bool = False
) -> None:
    """Log an error with request details and trace ID"""
    
    # Get request information
    method = request.method
    url = str(request.url)
    client_host = request.client.host if request.client else "unknown"
    
    # Build error log
    log_data = {
        "trace_id": trace_id,
        "error_type": exc.__class__.__name__,
        "error_message": str(exc),
        "request": {
            "method": method,
            "url": url,
            "client_ip": client_host,
            "headers": dict(request.headers)
        }
    }
    
    # Add details if provided
    if details:
        log_data["details"] = details
    
    # Add stack trace for unexpected errors
    if include_stack:
        log_data["stack_trace"] = traceback.format_exc()
    
    # Log as error
    logger.error(f"Error handling request: {json.dumps(log_data)}")

def format_validation_errors(errors: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Format validation errors into field:messages structure"""
    formatted_errors: Dict[str, List[str]] = {}
    
    for error in errors:
        # Get field path
        loc = error.get("loc", [])
        
        # Skip request body/query type errors
        if loc and loc[0] in ("body", "query", "path", "header"):
            loc = loc[1:]
        
        # Join path parts with dots
        field = ".".join(str(item) for item in loc)
        
        # Get error message
        message = error.get("msg", "Invalid value")
        
        # Add to formatted errors
        if field not in formatted_errors:
            formatted_errors[field] = []
        
        formatted_errors[field].append(message)
    
    return formatted_errors

def error_middleware(enable_tracing: bool = True):
    """
    Create error handling middleware that wraps the entire request lifecycle.
    
    This middleware captures exceptions from the request processing pipeline
    and ensures consistent error responses.
    """
    
    async def error_middleware_impl(request: Request, call_next: Callable) -> Response:
        try:
            # Generate trace ID
            trace_id = f"trace_{uuid.uuid4().hex}"
            
            # Add trace ID to request state
            request.state.trace_id = trace_id
            
            # Process request
            response = await call_next(request)
            return response
            
        except Exception as exc:
            # Handle exceptions not caught by exception handlers
            
            # Generate trace ID if not already set
            trace_id = getattr(request.state, "trace_id", f"err_{uuid.uuid4().hex}")
            
            # Log error
            log_error(request, exc, trace_id, include_stack=True)
            
            # Convert to response format
            content = {
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            return JSONResponse(
                status_code=500,
                content=content
            )
    
    return error_middleware_impl

def setup_error_handling(app: FastAPI) -> None:
    """Set up complete error handling for a FastAPI application"""
    # Add middleware
    app.middleware("http")(error_middleware())
    
    # Add exception handlers
    setup_error_handlers(app)