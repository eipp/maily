"""
Simplified test version of the AI Service main file
"""

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

# Add the parent directory to sys.path to allow imports to work when running directly
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import only the Redis client to test if it works
from ai_service.utils.redis_client import init_redis, close_redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize connections
    logger.info("Initializing Redis connection")
    try:
        await init_redis()
        logger.info("Redis connection initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Redis connection: {e}")
    
    logger.info("AI Service startup complete")
    yield
    
    # Shutdown: Close connections
    logger.info("Closing Redis connection")
    await close_redis()
    
    logger.info("AI Service shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="Maily AI Service Test",
    description="Test version of AI Service for Maily",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/", tags=["Status"])
async def root():
    return {"status": "ok", "service": "maily-ai-service-test"}

# Health check endpoint
@app.get("/health", tags=["Status"])
async def health():
    return {"status": "healthy"}

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
        "main_test:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_level=log_level,
    )
