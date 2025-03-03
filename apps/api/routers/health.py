"""
Health check endpoints for the API service.

This module provides health check endpoints for the API service, including
detailed health checks for all dependencies.
"""

import logging
import os
import time
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from apps.api.utils.resilience import get_circuit_breaker
from apps.api.config.settings import get_settings

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/health",
    tags=["Health"],
)

# Define models
class ComponentHealth(BaseModel):
    """Health status of a component."""
    status: str = Field(..., description="Health status of the component")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details about the component health")
    latency_ms: Optional[float] = Field(None, description="Latency in milliseconds")
    last_check: Optional[str] = Field(None, description="ISO timestamp of the last health check")

class CircuitBreakerStatus(BaseModel):
    """Status of a circuit breaker."""
    name: str = Field(..., description="Name of the circuit breaker")
    state: str = Field(..., description="Current state of the circuit breaker")
    failure_count: int = Field(..., description="Current failure count")
    failure_threshold: int = Field(..., description="Failure threshold")
    recovery_timeout: float = Field(..., description="Recovery timeout in seconds")
    last_failure_time: Optional[float] = Field(None, description="Timestamp of the last failure")

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Overall health status")
    timestamp: str = Field(..., description="ISO timestamp of the health check")
    version: str = Field(..., description="API version")
    environment: str = Field(..., description="Environment (production, staging, development)")
    uptime_seconds: float = Field(..., description="API uptime in seconds")
    components: Dict[str, ComponentHealth] = Field(..., description="Health status of individual components")
    circuit_breakers: List[CircuitBreakerStatus] = Field(default_factory=list, description="Status of circuit breakers")

# Start time of the service
START_TIME = time.time()

