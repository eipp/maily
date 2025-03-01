"""Service-to-service authentication client for maily services."""
import os
import logging
import time
from typing import Dict, Any, Optional
import json

import httpx
from jose import jwt

logger = logging.getLogger(__name__)

# Service authentication configuration
TOKEN_ENDPOINT = os.getenv("SERVICE_TOKEN_ENDPOINT", "http://auth-service/api/v1/service/token")
PRIVATE_KEY_PATH = os.getenv("SERVICE_PRIVATE_KEY_PATH", "/vault/secrets/service-key.pem")
SERVICE_ID = os.getenv("SERVICE_ID")
SERVICE_NAME = os.getenv("SERVICE_NAME")


class ServiceAuthClient:
    """Client for service-to-service authentication."""

    def __init__(
        self,
        service_name: Optional[str] = None,
        service_id: Optional[str] = None,
        token_endpoint: Optional[str] = None,
        private_key_path: Optional[str] = None
    ):
        """Initialize the service authentication client.

        Args:
            service_name: Name of the service. Defaults to SERVICE_NAME env var.
            service_id: ID of the service. Defaults to SERVICE_ID env var.
            token_endpoint: URL of the token endpoint. Defaults to TOKEN_ENDPOINT env var.
            private_key_path: Path to the service's private key. Defaults to PRIVATE_KEY_PATH env var.
        """
        self.service_name = service_name or SERVICE_NAME
        self.service_id = service_id or SERVICE_ID
        self.token_endpoint = token_endpoint or TOKEN_ENDPOINT
        self.private_key_path = private_key_path or PRIVATE_KEY_PATH

        if not self.service_name or not self.service_id:
            raise ValueError("Service name and ID must be provided")

        self._token = None
        self._token_expiry = 0

    async def _load_private_key(self) -> str:
        """Load the service's private key from file.

        Returns:
            The private key as a string.

        Raises:
            FileNotFoundError: If the private key file doesn't exist.
            PermissionError: If the private key file can't be read.
        """
        try:
            with open(self.private_key_path, "r") as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Private key file not found: {self.private_key_path}")
            raise
        except PermissionError:
            logger.error(f"Permission denied when reading private key file: {self.private_key_path}")
            raise

    async def _create_service_assertion(self) -> str:
        """Create a signed JWT assertion for the service.

        Returns:
            A signed JWT assertion.
        """
        private_key = await self._load_private_key()

        now = int(time.time())
        payload = {
            "iss": self.service_id,
            "sub": self.service_id,
            "aud": self.token_endpoint,
            "name": self.service_name,
            "iat": now,
            "exp": now + 60,  # 1 minute expiry for assertion
            "jti": f"jti-{now}"
        }

        return jwt.encode(payload, private_key, algorithm="RS256")

    async def get_service_token(self, force_refresh: bool = False) -> str:
        """Get a service token for authentication.

        Args:
            force_refresh: Force a token refresh even if the current token is still valid.

        Returns:
            A service token.

        Raises:
            httpx.HTTPError: If the token request fails.
        """
        now = time.time()

        # Return cached token if it's still valid and not forced to refresh
        if not force_refresh and self._token and now < self._token_expiry - 60:  # 1 minute buffer
            return self._token

        try:
            assertion = await self._create_service_assertion()

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_endpoint,
                    json={
                        "grant_type": "client_credentials",
                        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                        "client_assertion": assertion
                    }
                )
                response.raise_for_status()

                token_data = response.json()
                self._token = token_data["access_token"]
                # Convert expires_in (seconds) to absolute time
                self._token_expiry = now + token_data["expires_in"]

                return self._token
        except httpx.HTTPError as e:
            logger.error(f"Failed to get service token: {str(e)}")
            raise

    async def get_auth_headers(self, force_refresh: bool = False) -> Dict[str, str]:
        """Get authentication headers for service-to-service requests.

        Args:
            force_refresh: Force a token refresh even if the current token is still valid.

        Returns:
            A dictionary of authentication headers.
        """
        token = await self.get_service_token(force_refresh)
        return {"Authorization": f"Bearer {token}"}

    async def call_service_api(
        self,
        url: str,
        method: str = "GET",
        data: Any = None,
        json_data: Any = None,
        params: Dict[str, Any] = None,
        headers: Dict[str, str] = None
    ) -> httpx.Response:
        """Call a service API with authentication.

        Args:
            url: The URL to call.
            method: The HTTP method to use. Defaults to GET.
            data: The request data. Defaults to None.
            json_data: The request JSON data. Defaults to None.
            params: The request parameters. Defaults to None.
            headers: Additional headers to include. Defaults to None.

        Returns:
            The response from the service.

        Raises:
            httpx.HTTPError: If the request fails.
        """
        auth_headers = await self.get_auth_headers()

        if headers:
            request_headers = {**headers, **auth_headers}
        else:
            request_headers = auth_headers

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                url,
                data=data,
                json=json_data,
                params=params,
                headers=request_headers
            )
            response.raise_for_status()
            return response


# Singleton instance for easy import and use
service_auth_client = ServiceAuthClient()
