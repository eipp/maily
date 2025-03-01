#!/usr/bin/env python3
"""
Main application for the Maily API.

This module serves as the entry point for the Maily API, implementing a hexagonal
architecture with clear separation between domain logic and external adapters.
"""

import asyncio
import atexit
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from contextlib import asynccontextmanager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import structured logging
try:
    from apps.api.monitoring.logging import setup_app_logging, info, error, warning, exception
except ImportError:
    # Mock logging functions if not available
    def setup_app_logging(app): pass
    def info(message, **kwargs): logger.info(message)
    def error(message, **kwargs): logger.error(message)
    def warning(message, **kwargs): logger.warning(message)
    def exception(message, **kwargs): logger.exception(message)

# Import OpenTelemetry tracing if available
try:
    from apps.api.monitoring.tracing import tracing_manager, tracing_middleware
except ImportError:
    # Mock tracing if not available
    class TracingManager:
        def setup_tracing(self, app, sqlalchemy_engine=None, redis_client=None): pass
        def shutdown(self): pass

    tracing_manager = TracingManager()

    async def tracing_middleware(request, call_next):
        return await call_next(request)

# Import standard dependencies
from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.http import RequestSizeLimitMiddleware
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Import project modules
try:
    # Try to import from apps.api
    from apps.api.config import Settings
    from apps.api.routers import router
    from apps.api.middleware.security import (
        rate_limit_middleware,
        security_middleware,
        waf_middleware,
    )
    from apps.api.monitoring.metrics import MetricsManager
    from apps.api.config.settings import get_settings
    from apps.api.routers import (
        integrations, auth, policies, campaigns, templates,
        health, privacy, models, platforms, contacts, canvas, websocket,
        ai, ai_cached,
    )
    from apps.api.endpoints import users, analytics, mailydocs
    from apps.api.metrics.prometheus import initialize_metrics_endpoint
    from apps.api.ai.monitoring.ai_dashboard import register_ai_dashboard
except ImportError:
    # Mock imports if not available
    class Settings:
        def __init__(self):
            self.app_name = "Maily API"
            self.debug = os.environ.get("DEBUG", "False").lower() == "true"
            self.environment = os.environ.get("ENVIRONMENT", "development")
            self.version = os.environ.get("VERSION", "0.1.0")
            self.api_prefix = os.environ.get("API_PREFIX", "/api/v1")
            self.allowed_hosts = os.environ.get("ALLOWED_HOSTS", "*").split(",")

    def get_settings():
        return Settings()

    router = None

    async def security_middleware(request, call_next):
        return await call_next(request)

    async def rate_limit_middleware(request, call_next):
        return await call_next(request)

    async def waf_middleware(request, call_next):
        return await call_next(request)

    class MetricsManager:
        def update_system_info(self, info): pass

    def initialize_metrics_endpoint(app): pass

    def register_ai_dashboard(app): pass

# Import AI service
try:
    from apps.api.ai import AIService
    ai_service = AIService()
except ImportError:
    # Mock model service if not available
    class MockAIService:
        async def generate_text(self, prompt, **kwargs):
            return {"content": f"Mock response for: {prompt}", "model_name": "mock-model"}

        async def check_health(self):
            return {"status": "healthy", "mock": True}

    ai_service = MockAIService()

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Maily API",
    description="AI-driven email marketing platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request size limit middleware
app.add_middleware(
    RequestSizeLimitMiddleware,
    max_request_size=10 * 1024 * 1024  # 10 MB
)

# Add security middleware
@app.middleware("http")
async def security_middleware_wrapper(request: Request, call_next):
    return await security_middleware(request, call_next)

# Add rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware_wrapper(request: Request, call_next):
    return await rate_limit_middleware(request, call_next)

# Add WAF middleware
@app.middleware("http")
async def waf_middleware_wrapper(request: Request, call_next):
    return await waf_middleware(request, call_next)

# Add tracing middleware
@app.middleware("http")
async def tracing_middleware_wrapper(request: Request, call_next):
    return await tracing_middleware(request, call_next)

# Setup API key authentication
api_key_header = APIKeyHeader(name="X-API-Key")

# Define models
class AudienceSegment(BaseModel):
    segments: List[str] = Field(default_factory=list)
    exclusions: List[str] = Field(default_factory=list)

class CampaignRequest(BaseModel):
    task: str
    model_name: str
    audience: Optional[AudienceSegment] = None

class CampaignResponse(BaseModel):
    campaign_id: str
    status: str
    preview_url: str
    estimated_audience: int

class HealthResponse(BaseModel):
    status: str
    components: Dict[str, str]
    uptime: float
    services: Dict[str, str]
    timestamp: str
    details: Dict[str, Any] = Field(default_factory=dict)
    environment: Dict[str, Any] = Field(default_factory=dict)

class ModelConfig(BaseModel):
    model_name: str
    api_key: str
    temperature: float = 0.7
    max_tokens: int = 1000

class ModelConfigResponse(BaseModel):
    status: str
    model_name: str
    config_id: str

# Initialize services
settings = get_settings()
metrics_manager = MetricsManager()

# Setup API routes
if router:
    app.include_router(router, prefix=settings.api_prefix)

# Authentication function
async def verify_api_key(api_key: str = Depends(api_key_header)) -> str:
    """
    Verify the API key.

    Args:
        api_key: The API key from the request header.

    Returns:
        The verified API key.

    Raises:
        HTTPException: If the API key is invalid.
    """
    # In a real implementation, this would verify the API key against a database
    if not api_key or len(api_key) < 32:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return api_key

# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def check_health():
    """
    Check the health of the API and its dependencies.

    Returns:
        A HealthResponse object with the health status.
    """
    start_time = datetime.now(timezone.utc)

    # Check AI service health
    ai_health = await ai_service.check_health()

    # Calculate uptime
    uptime = (datetime.now(timezone.utc) - start_time).total_seconds()

    return HealthResponse(
        status="healthy",
        components={
            "api": "healthy",
            "ai": "healthy" if ai_health.get("status") == "healthy" else "unhealthy",
        },
        uptime=uptime,
        services={
            "ai_service": "healthy" if ai_health.get("status") == "healthy" else "unhealthy",
        },
        timestamp=datetime.now(timezone.utc).isoformat(),
        details={
            "ai_service": ai_health,
        },
        environment={
            "version": settings.version,
            "environment": settings.environment,
        },
    )

# Configure model endpoint
@app.post("/configure_model", response_model=ModelConfigResponse, tags=["AI Models"])
async def configure_model(config: ModelConfig, api_key: str = Depends(verify_api_key)):
    """
    Configure an AI model for use.

    Args:
        config: The model configuration.
        api_key: The API key from the request header.

    Returns:
        A ModelConfigResponse object with the configuration status.
    """
    # In a real implementation, this would store the configuration in a database
    config_id = f"config_{datetime.now(timezone.utc).timestamp()}"

    return ModelConfigResponse(
        status="configured",
        model_name=config.model_name,
        config_id=config_id,
    )

# Create campaign endpoint
@app.post("/create_campaign", response_model=CampaignResponse, tags=["Campaigns"])
async def create_campaign(
    campaign: CampaignRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key),
):
    """
    Create a new email campaign.

    Args:
        campaign: The campaign request.
        background_tasks: FastAPI background tasks.
        api_key: The API key from the request header.

    Returns:
        A CampaignResponse object with the campaign details.
    """
    # Generate a campaign ID
    campaign_id = f"campaign_{datetime.now(timezone.utc).timestamp()}"

    # Estimate audience size
    estimated_audience = 1000  # Mock value

    # In a real implementation, this would create a campaign in the database
    # and start a background task to generate the campaign content
    background_tasks.add_task(
        generate_campaign_content,
        campaign_id,
        campaign.task,
        campaign.model_name,
    )

    return CampaignResponse(
        campaign_id=campaign_id,
        status="created",
        preview_url=f"https://example.com/preview/{campaign_id}",
        estimated_audience=estimated_audience,
    )

# Router-style campaign endpoint
@app.post("/api/v1/campaigns", response_model=CampaignResponse, tags=["Campaigns"])
async def create_campaign_router(
    campaign: CampaignRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key),
):
    """
    Create a new email campaign (router-style endpoint).

    Args:
        campaign: The campaign request.
        background_tasks: FastAPI background tasks.
        api_key: The API key from the request header.

    Returns:
        A CampaignResponse object with the campaign details.
    """
    return await create_campaign(campaign, background_tasks, api_key)

# Background task for generating campaign content
async def generate_campaign_content(campaign_id: str, task: str, model_name: str):
    """
    Generate content for a campaign.

    Args:
        campaign_id: The ID of the campaign.
        task: The task description.
        model_name: The name of the model to use.
    """
    try:
        # Generate content using the model service
        response = await ai_service.generate_text(
            prompt=f"Generate email campaign content for: {task}",
            model_name=model_name,
        )

        # In a real implementation, this would update the campaign in the database
        logger.info(f"Generated content for campaign {campaign_id}: {response.content[:100]}...")
    except Exception as e:
        logger.error(f"Error generating content for campaign {campaign_id}: {str(e)}")

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    Handle HTTP exceptions.

    Args:
        request: The request that caused the exception.
        exc: The exception.

    Returns:
        A JSON response with the error details.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "code": exc.status_code,
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """
    Handle general exceptions.

    Args:
        request: The request that caused the exception.
        exc: The exception.

    Returns:
        A JSON response with the error details.
    """
    logger.exception(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "code": 500,
            "details": str(exc) if settings.debug else None,
        },
    )

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """
    Run startup tasks.
    """
    # Set up structured logging
    setup_app_logging(app)

    # Set up tracing
    tracing_manager.setup_tracing(app)

    # Initialize metrics endpoint
    initialize_metrics_endpoint(app)

    # Register AI dashboard routes
    register_ai_dashboard(app)

    logger.info("API started")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Run shutdown tasks.
    """
    # Shutdown tracing
    tracing_manager.shutdown()

    logger.info("API shutdown")

# Cleanup function
def cleanup():
    """
    Clean up resources.
    """
    logger.info("Cleaning up resources")

# Register cleanup function
atexit.register(cleanup)

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(health.router)
app.include_router(ai.router)
app.include_router(ai_cached.router)
app.include_router(integrations.router)
app.include_router(policies.router)
app.include_router(campaigns.router)
app.include_router(templates.router)
app.include_router(privacy.router)
app.include_router(models.router)
app.include_router(platforms.router)
app.include_router(contacts.router)
app.include_router(canvas.router)
app.include_router(websocket.router)
app.include_router(analytics.router)
app.include_router(mailydocs.router)
