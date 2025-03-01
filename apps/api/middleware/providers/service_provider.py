"""Service-to-Service Authentication Provider implementation using HashiCorp Vault."""
import logging
import os
from typing import Dict, Any, Optional
import time
import json

from jose import jwt, JWTError
import httpx

from ..standardized_auth import ServiceTokenProvider, JWTVerificationError
from database.session import get_db

logger = logging.getLogger(__name__)

# Service authentication configuration
VAULT_ADDR = os.getenv("VAULT_ADDR", "http://vault:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN")
VAULT_JWT_ROLE = os.getenv("VAULT_JWT_ROLE", "maily-services")
SERVICE_TOKEN_ISSUER = os.getenv("SERVICE_TOKEN_ISSUER", "maily-auth")


class VaultServiceTokenProvider(ServiceTokenProvider):
    """Vault-backed service token authentication provider."""

    def __init__(self):
        """Initialize the Vault service token provider."""
        self.vault_addr = VAULT_ADDR
        self.vault_token = VAULT_TOKEN
        self.vault_jwt_role = VAULT_JWT_ROLE
        self.issuer = SERVICE_TOKEN_ISSUER
        self.jwks = None
        self.jwks_last_update = 0

    async def _get_service_jwks(self):
        """Get or refresh the JWKS from Vault."""
        # Refresh JWKS every 15 minutes
        now = time.time()
        if self.jwks is None or now - self.jwks_last_update > 900:  # 15 minutes
            try:
                headers = {"X-Vault-Token": self.vault_token}
                async with httpx.AsyncClient() as client:
                    # Get the JWKS from Vault's JWT auth backend
                    response = await client.get(
                        f"{self.vault_addr}/v1/auth/jwt/jwks",
                        headers=headers
                    )
                    response.raise_for_status()
                    self.jwks = response.json()
                    self.jwks_last_update = now
            except Exception as e:
                logger.error(f"Failed to get JWKS from Vault: {str(e)}")
                if self.jwks is None:
                    raise JWTVerificationError(f"Failed to get JWKS from Vault: {str(e)}")
        return self.jwks

    async def verify_service_token(self, token: str) -> Dict[str, Any]:
        """Verify a service token and return service information.

        Args:
            token: The service token to verify.

        Returns:
            Service information if the token is valid.

        Raises:
            JWTVerificationError: If token verification fails.
        """
        try:
            # Get the JWKS
            jwks = await self._get_service_jwks()

            # Decode the token header to get the key ID
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            if not kid:
                raise JWTVerificationError("Invalid token: missing key ID")

            # Find the key in the JWKS
            key = None
            for jwk in jwks.get("keys", []):
                if jwk.get("kid") == kid:
                    key = jwk
                    break

            if not key:
                raise JWTVerificationError(f"Key ID {kid} not found in JWKS")

            # Verify the token
            payload = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                issuer=self.issuer
            )

            # Extract service information from the token
            service_name = payload.get("service")
            if not service_name:
                raise JWTVerificationError("Invalid token: missing service name")

            service_id = payload.get("sub")
            if not service_id:
                raise JWTVerificationError("Invalid token: missing subject")

            # Check token expiration
            exp = payload.get("exp")
            if not exp or exp < time.time():
                raise JWTVerificationError("Token expired")

            # Check service permissions
            permissions = payload.get("permissions", [])

            # Return the service information
            return {
                "id": service_id,
                "service_name": service_name,
                "permissions": permissions,
                "auth_method": "service_token",
                "token_id": payload.get("jti")
            }
        except JWTError as e:
            logger.error(f"Service token verification error: {str(e)}")
            raise JWTVerificationError(f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error(f"Service authentication error: {str(e)}")
            raise JWTVerificationError(f"Service authentication error: {str(e)}")

    async def validate_service_permission(self, service_info: Dict[str, Any], required_permission: str) -> bool:
        """Validate if a service has the required permission.

        Args:
            service_info: The service information.
            required_permission: The permission to check.

        Returns:
            True if the service has the permission, False otherwise.
        """
        permissions = service_info.get("permissions", [])
        return (
            required_permission in permissions or
            "*" in permissions
        )
