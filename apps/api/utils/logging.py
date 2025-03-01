import os
import json
import logging
import datetime
from typing import Any, Dict, Optional

# Configure logger
def configure_logger(name: str = "mailydocs", level: str = None) -> logging.Logger:
    """
    Configure a logger with JSON formatting for structured logging.

    Args:
        name: The name of the logger
        level: The logging level (INFO, DEBUG, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    if level is None:
        level = os.environ.get("LOG_LEVEL", "INFO")

    logger = logging.getLogger(name)

    # Set level based on environment or parameter
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO

    logger.setLevel(numeric_level)

    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler()

    # Create formatter for JSON logs
    formatter = JsonFormatter(name)
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    return logger

class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": self.service_name,
            "message": record.getMessage(),
            "logger": record.name,
            "path": record.pathname,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        return json.dumps(log_data)

def log_document_event(event_type: str, document_id: str, logger: logging.Logger, **kwargs) -> None:
    """
    Log a document-related event with structured data.

    Args:
        event_type: Type of event (created, generated, viewed, etc.)
        document_id: ID of the document
        logger: Logger instance
        **kwargs: Additional event data
    """
    extra = {
        "extra": {
            "event_type": event_type,
            "document_id": document_id,
            "context": kwargs
        }
    }

    logger.info(f"Document event: {event_type}", extra=extra)

def log_error(error: Exception, context: Dict[str, Any], logger: logging.Logger) -> None:
    """
    Log an error with context information.

    Args:
        error: The exception
        context: Context information
        logger: Logger instance
    """
    extra = {
        "extra": {
            "error_type": type(error).__name__,
            "context": context
        }
    }

    logger.error(f"Error: {str(error)}", exc_info=error, extra=extra)

def setup_mailydocs_logger() -> logging.Logger:
    """Set up the MailyDocs logger with appropriate configuration."""
    return configure_logger("mailydocs")
