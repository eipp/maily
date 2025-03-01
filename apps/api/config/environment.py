"""
Environment Configuration Management

Provides a robust system for loading and validating environment variables,
with support for different environments, schema validation, and secure handling.
"""

import os
import sys
import json
import logging
from typing import Any, Dict, List, Optional, Set, Union, Type, TypeVar, Generic, cast
from enum import Enum
from pathlib import Path
import re

# Try to import pydantic
try:
    from pydantic import BaseModel, Field, validator, root_validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    # Use a minimal implementation if pydantic isn't available
    class BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    def Field(*args, **kwargs):
        return None

    def validator(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

    def root_validator(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

logger = logging.getLogger(__name__)

# Environment enum
class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"

# Default environment variable names
ENV_VAR_NAME = "MAILY_ENV"
CONFIG_FILE_VAR_NAME = "MAILY_CONFIG_FILE"

# Type variable for generic typing
T = TypeVar('T')

class EnvironmentConfig(BaseModel if PYDANTIC_AVAILABLE else object):
    """Base configuration model with common settings."""

    # Environment
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Application environment"
    )

    # Debug settings
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Application log level"
    )

    # Security
    secret_key: str = Field(
        description="Secret key for signing tokens and cookies"
    )

    # Database
    database_url: str = Field(
        description="Database connection URL"
    )
    database_pool_size: int = Field(
        default=5,
        description="Database connection pool size"
    )
    database_max_overflow: int = Field(
        default=10,
        description="Maximum overflow connections"
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )

    # API settings
    api_host: str = Field(
        default="0.0.0.0",
        description="API host to bind to"
    )
    api_port: int = Field(
        default=8000,
        description="API port to bind to"
    )
    api_workers: int = Field(
        default=4,
        description="Number of API workers"
    )
    api_timeout: int = Field(
        default=60,
        description="API request timeout in seconds"
    )
    cors_origins: List[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins"
    )

    # Web settings
    web_url: str = Field(
        default="http://localhost:3000",
        description="Web application URL"
    )

    # Email settings
    email_provider: str = Field(
        default="sendgrid",
        description="Email provider (sendgrid, mailgun, resend)"
    )
    email_api_key: Optional[str] = Field(
        default=None,
        description="Email provider API key"
    )
    email_from_address: str = Field(
        default="no-reply@justmaily.com",
        description="Email from address"
    )

    # AI settings
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key"
    )
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key"
    )
    google_ai_api_key: Optional[str] = Field(
        default=None,
        description="Google AI API key"
    )

    # Storage settings
    storage_provider: str = Field(
        default="local",
        description="Storage provider (local, s3, gcs)"
    )
    storage_bucket: Optional[str] = Field(
        default=None,
        description="Storage bucket name"
    )
    storage_access_key: Optional[str] = Field(
        default=None,
        description="Storage access key"
    )
    storage_secret_key: Optional[str] = Field(
        default=None,
        description="Storage secret key"
    )

    # Rate limiting
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting"
    )
    rate_limit_requests: int = Field(
        default=100,
        description="Maximum requests per window"
    )
    rate_limit_window: int = Field(
        default=60,
        description="Rate limit window in seconds"
    )

    # Feature flags
    features_enabled: Dict[str, bool] = Field(
        default={},
        description="Feature flags"
    )

    # Additional settings
    extra: Dict[str, Any] = Field(
        default={},
        description="Additional configuration values"
    )

    # Validators
    @validator("secret_key")
    def validate_secret_key(cls, v):
        """Validate secret key is strong enough."""
        if not v or len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters")
        return v

    @validator("database_url")
    def validate_database_url(cls, v):
        """Validate database URL format."""
        if not v:
            raise ValueError("Database URL is required")

        if not (v.startswith("postgresql://") or
                v.startswith("postgres://") or
                v.startswith("sqlite:///")):
            raise ValueError("Unsupported database URL format")

        return v

    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()

    @validator("email_provider")
    def validate_email_provider(cls, v):
        """Validate email provider is supported."""
        valid_providers = ["sendgrid", "mailgun", "resend", "none"]
        if v.lower() not in valid_providers:
            raise ValueError(f"Email provider must be one of {valid_providers}")
        return v.lower()

    @validator("storage_provider")
    def validate_storage_provider(cls, v):
        """Validate storage provider is supported."""
        valid_providers = ["local", "s3", "gcs"]
        if v.lower() not in valid_providers:
            raise ValueError(f"Storage provider must be one of {valid_providers}")
        return v.lower()

    @root_validator
    def validate_storage_credentials(cls, values):
        """Validate storage credentials if using cloud storage."""
        provider = values.get("storage_provider", "")

        if provider in ["s3", "gcs"]:
            # Check for required credentials
            if not values.get("storage_bucket"):
                raise ValueError(f"{provider} storage requires storage_bucket")

            if provider == "s3" and (not values.get("storage_access_key") or not values.get("storage_secret_key")):
                raise ValueError("S3 storage requires storage_access_key and storage_secret_key")

        return values

    @root_validator
    def validate_email_credentials(cls, values):
        """Validate email credentials if using email provider."""
        provider = values.get("email_provider", "")

        if provider not in ["none", ""]:
            # Check for required credentials
            if not values.get("email_api_key"):
                raise ValueError(f"{provider} email provider requires email_api_key")

        return values

    @root_validator
    def set_environment_specific_defaults(cls, values):
        """Set environment-specific defaults."""
        env = values.get("environment", Environment.DEVELOPMENT)

        # Production-specific defaults
        if env == Environment.PRODUCTION:
            # Ensure debug is off in production
            values["debug"] = False

            # Increase workers and connection pools in production
            if "api_workers" not in values:
                values["api_workers"] = 8

            if "database_pool_size" not in values:
                values["database_pool_size"] = 10

        # Development-specific defaults
        elif env == Environment.DEVELOPMENT:
            # Enable debug in development
            if "debug" not in values:
                values["debug"] = True

        # Test-specific defaults
        elif env == Environment.TEST:
            # Disable rate limiting in tests
            values["rate_limit_enabled"] = False

        return values

    class Config:
        if PYDANTIC_AVAILABLE:
            use_enum_values = True
            validate_assignment = True
            extra = "ignore"