# Health check functions
async def check_database_health() -> ComponentHealth:
    """Check the health of the database."""
    start_time = time.time()
    try:
        # Import here to avoid circular imports
        from apps.api.utils.db_session import get_db
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy import text
        
        # Get a database session
        db_session = get_db()
        session = await anext(db_session.__aiter__())
        
        # Execute a simple query
        result = await session.execute(text("SELECT 1"))
        await session.close()
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        return ComponentHealth(
            status="healthy",
            details={"connection": "successful"},
            latency_ms=latency_ms,
            last_check=datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return ComponentHealth(
            status="unhealthy",
            details={"error": str(e)},
            latency_ms=(time.time() - start_time) * 1000,
            last_check=datetime.now(timezone.utc).isoformat()
        )

async def check_redis_health() -> ComponentHealth:
    """Check the health of Redis."""
    start_time = time.time()
    try:
        # Check if Redis is configured
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            return ComponentHealth(
                status="skipped",
                details={"reason": "Redis not configured"},
                last_check=datetime.now(timezone.utc).isoformat()
            )
        
        # Import Redis client
        import redis.asyncio as redis
        
        # Connect to Redis
        redis_client = redis.from_url(redis_url)
        
        # Ping Redis
        await redis_client.ping()
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        return ComponentHealth(
            status="healthy",
            details={"connection": "successful"},
            latency_ms=latency_ms,
            last_check=datetime.now(timezone.utc).isoformat()
        )
    except ImportError:
        return ComponentHealth(
            status="skipped",
            details={"reason": "Redis client not installed"},
            last_check=datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return ComponentHealth(
            status="unhealthy",
            details={"error": str(e)},
            latency_ms=(time.time() - start_time) * 1000,
            last_check=datetime.now(timezone.utc).isoformat()
        )

async def check_ai_service_health() -> ComponentHealth:
    """Check the health of the AI service."""
    start_time = time.time()
    try:
        # Import here to avoid circular imports
        from apps.api.ai import AIService
        
        # Get AI service
        ai_service = AIService()
        
        # Check health
        health = await ai_service.check_health()
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        if health.get("status") == "healthy":
            return ComponentHealth(
                status="healthy",
                details=health,
                latency_ms=latency_ms,
                last_check=datetime.now(timezone.utc).isoformat()
            )
        else:
            return ComponentHealth(
                status="unhealthy",
                details=health,
                latency_ms=latency_ms,
                last_check=datetime.now(timezone.utc).isoformat()
            )
    except Exception as e:
        logger.error(f"AI service health check failed: {str(e)}")
        return ComponentHealth(
            status="unhealthy",
            details={"error": str(e)},
            latency_ms=(time.time() - start_time) * 1000,
            last_check=datetime.now(timezone.utc).isoformat()
        )

async def check_email_service_health() -> ComponentHealth:
    """Check the health of the email service."""
    start_time = time.time()
    try:
        # Check if email service is configured
        email_api_key = os.getenv("EMAIL_SERVICE_API_KEY")
        email_api_url = os.getenv("EMAIL_SERVICE_URL")
        
        if not email_api_key or not email_api_url:
            return ComponentHealth(
                status="skipped",
                details={"reason": "Email service not configured"},
                last_check=datetime.now(timezone.utc).isoformat()
            )
        
        # Import here to avoid circular imports
        import httpx
        
        # Make a request to the email service health endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{email_api_url}/health",
                headers={"X-API-Key": email_api_key},
                timeout=5.0
            )
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                return ComponentHealth(
                    status="healthy",
                    details=response.json(),
                    latency_ms=latency_ms,
                    last_check=datetime.now(timezone.utc).isoformat()
                )
            else:
                return ComponentHealth(
                    status="unhealthy",
                    details={
                        "status_code": response.status_code,
                        "response": response.text
                    },
                    latency_ms=latency_ms,
                    last_check=datetime.now(timezone.utc).isoformat()
                )
    except ImportError:
        return ComponentHealth(
            status="skipped",
            details={"reason": "httpx not installed"},
            last_check=datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        logger.error(f"Email service health check failed: {str(e)}")
        return ComponentHealth(
            status="unhealthy",
            details={"error": str(e)},
            latency_ms=(time.time() - start_time) * 1000,
            last_check=datetime.now(timezone.utc).isoformat()
        )

async def check_campaign_service_health() -> ComponentHealth:
    """Check the health of the campaign service."""
    start_time = time.time()
    try:
        # Check if campaign service is configured
        campaign_api_key = os.getenv("CAMPAIGN_SERVICE_API_KEY")
        campaign_api_url = os.getenv("CAMPAIGN_SERVICE_URL")
        
        if not campaign_api_key or not campaign_api_url:
            return ComponentHealth(
                status="skipped",
                details={"reason": "Campaign service not configured"},
                last_check=datetime.now(timezone.utc).isoformat()
            )
        
        # Import here to avoid circular imports
        import httpx
        
        # Make a request to the campaign service health endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{campaign_api_url}/health",
                headers={"X-API-Key": campaign_api_key},
                timeout=5.0
            )
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                return ComponentHealth(
                    status="healthy",
                    details=response.json(),
                    latency_ms=latency_ms,
                    last_check=datetime.now(timezone.utc).isoformat()
                )
            else:
                return ComponentHealth(
                    status="unhealthy",
                    details={
                        "status_code": response.status_code,
                        "response": response.text
                    },
                    latency_ms=latency_ms,
                    last_check=datetime.now(timezone.utc).isoformat()
                )
    except ImportError:
        return ComponentHealth(
            status="skipped",
            details={"reason": "httpx not installed"},
            last_check=datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        logger.error(f"Campaign service health check failed: {str(e)}")
        return ComponentHealth(
            status="unhealthy",
            details={"error": str(e)},
            latency_ms=(time.time() - start_time) * 1000,
            last_check=datetime.now(timezone.utc).isoformat()
        )

async def check_analytics_service_health() -> ComponentHealth:
    """Check the health of the analytics service."""
    start_time = time.time()
    try:
        # Check if analytics service is configured
        analytics_api_key = os.getenv("ANALYTICS_SERVICE_API_KEY")
        analytics_api_url = os.getenv("ANALYTICS_SERVICE_URL")
        
        if not analytics_api_key or not analytics_api_url:
            return ComponentHealth(
                status="skipped",
                details={"reason": "Analytics service not configured"},
                last_check=datetime.now(timezone.utc).isoformat()
            )
        
        # Import here to avoid circular imports
        import httpx
        
        # Make a request to the analytics service health endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{analytics_api_url}/health",
                headers={"X-API-Key": analytics_api_key},
                timeout=5.0
            )
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                return ComponentHealth(
                    status="healthy",
                    details=response.json(),
                    latency_ms=latency_ms,
                    last_check=datetime.now(timezone.utc).isoformat()
                )
            else:
                return ComponentHealth(
                    status="unhealthy",
                    details={
                        "status_code": response.status_code,
                        "response": response.text
                    },
                    latency_ms=latency_ms,
                    last_check=datetime.now(timezone.utc).isoformat()
                )
    except ImportError:
        return ComponentHealth(
            status="skipped",
            details={"reason": "httpx not installed"},
            last_check=datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        logger.error(f"Analytics service health check failed: {str(e)}")
        return ComponentHealth(
            status="unhealthy",
            details={"error": str(e)},
            latency_ms=(time.time() - start_time) * 1000,
            last_check=datetime.now(timezone.utc).isoformat()
        )

async def get_circuit_breaker_statuses() -> List[CircuitBreakerStatus]:
    """Get the status of all circuit breakers."""
    from apps.api.utils.resilience import _circuit_breakers
    
    statuses = []
    for name, cb in _circuit_breakers.items():
        statuses.append(CircuitBreakerStatus(
            name=name,
            state=cb.state.value,
            failure_count=cb.failure_count,
            failure_threshold=cb.failure_threshold,
            recovery_timeout=cb.recovery_timeout,
            last_failure_time=cb.last_failure_time if cb.last_failure_time > 0 else None
        ))
    
    return statuses

# Health check endpoint
@router.get(
    "",
    response_model=HealthResponse,
    summary="Get health status",
    description="Get detailed health status of the API and its dependencies",
)
async def health_check():
    """
    Get detailed health status of the API and its dependencies.
    
    This endpoint performs health checks on all components and returns a detailed
    health status report.
    """
    # Get settings
    settings = get_settings()
    
    # Run health checks in parallel
    db_health, redis_health, ai_health, email_health, campaign_health, analytics_health = await asyncio.gather(
        check_database_health(),
        check_redis_health(),
        check_ai_service_health(),
        check_email_service_health(),
        check_campaign_service_health(),
        check_analytics_service_health(),
    )
    
    # Get circuit breaker statuses
    circuit_breaker_statuses = await get_circuit_breaker_statuses()
    
    # Determine overall status
    components = {
        "database": db_health,
        "redis": redis_health,
        "ai_service": ai_health,
        "email_service": email_health,
        "campaign_service": campaign_health,
        "analytics_service": analytics_health,
    }
    
    # Count unhealthy components (excluding skipped ones)
    unhealthy_count = sum(1 for c in components.values() if c.status == "unhealthy")
    
    # Determine overall status
    if unhealthy_count == 0:
        status = "healthy"
    elif unhealthy_count <= 2:  # Allow up to 2 unhealthy components
        status = "degraded"
    else:
        status = "unhealthy"
    
    # Calculate uptime
    uptime_seconds = time.time() - START_TIME
    
    # Create response
    response = HealthResponse(
        status=status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        version=settings.version,
        environment=settings.environment,
        uptime_seconds=uptime_seconds,
        components=components,
        circuit_breakers=circuit_breaker_statuses,
    )
    
    # Set appropriate status code
    if status == "unhealthy":
        return response
    
    return response

# Liveness probe endpoint
@router.get(
    "/liveness",
    summary="Liveness probe",
    description="Simple liveness probe for Kubernetes",
)
async def liveness_probe():
    """
    Simple liveness probe for Kubernetes.
    
    This endpoint returns a 200 OK response if the service is running.
    """
    return {"status": "alive"}

# Readiness probe endpoint
@router.get(
    "/readiness",
    summary="Readiness probe",
    description="Readiness probe for Kubernetes",
)
async def readiness_probe():
    """
    Readiness probe for Kubernetes.
    
    This endpoint checks if the service is ready to handle requests.
    """
    try:
        # Check database connection
        db_health = await check_database_health()
        if db_health.status == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection failed"
            )
        
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness probe failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )

# Circuit breaker status endpoint
@router.get(
    "/circuit-breakers",
    response_model=List[CircuitBreakerStatus],
    summary="Get circuit breaker statuses",
    description="Get the status of all circuit breakers",
)
async def circuit_breaker_status():
    """
    Get the status of all circuit breakers.
    
    This endpoint returns the status of all circuit breakers in the system.
    """
    return await get_circuit_breaker_statuses()
