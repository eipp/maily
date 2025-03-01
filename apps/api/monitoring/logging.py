"""Structured logging module for Maily API.

This module provides structured logging capabilities for the Maily API service,
enabling consistent log formatting, log enrichment, and integration with
Grafana Loki for centralized log management.
"""

import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Union

from fastapi import FastAPI, Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

# Environment variables
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "json")  # json or text
LOG_RETENTION = os.getenv("LOG_RETENTION", "10 days")
LOG_ROTATION = os.getenv("LOG_ROTATION", "500 MB")
SERVICE_NAME = os.getenv("SERVICE_NAME", "maily-api")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

# Define log levels
LOG_LEVELS = {
    "TRACE": 5,
    "DEBUG": 10,
    "INFO": 20,
    "SUCCESS": 25,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}


class InterceptHandler(logging.Handler):
    """Intercept standard logging messages and redirect them to Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record.

        Args:
            record: The log record to emit
        """
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where the logged message originated
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


class JsonFormatter:
    """Format logs as JSON for structured logging."""

    def __init__(self):
        """Initialize the JSON formatter."""
        self.service_name = SERVICE_NAME
        self.environment = ENVIRONMENT

    def __call__(self, record: Dict[str, Any]) -> str:
        """Format the log record as JSON.

        Args:
            record: The log record to format

        Returns:
            The formatted log record as a JSON string
        """
        log_record = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "message": record["message"],
            "service": self.service_name,
            "environment": self.environment,
        }

        # Add exception info if present
        if record["exception"]:
            log_record["exception"] = record["exception"]

        # Add extra fields
        log_record.update(record["extra"])

        return json.dumps(log_record)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging with request ID tracking."""

    async def dispatch(
        self, request: Request, call_next: callable
    ) -> Response:
        """Process the request and log request/response details.

        Args:
            request: The FastAPI request
            call_next: The next middleware in the chain

        Returns:
            The response from the next middleware
        """
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Add request ID to request state for access in route handlers
        request.state.request_id = request_id

        # Start timer
        start_time = time.time()

        # Log request
        logger.bind(
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        ).info(f"Request started: {request.method} {request.url.path}")

        try:
            # Process request
            response = await call_next(request)

            # Calculate request duration
            duration = time.time() - start_time

            # Log response
            logger.bind(
                request_id=request_id,
                status_code=response.status_code,
                duration=duration,
            ).info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code} ({duration:.3f}s)"
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response
        except Exception as e:
            # Calculate request duration
            duration = time.time() - start_time

            # Log exception
            logger.bind(
                request_id=request_id,
                duration=duration,
                error=str(e),
            ).error(
                f"Request failed: {request.method} {request.url.path} - {str(e)}"
            )

            # Re-raise the exception
            raise


def setup_logging():
    """Set up structured logging for the application."""
    # Remove default handlers
    logging.root.handlers = []
    logging.root.setLevel(LOG_LEVELS.get(LOG_LEVEL, logging.INFO))

    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Remove default loguru handler
    logger.remove()

    # Configure loguru
    if LOG_FORMAT.lower() == "json":
        # JSON formatter for structured logging
        log_format = JsonFormatter()
    else:
        # Text formatter for human-readable logs
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level> | "
            "{extra}"
        )

    # Add file handler
    logger.add(
        f"logs/{SERVICE_NAME}_{{time}}.log",
        format=log_format,
        rotation=LOG_ROTATION,
        retention=LOG_RETENTION,
        level=LOG_LEVEL,
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

    # Add stderr handler
    logger.add(
        sys.stderr,
        format=log_format,
        level=LOG_LEVEL,
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

    # Intercept logs from other modules
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    logger.info(
        f"Logging initialized: level={LOG_LEVEL}, format={LOG_FORMAT}, "
        f"service={SERVICE_NAME}, environment={ENVIRONMENT}"
    )


def setup_app_logging(app: FastAPI):
    """Set up logging for a FastAPI application.

    Args:
        app: The FastAPI application
    """
    # Set up structured logging
    setup_logging()

    # Add logging middleware
    app.add_middleware(LoggingMiddleware)

    # Log application startup
    @app.on_event("startup")
    async def startup_event():
        logger.info(f"Application startup: {app.title} v{app.version}")

    # Log application shutdown
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info(f"Application shutdown: {app.title} v{app.version}")


def get_request_id() -> Optional[str]:
    """Get the current request ID from context.

    Returns:
        The current request ID or None if not available
    """
    try:
        from starlette.concurrency import iterate_in_threadpool
        from starlette.middleware.base import RequestResponseEndpoint

        # Get current request from context
        from fastapi import Request

        request = Request.scope.get("request")
        if request and hasattr(request.state, "request_id"):
            return request.state.request_id
    except Exception:
        pass

    return None


def log_with_context(
    level: str,
    message: str,
    **kwargs: Any
) -> None:
    """Log a message with context.

    Args:
        level: The log level
        message: The log message
        **kwargs: Additional context to include in the log
    """
    # Add request ID if available
    request_id = get_request_id()
    if request_id:
        kwargs["request_id"] = request_id

    # Log with context
    logger.bind(**kwargs).log(level, message)


# Convenience functions for logging with context
def debug(message: str, **kwargs: Any) -> None:
    """Log a debug message with context.

    Args:
        message: The log message
        **kwargs: Additional context to include in the log
    """
    log_with_context("DEBUG", message, **kwargs)


def info(message: str, **kwargs: Any) -> None:
    """Log an info message with context.

    Args:
        message: The log message
        **kwargs: Additional context to include in the log
    """
    log_with_context("INFO", message, **kwargs)


def warning(message: str, **kwargs: Any) -> None:
    """Log a warning message with context.

    Args:
        message: The log message
        **kwargs: Additional context to include in the log
    """
    log_with_context("WARNING", message, **kwargs)


def error(message: str, **kwargs: Any) -> None:
    """Log an error message with context.

    Args:
        message: The log message
        **kwargs: Additional context to include in the log
    """
    log_with_context("ERROR", message, **kwargs)


def critical(message: str, **kwargs: Any) -> None:
    """Log a critical message with context.

    Args:
        message: The log message
        **kwargs: Additional context to include in the log
    """
    log_with_context("CRITICAL", message, **kwargs)


def exception(message: str, exc: Exception, **kwargs: Any) -> None:
    """Log an exception with context.

    Args:
        message: The log message
        exc: The exception
        **kwargs: Additional context to include in the log
    """
    log_with_context("ERROR", message, exception=str(exc), **kwargs)
