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
import time
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
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.http import RequestSizeLimitMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError

# Import project modules
try:
    # Try to import from apps.api
    from apps.api.config import Settings
    from apps.api.routers import router
    from apps.api.middleware.security import (
        security_middleware,
        waf_middleware,
    )
    from apps.api.middleware.rate_limiting import add_rate_limiting_middleware
    from apps.api.middleware.owasp_middleware import setup_owasp_middleware
    from apps.api.middleware.security_headers import EnhancedSecurityHeadersMiddleware, SecurityConfig
    from apps.api.utils.openapi_generator import setup_openapi_documentation
    from apps.api.monitoring.metrics import MetricsManager
    from apps.api.config.settings import get_settings
    from apps.api.routers import (
        integrations, auth, policies, campaigns, templates,
        health, privacy, models, platforms, contacts, canvas, websocket,
        ai, ai_cached, blockchain,
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
        def __init__(self): pass
        def setup_metrics(self, app): pass
        def start_metrics_server(self): pass
        def shutdown(self): pass

    def initialize_metrics_endpoint(app): pass
    def register_ai_dashboard(app): pass
    def setup_owasp_middleware(app): pass
    def setup_openapi_documentation(app): pass

    class SecurityConfig: pass
    class EnhancedSecurityHeadersMiddleware: pass

# Try to import AI service
try:
    from apps.api.ai.service import AIService
except ImportError:
    # Mock AI service if not available
    class MockAIService:
        async def generate_text(self, prompt, **kwargs):
            return {"text": "This is a mock response because the AI service is not available."}
        
        async def check_health(self):
            return {"status": "Not available (mock)"}
    
    AIService = MockAIService

# Configure settings
load_dotenv()
settings = get_settings()

# API key authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Create lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup activities
    info("Starting Maily API service")
    
    # Initialize services and connections
    try:
        # Initialize metrics and monitoring
        metrics_manager = MetricsManager()
        metrics_manager.setup_metrics(app)
        metrics_manager.start_metrics_server()
        
        # Initialize tracing
        tracing_manager.setup_tracing(app)
        
        yield
    except Exception as e:
        error(f"Error during API startup: {str(e)}")
        exception("Startup exception")
        raise
    finally:
        # Shutdown activities
        info("Shutting down Maily API service")
        
        # Clean up resources
        try:
            metrics_manager.shutdown()
            tracing_manager.shutdown()
        except Exception as e:
            error(f"Error during API shutdown: {str(e)}")
            exception("Shutdown exception")

# Create FastAPI app with lifespan
app = FastAPI(
    title=settings.app_name,
    description="Maily API for campaign management and analytics",
    version=settings.version,
    lifespan=lifespan,
)

# Add middleware in correct order (most general to most specific)
# 1. Trusted Host middleware (security)
app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts
)

# 2. Request size limiting (prevent DoS)
app.add_middleware(
    RequestSizeLimitMiddleware, max_size=20 * 1024 * 1024  # 20 MB max
)

# 3. CORS middleware (must come before other custom middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID"],
)

# 4. Security headers middleware
app.add_middleware(
    EnhancedSecurityHeadersMiddleware,
    config=SecurityConfig(),
    exclude_paths=["/docs", "/redoc", "/openapi.json"]
)

# 5. Add OWASP middleware
setup_owasp_middleware(app)

# 6. Add rate limiting (needs to be before application-specific middleware)
add_rate_limiting_middleware(app)

# 7. Tracing for APM (after security, before app-specific)
@app.middleware("http")
async def tracing_middleware_wrapper(request: Request, call_next):
    with info(f"Processing request: {request.method} {request.url.path}"):
        start_time = time.time()
        try:
            response = await tracing_middleware(request, call_next)
            duration = time.time() - start_time
            info(f"Request completed in {duration:.3f}s")
            return response
        except Exception as e:
            error(f"Error processing request: {str(e)}")
            exception("Request processing exception")
            raise

# 8. WAF (web application firewall) middleware
@app.middleware("http")
async def waf_middleware_wrapper(request: Request, call_next):
    try:
        return await waf_middleware(request, call_next)
    except Exception as e:
        error(f"WAF middleware error: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Invalid request detected by security filters"}
        )

