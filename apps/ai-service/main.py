import os
import logging
import sys

# Configure logging with proper level handling
def get_log_level(level_str):
    """Convert string log level to logging level, case-insensitive"""
    level_str = level_str.upper()
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    return level_map.get(level_str, logging.INFO)

# Configure logging first, before any other imports
log_level_str = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=get_log_level(log_level_str),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("ai_service")

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

# Add the parent directory to sys.path to allow imports to work when running directly
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Use absolute imports that work both when imported as a module and when run directly
from ai_service.routers import generation, conversation, tools
from ai_service.routers.agent_coordinator_router import router as agent_coordinator_router
from ai_service.utils.database import init_db, close_db
from ai_service.utils.redis_client import init_redis, close_redis
from ai_service.utils.llm_client import init_llm_client, close_llm_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize connections
    logger.info("Initializing database connection")
    await init_db()
    
    logger.info("Initializing Redis connection")
    await init_redis()
    
    logger.info("Initializing LLM client")
    await init_llm_client()
    
    logger.info("AI Service startup complete")
    yield
    
    # Shutdown: Close connections
    logger.info("Closing database connection")
    await close_db()
    
    logger.info("Closing Redis connection")
    await close_redis()
    
    logger.info("Closing LLM client")
    await close_llm_client()
    
    logger.info("AI Service shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="Maily AI Service",
    description="AI Service for Maily - Email Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include routers
app.include_router(generation.router, prefix="/api/v1/generation", tags=["Generation"])
app.include_router(conversation.router, prefix="/api/v1/conversation", tags=["Conversation"])
app.include_router(tools.router, prefix="/api/v1/tools", tags=["Tools"])
app.include_router(agent_coordinator_router.router, prefix="/api", tags=["AI Mesh Network"])

# Root endpoint
@app.get("/", tags=["Status"])
async def root():
    return {"status": "ok", "service": "maily-ai-service"}

# Health check endpoint
@app.get("/health", tags=["Status"])
async def health():
    return {"status": "healthy"}

# Readiness check endpoint
@app.get("/ready", tags=["Status"])
async def ready():
    return {"status": "ready"}

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )

if __name__ == "__main__":
    import uvicorn
    
    # Use lowercase log level for uvicorn as it expects lowercase
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    # When running directly, use the module name relative to the current directory
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_level=log_level,
    )
