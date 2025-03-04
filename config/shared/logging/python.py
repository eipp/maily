"""
Standardized structured logging configuration for Python services.
"""

import logging
import json
import sys
import os
import traceback
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

# Default configuration
DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_LEVEL = 'INFO'
DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


class StructuredLogFormatter(logging.Formatter):
    """
    Formatter for structured JSON logs with consistent fields.
    """

    def __init__(self, service_name: str, environment: str):
        """
        Initialize the formatter with service context.
        
        Args:
            service_name: The name of the service.
            environment: The current environment (production, staging, development).
        """
        super().__init__()
        self.service_name = service_name
        self.environment = environment

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as a JSON string.
        
        Args:
            record: The log record to format.
            
        Returns:
            JSON formatted log string.
        """
        # Base log data
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": self.service_name,
            "environment": self.environment,
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        
        # Add exception info if available
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields from the record
        if hasattr(record, "trace_id"):
            log_data["trace_id"] = record.trace_id
            
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id
            
        # Add any extra attributes
        for key, value in record.__dict__.items():
            if key not in ["args", "asctime", "created", "exc_info", "exc_text", 
                          "filename", "funcName", "id", "levelname", "levelno", 
                          "lineno", "module", "msecs", "message", "msg", "name", 
                          "pathname", "process", "processName", "relativeCreated", 
                          "stack_info", "thread", "threadName"]:
                log_data[key] = value
                
        return json.dumps(log_data)


def configure_logger(service_name: str, 
                    environment: Optional[str] = None, 
                    log_level: Optional[str] = None) -> logging.Logger:
    """
    Configure a logger with standardized settings.
    
    Args:
        service_name: The name of the service.
        environment: The current environment (production, staging, development).
        log_level: The log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        
    Returns:
        Configured logger instance.
    """
    # Use environment variables as defaults if not specified
    if environment is None:
        environment = os.environ.get("ENVIRONMENT", "development")
        
    if log_level is None:
        log_level = os.environ.get("LOG_LEVEL", DEFAULT_LEVEL)
    
    # Create the logger
    logger = logging.getLogger(service_name)
    
    # Set log level
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler with structured formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredLogFormatter(service_name, environment))
    logger.addHandler(console_handler)
    
    # Add file handler in production
    if environment == "production":
        # Error log file
        error_handler = logging.FileHandler(f"/var/log/maily/{service_name}-error.log")
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(StructuredLogFormatter(service_name, environment))
        logger.addHandler(error_handler)
        
        # Combined log file
        file_handler = logging.FileHandler(f"/var/log/maily/{service_name}-combined.log")
        file_handler.setFormatter(StructuredLogFormatter(service_name, environment))
        logger.addHandler(file_handler)
    
    return logger


class RequestContextFilter(logging.Filter):
    """
    Logging filter that adds request-specific context to log records.
    """
    
    def __init__(self, request=None):
        """
        Initialize with an optional request object.
        
        Args:
            request: The web request object (FastAPI or similar).
        """
        super().__init__()
        self.request = request
        self.trace_id = getattr(request, "trace_id", str(uuid.uuid4()))
        self.user_id = getattr(request, "user_id", "anonymous")
        self.correlation_id = getattr(request, "correlation_id", None)
        
    def filter(self, record):
        """
        Add request context to the log record.
        
        Args:
            record: The log record to enhance.
            
        Returns:
            True to include the record in output.
        """
        record.trace_id = self.trace_id
        record.user_id = self.user_id
        
        if self.correlation_id:
            record.correlation_id = self.correlation_id
            
        if self.request:
            # Add request-specific fields if available
            record.method = getattr(self.request, "method", None)
            record.path = getattr(self.request, "path", None)
            record.client_ip = getattr(self.request, "client", {}).get("host", None)
        
        return True


def get_request_logger(service_logger, request):
    """
    Create a request-scoped logger with request context.
    
    Args:
        service_logger: The base service logger.
        request: The request object.
        
    Returns:
        Logger with request context.
    """
    # Create a child logger
    logger = service_logger.getChild(f"request.{id(request)}")
    
    # Add request context filter
    context_filter = RequestContextFilter(request)
    logger.addFilter(context_filter)
    
    return logger