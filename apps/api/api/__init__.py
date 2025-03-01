from fastapi import FastAPI
from loguru import logger
from prometheus_fastapi_instrumentator import Instrumentator

from ..config import settings
from .errors import MailyError, general_error_handler, maily_error_handler
from .health import router as health_router
from .middleware import setup_middleware
from ..routers import router as api_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Maily AI Infrastructure",
        version="1.0.0",
        description="Maily AI Infrastructure API provides endpoints for managing email campaigns with AI-powered content generation, design suggestions, and analytics.",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Configure middleware
    setup_middleware(app)

    # Add Prometheus instrumentation
    Instrumentator().instrument(app).expose(app)

    # Include routers
    app.include_router(api_router, prefix="/api/v1")
    app.include_router(health_router, prefix="/health")

    # Add error handlers
    app.add_exception_handler(MailyError, maily_error_handler)
    app.add_exception_handler(Exception, general_error_handler)

    logger.info("FastAPI application configured successfully")
    return app


app = create_app()
