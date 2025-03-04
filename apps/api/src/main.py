"""
API Service entry point.

This module initializes and configures the FastAPI application.
"""

import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

# Import settings and configurations
from apps.api.src.config.settings import get_settings
from apps.api.src.api.health import router as health_router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    # Get settings
    settings = get_settings()
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        description="Maily API Service",
        version=settings.version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add routers
    app.include_router(health_router)
    
    # Add startup and shutdown events
    @app.on_event("startup")
    async def startup_event():
        """Initialize services on startup."""
        logger.info(f"Starting API service ({settings.version}) in {settings.environment} mode")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown."""
        logger.info("Shutting down API service")
    
    return app

# Create app instance
app = create_app()

# Entry point for running the application
if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.debug)