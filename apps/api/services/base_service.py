"""
Base service class for standardizing service initialization and common methods.
"""
import logging
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel
from fastapi import Depends, HTTPException, status

from apps.api.database.session import get_db
from apps.api.config.settings import get_settings
from apps.api.utils.metrics import MetricsCollector

logger = logging.getLogger(__name__)

class ServiceMetrics(BaseModel):
    """Standard metrics model for services"""
    requests_count: int = 0
    success_count: int = 0
    error_count: int = 0
    latency_ms: List[float] = []

    def get_average_latency(self) -> float:
        """Calculate average latency"""
        if not self.latency_ms:
            return 0.0
        return sum(self.latency_ms) / len(self.latency_ms)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            "requests_count": self.requests_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "average_latency_ms": self.get_average_latency(),
            "total_latency_ms": sum(self.latency_ms)
        }

class BaseService:
    """
    Base service class with standardized initialization and common methods.

    This class provides a foundation for all services in the application,
    ensuring consistent initialization, logging, and error handling.
    """

    def __init__(self, db=None, settings=None):
        """
        Initialize the service with database session and settings.

        Args:
            db: Database session (optional)
            settings: Application settings (optional)
        """
        self.db = db
        self.settings = settings or get_settings()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.metrics = ServiceMetrics()
        self.metrics_collector = MetricsCollector()

    async def initialize(self) -> None:
        """
        Perform async initialization tasks.

        This method should be called after instantiation for services
        that require async initialization.
        """
        pass

    def log_error(self, error: Exception, context: Dict[str, Any] = None) -> None:
        """
        Log an error with standardized format.

        Args:
            error: The exception that occurred
            context: Additional context information
        """
        error_context = context or {}
        error_type = type(error).__name__

        self.logger.error(
            f"Error in {self.__class__.__name__}: {str(error)}",
            extra={
                "error_type": error_type,
                "service": self.__class__.__name__,
                **error_context
            }
        )

        self.metrics.error_count += 1

    def log_success(self, operation: str, latency_ms: float = 0.0) -> None:
        """
        Log a successful operation.

        Args:
            operation: Name of the operation
            latency_ms: Operation latency in milliseconds
        """
        self.logger.info(
            f"Operation '{operation}' completed successfully",
            extra={
                "operation": operation,
                "service": self.__class__.__name__,
                "latency_ms": latency_ms
            }
        )

        self.metrics.success_count += 1
        self.metrics.latency_ms.append(latency_ms)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get service metrics.

        Returns:
            Dictionary of service metrics
        """
        return self.metrics.to_dict()

    def reset_metrics(self) -> None:
        """Reset service metrics."""
        self.metrics = ServiceMetrics()

    @staticmethod
    def handle_common_exceptions(func):
        """
        Decorator for handling common exceptions in service methods.

        Args:
            func: The function to wrap

        Returns:
            Wrapped function with exception handling
        """
        async def wrapper(self, *args, **kwargs):
            try:
                return await func(self, *args, **kwargs)
            except HTTPException:
                # Re-raise HTTP exceptions as they're already properly formatted
                raise
            except Exception as e:
                self.log_error(e, {"args": args, "kwargs": kwargs})
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Service error: {str(e)}"
                )

        return wrapper
