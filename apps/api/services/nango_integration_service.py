from typing import Dict, Any, List, Optional
import os
import json
import logging
import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class NangoIntegrationService:
    """
    Service for integrating with Nango.dev to manage platform connections.

    This service provides methods for authenticating with third-party platforms,
    managing connections, and synchronizing data using Nango.

    Nango.dev significantly simplifies platform integrations by handling:
    - OAuth flows and token management
    - API access and normalization
    - Data synchronization
    """

    def __init__(self):
        self.base_url = os.getenv("NANGO_API_URL", "https://api.nango.dev")
        self.secret_key = os.getenv("NANGO_SECRET_KEY")
        self.public_key = os.getenv("NANGO_PUBLIC_KEY")

        if not self.secret_key or not self.public_key:
            logger.warning("NANGO_SECRET_KEY or NANGO_PUBLIC_KEY environment variables not set")

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.secret_key}" if self.secret_key else "",
                "Content-Type": "application/json"
            }
        )

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def get_auth_link(self, connection_id: str, user_id: str, provider: str) -> str:
        """
        Get an authorization URL for a platform.

        Args:
            connection_id: Unique identifier for the connection
            user_id: User ID to connect the platform for
            provider: Platform provider (e.g., 'linkedin', 'twitter')

        Returns:
            Authorization URL
        """
        try:
            response = await self.client.post(
                "/auth/link",
                json={
                    "connection_id": connection_id,
                    "provider_config_key": provider,
                    "redirect_uri": f"{self.base_url}/oauth/callback",
                    "public_key": self.public_key,
                    "user_id": user_id
                }
            )

            if response.status_code != 200:
                logger.error(f"Error getting auth link: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Error getting auth link: {response.text}"
                )

            data = response.json()
            return data.get("auth_url")
        except Exception as e:
            logger.error(f"Error getting auth link: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error getting auth link: {str(e)}"
            )

    async def handle_callback(self, code: str, state: str) -> Dict[str, Any]:
        """
        Handle the OAuth callback from a platform.

        Args:
            code: Authorization code from the callback
            state: State parameter from the callback

        Returns:
            Connection details
        """
        try:
            response = await self.client.post(
                "/oauth/callback",
                json={
                    "code": code,
                    "state": state
                }
            )

            if response.status_code != 200:
                logger.error(f"Error handling callback: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Error handling callback: {response.text}"
                )

            return response.json()
        except Exception as e:
            logger.error(f"Error handling callback: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error handling callback: {str(e)}"
            )

    async def list_connections(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List all connections for a user.

        Args:
            user_id: User ID to list connections for

        Returns:
            List of connections
        """
        try:
            response = await self.client.get(
                f"/connections?user_id={user_id}"
            )

            if response.status_code != 200:
                logger.error(f"Error listing connections: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Error listing connections: {response.text}"
                )

            data = response.json()
            return data.get("connections", [])
        except Exception as e:
            logger.error(f"Error listing connections: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error listing connections: {str(e)}"
            )

    async def delete_connection(self, connection_id: str, provider: str) -> Dict[str, Any]:
        """
        Delete a connection.

        Args:
            connection_id: Connection ID to delete
            provider: Platform provider

        Returns:
            Deletion result
        """
        try:
            response = await self.client.delete(
                f"/connection/{provider}/{connection_id}"
            )

            if response.status_code != 200:
                logger.error(f"Error deleting connection: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Error deleting connection: {response.text}"
                )

            return response.json()
        except Exception as e:
            logger.error(f"Error deleting connection: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error deleting connection: {str(e)}"
            )

    async def trigger_sync(
        self,
        connection_id: str,
        provider: str,
        sync_name: str
    ) -> Dict[str, Any]:
        """
        Trigger a sync for a connection.

        Args:
            connection_id: Connection ID to sync
            provider: Platform provider
            sync_name: Name of the sync to trigger

        Returns:
            Sync result
        """
        try:
            response = await self.client.post(
                f"/sync/{sync_name}/{provider}/{connection_id}/trigger"
            )

            if response.status_code != 200:
                logger.error(f"Error triggering sync: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Error triggering sync: {response.text}"
                )

            return response.json()
        except Exception as e:
            logger.error(f"Error triggering sync: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error triggering sync: {str(e)}"
            )

    async def get_sync_records(
        self,
        connection_id: str,
        provider: str,
        sync_name: str,
        model_name: str,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get sync records for a connection.

        Args:
            connection_id: Connection ID to get records for
            provider: Platform provider
            sync_name: Name of the sync
            model_name: Name of the model to get records for
            limit: Maximum number of records to return
            cursor: Pagination cursor

        Returns:
            Sync records
        """
        try:
            url = f"/sync/{sync_name}/{provider}/{connection_id}/records/{model_name}?limit={limit}"
            if cursor:
                url += f"&cursor={cursor}"

            response = await self.client.get(url)

            if response.status_code != 200:
                logger.error(f"Error getting sync records: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Error getting sync records: {response.text}"
                )

            return response.json()
        except Exception as e:
            logger.error(f"Error getting sync records: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error getting sync records: {str(e)}"
            )

    async def get_connection(self, connection_id: str, provider: str) -> Dict[str, Any]:
        """
        Get details for a specific connection.

        Args:
            connection_id: Connection ID to get details for
            provider: Platform provider

        Returns:
            Connection details
        """
        try:
            response = await self.client.get(
                f"/connection/{provider}/{connection_id}"
            )

            if response.status_code != 200:
                logger.error(f"Error getting connection: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Error getting connection: {response.text}"
                )

            return response.json()
        except Exception as e:
            logger.error(f"Error getting connection: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error getting connection: {str(e)}"
            )
