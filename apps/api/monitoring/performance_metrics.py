"""
Performance metrics service for monitoring and telemetry.
Collects and reports metrics for system performance and health.
"""
from typing import Dict, List, Any, Optional, Union
from enum import Enum
import time
from datetime import datetime
import os
import json
import structlog
import asyncio
import threading
from prometheus_client import Counter, Histogram, Gauge, Summary, start_http_server

logger = structlog.get_logger(__name__)

class MetricType(str, Enum):
    """Types of metrics in the system."""
    API = "api"                  # API request metrics
    DATABASE = "database"        # Database operation metrics
    CACHE = "cache"              # Cache operation metrics
    AI = "ai"                    # AI operation metrics
    AI_REQUEST = "ai_request"    # AI request metrics
    AI_RESPONSE = "ai_response"  # AI response metrics
    AI_ERROR = "ai_error"        # AI error metrics
    INTEGRATION = "integration"  # External integration metrics
    SYSTEM = "system"            # System-level metrics
    CUSTOM = "custom"            # Custom metrics

class ExportFormat(str, Enum):
    """Metric export formats."""
    PROMETHEUS = "prometheus"
    JSON = "json"
    CSV = "csv"

class MetricsService:
    """Service for collecting and reporting performance metrics."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        """Singleton pattern to ensure only one metrics service exists."""
        if cls._instance is None:
            cls._instance = super(MetricsService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        app_name: str = "maily",
        enabled: bool = True,
        export_formats: List[ExportFormat] = None,
        prometheus_port: int = 9090,
        export_interval: int = 60
    ):
        """Initialize metrics service."""
        # Only initialize once
        if getattr(self, '_initialized', False):
            return

        self.app_name = app_name
        self.enabled = enabled
        self.export_formats = export_formats or [ExportFormat.PROMETHEUS]
        self.prometheus_port = prometheus_port
        self.export_interval = export_interval

        # Initialize metric collections
        self.counters = {}
        self.histograms = {}
        self.gauges = {}
        self.summaries = {}

        # Recent metrics buffer for internal querying
        self.recent_metrics = []
        self.max_recent_metrics = 1000

        # Setup metrics export
        if self.enabled:
            self._setup_exports()

        self._initialized = True
        logger.info("Metrics service initialized", app_name=app_name, enabled=enabled)

    def _setup_exports(self):
        """Setup metrics exports based on configured formats."""
        if ExportFormat.PROMETHEUS in self.export_formats:
            try:
                start_http_server(self.prometheus_port)
                logger.info("Prometheus metrics server started", port=self.prometheus_port)
            except Exception as e:
                logger.error("Failed to start Prometheus server", error=str(e))

        # Start export thread for other formats
        if any(f in self.export_formats for f in [ExportFormat.JSON, ExportFormat.CSV]):
            export_thread = threading.Thread(
                target=self._export_loop,
                daemon=True
            )
            export_thread.start()

    def _export_loop(self):
        """Background thread for periodic metrics export."""
        while True:
            try:
                time.sleep(self.export_interval)

                # Export metrics based on configured formats
                if ExportFormat.JSON in self.export_formats:
                    self._export_json()

                if ExportFormat.CSV in self.export_formats:
                    self._export_csv()

            except Exception as e:
                logger.error("Metrics export error", error=str(e))

    def _export_json(self):
        """Export metrics to JSON file."""
        try:
            metrics_dir = os.path.join(os.getcwd(), "metrics")
            os.makedirs(metrics_dir, exist_ok=True)

            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(metrics_dir, f"metrics_{timestamp}.json")

            # Collect metrics
            metrics_data = {
                "app_name": self.app_name,
                "timestamp": datetime.now().isoformat(),
                "counters": {name: counter._value.get() for name, counter in self.counters.items()},
                "gauges": {name: gauge._value.get() for name, gauge in self.gauges.items()},
                "recent_metrics": self.recent_metrics[-100:]  # Last 100 metrics
            }

            # Write to file
            with open(filename, "w") as f:
                json.dump(metrics_data, f, indent=2)

            logger.debug("Metrics exported to JSON", filename=filename)

        except Exception as e:
            logger.error("JSON export error", error=str(e))

    def _export_csv(self):
        """Export metrics to CSV file."""
        try:
            metrics_dir = os.path.join(os.getcwd(), "metrics")
            os.makedirs(metrics_dir, exist_ok=True)

            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(metrics_dir, f"metrics_{timestamp}.csv")

            # Write header and metrics
            with open(filename, "w") as f:
                f.write("timestamp,metric_name,metric_type,value\n")

                # Write counters
                for name, counter in self.counters.items():
                    f.write(f"{timestamp},{name},counter,{counter._value.get()}\n")

                # Write gauges
                for name, gauge in self.gauges.items():
                    f.write(f"{timestamp},{name},gauge,{gauge._value.get()}\n")

            logger.debug("Metrics exported to CSV", filename=filename)

        except Exception as e:
            logger.error("CSV export error", error=str(e))

    def record_metric(
        self,
        metric_type: Union[MetricType, str],
        name: str,
        value: float = 1.0,
        duration_ms: float = None,
        metadata: Dict[str, Any] = None,
        success: bool = True,
        error: str = None
    ):
        """Record a metric.

        Args:
            metric_type: Type of metric
            name: Metric name
            value: Metric value
            duration_ms: Optional duration in milliseconds
            metadata: Optional metadata
            success: Whether the operation was successful
            error: Optional error message
        """
        if not self.enabled:
            return

        # Normalize metric type to string
        if isinstance(metric_type, MetricType):
            metric_type = metric_type.value

        # Create full metric name
        full_name = f"{self.app_name}_{metric_type}_{name}"

        # Record counter
        counter_name = full_name
        if counter_name not in self.counters:
            self.counters[counter_name] = Counter(counter_name, full_name)
        self.counters[counter_name].inc(value)

        # Record duration if provided
        if duration_ms is not None:
            histogram_name = f"{full_name}_duration_ms"
            if histogram_name not in self.histograms:
                self.histograms[histogram_name] = Histogram(
                    histogram_name,
                    f"{full_name} duration in milliseconds",
                    buckets=(1, 5, 10, 50, 100, 500, 1000, 5000, 10000)
                )
            self.histograms[histogram_name].observe(duration_ms)

        # Record success/failure if relevant
        if metric_type in ["api", "integration", "ai", "ai_request", "ai_response"]:
            success_name = f"{full_name}_success"
            if success_name not in self.counters:
                self.counters[success_name] = Counter(
                    success_name,
                    f"{full_name} success count"
                )
            if success:
                self.counters[success_name].inc()

            # Record error if provided
            if not success and error:
                error_name = f"{full_name}_error"
                if error_name not in self.counters:
                    self.counters[error_name] = Counter(
                        error_name,
                        f"{full_name} error count"
                    )
                self.counters[error_name].inc()

        # Store in recent metrics buffer
        metric_entry = {
            "name": name,
            "type": metric_type,
            "value": value,
            "timestamp": datetime.now().isoformat(),
            "duration_ms": duration_ms,
            "metadata": metadata or {},
            "success": success,
            "error": error
        }

        self.recent_metrics.append(metric_entry)

        # Trim buffer if needed
        if len(self.recent_metrics) > self.max_recent_metrics:
            self.recent_metrics = self.recent_metrics[-self.max_recent_metrics:]

# Singleton instance getter
def get_metrics_service() -> MetricsService:
    """Get the metrics service instance."""
    return MetricsService()
