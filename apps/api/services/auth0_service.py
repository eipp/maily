"""Auth0 service for user management and authentication."""
import json
import logging
from typing import Any, Dict, List, Optional

import requests
from fastapi import HTTPException, status

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
            HTTPException: If the token cannot be retrieved.
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
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json().get("access_token")
        except requests.RequestException as e:
            logger.error(f"Failed to get Auth0 management token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to authenticate with Auth0",
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
            HTTPException: If the user cannot be retrieved.
        """
        headers = await self._get_headers()
        url = f"https://{self.domain}/api/v2/users/{user_id}"

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get user from Auth0: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_id}",
            )

    async def get_user_roles(self, user_id: str) -> List[Dict[str, Any]]:
        """Get a user's roles from Auth0.

        Args:
            user_id: The Auth0 user ID.

        Returns:
            The user's roles.

        Raises:
            HTTPException: If the roles cannot be retrieved.
        """
        headers = await self._get_headers()
        url = f"https://{self.domain}/api/v2/users/{user_id}/roles"

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get user roles from Auth0: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Roles not found for user: {user_id}",
            )

    async def assign_roles_to_user(self, user_id: str, role_ids: List[str]) -> bool:
        """Assign roles to a user in Auth0.

        Args:
            user_id: The Auth0 user ID.
            role_ids: The role IDs to assign.

        Returns:
            True if the roles were assigned successfully.

        Raises:
            HTTPException: If the roles cannot be assigned.
        """
        headers = await self._get_headers()
        url = f"https://{self.domain}/api/v2/users/{user_id}/roles"
        payload = {"roles": role_ids}

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to assign roles to user in Auth0: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to assign roles to user: {user_id}",
            )

    async def remove_roles_from_user(self, user_id: str, role_ids: List[str]) -> bool:
        """Remove roles from a user in Auth0.

        Args:
            user_id: The Auth0 user ID.
            role_ids: The role IDs to remove.

        Returns:
            True if the roles were removed successfully.

        Raises:
            HTTPException: If the roles cannot be removed.
        """
        headers = await self._get_headers()
        url = f"https://{self.domain}/api/v2/users/{user_id}/roles"
        payload = {"roles": role_ids}

        try:
            response = requests.delete(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to remove roles from user in Auth0: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to remove roles from user: {user_id}",
            )

    async def get_roles(self) -> List[Dict[str, Any]]:
        """Get all roles from Auth0.

        Returns:
            The roles.

        Raises:
            HTTPException: If the roles cannot be retrieved.
        """
        headers = await self._get_headers()
        url = f"https://{self.domain}/api/v2/roles"

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get roles from Auth0: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to get roles from Auth0",
            )

    async def create_role(self, name: str, description: str) -> Dict[str, Any]:
        """Create a role in Auth0.

        Args:
            name: The role name.
            description: The role description.

        Returns:
            The created role.

        Raises:
            HTTPException: If the role cannot be created.
        """
        headers = await self._get_headers()
        url = f"https://{self.domain}/api/v2/roles"
        payload = {
            "name": name,
            "description": description,
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to create role in Auth0: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create role: {name}",
            )

    async def enable_mfa_for_user(self, user_id: str) -> bool:
        """Enable MFA for a user in Auth0.

        Args:
            user_id: The Auth0 user ID.

        Returns:
            True if MFA was enabled successfully.

        Raises:
            HTTPException: If MFA cannot be enabled.
        """
        headers = await self._get_headers()
        url = f"https://{self.domain}/api/v2/users/{user_id}"
        payload = {
            "user_metadata": {
                "mfa_enabled": True,
            }
        }

        try:
            response = requests.patch(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to enable MFA for user in Auth0: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to enable MFA for user: {user_id}",
            )

    async def get_users_with_role(self, role_id: str) -> List[Dict[str, Any]]:
        """Get all users with a specific role from Auth0.

        Args:
            role_id: The role ID.

        Returns:
            The users with the role.

        Raises:
            HTTPException: If the users cannot be retrieved.
        """
        headers = await self._get_headers()
        url = f"https://{self.domain}/api/v2/roles/{role_id}/users"

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get users with role from Auth0: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Users not found for role: {role_id}",
            )


# Create a singleton instance
auth0_service = Auth0Service()
