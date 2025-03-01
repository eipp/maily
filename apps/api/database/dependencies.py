"""
Dependency injection for database and other services.
Uses FastAPI dependency injection system for clean service pattern implementation.
"""
from typing import Generator, Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from redis import Redis
from prometheus_client import Counter, Histogram
import os
import time
import structlog

from ..monitoring.performance_metrics import MetricsService
from ..cache.tiered_cache_service import CacheService
from ..errors.maily_error import MailyError, AuthenticationError, AuthorizationError

logger = structlog.get_logger(__name__)

# Database dependency
def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    from ..database.session import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Redis dependency
def get_redis_client() -> Redis:
    """Get Redis client from environment configuration."""
    from ..cache.redis_client import create_redis_client

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return create_redis_client(redis_url)

# Cache service dependency
def get_cache_service(
    redis_client: Redis = Depends(get_redis_client),
) -> CacheService:
    """Get cache service with TTL policies."""
    return CacheService(redis_client)

# Metrics service dependency
def get_metrics_service() -> MetricsService:
    """Get metrics service for instrumentation."""
    from ..monitoring.performance_metrics import get_metrics_service

    return get_metrics_service()

# Current user dependency
async def get_current_user(
    token: str = Depends(get_token_from_header),
    db: Session = Depends(get_db),
    cache: CacheService = Depends(get_cache_service),
) -> Dict[str, Any]:
    """Get current user from JWT token.

    Args:
        token: JWT token from Authorization header
        db: Database session
        cache: Cache service

    Returns:
        User data

    Raises:
        AuthenticationError: If token is invalid or missing
    """
    from ..services.auth_service import AuthService

    auth_service = AuthService(db, cache)

    try:
        # Try to get from cache first
        cache_key = f"user:token:{token}"
        cached_user = cache.get(cache_key)

        if cached_user:
            return cached_user

        # Verify token and get user
        user_data = await auth_service.verify_token(token)

        if not user_data:
            raise AuthenticationError("Invalid token")

        # Cache for future requests (short TTL)
        cache.set(cache_key, user_data, "session")

        return user_data

    except Exception as e:
        logger.error("Authentication failed", error=str(e))
        raise AuthenticationError("Invalid or expired token")

# Token extraction
def get_token_from_header(authorization: Optional[str] = None) -> str:
    """Extract token from Authorization header.

    Args:
        authorization: Authorization header

    Returns:
        JWT token

    Raises:
        AuthenticationError: If token is missing
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError("Missing or invalid Authorization header")

    return authorization.replace("Bearer ", "")

# Request timing middleware
async def add_timing_middleware(request, call_next):
    """Middleware to add timing information to response headers."""
    start_time = time.time()

    # Execute request
    response = await call_next(request)

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Add timing header
    response.headers["X-Process-Time-Ms"] = str(int(duration_ms))

    return response

# Request ID middleware
async def add_request_id_middleware(request, call_next):
    """Middleware to add request ID to context."""
    import uuid

    request_id = str(uuid.uuid4())
    structlog.contextvars.bind_contextvars(request_id=request_id)

    # Add to request state
    request.state.request_id = request_id

    # Execute request
    response = await call_next(request)

    # Add request ID header
    response.headers["X-Request-ID"] = request_id

    return response

# Error handler middleware
async def handle_exceptions_middleware(request, call_next):
    """Global exception handler middleware."""
    try:
        return await call_next(request)
    except MailyError as e:
        logger.error(
            "Application error",
            error_type=e.__class__.__name__,
            error_message=str(e),
            status_code=e.status_code,
            error_code=e.error_code,
            request_path=request.url.path,
            request_id=getattr(request.state, "request_id", None),
        )

        # Return standardized error response
        from ..models.api_response import ApiResponse

        return ApiResponse.error(
            message=str(e),
            code=e.error_code,
            status_code=e.status_code
        ).to_response()
    except Exception as e:
        logger.exception(
            "Unhandled exception",
            error_type=e.__class__.__name__,
            error_message=str(e),
            request_path=request.url.path,
            request_id=getattr(request.state, "request_id", None),
        )

        # Return generic error response
        from ..models.api_response import ApiResponse

        return ApiResponse.error(
            message="Internal server error",
            code="internal_error",
            status_code=500
        ).to_response()