class ConfigurationLoader:
    """
    Loads configuration from environment variables and files.

    Supports:
    - Loading from environment variables
    - Loading from .env files
    - Loading from JSON/YAML configuration files
    - Environment-specific configurations
    - Secure handling of sensitive values
    """

    def __init__(
        self,
        env_var_prefix: str = "MAILY_",
        env_var_name: str = ENV_VAR_NAME,
        config_file_var_name: str = CONFIG_FILE_VAR_NAME,
        config_dir: Optional[str] = None,
        config_schema: Optional[Type[T]] = None,
        secrets_file: Optional[str] = None,
    ):
        """
        Initialize configuration loader.

        Args:
            env_var_prefix: Prefix for environment variables
            env_var_name: Name of environment variable containing the environment
            config_file_var_name: Name of environment variable containing config file path
            config_dir: Directory containing configuration files
            config_schema: Configuration schema class
            secrets_file: Path to secrets file
        """
        self.env_var_prefix = env_var_prefix
        self.env_var_name = env_var_name
        self.config_file_var_name = config_file_var_name
        self.config_dir = config_dir or os.path.dirname(os.path.abspath(__file__))
        self.config_schema = config_schema or EnvironmentConfig
        self.secrets_file = secrets_file

        # Determine environment
        self.environment = self._get_environment()

        # Initialize config dict
        self.config_dict = {}

        # Track loaded config sources
        self.loaded_sources = []

    def _get_environment(self) -> Environment:
        """Get current environment from environment variable."""
        env_value = os.environ.get(self.env_var_name, "development").lower()

        try:
            return Environment(env_value)
        except ValueError:
            logger.warning(
                f"Invalid environment value: {env_value}. Using development."
            )
            return Environment.DEVELOPMENT

    def _load_env_file(self, env_file: str) -> Dict[str, str]:
        """Load variables from .env file."""
        env_vars = {}

        try:
            if os.path.exists(env_file):
                with open(env_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue

                        if "=" in line:
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip()

                            # Remove quotes if present
                            if value.startswith('"') and value.endswith('"'):
                                value = value[1:-1]
                            elif value.startswith("'") and value.endswith("'"):
                                value = value[1:-1]

                            env_vars[key] = value

                self.loaded_sources.append(f"env-file:{env_file}")
                logger.debug(f"Loaded environment variables from {env_file}")
        except Exception as e:
            logger.warning(f"Error loading .env file {env_file}: {str(e)}")

        return env_vars

    def _load_json_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        config = {}

        try:
            if os.path.exists(config_file):
                with open(config_file, "r") as f:
                    config = json.load(f)

                self.loaded_sources.append(f"json:{config_file}")
                logger.debug(f"Loaded configuration from {config_file}")
        except Exception as e:
            logger.warning(f"Error loading config file {config_file}: {str(e)}")

        return config

    def _load_yaml_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        config = {}

        try:
            # Import yaml here to avoid dependency for users not using YAML
            import yaml

            if os.path.exists(config_file):
                with open(config_file, "r") as f:
                    config = yaml.safe_load(f)

                self.loaded_sources.append(f"yaml:{config_file}")
                logger.debug(f"Loaded configuration from {config_file}")
        except ImportError:
            logger.warning("YAML support requires pyyaml package")
        except Exception as e:
            logger.warning(f"Error loading config file {config_file}: {str(e)}")

        return config

    def _load_secrets(self) -> Dict[str, str]:
        """Load secrets from secrets file."""
        secrets = {}

        if not self.secrets_file:
            return secrets

        try:
            if os.path.exists(self.secrets_file):
                with open(self.secrets_file, "r") as f:
                    secrets = json.load(f)

                self.loaded_sources.append(f"secrets:{self.secrets_file}")
                logger.debug(f"Loaded secrets from {self.secrets_file}")
        except Exception as e:
            logger.warning(f"Error loading secrets file {self.secrets_file}: {str(e)}")

        return secrets

    def _convert_env_vars(self) -> Dict[str, Any]:
        """
        Convert environment variables to nested dictionary.

        Example:
            MAILY_DATABASE_URL=... -> {"database": {"url": ...}}
        """
        result = {}
        prefix_len = len(self.env_var_prefix)

        for key, value in os.environ.items():
            # Only process variables with the prefix
            if key.startswith(self.env_var_prefix):
                # Remove prefix and split by underscore
                key_parts = key[prefix_len:].lower().split("_")

                # Convert boolean values
                if value.lower() in ["true", "yes", "1", "t", "y"]:
                    value = True
                elif value.lower() in ["false", "no", "0", "f", "n"]:
                    value = False
                # Convert integer values
                elif value.isdigit():
                    value = int(value)
                # Convert float values
                elif value.replace(".", "", 1).isdigit() and value.count(".") == 1:
                    value = float(value)
                # Convert list values
                elif value.startswith("[") and value.endswith("]"):
                    try:
                        value = json.loads(value)
                    except:
                        pass

                # Build nested dictionary
                current = result
                for i, part in enumerate(key_parts):
                    if i == len(key_parts) - 1:
                        # Last part, set the value
                        current[part] = value
                    else:
                        # Create nested dictionary if needed
                        if part not in current:
                            current[part] = {}
                        current = current[part]

        self.loaded_sources.append("env-vars")
        return result

    def _flatten_dict(
        self,
        nested_dict: Dict[str, Any],
        parent_key: str = "",
        sep: str = "_"
    ) -> Dict[str, Any]:
        """Flatten a nested dictionary to a flat one with separated keys."""
        items = []
        for key, value in nested_dict.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key

            if isinstance(value, dict):
                items.extend(
                    self._flatten_dict(value, new_key, sep).items()
                )
            else:
                items.append((new_key, value))

        return dict(items)

    def _merge_dicts(self, dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge two dictionaries, with dict2 taking precedence."""
        result = dict1.copy()

        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_dicts(result[key], value)
            else:
                result[key] = value

        return result

    def load_config(self) -> T:
        """
        Load configuration from all available sources.

        Order of precedence (highest to lowest):
        1. Environment variables
        2. Environment-specific configuration file
        3. Secrets file
        4. Common configuration file
        5. Default values from schema

        Returns:
            Configuration object
        """
        # Reset configuration
        self.config_dict = {}
        self.loaded_sources = []

        # Determine configuration file paths
        config_dir = os.path.abspath(self.config_dir)
        common_config_file = os.path.join(config_dir, "config.json")
        env_config_file = os.path.join(config_dir, f"config.{self.environment}.json")
        env_file = os.path.join(config_dir, ".env")
        env_specific_file = os.path.join(config_dir, f".env.{self.environment}")

        # Check for config file override
        config_file_override = os.environ.get(self.config_file_var_name)
        if config_file_override:
            if os.path.exists(config_file_override):
                env_config_file = config_file_override
            else:
                logger.warning(f"Config file override {config_file_override} does not exist")

        # Load common configuration (lowest precedence)
        common_config = {}
        if os.path.exists(common_config_file):
            if common_config_file.endswith(".json"):
                common_config = self._load_json_config(common_config_file)
            elif common_config_file.endswith((".yml", ".yaml")):
                common_config = self._load_yaml_config(common_config_file)

        # Load environment-specific configuration
        env_config = {}
        if os.path.exists(env_config_file):
            if env_config_file.endswith(".json"):
                env_config = self._load_json_config(env_config_file)
            elif env_config_file.endswith((".yml", ".yaml")):
                env_config = self._load_yaml_config(env_config_file)

        # Load secrets
        secrets = self._load_secrets()

        # Load environment variables from .env files
        if os.path.exists(env_file):
            for key, value in self._load_env_file(env_file).items():
                os.environ.setdefault(key, value)

        if os.path.exists(env_specific_file):
            for key, value in self._load_env_file(env_specific_file).items():
                os.environ[key] = value

        # Load environment variables
        env_vars = self._convert_env_vars()

        # Merge configurations in order of precedence
        self.config_dict = common_config
        self.config_dict = self._merge_dicts(self.config_dict, secrets)
        self.config_dict = self._merge_dicts(self.config_dict, env_config)
        self.config_dict = self._merge_dicts(self.config_dict, env_vars)

        # Add environment to config
        self.config_dict["environment"] = self.environment

        # Create configuration object
        flattened_config = self._flatten_dict(self.config_dict)

        try:
            config_obj = self.config_schema(**flattened_config)
            return cast(T, config_obj)
        except Exception as e:
            logger.error(f"Error creating configuration object: {str(e)}")
            logger.error(f"Loaded config: {self.config_dict}")

            # In development, raise the error for debugging
            if self.environment == Environment.DEVELOPMENT:
                raise

            # In production, use a default configuration
            logger.warning("Using default configuration")
            return cast(T, self.config_schema())

    def get_source_info(self) -> List[str]:
        """Get information about loaded configuration sources."""
        return self.loaded_sources

    def dump_config(self, exclude_sensitive: bool = True) -> Dict[str, Any]:
        """
        Dump configuration as dictionary.

        Args:
            exclude_sensitive: Whether to exclude sensitive values

        Returns:
            Configuration dictionary
        """
        # Create a copy of the config dict
        config_copy = self.config_dict.copy()

        # Mask sensitive values if requested
        if exclude_sensitive:
            sensitive_keys = [
                "secret_key", "password", "secret", "key", "token", "api_key"
            ]

            # Recursively mask sensitive values
            def mask_sensitive_values(config: Dict[str, Any], sensitive_keys: List[str]) -> None:
                for key, value in config.items():
                    if isinstance(value, dict):
                        mask_sensitive_values(value, sensitive_keys)
                    elif any(sensitive in key.lower() for sensitive in sensitive_keys) and value:
                        config[key] = "********"

            mask_sensitive_values(config_copy, sensitive_keys)

        return config_copy


# Create a global configuration instance
config_loader = ConfigurationLoader()
config = config_loader.load_config()

def get_config() -> EnvironmentConfig:
    """Get the global configuration instance."""
    return config

def reload_config() -> EnvironmentConfig:
    """Reload the global configuration."""
    global config
    config = config_loader.load_config()
    return config
