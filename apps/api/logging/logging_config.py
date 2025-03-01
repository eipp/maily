"""
Enhanced logging configuration with structured logging and context.
"""
import logging
import sys
import time
import json
from typing import Optional, Dict, Any, List, Union
import uuid
import structlog
from structlog.contextvars import merge_contextvars
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from contextvars import ContextVar

# Context variables for request tracking
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
tenant_id_var: ContextVar[Optional[str]] = ContextVar("tenant_id", default=None)

def setup_logging(log_level: str = "INFO", json_logs: bool = True, log_request_id: bool = True):
    """Set up structured logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Whether to output logs in JSON format
        log_request_id: Whether to include request_id in logs
    """
    log_level_num = getattr(logging, log_level.upper(), logging.INFO)

    # Configure standard logging
    logging.basicConfig(
        level=log_level_num,
        format="%(message)s",
        stream=sys.stdout,
    )

    # Set up shared processors
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Add JSON renderer if enabled, otherwise use console renderer
    if json_logs:
        shared_processors.append(structlog.processors.JSONRenderer())
    else:
        shared_processors.append(
            structlog.dev.ConsoleRenderer(colors=True, exception_formatter=structlog.dev.pretty_exc_info)
        )

    # Configure structlog
    structlog.configure(
        processors=shared_processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def get_request_id() -> str:
    """Get the current request ID from context or generate a new one.

    Returns:
        Current request ID string
    """
    request_id = request_id_var.get()
    if not request_id:
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)
    return request_id

def get_user_id() -> Optional[str]:
    """Get the current user ID from context.

    Returns:
        Current user ID or None
    """
    return user_id_var.get()

def get_tenant_id() -> Optional[str]:
    """Get the current tenant ID from context.

    Returns:
        Current tenant ID or None
    """
    return tenant_id_var.get()

def bind_contextvars(
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    **kwargs
):
    """Bind values to context variables for logging.

    Args:
        request_id: Request ID to bind
        user_id: User ID to bind
        tenant_id: Tenant ID to bind
        **kwargs: Additional context key-value pairs
    """
    if request_id:
        request_id_var.set(request_id)
        structlog.contextvars.bind_contextvars(request_id=request_id)

    if user_id:
        user_id_var.set(user_id)
        structlog.contextvars.bind_contextvars(user_id=user_id)

    if tenant_id:
        tenant_id_var.set(tenant_id)
        structlog.contextvars.bind_contextvars(tenant_id=tenant_id)

    if kwargs:
        structlog.contextvars.bind_contextvars(**kwargs)

def clear_contextvars():
    """Clear all context variables."""
    structlog.contextvars.clear_contextvars()
    # Reinitialize with empty values
    request_id_var.set("")
    user_id_var.set(None)
    tenant_id_var.set(None)

def get_logger(name: str = "maily"):
    """Get a configured structlog logger.

    Args:
        name: Logger name

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging with context tracking."""

    def __init__(
        self,
        app: ASGIApp,
        log_request_body: bool = False,
        log_response_body: bool = False,
        excluded_paths: List[str] = None
    ):
        """Initialize the logging middleware.

        Args:
            app: The ASGI application
            log_request_body: Whether to log request bodies
            log_response_body: Whether to log response bodies
            excluded_paths: List of path prefixes to exclude from logging
        """
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.excluded_paths = excluded_paths or ["/health", "/metrics", "/docs", "/openapi.json"]
        self.logger = get_logger("maily.http")

    async def dispatch(self, request: Request, call_next):
        """Process the request and log with context.

        Args:
            request: The FastAPI request
            call_next: The next middleware or endpoint handler

        Returns:
            The response
        """
        # Skip logging for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)

        # Initialize context with request ID and path
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        start_time = time.time()

        # Bind context variables for this request
        bind_contextvars(
            request_id=request_id,
            path=request.url.path,
            method=request.method,
            client_ip=request.client.host if request.client else None
        )

        # Log the request
        request_logging_extras = {}
        if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Clone the request to read the body
                body = await request.body()
                # Only log if it's not too large
                if len(body) < 10000:  # Limit to 10KB
                    try:
                        request_logging_extras["body"] = json.loads(body)
                    except:
                        request_logging_extras["body"] = body.decode("utf-8", errors="replace")
            except:
                pass

        self.logger.info(
            f"Request started: {request.method} {request.url.path}",
            user_agent=request.headers.get("user-agent"),
            referer=request.headers.get("referer"),
            content_length=request.headers.get("content-length"),
            **request_logging_extras
        )

        try:
            # Process the request
            response = await call_next(request)

            # Calculate duration
            duration_ms = round((time.time() - start_time) * 1000, 2)

            # Log the response
            response_logging_extras = {}
            if self.log_response_body and response.status_code >= 400:
                # For error responses, try to capture the response body
                try:
                    # This is a bit hacky but works in many cases
                    if hasattr(response, "body"):
                        body = response.body
                        if body and len(body) < 10000:  # Limit to 10KB
                            try:
                                response_logging_extras["body"] = json.loads(body)
                            except:
                                response_logging_extras["body"] = body.decode("utf-8", errors="replace")
                except:
                    pass

            log_method = self.logger.info if response.status_code < 500 else self.logger.error
            log_method(
                f"Request completed: {request.method} {request.url.path}",
                status_code=response.status_code,
                duration_ms=duration_ms,
                **response_logging_extras
            )

            # Add request ID header to response
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Log exceptions
            duration_ms = round((time.time() - start_time) * 1000, 2)
            self.logger.exception(
                f"Request failed: {request.method} {request.url.path}",
                error=str(e),
                error_type=e.__class__.__name__,
                duration_ms=duration_ms
            )
            raise
        finally:
            # Always clear context after request is processed
            clear_contextvars()

def setup_app_logging(app: FastAPI, log_level: str = "INFO", json_logs: bool = True):
    """Configure logging for a FastAPI application.

    Args:
        app: FastAPI application
        log_level: Logging level
        json_logs: Whether to output logs in JSON format
    """
    # Set up basic logging configuration
    setup_logging(log_level, json_logs)

    # Add logging middleware to the application
    app.add_middleware(LoggingMiddleware)

    # Add request context middleware to include request ID in all logs
    @app.middleware("http")
    async def add_request_context(request: Request, call_next):
        # Extract request ID or generate a new one
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Extract user ID if available from auth
        user_id = None
        if hasattr(request.state, "user") and hasattr(request.state.user, "id"):
            user_id = str(request.state.user.id)

        # Bind context variables
        bind_contextvars(
            request_id=request_id,
            user_id=user_id
        )

        # Process the request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response