# 9. Security middleware (authentication, etc.)
@app.middleware("http")
async def security_middleware_wrapper(request: Request, call_next):
    try:
        return await security_middleware(request, call_next)
    except HTTPException as e:
        # Re-raise HTTP exceptions for proper status codes
        raise
    except Exception as e:
        error(f"Security middleware error: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Authentication error"}
        )

# 10. Rate limit middleware
@app.middleware("http")
async def rate_limit_middleware_wrapper(request: Request, call_next):
    try:
        return await rate_limit_middleware(request, call_next)
    except HTTPException as e:
        # Re-raise HTTP exceptions for proper status codes
        raise
    except Exception as e:
        error(f"Rate limiting error: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit exceeded"}
        )

# Add OpenAPI documentation
setup_openapi_documentation(app)

# Data models
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


# Dependency functions
async def verify_api_key(api_key: str = Depends(api_key_header)) -> str:
    """
    Verifies that the API key is valid.
    
    Args:
        api_key: The API key from the request header.
        
    Returns:
        The validated API key if valid.
        
    Raises:
        HTTPException: If the API key is invalid or missing.
    """
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
            headers={"WWW-Authenticate": "APIKey"},
        )
    
    # Import database services here to avoid circular imports
    try:
        from apps.api.services.api_key_service import validate_api_key, get_api_key_scopes
    
        # Validate API key against database
        is_valid, api_key_record = await validate_api_key(api_key)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "APIKey"},
            )
        
        # Get API key scopes for authorization
        scopes = await get_api_key_scopes(api_key)
        
        # Attach scopes to request state for later use
        from fastapi import Request
        request = Request.scope.get("fastapi_astack")[-1]["request"]
        request.state.api_key_scopes = scopes
        request.state.api_key_id = api_key_record["id"]
        
        return api_key
    except ImportError:
        # Fallback for development/testing only
        if os.environ.get("ENVIRONMENT") == "production":
            error("API key service not available in production")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service unavailable",
            )
        
        warning("Using development API key validation")
        if not api_key or len(api_key) < 8:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "APIKey"},
            )
        
        return api_key


# Routes
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def check_health():
    """
    Checks the health of the API and its dependencies.
    
    Returns:
        A HealthResponse object with status information for all components.
    """
    start_time = os.environ.get("APP_START_TIME", time.time())
    uptime = time.time() - float(start_time)
    
    # Check AI service health
    ai_service = AIService()
    ai_health = await ai_service.check_health()
    
    # Build response
    components = {
        "api": "healthy",
        "ai_service": ai_health.get("status", "unknown"),
        # Add other components here
    }
    
    services = {
        "database": "connected",  # Placeholder
        "cache": "connected",     # Placeholder
        "message_queue": "connected",  # Placeholder
    }
    
    return HealthResponse(
        status="healthy" if all(c == "healthy" for c in components.values()) else "degraded",
        components=components,
        uptime=uptime,
        services=services,
        timestamp=datetime.now(timezone.utc).isoformat(),
        details={
            "version": settings.version,
            "environment": settings.environment,
        },
        environment={
            "debug": settings.debug,
            "api_prefix": settings.api_prefix,
        },
    )


@app.post("/configure_model", response_model=ModelConfigResponse, tags=["AI Models"])
async def configure_model(config: ModelConfig, api_key: str = Depends(verify_api_key)):
    """
    Configures an AI model for use with the API.
    
    Args:
        config: The model configuration.
        api_key: The validated API key.
        
    Returns:
        A ModelConfigResponse object with the configuration status.
    """
    # TODO: Implement model configuration storage
    config_id = f"config_{int(time.time())}"
    
    # Log model configuration
    info(f"Model configured: {config.model_name}", config_id=config_id)
    
    return ModelConfigResponse(
        status="configured",
        model_name=config.model_name,
        config_id=config_id,
    )


