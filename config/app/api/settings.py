"""
Centralized settings for the API service.
All configuration should be defined here and accessed via the settings object.
"""

import os
import logging
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
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
    BLOCKCHAIN_ENABLED: bool = os.getenv("BLOCKCHAIN_ENABLED", "true").lower() == "true"
    POLYGON_RPC_URL: str = os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com")
    BLOCKCHAIN_PRIVATE_KEY: str = os.getenv("BLOCKCHAIN_PRIVATE_KEY", "")
    EMAIL_VERIFICATION_CONTRACT_ADDRESS: str = os.getenv("EMAIL_VERIFICATION_CONTRACT_ADDRESS", "")
    CERTIFICATE_CONTRACT_ADDRESS: str = os.getenv("CERTIFICATE_CONTRACT_ADDRESS", "")
    VERIFICATION_CONTRACT_ADDRESS: str = os.getenv("VERIFICATION_CONTRACT_ADDRESS", "")
    BLOCKCHAIN_NETWORK: str = os.getenv("BLOCKCHAIN_NETWORK", "polygon")
    MULTICALL_CONTRACT_ADDRESS: str = os.getenv("MULTICALL_CONTRACT_ADDRESS", "0x11ce4B23bD875D7F5C6a31084f55fDe1e9A87507")
    GAS_PRICE_MULTIPLIER: float = float(os.getenv("GAS_PRICE_MULTIPLIER", "1.1"))
    MAX_GAS_PRICE_GWEI: int = int(os.getenv("MAX_GAS_PRICE_GWEI", "100"))
    BLOCKCHAIN_RETRY_ATTEMPTS: int = int(os.getenv("BLOCKCHAIN_RETRY_ATTEMPTS", "3"))
    BATCH_SIZE_LIMIT: int = int(os.getenv("BATCH_SIZE_LIMIT", "10"))
    BATCH_PROCESSING_TIMEOUT: int = int(os.getenv("BATCH_PROCESSING_TIMEOUT", "30000"))  # ms
    
    # ABI paths (can be overridden with environment variables)
    VERIFICATION_CONTRACT_ABI_PATH: str = os.getenv("VERIFICATION_CONTRACT_ABI_PATH", "contracts/VerificationABI.json")
    CERTIFICATE_CONTRACT_ABI_PATH: str = os.getenv("CERTIFICATE_CONTRACT_ABI_PATH", "contracts/CertificateABI.json")
    EMAIL_VERIFICATION_ABI_PATH: str = os.getenv("EMAIL_VERIFICATION_ABI_PATH", "contracts/EmailVerificationABI.json")
    
    # Contract ABIs (loaded at runtime)
    VERIFICATION_CONTRACT_ABI: list = []
    CERTIFICATE_CONTRACT_ABI: list = []
    EMAIL_VERIFICATION_ABI: list = []

    # Document Analytics
    ANALYTICS_ENABLED: bool = os.getenv("ANALYTICS_ENABLED", "true").lower() == "true"
    ANALYTICS_RETENTION_DAYS: int = int(os.getenv("ANALYTICS_RETENTION_DAYS", "365"))

    class Config:
        env_file = ".env"
        case_sensitive = True


def load_blockchain_abis():
    """Load blockchain ABIs from JSON files"""
    import json
    import os
    
    logger = logging.getLogger("api.config.settings")
    settings = Settings()
    
    # Setup contracts directory
    contracts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "apps/api/contracts")
    os.makedirs(contracts_dir, exist_ok=True)
    
    # Helper to load ABI files
    def load_abi(file_path, default_name):
        try:
            # Try absolute path first
            if os.path.isfile(file_path):
                with open(file_path) as f:
                    return json.load(f)
            
            # Try relative to contracts directory
            rel_path = os.path.join(contracts_dir, os.path.basename(file_path))
            if os.path.isfile(rel_path):
                with open(rel_path) as f:
                    return json.load(f)
                
            # Try default name in contracts directory
            default_path = os.path.join(contracts_dir, default_name)
            if os.path.isfile(default_path):
                with open(default_path) as f:
                    return json.load(f)
                
            logger.warning(f"Could not find ABI file: {file_path} or {default_name}")
            return []
        except Exception as e:
            logger.error(f"Error loading ABI file {file_path}: {e}")
            return []
    
    # Load ABIs
    settings.VERIFICATION_CONTRACT_ABI = load_abi(
        settings.VERIFICATION_CONTRACT_ABI_PATH, "VerificationABI.json"
    )
    settings.CERTIFICATE_CONTRACT_ABI = load_abi(
        settings.CERTIFICATE_CONTRACT_ABI_PATH, "CertificateABI.json"
    )
    settings.EMAIL_VERIFICATION_ABI = load_abi(
        settings.EMAIL_VERIFICATION_ABI_PATH, "EmailVerificationABI.json"
    )
    
    return settings


settings = load_blockchain_abis()