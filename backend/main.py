import os
import logging
import sys
import atexit
from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from loguru import logger
from dotenv import load_dotenv
from langfuse import Langfuse
from routes import router
from middleware.security import (
    security_middleware,
    rate_limit_middleware,
    waf_middleware
)
from fastapi.middleware.http import RequestSizeLimitMiddleware
from fastapi.security import APIKeyHeader
from typing import Optional, List, Dict
from datetime import datetime, timezone
import asyncio

from .models import (
    HealthResponse,
    ModelConfig,
    ModelConfigResponse,
    CampaignRequest,
    CampaignResponse
)
from .services import (
    AIService,
    CampaignService,
    RateLimiter,
    MetricsCollector
)
from .config import Settings

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger.remove()  # Remove default handler
logger.add(
    "logs/maily_{time}.log",
    rotation="500 MB",
    retention="10 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
)
logger.add(sys.stderr, level="WARNING")

# Initialize Langfuse
LANGFUSE_API_KEY = os.getenv("LANGFUSE_API_KEY")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "pk-lf-70bdc4f8-4b1c-4791-a54d-7ea2c3b93b88")
langfuse = Langfuse(public_key=LANGFUSE_PUBLIC_KEY, secret_key=LANGFUSE_API_KEY) if LANGFUSE_API_KEY else None

# Create FastAPI app
app = FastAPI(
    title="Maily API",
    description="AI-Powered Email Marketing Platform API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Security middleware
app.middleware("http")(security_middleware)
app.middleware("http")(rate_limit_middleware)
app.middleware("http")(waf_middleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://maily.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Request size limits
app.add_middleware(
    RequestSizeLimitMiddleware,
    max_content_length=1024 * 1024  # 1MB
)

# Add Prometheus instrumentation
Instrumentator().instrument(app).expose(app)

# Include routers
app.include_router(router)

# Load application settings
settings = Settings()

# Initialize services
ai_service = AIService(settings)
campaign_service = CampaignService(settings)
rate_limiter = RateLimiter(settings)
metrics_collector = MetricsCollector(settings)

# API Key security scheme
api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Depends(api_key_header)) -> str:
    """
    Verify the API key and rate limit the request.
    
    Args:
        api_key: The API key from the request header
        
    Returns:
        str: The verified API key
        
    Raises:
        HTTPException: If the API key is invalid or rate limit is exceeded
    """
    if api_key != settings.API_KEY:
        logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Check rate limit
    if not await rate_limiter.check_limit(api_key):
        logger.warning(f"Rate limit exceeded for key: {api_key[:8]}...")
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": "3600"}
        )
    
    return api_key

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def check_health():
    """
    Check the health status of all system components.
    Verifies database connection, Redis availability, and AI service status.
    """
    try:
        # Check all component statuses concurrently
        db_status, redis_status, ai_status = await asyncio.gather(
            campaign_service.check_db_health(),
            rate_limiter.check_redis_health(),
            ai_service.check_health(),
            return_exceptions=True
        )
        
        # Determine overall system health
        components = {
            "database": "connected" if not isinstance(db_status, Exception) else "disconnected",
            "redis": "connected" if not isinstance(redis_status, Exception) else "disconnected",
            "ai_service": "operational" if not isinstance(ai_status, Exception) else "unavailable"
        }
        
        status = "healthy" if all(s == "connected" or s == "operational" for s in components.values()) else "degraded"
        
        return {
            "status": status,
            "components": components,
            "uptime": metrics_collector.get_uptime()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/configure_model", response_model=ModelConfigResponse, tags=["AI Models"])
async def configure_model(
    config: ModelConfig,
    api_key: str = Depends(verify_api_key)
):
    """
    Configure an AI model with API key and custom settings.
    
    Args:
        config: Model configuration parameters
        api_key: Verified API key from the request
        
    Returns:
        ModelConfigResponse: Configuration status and details
        
    Raises:
        HTTPException: If configuration fails or model is unsupported
    """
    try:
        # Validate and configure the AI model
        config_id = await ai_service.configure_model(
            model_name=config.model_name,
            api_key=config.api_key,
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )
        
        # Log successful configuration
        logger.info(f"Model {config.model_name} configured successfully")
        
        return {
            "status": "configured",
            "model_name": config.model_name,
            "config_id": config_id
        }
    except ValueError as e:
        logger.error(f"Model configuration failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during model configuration: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/create_campaign", response_model=CampaignResponse, tags=["Campaigns"])
async def create_campaign(
    campaign: CampaignRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """
    Create a new email marketing campaign with AI-generated content.
    
    Args:
        campaign: Campaign creation request parameters
        background_tasks: FastAPI background tasks handler
        api_key: Verified API key from the request
        
    Returns:
        CampaignResponse: Campaign creation status and details
        
    Raises:
        HTTPException: If campaign creation fails or validation errors occur
    """
    try:
        # Validate audience segments
        if campaign.audience:
            await campaign_service.validate_segments(
                campaign.audience.segments,
                campaign.audience.exclusions
            )
        
        # Create campaign in draft state
        campaign_id = await campaign_service.create_campaign(campaign)
        
        # Schedule content generation in background
        background_tasks.add_task(
            ai_service.generate_campaign_content,
            campaign_id=campaign_id,
            task=campaign.task,
            model_name=campaign.model_name
        )
        
        # Get estimated audience size
        estimated_audience = await campaign_service.estimate_audience_size(
            campaign.audience.segments if campaign.audience else None,
            campaign.audience.exclusions if campaign.audience else None
        )
        
        # Log campaign creation
        logger.info(f"Campaign created: {campaign_id}")
        
        return {
            "campaign_id": campaign_id,
            "status": "draft",
            "preview_url": f"{settings.PREVIEW_URL}/{campaign_id}",
            "estimated_audience": estimated_audience
        }
    except ValueError as e:
        logger.error(f"Campaign creation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during campaign creation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    Global HTTP exception handler for consistent error responses.
    Logs errors and returns formatted error messages.
    """
    logger.error(f"HTTP error: {exc.status_code} - {exc.detail}")
    return {
        "error": "http_error",
        "message": exc.detail,
        "status_code": exc.status_code
    }

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """
    Global exception handler for unexpected errors.
    Logs errors and returns a generic error message.
    """
    logger.error(f"Unexpected error: {str(exc)}")
    return {
        "error": "internal_error",
        "message": "An unexpected error occurred",
        "status_code": 500
    }

def cleanup():
    """Cleanup resources on shutdown."""
    try:
        if langfuse:
            langfuse.flush()
            logger.info("Flushed Langfuse traces")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

atexit.register(cleanup)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
