#!/usr/bin/env python3
"""
Script to run the Maily WebSocket server for development and testing.

This script launches a standalone WebSocket server to support the 
Cognitive Canvas real-time collaboration features.
"""

import asyncio
import os
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Create FastAPI application configured for WebSocket endpoints."""
    app = FastAPI(
        title="Maily WebSocket Server",
        description="WebSocket server for Cognitive Canvas real-time collaboration",
        version="1.0.0",
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Import WebSocket router
    from apps.api.routers.canvas_websocket import router as canvas_websocket_router
    app.include_router(canvas_websocket_router)
    
    # Add root healthcheck
    @app.get("/")
    async def root():
        return {"status": "WebSocket server is running"}
    
    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "services": {
                "websocket": "running"
            }
        }
    
    return app

async def main():
    """Run the WebSocket server."""
    # Create FastAPI app
    app = create_app()
    
    # Configure Uvicorn server
    port = int(os.getenv("WEBSOCKET_PORT", "8001"))
    host = os.getenv("WEBSOCKET_HOST", "0.0.0.0")
    
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="info",
        loop="asyncio",
        reload=True,
    )
    
    # Start server
    server = uvicorn.Server(config)
    logger.info(f"Starting WebSocket server on {host}:{port}")
    await server.serve()

if __name__ == "__main__":
    import uvloop
    try:
        uvloop.install()
        logger.info("Using uvloop for improved performance")
    except ImportError:
        logger.info("uvloop not available, using standard asyncio event loop")
    
    # Run the server
    asyncio.run(main())