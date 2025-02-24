from fastapi import Depends, HTTPException
from typing import Generator, Optional
from .services.database import get_db_connection
from .models import MODEL_REGISTRY
from .cache.redis import redis_client
from .errors import DatabaseError, AuthenticationError
from .config.settings import settings

async def get_db() -> Generator:
    """Dependency for database connection."""
    conn = None
    try:
        conn = get_db_connection()
        yield conn
    finally:
        if conn:
            conn.close()

def get_model_service(model_name: str = Depends()):
    """Dependency for model service."""
    if model_name not in MODEL_REGISTRY:
        raise HTTPException(status_code=400, detail=f"Model {model_name} not supported")
    return MODEL_REGISTRY[model_name]

def get_redis():
    """Dependency for Redis client."""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis service unavailable")
    return redis_client

def get_current_user(api_key: str = Depends()):
    """Dependency for user authentication."""
    if not api_key or api_key != settings.API_KEY:
        raise AuthenticationError("Invalid API key")
    return {"user_id": 1}  # TODO: Implement proper user authentication 