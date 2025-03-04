"""
Main FastAPI application with standardized architecture patterns.
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import logging
import time
from typing import List

# Import core modules
from .config.settings import get_settings
from .logging.logging_config import setup_logging, LoggingMiddleware, bind_contextvars
from .errors.handler import register_exception_handlers
from .schemas.api_response import ApiResponse
from .cache.redis_service import get_cache_service

# Import routers
from .routers import campaign_router

# Initialize logger
logger = structlog.get_logger("justmaily.com")

def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application
    """
    # Get settings
    settings = get_settings()

    # Configure logging
    setup_logging(
        log_level=settings.LOG_LEVEL,
        json_logs=settings.ENVIRONMENT.lower() != "development"
    )

    # Create FastAPI app
    app = FastAPI(
        title=settings.API_TITLE,
        description="Maily API - AI-driven email marketing platform",
        version=settings.API_VERSION,
        docs_url="/docs" if settings.SHOW_DOCS else None,
        redoc_url="/redoc" if settings.SHOW_DOCS else None,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add logging middleware
    app.add_middleware(
        LoggingMiddleware,
        log_request_body=settings.LOG_REQUEST_BODY,
        log_response_body=settings.LOG_RESPONSE_BODY,
        excluded_paths=["/health", "/metrics"]
    )

    # Register exception handlers
    register_exception_handlers(app)

    # Add request timing middleware
    @app.middleware("http")
    async def add_timing_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response

    # Register routers
    app.include_router(campaign_router.router, prefix=settings.API_PREFIX)

    # Add startup and shutdown events
    @app.on_event("startup")
    async def startup_event():
        logger.info(
            "Starting Maily API",
            environment=settings.ENVIRONMENT,
            version=settings.API_VERSION
        )

        # Initialize Redis connection on startup to validate it works
        try:
            cache = get_cache_service()
            logger.info("Redis connection initialized successfully")
        except Exception as e:
            logger.error(
                "Failed to initialize Redis connection",
                error=str(e),
                error_type=e.__class__.__name__
            )

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down Maily API")

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy", "version": settings.API_VERSION}

    # Not found handler for unknown routes
    @app.exception_handler(404)
    async def custom_404_handler(request: Request, exc):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ApiResponse.error(
                error_code="not_found",
                message=f"URL not found: {request.url.path}"
            ).dict()
        )

    return app

# Create application instance
app = create_application()

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "main_standard:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
