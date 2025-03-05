"""Vault service for managing secrets."""
import os
import logging
import hashlib
import time
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Callable
import httpx
import aiofiles
from packages.error_handling.python.errors import ConfigurationError, ServiceUnavailableError

logger = logging.getLogger(__name__)

# Vault configuration
VAULT_ADDR = os.getenv("VAULT_ADDR", "http://vault:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN")
VAULT_TOKEN_FILE = os.getenv("VAULT_TOKEN_FILE", "/vault/secrets/token")
VAULT_ROLE = os.getenv("VAULT_ROLE", "maily")
VAULT_SECRET_PREFIX = os.getenv("VAULT_SECRET_PREFIX", "maily")
VAULT_CONFIG_PATH = os.getenv("VAULT_CONFIG_PATH", f"{VAULT_SECRET_PREFIX}/data/config")
VAULT_API_KEYS_PATH = os.getenv("VAULT_API_KEYS_PATH", f"{VAULT_SECRET_PREFIX}/data/api-keys")
VAULT_CREDENTIALS_PATH = os.getenv("VAULT_CREDENTIALS_PATH", f"{VAULT_SECRET_PREFIX}/data/credentials")

# Secret cache TTL in seconds
SECRET_CACHE_TTL = int(os.getenv("VAULT_SECRET_CACHE_TTL", "300"))  # 5 minutes default


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
        self._token_expiry = 0
        
        # Secret cache for improved performance
        self._secret_cache: Dict[str, Tuple[Dict[str, Any], float]] = {}
        
        # Secret listeners for automatic updates
        self._secret_listeners: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}
        
        # Secret watchers for KV-V2 secrets
        self._secret_watchers: Dict[str, asyncio.Task] = {}
        
        # Health check state
        self._healthy = False
        self._last_health_check = 0
        
        # Start the secret watchers for critical paths
        asyncio.create_task(self._initialize_watchers())
    
    async def _initialize_watchers(self) -> None:
        """Initialize secret watchers for critical configuration paths."""
        try:
            # Wait a bit to ensure other services are initialized
            await asyncio.sleep(5)
            
            # Start watchers for critical paths
            await self.watch_secret(VAULT_CONFIG_PATH)
            await self.watch_secret(VAULT_API_KEYS_PATH)
            await self.watch_secret(VAULT_CREDENTIALS_PATH)
            
            # Do an initial health check
            await self.health_check()
        except Exception as e:
            logger.error(f"Failed to initialize secret watchers: {e}")

    async def _get_token(self) -> str:
        """Get the Vault token.

        Returns:
            The Vault token.

        Raises:
            ValueError: If no token is available.
            ServiceUnavailableError: If Vault is unavailable.
        """
        try:
            # Return cached token if available and not expired
            current_time = time.time()
            if self._token and current_time < self._token_expiry:
                return self._token

            # Try to use provided token
            if self._vault_token:
                self._token = self._vault_token
                self._token_expiry = current_time + 3600  # Assume 1 hour validity
                return self._token

            # Try to read token from file (Vault Agent injected token)
            try:
                if os.path.exists(VAULT_TOKEN_FILE):
                    async with aiofiles.open(VAULT_TOKEN_FILE, "r") as f:
                        token = (await f.read()).strip()
                        # Check if token is valid
                        try:
                            await self._validate_token(token)
                            self._token = token
                            self._token_expiry = current_time + 3600  # Assume 1 hour validity
                            return self._token
                        except Exception as e:
                            logger.warning(f"Invalid token in file {VAULT_TOKEN_FILE}: {str(e)}")
            except Exception as e:
                logger.warning(f"Failed to read token from file {VAULT_TOKEN_FILE}: {str(e)}")

            # Try to authenticate using Kubernetes auth method
            try:
                # Read service account token
                async with aiofiles.open("/var/run/secrets/kubernetes.io/serviceaccount/token", "r") as f:
                    jwt_token = (await f.read()).strip()

                # Authenticate to Vault
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        f"{self.vault_addr}/v1/auth/kubernetes/login",
                        json={"jwt": jwt_token, "role": VAULT_ROLE}
                    )
                    response.raise_for_status()

                    auth_data = response.json()
                    self._token = auth_data["auth"]["client_token"]
                    # Get token TTL and set expiry (with 10% buffer)
                    ttl = auth_data["auth"].get("lease_duration", 3600)
                    self._token_expiry = current_time + (ttl * 0.9)
                    return self._token
            except Exception as e:
                logger.warning(f"Failed to authenticate to Vault using Kubernetes: {str(e)}")

            # Try to authenticate using AppRole if available
            try:
                role_id_file = os.getenv("VAULT_ROLE_ID_FILE")
                secret_id_file = os.getenv("VAULT_SECRET_ID_FILE")
                
                if role_id_file and secret_id_file and os.path.exists(role_id_file) and os.path.exists(secret_id_file):
                    async with aiofiles.open(role_id_file, "r") as f:
                        role_id = (await f.read()).strip()
                    
                    async with aiofiles.open(secret_id_file, "r") as f:
                        secret_id = (await f.read()).strip()
                    
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.post(
                            f"{self.vault_addr}/v1/auth/approle/login",
                            json={"role_id": role_id, "secret_id": secret_id}
                        )
                        response.raise_for_status()
                        
                        auth_data = response.json()
                        self._token = auth_data["auth"]["client_token"]
                        # Get token TTL and set expiry (with 10% buffer)
                        ttl = auth_data["auth"].get("lease_duration", 3600)
                        self._token_expiry = current_time + (ttl * 0.9)
                        return self._token
            except Exception as e:
                logger.warning(f"Failed to authenticate to Vault using AppRole: {str(e)}")

            # No token available
            raise ConfigurationError("No Vault token available. Set VAULT_TOKEN env var or mount token file.")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error while getting Vault token: {e}")
            raise ServiceUnavailableError(f"Failed to connect to Vault: {str(e)}")
        except Exception as e:
            logger.error(f"Error while getting Vault token: {e}")
            raise ConfigurationError(f"Error retrieving Vault token: {str(e)}")

    async def _validate_token(self, token: str) -> bool:
        """Validate a Vault token.

        Args:
            token: The token to validate.

        Returns:
            True if the token is valid, False otherwise.

        Raises:
            httpx.HTTPError: If the request fails.
        """
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{self.vault_addr}/v1/auth/token/lookup-self",
                headers={"X-Vault-Token": token}
            )
            response.raise_for_status()
            return True

    async def health_check(self) -> bool:
        """Check if Vault is healthy.

        Returns:
            True if Vault is healthy, False otherwise.
        """
        current_time = time.time()
        # Only check health every 30 seconds
        if current_time - self._last_health_check < 30:
            return self._healthy
        
        try:
            self._last_health_check = current_time
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.vault_addr}/v1/sys/health"
                )
                response.raise_for_status()
                health_data = response.json()
                
                # Check if Vault is initialized, unsealed, and standby status is acceptable
                if health_data.get("initialized") and not health_data.get("sealed"):
                    self._healthy = True
                    return True
                    
                self._healthy = False
                return False
        except Exception as e:
            logger.warning(f"Vault health check failed: {e}")
            self._healthy = False
            return False

    async def _invalidate_cache(self, path: str) -> None:
        """Invalidate cache for a specific path.

        Args:
            path: The path to invalidate.
        """
        if path in self._secret_cache:
            del self._secret_cache[path]
            logger.debug(f"Invalidated cache for {path}")

    async def list_secrets(self, path: str) -> List[str]:
        """List secrets at a path.

        Args:
            path: The path to list secrets at.

        Returns:
            A list of secret names.

        Raises:
            ServiceUnavailableError: If Vault is unavailable.
            ConfigurationError: If the request fails due to configuration.
        """
        try:
            token = await self._get_token()

            # Ensure path is properly formatted (remove leading/trailing slashes)
            path = path.strip("/")

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.vault_addr}/v1/{path}",
                    headers={"X-Vault-Token": token},
                    params={"list": "true"}
                )
                response.raise_for_status()

                data = response.json()
                return data.get("data", {}).get("keys", [])
        except httpx.HTTPError as e:
            if e.response and e.response.status_code == 404:
                return []  # Path doesn't exist, return empty list
            logger.error(f"HTTP error while listing secrets at {path}: {e}")
            raise ServiceUnavailableError(f"Failed to connect to Vault: {str(e)}")
        except ConfigurationError:
            raise  # Re-raise configuration errors
        except Exception as e:
            logger.error(f"Error while listing secrets at {path}: {e}")
            raise ConfigurationError(f"Error listing secrets: {str(e)}")

    async def get_secret(self, path: str, use_cache: bool = True) -> Dict[str, Any]:
        """Get a secret.

        Args:
            path: The path to the secret.
            use_cache: Whether to use the cache. Defaults to True.

        Returns:
            The secret data.

        Raises:
            ServiceUnavailableError: If Vault is unavailable.
            ConfigurationError: If the request fails due to configuration.
        """
        try:
            # Check cache if enabled
            current_time = time.time()
            if use_cache and path in self._secret_cache:
                secret_data, expiry = self._secret_cache[path]
                if current_time < expiry:
                    return secret_data
            
            token = await self._get_token()

            # Ensure path is properly formatted (remove leading/trailing slashes)
            path = path.strip("/")

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.vault_addr}/v1/{path}",
                    headers={"X-Vault-Token": token}
                )
                response.raise_for_status()

                data = response.json()
                secret_data = data.get("data", {})
                
                # For KV-V2 secrets, data is nested under data
                if "data" in secret_data:
                    secret_data = secret_data.get("data", {})
                
                # Update cache with the fetched data
                if use_cache:
                    self._secret_cache[path] = (secret_data, current_time + SECRET_CACHE_TTL)
                
                return secret_data
        except httpx.HTTPError as e:
            if e.response and e.response.status_code == 404:
                return {}  # Secret doesn't exist, return empty dict
            logger.error(f"HTTP error while getting secret at {path}: {e}")
            raise ServiceUnavailableError(f"Failed to connect to Vault: {str(e)}")
        except ConfigurationError:
            raise  # Re-raise configuration errors
        except Exception as e:
            logger.error(f"Error while getting secret at {path}: {e}")
            raise ConfigurationError(f"Error retrieving secret: {str(e)}")

    async def create_or_update_secret(self, path: str, data: Dict[str, Any]) -> None:
        """Create or update a secret.

        Args:
            path: The path to the secret.
            data: The secret data.

        Raises:
            ServiceUnavailableError: If Vault is unavailable.
            ConfigurationError: If the request fails due to configuration.
        """
        try:
            token = await self._get_token()

            # Ensure path is properly formatted (remove leading/trailing slashes)
            path = path.strip("/")
            
            # Determine if this is a KV-V2 secret path
            is_kv_v2 = "/data/" in path
            
            # Prepare the request data based on secret engine version
            request_data = {"data": data} if is_kv_v2 else data

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.vault_addr}/v1/{path}",
                    headers={"X-Vault-Token": token},
                    json=request_data
                )
                response.raise_for_status()
            
            # Invalidate the cache for this path
            await self._invalidate_cache(path)
            
            # Notify listeners if any
            await self._notify_listeners(path, data)
        except httpx.HTTPError as e:
            logger.error(f"HTTP error while updating secret at {path}: {e}")
            raise ServiceUnavailableError(f"Failed to connect to Vault: {str(e)}")
        except ConfigurationError:
            raise  # Re-raise configuration errors
        except Exception as e:
            logger.error(f"Error while updating secret at {path}: {e}")
            raise ConfigurationError(f"Error updating secret: {str(e)}")

    async def patch_secret(self, path: str, data: Dict[str, Any]) -> None:
        """Patch an existing secret.

        Args:
            path: The path to the secret.
            data: The data to patch.

        Raises:
            ServiceUnavailableError: If Vault is unavailable.
            ConfigurationError: If the request fails due to configuration.
        """
        try:
            # Get current secret data
            current_data = await self.get_secret(path, use_cache=False)
            
            # Merge the current data with the new data
            updated_data = {**current_data, **data}
            
            # Update the secret with the merged data
            await self.create_or_update_secret(path, updated_data)
        except Exception as e:
            logger.error(f"Error while patching secret at {path}: {e}")
            raise

    async def delete_secret(self, path: str) -> None:
        """Delete a secret.

        Args:
            path: The path to the secret.

        Raises:
            ServiceUnavailableError: If Vault is unavailable.
            ConfigurationError: If the request fails due to configuration.
        """
        try:
            token = await self._get_token()

            # Ensure path is properly formatted (remove leading/trailing slashes)
            path = path.strip("/")

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.delete(
                    f"{self.vault_addr}/v1/{path}",
                    headers={"X-Vault-Token": token}
                )
                response.raise_for_status()
            
            # Invalidate the cache for this path
            await self._invalidate_cache(path)
            
            # Notify listeners if any
            await self._notify_listeners(path, {})
        except httpx.HTTPError as e:
            if e.response and e.response.status_code == 404:
                return  # Secret doesn't exist, ignore
            logger.error(f"HTTP error while deleting secret at {path}: {e}")
            raise ServiceUnavailableError(f"Failed to connect to Vault: {str(e)}")
        except ConfigurationError:
            raise  # Re-raise configuration errors
        except Exception as e:
            logger.error(f"Error while deleting secret at {path}: {e}")
            raise ConfigurationError(f"Error deleting secret: {str(e)}")

    async def get_database_credentials(self, database: str) -> Dict[str, str]:
        """Get dynamic database credentials.

        Args:
            database: The name of the database.

        Returns:
            A dictionary with database credentials (username, password).

        Raises:
            ServiceUnavailableError: If Vault is unavailable.
            ConfigurationError: If the request fails due to configuration.
        """
        try:
            token = await self._get_token()

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.vault_addr}/v1/database/creds/{database}",
                    headers={"X-Vault-Token": token}
                )
                response.raise_for_status()

                data = response.json()
                return {
                    "username": data.get("data", {}).get("username"),
                    "password": data.get("data", {}).get("password"),
                    "lease_id": data.get("lease_id"),
                    "lease_duration": data.get("lease_duration"),
                    "renewable": data.get("renewable", False)
                }
        except httpx.HTTPError as e:
            logger.error(f"HTTP error while getting database credentials for {database}: {e}")
            raise ServiceUnavailableError(f"Failed to connect to Vault: {str(e)}")
        except ConfigurationError:
            raise  # Re-raise configuration errors
        except Exception as e:
            logger.error(f"Error while getting database credentials for {database}: {e}")
            raise ConfigurationError(f"Error getting database credentials: {str(e)}")

    async def renew_lease(self, lease_id: str, increment: Optional[int] = None) -> Dict[str, Any]:
        """Renew a lease.

        Args:
            lease_id: The ID of the lease to renew.
            increment: Optional increment in seconds for the lease.

        Returns:
            The renewal information.

        Raises:
            ServiceUnavailableError: If Vault is unavailable.
            ConfigurationError: If the request fails due to configuration.
        """
        try:
            token = await self._get_token()

            request_data = {}
            if increment is not None:
                request_data["increment"] = increment

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.put(
                    f"{self.vault_addr}/v1/sys/leases/renew",
                    headers={"X-Vault-Token": token},
                    json={"lease_id": lease_id, **request_data}
                )
                response.raise_for_status()

                return response.json().get("data", {})
        except httpx.HTTPError as e:
            logger.error(f"HTTP error while renewing lease {lease_id}: {e}")
            raise ServiceUnavailableError(f"Failed to connect to Vault: {str(e)}")
        except ConfigurationError:
            raise  # Re-raise configuration errors
        except Exception as e:
            logger.error(f"Error while renewing lease {lease_id}: {e}")
            raise ConfigurationError(f"Error renewing lease: {str(e)}")

    async def get_service_token(self, service: str, ttl: str = "1h") -> str:
        """Get a service token.

        Args:
            service: The name of the service.
            ttl: The time-to-live for the token (e.g., "1h", "30m").

        Returns:
            The service token.

        Raises:
            ServiceUnavailableError: If Vault is unavailable.
            ConfigurationError: If the request fails due to configuration.
        """
        try:
            token = await self._get_token()

            async with httpx.AsyncClient(timeout=10.0) as client:
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
        except httpx.HTTPError as e:
            logger.error(f"HTTP error while getting service token for {service}: {e}")
            raise ServiceUnavailableError(f"Failed to connect to Vault: {str(e)}")
        except ConfigurationError:
            raise  # Re-raise configuration errors
        except Exception as e:
            logger.error(f"Error while getting service token for {service}: {e}")
            raise ConfigurationError(f"Error getting service token: {str(e)}")

    async def generate_encryption_key(self, key_name: str, key_type: str = "aes256-gcm96") -> Dict[str, Any]:
        """Generate a new encryption key in the transit engine.

        Args:
            key_name: The name of the key.
            key_type: The type of the key.

        Returns:
            The key information.

        Raises:
            ServiceUnavailableError: If Vault is unavailable.
            ConfigurationError: If the request fails due to configuration.
        """
        try:
            token = await self._get_token()

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.vault_addr}/v1/transit/keys/{key_name}",
                    headers={"X-Vault-Token": token},
                    json={"type": key_type}
                )
                response.raise_for_status()

                # Fetch the key info to return
                info_response = await client.get(
                    f"{self.vault_addr}/v1/transit/keys/{key_name}",
                    headers={"X-Vault-Token": token}
                )
                info_response.raise_for_status()

                return info_response.json().get("data", {})
        except httpx.HTTPError as e:
            logger.error(f"HTTP error while generating encryption key {key_name}: {e}")
            raise ServiceUnavailableError(f"Failed to connect to Vault: {str(e)}")
        except ConfigurationError:
            raise  # Re-raise configuration errors
        except Exception as e:
            logger.error(f"Error while generating encryption key {key_name}: {e}")
            raise ConfigurationError(f"Error generating encryption key: {str(e)}")

    async def encrypt_data(self, key_name: str, plaintext: str) -> str:
        """Encrypt data using the transit engine.

        Args:
            key_name: The name of the key.
            plaintext: The plaintext to encrypt.

        Returns:
            The encrypted data (ciphertext).

        Raises:
            ServiceUnavailableError: If Vault is unavailable.
            ConfigurationError: If the request fails due to configuration.
        """
        try:
            token = await self._get_token()

            # Base64 encode the plaintext
            import base64
            encoded_plaintext = base64.b64encode(plaintext.encode()).decode()

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.vault_addr}/v1/transit/encrypt/{key_name}",
                    headers={"X-Vault-Token": token},
                    json={"plaintext": encoded_plaintext}
                )
                response.raise_for_status()

                data = response.json()
                return data.get("data", {}).get("ciphertext")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error while encrypting data with key {key_name}: {e}")
            raise ServiceUnavailableError(f"Failed to connect to Vault: {str(e)}")
        except ConfigurationError:
            raise  # Re-raise configuration errors
        except Exception as e:
            logger.error(f"Error while encrypting data with key {key_name}: {e}")
            raise ConfigurationError(f"Error encrypting data: {str(e)}")

    async def decrypt_data(self, key_name: str, ciphertext: str) -> str:
        """Decrypt data using the transit engine.

        Args:
            key_name: The name of the key.
            ciphertext: The ciphertext to decrypt.

        Returns:
            The decrypted data (plaintext).

        Raises:
            ServiceUnavailableError: If Vault is unavailable.
            ConfigurationError: If the request fails due to configuration.
        """
        try:
            token = await self._get_token()

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.vault_addr}/v1/transit/decrypt/{key_name}",
                    headers={"X-Vault-Token": token},
                    json={"ciphertext": ciphertext}
                )
                response.raise_for_status()

                data = response.json()
                
                # Base64 decode the plaintext
                import base64
                encoded_plaintext = data.get("data", {}).get("plaintext", "")
                plaintext = base64.b64decode(encoded_plaintext).decode()
                
                return plaintext
        except httpx.HTTPError as e:
            logger.error(f"HTTP error while decrypting data with key {key_name}: {e}")
            raise ServiceUnavailableError(f"Failed to connect to Vault: {str(e)}")
        except ConfigurationError:
            raise  # Re-raise configuration errors
        except Exception as e:
            logger.error(f"Error while decrypting data with key {key_name}: {e}")
            raise ConfigurationError(f"Error decrypting data: {str(e)}")

    async def generate_hmac(self, key_name: str, input_data: str, algorithm: str = "sha2-256") -> str:
        """Generate an HMAC using the transit engine.

        Args:
            key_name: The name of the key.
            input_data: The input data.
            algorithm: The HMAC algorithm to use.

        Returns:
            The HMAC signature.

        Raises:
            ServiceUnavailableError: If Vault is unavailable.
            ConfigurationError: If the request fails due to configuration.
        """
        try:
            token = await self._get_token()

            # Base64 encode the input data
            import base64
            encoded_input = base64.b64encode(input_data.encode()).decode()

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.vault_addr}/v1/transit/hmac/{key_name}/{algorithm}",
                    headers={"X-Vault-Token": token},
                    json={"input": encoded_input}
                )
                response.raise_for_status()

                data = response.json()
                return data.get("data", {}).get("hmac")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error while generating HMAC with key {key_name}: {e}")
            raise ServiceUnavailableError(f"Failed to connect to Vault: {str(e)}")
        except ConfigurationError:
            raise  # Re-raise configuration errors
        except Exception as e:
            logger.error(f"Error while generating HMAC with key {key_name}: {e}")
            raise ConfigurationError(f"Error generating HMAC: {str(e)}")

    async def rotate_key(self, key_name: str) -> bool:
        """Rotate a key in the transit engine.

        Args:
            key_name: The name of the key to rotate.

        Returns:
            True if the key was rotated successfully, False otherwise.

        Raises:
            ServiceUnavailableError: If Vault is unavailable.
            ConfigurationError: If the request fails due to configuration.
        """
        try:
            token = await self._get_token()

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.vault_addr}/v1/transit/keys/{key_name}/rotate",
                    headers={"X-Vault-Token": token}
                )
                response.raise_for_status()
                return True
        except httpx.HTTPError as e:
            logger.error(f"HTTP error while rotating key {key_name}: {e}")
            raise ServiceUnavailableError(f"Failed to connect to Vault: {str(e)}")
        except ConfigurationError:
            raise  # Re-raise configuration errors
        except Exception as e:
            logger.error(f"Error while rotating key {key_name}: {e}")
            raise ConfigurationError(f"Error rotating key: {str(e)}")

    async def register_secret_listener(self, path: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Register a callback for when a secret changes.

        Args:
            path: The path to the secret.
            callback: The callback function to call when the secret changes.
        """
        # Ensure path is properly formatted (remove leading/trailing slashes)
        path = path.strip("/")
        
        if path not in self._secret_listeners:
            self._secret_listeners[path] = []
        
        self._secret_listeners[path].append(callback)
        logger.debug(f"Registered listener for secret {path}")

    async def _notify_listeners(self, path: str, data: Dict[str, Any]) -> None:
        """Notify all listeners that a secret has changed.

        Args:
            path: The path to the secret.
            data: The new secret data.
        """
        # Ensure path is properly formatted (remove leading/trailing slashes)
        path = path.strip("/")
        
        listeners = self._secret_listeners.get(path, [])
        for listener in listeners:
            try:
                listener(data)
            except Exception as e:
                logger.error(f"Error in secret listener for {path}: {e}")

    async def watch_secret(self, path: str, interval_seconds: int = 60) -> None:
        """Watch a secret for changes and notify listeners.

        Args:
            path: The path to the secret.
            interval_seconds: How often to check for changes (in seconds).
        
        Note:
            This creates a background task that runs indefinitely, checking
            for changes to the secret at the specified interval.
        """
        # Ensure path is properly formatted (remove leading/trailing slashes)
        path = path.strip("/")
        
        # Cancel existing watcher if there is one
        if path in self._secret_watchers:
            self._secret_watchers[path].cancel()
            try:
                await self._secret_watchers[path]
            except asyncio.CancelledError:
                pass
        
        # Create a new watcher task
        self._secret_watchers[path] = asyncio.create_task(
            self._watch_secret_task(path, interval_seconds)
        )
        logger.debug(f"Started watcher for secret {path}")

    async def _watch_secret_task(self, path: str, interval_seconds: int) -> None:
        """Background task to watch a secret for changes.

        Args:
            path: The path to the secret.
            interval_seconds: How often to check for changes (in seconds).
        """
        # Keep track of the last hash of the secret
        last_hash = None
        
        try:
            # Initial fetch to get the current value
            try:
                secret_data = await self.get_secret(path, use_cache=False)
                last_hash = self._hash_secret(secret_data)
            except Exception as e:
                logger.warning(f"Failed to get initial value for secret {path}: {e}")
            
            # Watch loop
            while True:
                await asyncio.sleep(interval_seconds)
                
                try:
                    # Fetch the secret
                    secret_data = await self.get_secret(path, use_cache=False)
                    
                    # Hash the secret data
                    current_hash = self._hash_secret(secret_data)
                    
                    # Check if the hash has changed
                    if current_hash != last_hash:
                        logger.info(f"Secret {path} has changed, notifying listeners")
                        last_hash = current_hash
                        
                        # Update the cache
                        current_time = time.time()
                        self._secret_cache[path] = (secret_data, current_time + SECRET_CACHE_TTL)
                        
                        # Notify listeners
                        await self._notify_listeners(path, secret_data)
                except Exception as e:
                    logger.warning(f"Failed to check for changes to secret {path}: {e}")
        except asyncio.CancelledError:
            logger.debug(f"Watcher for secret {path} was cancelled")
        except Exception as e:
            logger.error(f"Watcher for secret {path} encountered an error: {e}")

    def _hash_secret(self, secret_data: Dict[str, Any]) -> str:
        """Generate a hash for a secret to detect changes.

        Args:
            secret_data: The secret data to hash.

        Returns:
            A hash of the secret data.
        """
        # Convert to sorted, stable JSON representation
        json_str = json.dumps(secret_data, sort_keys=True)
        # Generate a hash
        return hashlib.sha256(json_str.encode()).hexdigest()

    async def get_config(self) -> Dict[str, Any]:
        """Get the application configuration from Vault.

        Returns:
            The application configuration.

        Raises:
            ServiceUnavailableError: If Vault is unavailable.
            ConfigurationError: If the request fails due to configuration.
        """
        return await self.get_secret(VAULT_CONFIG_PATH)

    async def get_api_keys(self) -> Dict[str, Any]:
        """Get the API keys from Vault.

        Returns:
            The API keys.

        Raises:
            ServiceUnavailableError: If Vault is unavailable.
            ConfigurationError: If the request fails due to configuration.
        """
        return await self.get_secret(VAULT_API_KEYS_PATH)

    async def get_credentials(self, service: str = None) -> Dict[str, Any]:
        """Get credentials for a specific service from Vault.

        Args:
            service: The name of the service. If None, returns all credentials.

        Returns:
            The credentials.

        Raises:
            ServiceUnavailableError: If Vault is unavailable.
            ConfigurationError: If the request fails due to configuration.
        """
        creds = await self.get_secret(VAULT_CREDENTIALS_PATH)
        if service:
            return creds.get(service, {})
        return creds


# Singleton instance for easy import and use
vault_service = VaultService()
