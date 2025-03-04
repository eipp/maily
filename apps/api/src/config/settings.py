"""
API Service configuration settings.

This module defines the settings for the API service using Pydantic for validation.
"""

import os
import logging
from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """API service settings."""
    
    # Application
    app_name: str = os.getenv("APP_NAME", "Maily API")
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    environment: str = os.getenv("ENVIRONMENT", "development")
    version: str = os.getenv("VERSION", "0.1.0")
    api_prefix: str = os.getenv("API_PREFIX", "/api/v1")
    allowed_hosts: List[str] = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    
    # CORS settings
    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,https://justmaily.com,https://www.justmaily.com").split(",")
    
    # Database
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "maily")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "maily")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_POOL_MIN_SIZE: int = int(os.getenv("POSTGRES_POOL_MIN_SIZE", "5"))
    POSTGRES_POOL_MAX_SIZE: int = int(os.getenv("POSTGRES_POOL_MAX_SIZE", "20"))
    POSTGRES_POOL_MAX_IDLE: int = int(os.getenv("POSTGRES_POOL_MAX_IDLE", "10"))

    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    REDIS_POOL_SIZE: int = int(os.getenv("REDIS_POOL_SIZE", "10"))

    # API
    API_KEY: str = os.getenv("API_KEY", "mock-api-key")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    LOG_ROTATION: str = "500 MB"
    LOG_RETENTION: str = "10 days"

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Auth0
    AUTH0_DOMAIN: str = os.getenv("AUTH0_DOMAIN", "")
    AUTH0_API_AUDIENCE: str = os.getenv("AUTH0_API_AUDIENCE", "")
    AUTH0_CLIENT_ID: str = os.getenv("AUTH0_CLIENT_ID", "")
    AUTH0_CLIENT_SECRET: str = os.getenv("AUTH0_CLIENT_SECRET", "")
    AUTH0_CALLBACK_URL: str = os.getenv("AUTH0_CALLBACK_URL", "")
    AUTH0_LOGOUT_URL: str = os.getenv("AUTH0_LOGOUT_URL", "")
    AUTH0_MFA_ENABLED: bool = os.getenv("AUTH0_MFA_ENABLED", "true").lower() == "true"
    AUTH0_ADMIN_ROLES: List[str] = ["admin"]

    # Open Policy Agent
    OPA_URL: str = os.getenv("OPA_URL", "http://opa:8181")
    OPA_POLICY_PATH: str = os.getenv("OPA_POLICY_PATH", "v1/data/maily/authz")
    OPA_TIMEOUT: int = int(os.getenv("OPA_TIMEOUT", "5"))

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get settings instance.
    
    Uses lru_cache for performance.
    """
    return Settings()

# Export settings for import elsewhere
settings = get_settings()