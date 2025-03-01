"""
Edge Cache Middleware for Maily.

This middleware adds cache headers to API responses to enable edge caching
at CDN or reverse proxy level.
"""
import logging
import os
import time
import hashlib
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# Edge caching configuration
EDGE_CACHE_ENABLED = os.environ.get("EDGE_CACHE_ENABLED", "true").lower() == "true"
DEFAULT_CACHE_TTL = int(os.environ.get("EDGE_CACHE_DEFAULT_TTL", "60"))  # 60 seconds

# Cache TTLs for different endpoint types (in seconds)
CACHE_TTLS = {
    # Public endpoints
    "GET:/api/campaigns/public": 300,  # 5 minutes
    "GET:/api/templates/public": 600,  # 10 minutes
    "GET:/api/stats/public": 300,  # 5 minutes

    # User-specific endpoints (cached at edge with Vary: Authorization)
    "GET:/api/campaigns": 60,  # 1 minute
    "GET:/api/templates": 120,  # 2 minutes
    "GET:/api/stats": 60,  # 1 minute

    # Never cache these endpoints
    "POST:/api/auth/login": 0,
    "POST:/api/auth/register": 0,
    "POST:/api/campaigns": 0,
    "PUT:/api/campaigns": 0,
    "DELETE:/api/campaigns": 0,
}

# Cache key generation functions
def generate_cache_key(request: Request) -> str:
    """
    Generate a cache key for a request.

    Args:
        request: The request to generate a cache key for

    Returns:
        Cache key string
    """
    # Start with method and path
    key_parts = [request.method, request.url.path]

    # Add query parameters
    query_params = sorted(request.query_params.items())
    if query_params:
        key_parts.append("?" + "&".join(f"{k}={v}" for k, v in query_params))

    # Add user ID from authorization if available
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        # In a real implementation, you would extract the user ID from the token
        # For now, just use a hash of the token
        token = auth_header[7:]
        key_parts.append("user:" + hashlib.md5(token.encode()).hexdigest()[:8])

    return ":".join(key_parts)

class EdgeCacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware for adding cache headers to API responses.

    This middleware adds Cache-Control and other cache-related headers
    to API responses based on the endpoint and request method.
    """

    def __init__(
        self,
        app: ASGIApp,
        exclude_paths: Optional[List[str]] = None,
        cache_control_private: bool = True,
    ):
        """
        Initialize the middleware.

        Args:
            app: The ASGI application
            exclude_paths: List of paths to exclude from caching
            cache_control_private: Whether to use private cache control
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or []
        self.cache_control_private = cache_control_private

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and add cache headers to the response.

        Args:
            request: The request to process
            call_next: Function to call the next middleware

        Returns:
            The response with cache headers added
        """
        # Skip caching for excluded paths
        for path in self.exclude_paths:
            if request.url.path.startswith(path):
                return await call_next(request)

        # Process the request
        response = await call_next(request)

        # Skip caching if disabled
        if not EDGE_CACHE_ENABLED:
            return response

        # Skip caching for non-GET requests (except those explicitly configured)
        cache_key = f"{request.method}:{request.url.path}"
        if request.method != "GET" and cache_key not in CACHE_TTLS:
            return response

        # Skip caching for error responses
        if response.status_code >= 400:
            return response

        # Get TTL for this endpoint
        ttl = CACHE_TTLS.get(cache_key, DEFAULT_CACHE_TTL)

        # Skip caching if TTL is 0
        if ttl <= 0:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            return response

        # Add cache headers
        cache_control = f"{'private' if self.cache_control_private else 'public'}, max-age={ttl}"
        response.headers["Cache-Control"] = cache_control

        # Add Vary header for proper cache key generation
        vary_headers = ["Accept", "Accept-Encoding"]

        # Add Authorization to Vary if we're using private cache
        if self.cache_control_private:
            vary_headers.append("Authorization")

        response.headers["Vary"] = ", ".join(vary_headers)

        # Add ETag for conditional requests
        content = getattr(response, "body", None)
        if content:
            etag = f'W/"{hashlib.md5(content).hexdigest()}"'
            response.headers["ETag"] = etag

        return response

def add_edge_cache_middleware(app: FastAPI, **kwargs) -> None:
    """
    Add the edge cache middleware to a FastAPI application.

    Args:
        app: The FastAPI application
        **kwargs: Additional arguments for the middleware
    """
    app.add_middleware(EdgeCacheMiddleware, **kwargs)
