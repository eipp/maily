"""
Health monitoring service.

This service provides detailed health checks for all system components
with support for degraded operation modes and alerting.
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, Awaitable

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComponentStatus(str, Enum):
    """Component status enum."""
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class SystemStatus(str, Enum):
    """Overall system status enum."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"


class HealthCheckResult:
    """Result of a health check."""

    def __init__(
        self,
        status: ComponentStatus,
        component_name: str,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        latency_ms: float = 0,
        checked_at: Optional[datetime] = None
    ):
        """
        Initialize a health check result.

        Args:
            status: Component status
            component_name: Name of the component
            details: Additional details
            error: Error message if any
            latency_ms: Check latency in milliseconds
            checked_at: When the check was performed
        """
        self.status = status
        self.component_name = component_name
        self.details = details or {}
        self.error = error
        self.latency_ms = latency_ms
        self.checked_at = checked_at or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "status": self.status,
            "checked_at": self.checked_at.isoformat(),
            "latency_ms": self.latency_ms
        }

        if self.details:
            result["details"] = self.details

        if self.error:
            result["error"] = self.error

        return result


class HealthCheck:
    """Health check definition."""

    def __init__(
        self,
        name: str,
        check_function: Callable[[], Awaitable[HealthCheckResult]],
        critical: bool = False,
        timeout: float = 5.0,
        interval: float = 60.0
    ):
        """
        Initialize a health check.

        Args:
            name: Component name
            check_function: Async function that performs the check
            critical: Whether this component is critical for system operation
            timeout: Timeout in seconds
            interval: Check interval in seconds
        """
        self.name = name
        self.check_function = check_function
        self.critical = critical
        self.timeout = timeout
        self.interval = interval
        self.last_result = None
        self.last_check_time = None

    async def run(self) -> HealthCheckResult:
        """
        Run the health check with timeout.

        Returns:
            HealthCheckResult
        """
        start_time = time.time()
        self.last_check_time = datetime.now()

        try:
            # Run check with timeout
            result = await asyncio.wait_for(
                self.check_function(),
                timeout=self.timeout
            )

            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            result.latency_ms = latency_ms

        except asyncio.TimeoutError:
            # Check timed out
            latency_ms = (time.time() - start_time) * 1000
            result = HealthCheckResult(
                status=ComponentStatus.DEGRADED,
                component_name=self.name,
                error=f"Health check timed out after {self.timeout}s",
                latency_ms=latency_ms
            )

        except Exception as e:
            # Check failed
            latency_ms = (time.time() - start_time) * 1000
            result = HealthCheckResult(
                status=ComponentStatus.UNAVAILABLE,
                component_name=self.name,
                error=str(e),
                latency_ms=latency_ms
            )

        # Store result
        self.last_result = result

        return result


class AlertChannel:
    """Base class for alert channels."""

    async def send_alert(self, message: str, details: Dict[str, Any]) -> bool:
        """
        Send an alert.

        Args:
            message: Alert message
            details: Alert details

        Returns:
            True if alert was sent successfully
        """
        raise NotImplementedError("Subclasses must implement send_alert")


class LogAlertChannel(AlertChannel):
    """Alert channel that logs alerts."""

    async def send_alert(self, message: str, details: Dict[str, Any]) -> bool:
        """
        Send an alert by logging it.

        Args:
            message: Alert message
            details: Alert details

        Returns:
            True if alert was logged successfully
        """
        logger.warning(f"ALERT: {message}")
        logger.warning(f"Details: {json.dumps(details)}")
        return True


