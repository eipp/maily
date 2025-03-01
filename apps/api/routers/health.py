"""Health check routes for monitoring system status.

This module provides endpoints for checking the health and status of various
system components, including database connections and external services.
"""

import time

from fastapi import APIRouter, HTTPException, status
from loguru import logger
from sqlalchemy.orm import Session

from ..cache import redis_client
from ..database import get_db
from ..services import get_db_connection
from ..services.health import HealthService
from .schemas import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Check system health",
)
async def check_health(db: Session = Depends(get_db)) -> HealthResponse:
    """Check the health status of all system components.

    Args:
        db: Database session for checking database connectivity

    Returns:
        HealthResponse containing status of each component

    Raises:
        HTTPException: If any critical component is unhealthy
    """
    try:
        health_service = HealthService(db)
        status = await health_service.check_all()
        return HealthResponse(
            status="healthy" if all(status.values()) else "degraded", components=status
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}",
        )
