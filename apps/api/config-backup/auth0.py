"""Auth0 configuration for Maily."""
from pydantic import BaseSettings, Field


class Auth0Settings(BaseSettings):
    """Auth0 configuration settings."""

    DOMAIN: str = Field(..., env="AUTH0_DOMAIN")
    API_AUDIENCE: str = Field(..., env="AUTH0_API_AUDIENCE")
    ALGORITHMS: list[str] = Field(default=["RS256"])
    CLIENT_ID: str = Field(..., env="AUTH0_CLIENT_ID")
    CLIENT_SECRET: str = Field(..., env="AUTH0_CLIENT_SECRET")
    CALLBACK_URL: str = Field(..., env="AUTH0_CALLBACK_URL")
    LOGOUT_URL: str = Field(..., env="AUTH0_LOGOUT_URL")

    # MFA settings
    MFA_ENABLED: bool = Field(default=True, env="AUTH0_MFA_ENABLED")
    ADMIN_ROLES: list[str] = Field(default=["admin"], env="AUTH0_ADMIN_ROLES")

    class Config:
        """Pydantic config."""

        env_file = ".env"
        case_sensitive = True


auth0_settings = Auth0Settings()