class HealthService:
    """Service for monitoring system health."""

    def __init__(self, alert_channels: Optional[List[AlertChannel]] = None):
        """
        Initialize the health service.

        Args:
            alert_channels: List of alert channels
        """
        self.start_time = datetime.now()
        self.health_checks: Dict[str, HealthCheck] = {}
        self.alert_channels = alert_channels or [LogAlertChannel()]
        self.maintenance_mode = False
        self.latest_results: Dict[str, HealthCheckResult] = {}
        self.check_task = None

    def register_component(
        self,
        name: str,
        check_function: Callable[[], Awaitable[HealthCheckResult]],
        critical: bool = False,
        timeout: float = 5.0,
        interval: float = 60.0
    ) -> None:
        """
        Register a component to monitor.

        Args:
            name: Component name
            check_function: Async function that performs the check
            critical: Whether this component is critical for system operation
            timeout: Timeout in seconds
            interval: Check interval in seconds
        """
        self.health_checks[name] = HealthCheck(
            name=name,
            check_function=check_function,
            critical=critical,
            timeout=timeout,
            interval=interval
        )

    def register_database_check(
        self,
        db_service,
        name: str = "database",
        critical: bool = True
    ) -> None:
        """
        Register a database health check.

        Args:
            db_service: Database service with check_health method
            name: Component name
            critical: Whether this component is critical
        """
        async def check_database() -> HealthCheckResult:
            try:
                # Call database health check
                is_healthy = await db_service.check_db_health()

                if is_healthy:
                    return HealthCheckResult(
                        status=ComponentStatus.OPERATIONAL,
                        component_name=name,
                        details={"connections": "active"}
                    )
                else:
                    return HealthCheckResult(
                        status=ComponentStatus.DEGRADED,
                        component_name=name,
                        error="Database connection issues detected"
                    )
            except Exception as e:
                return HealthCheckResult(
                    status=ComponentStatus.UNAVAILABLE,
                    component_name=name,
                    error=str(e)
                )

        self.register_component(
            name=name,
            check_function=check_database,
            critical=critical
        )

    def register_redis_check(
        self,
        redis_service,
        name: str = "redis",
        critical: bool = False
    ) -> None:
        """
        Register a Redis health check.

        Args:
            redis_service: Redis service with check_redis_health method
            name: Component name
            critical: Whether this component is critical
        """
        async def check_redis() -> HealthCheckResult:
            try:
                # Call Redis health check
                is_healthy = await redis_service.check_redis_health()

                if is_healthy:
                    return HealthCheckResult(
                        status=ComponentStatus.OPERATIONAL,
                        component_name=name
                    )
                else:
                    return HealthCheckResult(
                        status=ComponentStatus.DEGRADED,
                        component_name=name,
                        error="Redis connection issues detected"
                    )
            except Exception as e:
                return HealthCheckResult(
                    status=ComponentStatus.UNAVAILABLE,
                    component_name=name,
                    error=str(e)
                )

        self.register_component(
            name=name,
            check_function=check_redis,
            critical=critical
        )

    def register_ai_service_check(
        self,
        ai_service,
        name: str = "ai_service",
        critical: bool = False
    ) -> None:
        """
        Register an AI service health check.

        Args:
            ai_service: AI service with check_health method
            name: Component name
            critical: Whether this component is critical
        """
        async def check_ai_service() -> HealthCheckResult:
            try:
                # Call AI service health check
                is_healthy = await ai_service.check_health()

                if is_healthy:
                    return HealthCheckResult(
                        status=ComponentStatus.OPERATIONAL,
                        component_name=name
                    )
                else:
                    return HealthCheckResult(
                        status=ComponentStatus.DEGRADED,
                        component_name=name,
                        error="AI service issues detected"
                    )
            except Exception as e:
                return HealthCheckResult(
                    status=ComponentStatus.UNAVAILABLE,
                    component_name=name,
                    error=str(e)
                )

        self.register_component(
            name=name,
            check_function=check_ai_service,
            critical=critical
        )

    async def check_all(self) -> Dict[str, Any]:
        """
        Check all registered components.

        Returns:
            Health check results
        """
        results = {}
        overall_status = SystemStatus.HEALTHY

        # Check if in maintenance mode
        if self.maintenance_mode:
            return {
                "status": SystemStatus.MAINTENANCE,
                "components": {},
                "uptime": (datetime.now() - self.start_time).total_seconds(),
                "timestamp": datetime.now().isoformat(),
                "message": "System is in maintenance mode"
            }

        # Run all health checks concurrently
        check_tasks = []
        for component_name, health_check in self.health_checks.items():
            check_tasks.append(health_check.run())

        # Gather results
        check_results = await asyncio.gather(*check_tasks, return_exceptions=True)

        # Process results
        for i, (component_name, health_check) in enumerate(self.health_checks.items()):
            result = check_results[i]

            # Handle exceptions
            if isinstance(result, Exception):
                result = HealthCheckResult(
                    status=ComponentStatus.UNAVAILABLE,
                    component_name=component_name,
                    error=str(result)
                )

            # Store result
            self.latest_results[component_name] = result
            results[component_name] = result.to_dict()

            # Update overall status
            if result.status == ComponentStatus.UNAVAILABLE and health_check.critical:
                overall_status = SystemStatus.UNHEALTHY
            elif result.status != ComponentStatus.OPERATIONAL and overall_status == SystemStatus.HEALTHY:
                overall_status = SystemStatus.DEGRADED

        # Build response
        return {
            "status": overall_status,
            "components": results,
            "uptime": (datetime.now() - self.start_time).total_seconds(),
            "timestamp": datetime.now().isoformat()
        }

    async def start_monitoring(self) -> None:
        """Start background health monitoring."""
        if self.check_task:
            return

        # Start background task
        self.check_task = asyncio.create_task(self._monitoring_loop())

    async def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        while True:
            try:
                # Check all components
                results = await self.check_all()

                # Check for alerts
                await self._process_alerts(results)

                # Wait for next check
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(60)  # Retry after a minute

    async def _process_alerts(self, results: Dict[str, Any]) -> None:
        """
        Process alerts based on health check results.

        Args:
            results: Health check results
        """
        # Check overall status
        if results["status"] == SystemStatus.UNHEALTHY:
            # Send alert for unhealthy system
            await self._send_alert(
                message="System is unhealthy",
                details=results
            )

        # Check individual components
        for component_name, result in results.get("components", {}).items():
            if result["status"] == ComponentStatus.UNAVAILABLE:
                # Send alert for unavailable component
                await self._send_alert(
                    message=f"Component {component_name} is unavailable",
                    details={
                        "component": component_name,
                        "error": result.get("error"),
                        "timestamp": result.get("checked_at")
                    }
                )

    async def _send_alert(self, message: str, details: Dict[str, Any]) -> None:
        """
        Send alert to all channels.

        Args:
            message: Alert message
            details: Alert details
        """
        for channel in self.alert_channels:
            try:
                await channel.send_alert(message, details)
            except Exception as e:
                logger.error(f"Failed to send alert: {e}")

    def set_maintenance_mode(self, enabled: bool) -> None:
        """
        Set maintenance mode.

        Args:
            enabled: Whether maintenance mode is enabled
        """
        self.maintenance_mode = enabled

        # Log maintenance mode change
        if enabled:
            logger.info("System entered maintenance mode")
        else:
            logger.info("System exited maintenance mode")

    def get_uptime(self) -> float:
        """
        Get system uptime in seconds.

        Returns:
            Uptime in seconds
        """
        return (datetime.now() - self.start_time).total_seconds()

    async def check_readiness(self) -> Dict[str, Any]:
        """
        Check if the system is ready to serve requests.

        Returns:
            Readiness status
        """
        # Only check critical components
        results = {}
        ready = True

        for component_name, health_check in self.health_checks.items():
            if health_check.critical:
                # Get the latest result or run a new check
                if (
                    component_name in self.latest_results and
                    self.latest_results[component_name].checked_at > datetime.now() - timedelta(minutes=1)
                ):
                    result = self.latest_results[component_name]
                else:
                    result = await health_check.run()
                    self.latest_results[component_name] = result

                # Store result
                results[component_name] = result.to_dict()

                # Update readiness
                if result.status == ComponentStatus.UNAVAILABLE:
                    ready = False

        return {
            "status": "ready" if ready else "not_ready",
            "checks": results,
            "timestamp": datetime.now().isoformat()
        }

    async def check_liveness(self) -> Dict[str, Any]:
        """
        Check if the system is alive.

        Returns:
            Liveness status
        """
        return {
            "status": "alive",
            "uptime": self.get_uptime(),
            "timestamp": datetime.now().isoformat()
        }


# Create a singleton instance
health_service = HealthService()
