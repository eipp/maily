"""Vault service for managing secrets."""
import os
import logging
from typing import Dict, Any, Optional, List
import json
import httpx
import aiofiles

logger = logging.getLogger(__name__)

# Vault configuration
VAULT_ADDR = os.getenv("VAULT_ADDR", "http://vault:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN")
VAULT_TOKEN_FILE = os.getenv("VAULT_TOKEN_FILE", "/vault/secrets/token")
VAULT_ROLE = os.getenv("VAULT_ROLE", "maily")


class VaultService:
    """Service for interacting with HashiCorp Vault."""

    def __init__(self, vault_addr: Optional[str] = None, vault_token: Optional[str] = None):
        """Initialize the Vault service.

        Args:
            vault_addr: The address of the Vault server. Defaults to VAULT_ADDR env var.
            vault_token: The Vault token. Defaults to VAULT_TOKEN env var.
        """
        self.vault_addr = vault_addr or VAULT_ADDR
        self._vault_token = vault_token or VAULT_TOKEN
        self._token = None

    async def _get_token(self) -> str:
        """Get the Vault token.

        Returns:
            The Vault token.

        Raises:
            ValueError: If no token is available.
        """
        # Return cached token if available
        if self._token:
            return self._token

        # Try to use provided token
        if self._vault_token:
            self._token = self._vault_token
            return self._token

        # Try to read token from file (Vault Agent injected token)
        try:
            if os.path.exists(VAULT_TOKEN_FILE):
                async with aiofiles.open(VAULT_TOKEN_FILE, "r") as f:
                    self._token = (await f.read()).strip()
                    return self._token
        except Exception as e:
            logger.warning(f"Failed to read token from file {VAULT_TOKEN_FILE}: {str(e)}")

        # Try to authenticate using Kubernetes auth method
        try:
            # Read service account token
            async with aiofiles.open("/var/run/secrets/kubernetes.io/serviceaccount/token", "r") as f:
                jwt_token = (await f.read()).strip()

            # Authenticate to Vault
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.vault_addr}/v1/auth/kubernetes/login",
                    json={"jwt": jwt_token, "role": VAULT_ROLE}
                )
                response.raise_for_status()

                auth_data = response.json()
                self._token = auth_data["auth"]["client_token"]
                return self._token
        except Exception as e:
            logger.warning(f"Failed to authenticate to Vault using Kubernetes: {str(e)}")

        # No token available
        raise ValueError("No Vault token available. Set VAULT_TOKEN env var or mount token file.")

    async def list_secrets(self, path: str) -> List[str]:
        """List secrets at a path.

        Args:
            path: The path to list secrets at.

        Returns:
            A list of secret names.

        Raises:
            httpx.HTTPError: If the request fails.
        """
        token = await self._get_token()

        # Ensure path is properly formatted (remove leading/trailing slashes)
        path = path.strip("/")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.vault_addr}/v1/{path}",
                headers={"X-Vault-Token": token},
                params={"list": "true"}
            )
            response.raise_for_status()

            data = response.json()
            return data.get("data", {}).get("keys", [])

    async def get_secret(self, path: str) -> Dict[str, Any]:
        """Get a secret.

        Args:
            path: The path to the secret.

        Returns:
            The secret data.

        Raises:
            httpx.HTTPError: If the request fails.
        """
        token = await self._get_token()

        # Ensure path is properly formatted (remove leading/trailing slashes)
        path = path.strip("/")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.vault_addr}/v1/{path}",
                headers={"X-Vault-Token": token}
            )
            response.raise_for_status()

            data = response.json()
            return data.get("data", {})

    async def create_or_update_secret(self, path: str, data: Dict[str, Any]) -> None:
        """Create or update a secret.

        Args:
            path: The path to the secret.
            data: The secret data.

        Raises:
            httpx.HTTPError: If the request fails.
        """
        token = await self._get_token()

        # Ensure path is properly formatted (remove leading/trailing slashes)
        path = path.strip("/")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.vault_addr}/v1/{path}",
                headers={"X-Vault-Token": token},
                json={"data": data}
            )
            response.raise_for_status()

    async def delete_secret(self, path: str) -> None:
        """Delete a secret.

        Args:
            path: The path to the secret.

        Raises:
            httpx.HTTPError: If the request fails.
        """
        token = await self._get_token()

        # Ensure path is properly formatted (remove leading/trailing slashes)
        path = path.strip("/")

        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.vault_addr}/v1/{path}",
                headers={"X-Vault-Token": token}
            )
            response.raise_for_status()

    async def get_database_credentials(self, database: str) -> Dict[str, str]:
        """Get dynamic database credentials.

        Args:
            database: The name of the database.

        Returns:
            A dictionary with database credentials (username, password).

        Raises:
            httpx.HTTPError: If the request fails.
        """
        token = await self._get_token()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.vault_addr}/v1/database/creds/{database}",
                headers={"X-Vault-Token": token}
            )
            response.raise_for_status()

            data = response.json()
            return {
                "username": data.get("data", {}).get("username"),
                "password": data.get("data", {}).get("password")
            }

    async def get_service_token(self, service: str, ttl: str = "1h") -> str:
        """Get a service token.

        Args:
            service: The name of the service.
            ttl: The time-to-live for the token (e.g., "1h", "30m").

        Returns:
            The service token.

        Raises:
            httpx.HTTPError: If the request fails.
        """
        token = await self._get_token()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.vault_addr}/v1/auth/token/create",
                headers={"X-Vault-Token": token},
                json={
                    "meta": {"service": service},
                    "ttl": ttl,
                    "policies": [f"service-{service}"]
                }
            )
            response.raise_for_status()

            data = response.json()
            return data.get("auth", {}).get("client_token")


# Singleton instance for easy import and use
vault_service = VaultService()
