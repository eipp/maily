import os
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "ivanpeychev")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "maily")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")

    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")

    # API
    API_KEY: str = os.getenv("API_KEY", "mock-api-key")

    # Langfuse
    LANGFUSE_API_KEY: str = os.getenv("LANGFUSE_API_KEY", "")
    LANGFUSE_PUBLIC_KEY: str = os.getenv(
        "LANGFUSE_PUBLIC_KEY", "pk-lf-70bdc4f8-4b1c-4791-a54d-7ea2c3b93b88"
    )

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

    # MailyDocs Settings
    DOCUMENT_STORAGE_PATH: str = os.getenv("DOCUMENT_STORAGE_PATH", "data/documents")
    DOCUMENT_BASE_URL: str = os.getenv("DOCUMENT_BASE_URL", "/documents")
    TEMP_DIRECTORY: str = os.getenv("TEMP_DIRECTORY", "/tmp/mailydocs")

    # Document Generation Limits
    MAX_DOCUMENT_SIZE_MB: int = int(os.getenv("MAX_DOCUMENT_SIZE_MB", "25"))
    MAX_TEMPLATE_SIZE_MB: int = int(os.getenv("MAX_TEMPLATE_SIZE_MB", "10"))
    MAX_SECTIONS_PER_DOCUMENT: int = int(os.getenv("MAX_SECTIONS_PER_DOCUMENT", "50"))

    # Blockchain Verification
    BLOCKCHAIN_ENABLED: bool = os.getenv("BLOCKCHAIN_ENABLED", "false").lower() == "true"
    BLOCKCHAIN_PROVIDER_URL: str = os.getenv("BLOCKCHAIN_PROVIDER_URL", "")
    BLOCKCHAIN_PRIVATE_KEY: str = os.getenv("BLOCKCHAIN_PRIVATE_KEY", "")
    BLOCKCHAIN_CONTRACT_ADDRESS: str = os.getenv("BLOCKCHAIN_CONTRACT_ADDRESS", "")
    BLOCKCHAIN_NETWORK: str = os.getenv("BLOCKCHAIN_NETWORK", "testnet")

    # Document Analytics
    ANALYTICS_ENABLED: bool = os.getenv("ANALYTICS_ENABLED", "true").lower() == "true"
    ANALYTICS_RETENTION_DAYS: int = int(os.getenv("ANALYTICS_RETENTION_DAYS", "365"))

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
