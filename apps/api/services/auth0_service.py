"""Auth0 service for user management and authentication."""
import json
import logging
from typing import Any, Dict, List, Optional

import httpx
from packages.error_handling.python.errors import (
    ServiceUnavailableError, 
    NotFoundError, 
    BadRequestError,
    ConflictError,
    ServerError,
    IntegrationError
)

from config.auth0 import auth0_settings

logger = logging.getLogger(__name__)


class Auth0Service:
    """Service for interacting with Auth0 Management API."""

    def __init__(self):
        """Initialize the Auth0 service."""
        self.domain = auth0_settings.DOMAIN
        self.client_id = auth0_settings.CLIENT_ID
        self.client_secret = auth0_settings.CLIENT_SECRET
        self.audience = f"https://{self.domain}/api/v2/"
        self.token = None
        self.headers = None

    async def _get_management_token(self) -> str:
        """Get a management API token from Auth0.

        Returns:
            The management API token.

        Raises:
            ServiceUnavailableError: If the token cannot be retrieved.
        """
        url = f"https://{self.domain}/oauth/token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "audience": self.audience,
            "grant_type": "client_credentials",
        }
        headers = {"Content-Type": "application/json"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                return response.json().get("access_token")
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get Auth0 management token: {str(e)}")
            raise ServiceUnavailableError(
                message="Failed to authenticate with Auth0",
                provider="auth0",
                details={"status_code": e.response.status_code, "error": str(e)},
                request_id=getattr(e.response, "headers", {}).get("X-Request-ID")
            )
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to Auth0: {str(e)}")
            raise IntegrationError(
                message="Could not connect to Auth0 service",
                provider="auth0",
                details={"error": str(e)},
                status_code=503
            )

    async def _get_headers(self) -> Dict[str, str]:
        """Get the headers for Auth0 Management API requests.

        Returns:
            The headers for Auth0 Management API requests.
        """
        if not self.token:
            self.token = await self._get_management_token()

        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get a user from Auth0.

        Args:
            user_id: The Auth0 user ID.

        Returns:
            The user information.

        Raises:
            NotFoundError: If the user cannot be found.
            IntegrationError: If there is an issue with the Auth0 API.
        """
        headers = await self._get_headers()
        url = f"https://{self.domain}/api/v2/users/{user_id}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get user from Auth0: {str(e)}")
            if e.response.status_code == 404:
                raise NotFoundError(
                    message=f"User not found: {user_id}",
                    provider="auth0",
                    details={"user_id": user_id},
                    request_id=getattr(e.response, "headers", {}).get("X-Request-ID")
                )
            raise IntegrationError(
                message=f"Failed to get user from Auth0: {e.response.status_code}",
                provider="auth0",
                details={"user_id": user_id, "status_code": e.response.status_code},
                status_code=500,
                request_id=getattr(e.response, "headers", {}).get("X-Request-ID")
            )
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to Auth0: {str(e)}")
            raise IntegrationError(
                message="Could not connect to Auth0 service",
                provider="auth0",
                details={"error": str(e), "user_id": user_id},
                status_code=503
            )

    async def get_user_roles(self, user_id: str) -> List[Dict[str, Any]]:
        """Get a user's roles from Auth0.

        Args:
            user_id: The Auth0 user ID.

        Returns:
            The user's roles.

        Raises:
            NotFoundError: If the roles cannot be found.
            IntegrationError: If there is an issue with the Auth0 API.
        """
        headers = await self._get_headers()
        url = f"https://{self.domain}/api/v2/users/{user_id}/roles"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get user roles from Auth0: {str(e)}")
            if e.response.status_code == 404:
                raise NotFoundError(
                    message=f"Roles not found for user: {user_id}",
                    provider="auth0",
                    details={"user_id": user_id},
                    request_id=getattr(e.response, "headers", {}).get("X-Request-ID")
                )
            raise IntegrationError(
                message=f"Failed to get user roles from Auth0: {e.response.status_code}",
                provider="auth0",
                details={"user_id": user_id, "status_code": e.response.status_code},
                status_code=500,
                request_id=getattr(e.response, "headers", {}).get("X-Request-ID")
            )
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to Auth0: {str(e)}")
            raise IntegrationError(
                message="Could not connect to Auth0 service",
                provider="auth0",
                details={"error": str(e), "user_id": user_id},
                status_code=503
            )

    async def assign_roles_to_user(self, user_id: str, role_ids: List[str]) -> bool:
        """Assign roles to a user in Auth0.

        Args:
            user_id: The Auth0 user ID.
            role_ids: The role IDs to assign.

        Returns:
            True if the roles were assigned successfully.

        Raises:
            BadRequestError: If the roles cannot be assigned.
            IntegrationError: If there is an issue with the Auth0 API.
        """
        headers = await self._get_headers()
        url = f"https://{self.domain}/api/v2/users/{user_id}/roles"
        payload = {"roles": role_ids}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                return True
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to assign roles to user in Auth0: {str(e)}")
            raise BadRequestError(
                message=f"Failed to assign roles to user: {user_id}",
                provider="auth0",
                details={"user_id": user_id, "role_ids": role_ids, "status_code": e.response.status_code},
                request_id=getattr(e.response, "headers", {}).get("X-Request-ID")
            )
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to Auth0: {str(e)}")
            raise IntegrationError(
                message="Could not connect to Auth0 service",
                provider="auth0",
                details={"error": str(e), "user_id": user_id, "role_ids": role_ids},
                status_code=503
            )

    async def remove_roles_from_user(self, user_id: str, role_ids: List[str]) -> bool:
        """Remove roles from a user in Auth0.

        Args:
            user_id: The Auth0 user ID.
            role_ids: The role IDs to remove.

        Returns:
            True if the roles were removed successfully.

        Raises:
            BadRequestError: If the roles cannot be removed.
            IntegrationError: If there is an issue with the Auth0 API.
        """
        headers = await self._get_headers()
        url = f"https://{self.domain}/api/v2/users/{user_id}/roles"
        payload = {"roles": role_ids}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(url, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                return True
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to remove roles from user in Auth0: {str(e)}")
            raise BadRequestError(
                message=f"Failed to remove roles from user: {user_id}",
                provider="auth0",
                details={"user_id": user_id, "role_ids": role_ids, "status_code": e.response.status_code},
                request_id=getattr(e.response, "headers", {}).get("X-Request-ID")
            )
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to Auth0: {str(e)}")
            raise IntegrationError(
                message="Could not connect to Auth0 service",
                provider="auth0",
                details={"error": str(e), "user_id": user_id, "role_ids": role_ids},
                status_code=503
            )

    async def get_roles(self) -> List[Dict[str, Any]]:
        """Get all roles from Auth0.

        Returns:
            The roles.

        Raises:
            ServiceUnavailableError: If the roles cannot be retrieved.
        """
        headers = await self._get_headers()
        url = f"https://{self.domain}/api/v2/roles"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get roles from Auth0: {str(e)}")
            raise ServiceUnavailableError(
                message="Failed to get roles from Auth0",
                provider="auth0",
                details={"status_code": e.response.status_code, "error": str(e)},
                request_id=getattr(e.response, "headers", {}).get("X-Request-ID")
            )
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to Auth0: {str(e)}")
            raise IntegrationError(
                message="Could not connect to Auth0 service",
                provider="auth0",
                details={"error": str(e)},
                status_code=503
            )

    async def create_role(self, name: str, description: str) -> Dict[str, Any]:
        """Create a role in Auth0.

        Args:
            name: The role name.
            description: The role description.

        Returns:
            The created role.

        Raises:
            BadRequestError: If the role cannot be created.
        """
        headers = await self._get_headers()
        url = f"https://{self.domain}/api/v2/roles"
        payload = {
            "name": name,
            "description": description,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to create role in Auth0: {str(e)}")
            raise BadRequestError(
                message=f"Failed to create role: {name}",
                provider="auth0",
                details={"name": name, "description": description, "status_code": e.response.status_code},
                request_id=getattr(e.response, "headers", {}).get("X-Request-ID")
            )
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to Auth0: {str(e)}")
            raise IntegrationError(
                message="Could not connect to Auth0 service",
                provider="auth0",
                details={"error": str(e), "name": name},
                status_code=503
            )

    async def enable_mfa_for_user(self, user_id: str) -> bool:
        """Enable MFA for a user in Auth0.

        Args:
            user_id: The Auth0 user ID.

        Returns:
            True if MFA was enabled successfully.

        Raises:
            BadRequestError: If MFA cannot be enabled.
        """
        headers = await self._get_headers()
        url = f"https://{self.domain}/api/v2/users/{user_id}"
        payload = {
            "user_metadata": {
                "mfa_enabled": True,
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(url, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                return True
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to enable MFA for user in Auth0: {str(e)}")
            raise BadRequestError(
                message=f"Failed to enable MFA for user: {user_id}",
                provider="auth0",
                details={"user_id": user_id, "status_code": e.response.status_code},
                request_id=getattr(e.response, "headers", {}).get("X-Request-ID")
            )
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to Auth0: {str(e)}")
            raise IntegrationError(
                message="Could not connect to Auth0 service",
                provider="auth0",
                details={"error": str(e), "user_id": user_id},
                status_code=503
            )

    async def get_users_with_role(self, role_id: str) -> List[Dict[str, Any]]:
        """Get all users with a specific role from Auth0.

        Args:
            role_id: The role ID.

        Returns:
            The users with the role.

        Raises:
            NotFoundError: If the users cannot be retrieved.
        """
        headers = await self._get_headers()
        url = f"https://{self.domain}/api/v2/roles/{role_id}/users"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get users with role from Auth0: {str(e)}")
            if e.response.status_code == 404:
                raise NotFoundError(
                    message=f"Users not found for role: {role_id}",
                    provider="auth0",
                    details={"role_id": role_id},
                    request_id=getattr(e.response, "headers", {}).get("X-Request-ID")
                )
            raise IntegrationError(
                message=f"Failed to get users with role from Auth0: {e.response.status_code}",
                provider="auth0",
                details={"role_id": role_id, "status_code": e.response.status_code},
                status_code=500,
                request_id=getattr(e.response, "headers", {}).get("X-Request-ID")
            )
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to Auth0: {str(e)}")
            raise IntegrationError(
                message="Could not connect to Auth0 service",
                provider="auth0",
                details={"error": str(e), "role_id": role_id},
                status_code=503
            )
            
    async def create_user(self, email: str, password: str, name: Optional[str] = None) -> Dict[str, Any]:
        """Create a new user in Auth0.

        Args:
            email: The user's email.
            password: The user's password.
            name: The user's name (optional).

        Returns:
            The created user information.

        Raises:
            BadRequestError: If the user cannot be created.
            ConflictError: If a user with this email already exists.
        """
        headers = await self._get_headers()
        url = f"https://{self.domain}/api/v2/users"
        
        payload = {
            "email": email,
            "password": password,
            "connection": "Username-Password-Authentication",
            "email_verified": False,
        }
        
        if name:
            payload["name"] = name
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to create user in Auth0: {str(e)}")
            
            # Check if it's a duplicate user error
            if e.response.status_code == 409:
                raise ConflictError(
                    message="A user with this email already exists",
                    provider="auth0",
                    details={"email": email},
                    request_id=getattr(e.response, "headers", {}).get("X-Request-ID")
                )
                
            # Check for validation errors
            if e.response.status_code == 400:
                try:
                    error_details = e.response.json()
                    if "message" in error_details:
                        raise BadRequestError(
                            message=error_details["message"],
                            provider="auth0",
                            details={"email": email},
                            request_id=getattr(e.response, "headers", {}).get("X-Request-ID")
                        )
                except (ValueError, KeyError):
                    pass
                    
            raise BadRequestError(
                message="Failed to create user",
                provider="auth0",
                details={"email": email, "status_code": e.response.status_code},
                request_id=getattr(e.response, "headers", {}).get("X-Request-ID")
            )
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to Auth0: {str(e)}")
            raise IntegrationError(
                message="Could not connect to Auth0 service",
                provider="auth0",
                details={"error": str(e), "email": email},
                status_code=503
            )
            
    async def send_password_reset_email(self, email: str) -> bool:
        """Send a password reset email to a user.

        Args:
            email: The user's email.

        Returns:
            True if the email was sent successfully.

        Raises:
            ServerError: If the email cannot be sent.
        """
        url = f"https://{self.domain}/dbconnections/change_password"
        
        payload = {
            "client_id": self.client_id,
            "email": email,
            "connection": "Username-Password-Authentication",
        }
        
        headers = {"Content-Type": "application/json"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                return True
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to send password reset email: {str(e)}")
            
            # Don't expose whether the email exists or not for security reasons
            # Just return success even if the email doesn't exist
            if e.response.status_code == 404:
                return True
                
            raise ServerError(
                message="Failed to send password reset email",
                provider="auth0",
                details={"email": email, "status_code": e.response.status_code},
                request_id=getattr(e.response, "headers", {}).get("X-Request-ID")
            )
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to Auth0: {str(e)}")
            raise IntegrationError(
                message="Could not connect to Auth0 service",
                provider="auth0",
                details={"error": str(e), "email": email},
                status_code=503
            )
            
    async def verify_email(self, user_id: str) -> bool:
        """Send an email verification email to a user.

        Args:
            user_id: The Auth0 user ID.

        Returns:
            True if the email was sent successfully.

        Raises:
            ServerError: If the email cannot be sent.
        """
        headers = await self._get_headers()
        url = f"https://{self.domain}/api/v2/jobs/verification-email"
        
        payload = {
            "user_id": user_id,
            "client_id": self.client_id,
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                return True
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to send verification email: {str(e)}")
            raise ServerError(
                message="Failed to send verification email",
                provider="auth0",
                details={"user_id": user_id, "status_code": e.response.status_code},
                request_id=getattr(e.response, "headers", {}).get("X-Request-ID")
            )
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to Auth0: {str(e)}")
            raise IntegrationError(
                message="Could not connect to Auth0 service",
                provider="auth0",
                details={"error": str(e), "user_id": user_id},
                status_code=503
            )
            
    async def list_users(self, page: int = 0, per_page: int = 100) -> List[Dict[str, Any]]:
        """List all users from Auth0.

        Args:
            page: The page number (0-based).
            per_page: The number of users per page.

        Returns:
            The users.

        Raises:
            ServiceUnavailableError: If the users cannot be retrieved.
        """
        headers = await self._get_headers()
        url = f"https://{self.domain}/api/v2/users"
        
        params = {
            "page": page,
            "per_page": per_page,
            "include_totals": True,
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=headers, timeout=10)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to list users from Auth0: {str(e)}")
            raise ServiceUnavailableError(
                message="Failed to list users from Auth0",
                provider="auth0",
                details={"status_code": e.response.status_code, "error": str(e)},
                request_id=getattr(e.response, "headers", {}).get("X-Request-ID")
            )
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to Auth0: {str(e)}")
            raise IntegrationError(
                message="Could not connect to Auth0 service",
                provider="auth0",
                details={"error": str(e), "page": page, "per_page": per_page},
                status_code=503
            )


# Create a singleton instance
auth0_service = Auth0Service()