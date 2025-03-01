import os
import asyncio
import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import aiofiles
import aioredis
from sqlalchemy.ext.asyncio import AsyncEngine
from datetime import datetime

from apps.api.db.connection import get_engine
from apps.api.config.settings import get_settings

router = APIRouter()
logger = logging.getLogger("mailydocs.health")
settings = get_settings()

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    components: Dict[str, Any]

async def check_database(engine: AsyncEngine) -> Dict[str, Any]:
    """Check database connection."""
    try:
        async with engine.connect() as conn:
            result = await conn.execute("SELECT 1")
            await result.fetchone()
            return {"status": "healthy", "latency_ms": 0}
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}

async def check_redis() -> Dict[str, Any]:
    """Check Redis connection."""
    try:
        redis = await aioredis.from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
            password=settings.REDIS_PASSWORD,
            encoding="utf-8",
            decode_responses=True
        )
        await redis.ping()
        await redis.close()
        return {"status": "healthy", "latency_ms": 0}
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}

async def check_document_storage() -> Dict[str, Any]:
    """Check document storage access."""
    try:
        storage_path = settings.DOCUMENT_STORAGE_PATH
        test_file_path = os.path.join(storage_path, "health_check_test.txt")

        # Check if directory exists
        if not os.path.exists(storage_path):
            os.makedirs(storage_path, exist_ok=True)

        # Try to write to storage
        async with aiofiles.open(test_file_path, mode='w') as f:
            await f.write(f"Health check: {datetime.now().isoformat()}")

        # Try to read from storage
        async with aiofiles.open(test_file_path, mode='r') as f:
            await f.read()

        # Clean up test file
        os.remove(test_file_path)

        return {"status": "healthy", "path": storage_path}
    except Exception as e:
        logger.error(f"Document storage health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e), "path": settings.DOCUMENT_STORAGE_PATH}

@router.get("/health", response_model=HealthResponse)
async def health_check(engine: AsyncEngine = Depends(get_engine)):
    """
    Health check endpoint for the MailyDocs service.

    Returns:
        HealthResponse: Health status of the service and its components
    """
    components = {}
    overall_status = "healthy"

    # Run all checks concurrently
    db_check, redis_check, storage_check = await asyncio.gather(
        check_database(engine),
        check_redis(),
        check_document_storage(),
        return_exceptions=True
    )

    # Process database check result
    if isinstance(db_check, Exception):
        components["database"] = {"status": "unhealthy", "error": str(db_check)}
        overall_status = "degraded"
    else:
        components["database"] = db_check
        if db_check["status"] != "healthy":
            overall_status = "degraded"

    # Process Redis check result
    if isinstance(redis_check, Exception):
        components["redis"] = {"status": "unhealthy", "error": str(redis_check)}
        overall_status = "degraded"
    else:
        components["redis"] = redis_check
        if redis_check["status"] != "healthy":
            overall_status = "degraded"

    # Process document storage check result
    if isinstance(storage_check, Exception):
        components["document_storage"] = {"status": "unhealthy", "error": str(storage_check)}
        overall_status = "degraded"
    else:
        components["document_storage"] = storage_check
        if storage_check["status"] != "healthy":
            overall_status = "degraded"

    # Additional service information
    components["service_info"] = {
        "name": "mailydocs",
        "environment": settings.ENVIRONMENT,
        "document_base_url": settings.DOCUMENT_BASE_URL,
        "blockchain_enabled": settings.BLOCKCHAIN_ENABLED
    }

    # If any critical component is unhealthy, the service is unhealthy
    if components["database"]["status"] == "unhealthy" or components["redis"]["status"] == "unhealthy":
        overall_status = "unhealthy"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is unhealthy"
        )

    response = HealthResponse(
        status=overall_status,
        timestamp=datetime.now().isoformat(),
        version=os.environ.get("BUILD_VERSION", "dev"),
        components=components
    )

    logger.info(f"Health check completed with status: {overall_status}")
    return response

@router.get("/health/liveness")
async def liveness_probe():
    """Simple liveness probe for Kubernetes."""
    return {"status": "alive"}

@router.get("/health/readiness")
async def readiness_probe(engine: AsyncEngine = Depends(get_engine)):
    """Readiness probe for Kubernetes."""
    try:
        db_status = await check_database(engine)
        if db_status["status"] != "healthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection failed"
            )

        redis_status = await check_redis()
        if redis_status["status"] != "healthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Redis connection failed"
            )

        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service is not ready: {str(e)}"
        )