@app.post("/create_campaign", response_model=CampaignResponse, tags=["Campaigns"])
async def create_campaign(
    campaign: CampaignRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key),
):
    """
    Creates a new campaign.
    
    Args:
        campaign: The campaign creation request.
        background_tasks: FastAPI background tasks.
        api_key: The validated API key.
        
    Returns:
        A CampaignResponse object with the created campaign details.
    """
    try:
        # Generate a unique campaign ID
        campaign_id = f"camp_{int(time.time())}"
        
        # Log campaign creation
        info(f"Campaign created: {campaign_id}", 
             task=campaign.task, 
             model=campaign.model_name)
        
        # Add background task to generate campaign content
        background_tasks.add_task(
            generate_campaign_content,
            campaign_id=campaign_id,
            task=campaign.task,
            model_name=campaign.model_name,
        )
        
        # Estimate audience size (placeholder)
        audience_size = 1000
        if campaign.audience and campaign.audience.segments:
            audience_size = len(campaign.audience.segments) * 500
            
        return CampaignResponse(
            campaign_id=campaign_id,
            status="processing",
            preview_url=f"/campaigns/{campaign_id}/preview",
            estimated_audience=audience_size,
        )
    except ValidationError as e:
        # Catch Pydantic validation errors
        error(f"Validation error in campaign creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        # Log unexpected errors
        exception(f"Error creating campaign: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during campaign creation",
        )


# Router-style endpoint for compatibility
@app.post("/api/v1/campaigns", response_model=CampaignResponse, tags=["Campaigns"])
async def create_campaign_router(
    campaign: CampaignRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key),
):
    """
    Router-style endpoint for creating a new campaign.
    Provides compatibility with the router-based API style.
    
    Args:
        campaign: The campaign creation request.
        background_tasks: FastAPI background tasks.
        api_key: The validated API key.
        
    Returns:
        A CampaignResponse object with the created campaign details.
    """
    return await create_campaign(campaign, background_tasks, api_key)


# Background task for campaign content generation
async def generate_campaign_content(campaign_id: str, task: str, model_name: str):
    """
    Generates content for a campaign using the specified AI model.
    
    Args:
        campaign_id: The ID of the campaign.
        task: The task description.
        model_name: The name of the AI model to use.
    """
    try:
        info(f"Generating campaign content: {campaign_id}", task=task, model=model_name)
        
        # Initialize AI service
        ai_service = AIService()
        
        # Generate content
        result = await ai_service.generate_text(prompt=task, model=model_name)
        
        # TODO: Save the generated content to the campaign
        info(f"Content generation completed: {campaign_id}")
    except Exception as e:
        error(f"Failed to generate campaign content: {str(e)}", campaign_id=campaign_id)
        exception(f"Content generation error for campaign {campaign_id}")


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    Handles HTTP exceptions with structured error responses.
    
    Args:
        request: The incoming request.
        exc: The HTTP exception.
        
    Returns:
        A JSON response with error details.
    """
    # Log the exception with appropriate level based on status code
    if exc.status_code >= 500:
        error(f"HTTP 5xx error: {exc.detail}", status_code=exc.status_code, path=request.url.path)
    elif exc.status_code >= 400:
        warning(f"HTTP 4xx error: {exc.detail}", status_code=exc.status_code, path=request.url.path)
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "request_id": request.headers.get("X-Request-ID", "unknown"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """
    Handles all uncaught exceptions with structured error responses.
    
    Args:
        request: The incoming request.
        exc: The exception.
        
    Returns:
        A JSON response with error details.
    """
    # Log the exception
    exception(f"Unhandled exception: {str(exc)}", path=request.url.path)
    
    # Don't expose internal error details in production
    if settings.environment == "production":
        error_detail = "Internal server error"
    else:
        error_detail = str(exc)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": error_detail,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "request_id": request.headers.get("X-Request-ID", "unknown"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """
    Executes when the FastAPI application starts.
    Sets up logging, metrics, and initializes services.
    """
    # Record application start time
    os.environ["APP_START_TIME"] = str(time.time())
    
    # Set up structured logging
    setup_app_logging(app)
    
    # Initialize metrics endpoint
    initialize_metrics_endpoint(app)
    
    # Register AI dashboard if available
    try:
        register_ai_dashboard(app)
    except Exception as e:
        warning(f"Failed to register AI dashboard: {str(e)}")
    
    # Include router and endpoints
    if router:
        app.include_router(router)
    
    info("Maily API started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Executes when the FastAPI application shuts down.
    Performs cleanup of resources.
    """
    info("Maily API shutting down")
    
    # Perform additional cleanup here if needed
    
    info("Maily API shutdown complete")


# Register cleanup function with atexit
def cleanup():
    """
    Performs final cleanup when the application exits.
    """
    try:
        # Perform any synchronous cleanup tasks here
        pass
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")

atexit.register(cleanup)

# If running as main script
if __name__ == "__main__":
    import uvicorn
    
    # Start the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=settings.debug,
    )

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
app.include_router(blockchain.router)
