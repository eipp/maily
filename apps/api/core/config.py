"""
Application configuration settings.
"""
from typing import List, Optional
from functools import lru_cache
from pydantic import BaseSettings


class Settings(BaseSettings):
    """
    Application settings.

    These settings can be configured using environment variables.
    """

    # Application settings
    APP_NAME: str = "Maily API"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    ALLOWED_HOSTS: List[str] = ["*"]

    # Database settings
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/maily"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    # Security settings
    SECRET_KEY: str = "your-secret-key"  # Change in production
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    # AI settings
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    DEFAULT_MODEL: str = "gpt-3.5-turbo"
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_MAX_TOKENS: int = 1000

    # AI cache settings
    AI_CACHE_ENABLED: bool = True
    AI_CACHE_TTL_SECONDS: int = 3600  # 1 hour
    AI_CACHE_MAX_SIZE: int = 1000  # Maximum number of cached responses

    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings.

    Returns:
        Settings instance.
    """
    return Settings()
