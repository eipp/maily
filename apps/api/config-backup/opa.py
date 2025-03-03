"""Open Policy Agent (OPA) configuration for Maily."""
from pydantic import BaseSettings, Field


class OPASettings(BaseSettings):
    """OPA configuration settings."""

    URL: str = Field(..., env="OPA_URL")
    POLICY_PATH: str = Field(default="v1/data/maily/authz", env="OPA_POLICY_PATH")
    TIMEOUT: int = Field(default=5, env="OPA_TIMEOUT")

    class Config:
        """Pydantic config."""

        env_file = ".env"
        case_sensitive = True


opa_settings = OPASettings()
