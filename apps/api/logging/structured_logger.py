"""
Structured Logging Module

Provides a standardized approach to logging across the application with features
like JSON formatting, sensitive data masking, request context tracking, and
integration with monitoring systems.
"""

import json
import logging
import time
import inspect
import os
import sys
import traceback
import socket
import uuid
from typing import Any, Dict, List, Optional, Set, Union, Callable
from functools import wraps
import re
from contextlib import contextmanager

# Try to import FastAPI request, but don't fail if it's not available
try:
    from fastapi import Request
    from starlette.middleware.base import BaseHTTPMiddleware
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    Request = Any
    BaseHTTPMiddleware = object

# Global request context for tracking request-specific data
class RequestContext:
    """Thread-local storage for request context."""
    _data = {}

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Get a value from the request context."""
        return cls._data.get(key, default)

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """Set a value in the request context."""
        cls._data[key] = value

    @classmethod
    def clear(cls) -> None:
        """Clear the request context."""
        cls._data.clear()

    @classmethod
    def get_all(cls) -> Dict[str, Any]:
        """Get all values from the request context."""
        return cls._data.copy()


class LoggingConfig:
    """Configuration for structured logging."""

    def __init__(
        self,
        app_name: str = "maily",
        environment: str = "development",
        log_level: int = logging.INFO,
        format_as_json: bool = True,
        include_timestamp: bool = True,
        include_hostname: bool = True,
        include_logger_name: bool = True,
        include_function_name: bool = True,
        include_path_name: bool = True,
        include_line_number: bool = True,
        include_process_id: bool = True,
        include_thread_id: bool = False,
        include_request_context: bool = True,
        include_stack_trace: bool = True,
        mask_sensitive_data: bool = True,
        sensitive_fields: List[str] = None,
        max_record_size: int = 10000,
    ):
        """Initialize logging configuration."""
        self.app_name = app_name
        self.environment = environment
        self.log_level = log_level
        self.format_as_json = format_as_json
        self.include_timestamp = include_timestamp
        self.include_hostname = include_hostname
        self.include_logger_name = include_logger_name
        self.include_function_name = include_function_name
        self.include_path_name = include_path_name
        self.include_line_number = include_line_number
        self.include_process_id = include_process_id
        self.include_thread_id = include_thread_id
        self.include_request_context = include_request_context
        self.include_stack_trace = include_stack_trace
        self.mask_sensitive_data = mask_sensitive_data
        self.sensitive_fields = sensitive_fields or ["password", "token", "secret", "key", "auth",
                                                     "credential", "credit_card", "ssn", "birth_date"]
        self.max_record_size = max_record_size

        # Additional derived configuration
        self.hostname = socket.gethostname()
        self.process_id = os.getpid()

        # Sensitive data patterns
        self._sensitive_patterns = self._compile_sensitive_patterns()

    def _compile_sensitive_patterns(self) -> List[re.Pattern]:
        """Compile regex patterns for sensitive data masking."""
        patterns = []

        # Create patterns for each sensitive field
        for field in self.sensitive_fields:
            # Match JSON double quoted strings with the field name
            patterns.append(re.compile(f'"{field}"\s*:\s*"([^"]*)"', re.IGNORECASE))

            # Match JSON single quoted strings with the field name
            patterns.append(re.compile(f"'{field}'\s*:\s*'([^']*)'", re.IGNORECASE))

            # Match URL query parameters
            patterns.append(re.compile(f"{field}=([^&\s]+)", re.IGNORECASE))

            # Match headers in format "Field-Name: value"
            patterns.append(re.compile(f"{field}:\s*([^\r\n]+)", re.IGNORECASE))

        # Add patterns for common sensitive data formats

        # Credit card numbers (simple pattern)
        patterns.append(re.compile(r'\b(?:\d{4}[- ]?){3}\d{4}\b'))

        # Social Security Numbers (simple pattern for US SSNs)
        patterns.append(re.compile(r'\b\d{3}-\d{2}-\d{4}\b'))

        # Email addresses in most contexts
        patterns.append(re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'))

        # API keys and tokens (simplified pattern, actual tokens may have different formats)
        patterns.append(re.compile(r'\b[A-Za-z0-9_\-]{20,}\b'))

        return patterns


class StructuredFormatter(logging.Formatter):
    """Formatter for structured logging, supporting JSON output."""

    def __init__(self, config: LoggingConfig):
        """Initialize the formatter with configuration."""
        super().__init__()
        self.config = config

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a structured string or JSON."""
        # Create the base structured record
        structured_record = self._create_structured_record(record)

        # Convert to JSON if configured
        if self.config.format_as_json:
            # Truncate if too large
            if len(str(structured_record)) > self.config.max_record_size:
                structured_record = self._truncate_record(structured_record)

            # Mask sensitive data if enabled
            if self.config.mask_sensitive_data:
                structured_record = self._mask_sensitive_data(structured_record)

            return json.dumps(structured_record)
        else:
            return self._format_text(structured_record)

    def _create_structured_record(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Create a structured representation of the log record."""
        # Start with base fields
        structured = {
            "level": record.levelname,
            "message": record.getMessage(),
            "app": self.config.app_name,
            "env": self.config.environment,
        }

        # Add timestamp if configured
        if self.config.include_timestamp:
            structured["timestamp"] = int(record.created * 1000)  # milliseconds
            structured["time"] = time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime(record.created))

        # Add hostname if configured
        if self.config.include_hostname:
            structured["hostname"] = self.config.hostname

        # Add logger name if configured
        if self.config.include_logger_name:
            structured["logger"] = record.name

        # Add code location if configured
        if self.config.include_path_name:
            structured["path"] = record.pathname

        if self.config.include_function_name:
            structured["function"] = record.funcName

        if self.config.include_line_number:
            structured["line"] = record.lineno

        # Add process and thread info if configured
        if self.config.include_process_id:
            structured["pid"] = self.config.process_id

        if self.config.include_thread_id:
            structured["thread_id"] = record.thread
            structured["thread_name"] = record.threadName

        # Add exception info if present
        if record.exc_info and self.config.include_stack_trace:
            structured["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "stacktrace": self._format_stacktrace(record.exc_info) if record.exc_info[2] else None
            }

        # Add request context if configured
        if self.config.include_request_context:
            context = RequestContext.get_all()
            if context:
                structured["request"] = context

        # Add any extra attributes
        if hasattr(record, "extra") and record.extra:
            structured.update(record.extra)

        return structured

    def _format_stacktrace(self, exc_info) -> str:
        """Format exception stack trace."""
        return "".join(traceback.format_exception(*exc_info))

    def _truncate_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Truncate record if it's too large."""
        # Create a truncated copy
        truncated = record.copy()

        # First try to truncate message if it's very long
        if "message" in truncated and len(truncated["message"]) > 1000:
            truncated["message"] = truncated["message"][:1000] + "... (truncated)"

        # If still too large, truncate stacktrace if present
        if "exception" in truncated and "stacktrace" in truncated["exception"]:
            if len(truncated["exception"]["stacktrace"]) > 2000:
                truncated["exception"]["stacktrace"] = \
                    truncated["exception"]["stacktrace"][:2000] + "... (truncated)"

        # If still too large, remove extra fields
        keys_to_try = ["request", "extra", "context"]
        for key in keys_to_try:
            if key in truncated and len(json.dumps(truncated)) > self.config.max_record_size:
                truncated[key] = {"truncated": True, "reason": "Log record too large"}

        return truncated

    def _mask_sensitive_data(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive data in the record."""
        # Convert to string for pattern matching
        record_str = json.dumps(record)

        # Apply each pattern
        for pattern in self.config._sensitive_patterns:
            record_str = pattern.sub(r'"\1": "***REDACTED***"', record_str)

        # Convert back to dict
        try:
            return json.loads(record_str)
        except json.JSONDecodeError:
            # If JSON parsing fails, return original with warning
            record["_warning"] = "Failed to mask sensitive data"
            return record

    def _format_text(self, structured_record: Dict[str, Any]) -> str:
        """Format the structured record as plain text."""
        time_str = structured_record.get("time", "")
        level = structured_record.get("level", "")
        logger = structured_record.get("logger", "")
        message = structured_record.get("message", "")

        context_parts = []
        for key, value in structured_record.items():
            if key not in ["time", "level", "logger", "message"]:
                context_parts.append(f"{key}={value}")

        context_str = " ".join(context_parts) if context_parts else ""

        return f"{time_str} {level:8} [{logger}] {message} {context_str}"


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to add request context to logs."""

    def __init__(self, app, config: Optional[LoggingConfig] = None):
        """Initialize the middleware."""
        super().__init__(app)
        self.config = config or LoggingConfig()

    async def dispatch(self, request: Request, call_next):
        """Process the request and add context."""
        # Clear any existing context
        RequestContext.clear()

        # Generate request ID if not provided
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Add basic request context
        RequestContext.set("request_id", request_id)
        RequestContext.set("method", request.method)
        RequestContext.set("path", request.url.path)
        RequestContext.set("client_ip", self._get_client_ip(request))
        RequestContext.set("user_agent", request.headers.get("User-Agent"))

        # Add to request headers for propagation
        request.headers["X-Request-ID"] = request_id

        # Process the request
        start_time = time.time()
        try:
            response = await call_next(request)

            # Add response context
            RequestContext.set("status_code", response.status_code)
            RequestContext.set("response_time", time.time() - start_time)

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response
        except Exception as e:
            # Log the exception
            RequestContext.set("error", str(e))
            RequestContext.set("error_type", type(e).__name__)
            RequestContext.set("response_time", time.time() - start_time)
            raise
        finally:
            # Don't clear context here to allow for post-request logging
            pass

    def _get_client_ip(self, request):
        """Get the client IP from the request."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else None


class StructuredLogger:
    """
    Structured logger with context tracking, sensitive data masking,
    and standardized formatting.
    """

    def __init__(
        self,
        name: str,
        config: Optional[LoggingConfig] = None
    ):
        """
        Initialize the structured logger.

        Args:
            name: Logger name
            config: Logging configuration
        """
        self.name = name
        self.config = config or LoggingConfig()

        # Create the logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.config.log_level)

        # Create and add formatter
        self.formatter = StructuredFormatter(self.config)

        # Check if handler already exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(self.formatter)
            self.logger.addHandler(handler)

    def debug(self, msg: str, **kwargs):
        """Log a debug message."""
        self._log(logging.DEBUG, msg, **kwargs)

    def info(self, msg: str, **kwargs):
        """Log an info message."""
        self._log(logging.INFO, msg, **kwargs)

    def warning(self, msg: str, **kwargs):
        """Log a warning message."""
        self._log(logging.WARNING, msg, **kwargs)

    def error(self, msg: str, **kwargs):
        """Log an error message."""
        self._log(logging.ERROR, msg, **kwargs)

    def critical(self, msg: str, **kwargs):
        """Log a critical message."""
        self._log(logging.CRITICAL, msg, **kwargs)

    def exception(self, msg: str, exc_info=True, **kwargs):
        """Log an exception."""
        self._log(logging.ERROR, msg, exc_info=exc_info, **kwargs)

    def _log(self, level: int, msg: str, exc_info=None, **kwargs):
        """Internal method to log messages with context."""
        # Create a copy of kwargs to avoid modifying the original
        extra = kwargs.copy()

        # Get caller info for better logging
        caller_frame = inspect.currentframe().f_back
        extra["pathname"] = caller_frame.f_code.co_filename
        extra["lineno"] = caller_frame.f_lineno
        extra["funcName"] = caller_frame.f_code.co_name

        # Add extra context for the log record
        extra["extra"] = kwargs

        # Log the message
        self.logger.log(level, msg, exc_info=exc_info, extra=extra)

    @contextmanager
    def context(self, **kwargs):
        """
        Context manager to add temporary context to logs.

        Example:
            with logger.context(user_id="123", action="login"):
                logger.info("User logged in")
        """
        # Save the original context
        original_context = RequestContext.get_all()

        # Add new context
        for key, value in kwargs.items():
            RequestContext.set(key, value)

        try:
            yield
        finally:
            # Restore original context
            RequestContext.clear()
            for key, value in original_context.items():
                RequestContext.set(key, value)

    def with_context(self, **context_kwargs):
        """
        Decorator to add context to all logs in a function.

        Example:
            @logger.with_context(component="auth_service")
            def authenticate(user_id):
                logger.info(f"Authenticating user")
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.context(**context_kwargs):
                    return func(*args, **kwargs)
            return wrapper
        return decorator

    def track_time(self, operation_name: str):
        """
        Decorator to track execution time of a function.

        Example:
            @logger.track_time("database_query")
            def fetch_user(user_id):
                # ...
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    elapsed = time.time() - start_time

                    self.info(
                        f"{operation_name} completed",
                        operation=operation_name,
                        duration_ms=round(elapsed * 1000, 2)
                    )

                    return result
                except Exception as e:
                    elapsed = time.time() - start_time

                    self.exception(
                        f"{operation_name} failed",
                        operation=operation_name,
                        duration_ms=round(elapsed * 1000, 2),
                        error=str(e)
                    )

                    raise
            return wrapper
        return decorator


# Create global logger instance
def get_logger(name: str, config: Optional[LoggingConfig] = None) -> StructuredLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name
        config: Optional logging configuration

    Returns:
        Structured logger instance
    """
    return StructuredLogger(name, config)


# Helper function to set up FastAPI logging middleware
def setup_logging_middleware(app, config: Optional[LoggingConfig] = None):
    """
    Set up logging middleware for a FastAPI application.

    Args:
        app: FastAPI application
        config: Optional logging configuration
    """
    if not FASTAPI_AVAILABLE:
        raise ImportError("FastAPI is required for the logging middleware")

    app.add_middleware(RequestContextMiddleware, config=config)
    return app
