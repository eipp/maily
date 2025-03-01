from typing import Dict, Any, List, Optional
import json
import logging
from fastapi import HTTPException, Depends

from .nango_integration_service import NangoIntegrationService
from .identity_resolution_service import IdentityResolutionService
from ..octotools_integration.octotools_service import OctoToolsService

logger = logging.getLogger(__name__)

class PlatformIntegrationOrchestrator:
    """
    Orchestrates the integration of third-party platforms using Nango and OctoTools.

    This service coordinates the authentication, data synchronization, and tool registration
    processes for integrating external platforms like LinkedIn, Twitter, Gmail, etc.

    By leveraging Nango.dev, this orchestrator is significantly simplified as Nango handles:
    - OAuth flows and token management
    - API access and normalization
    - Data synchronization
    """

    def __init__(
        self,
        octotools_service: OctoToolsService,
        nango_service: NangoIntegrationService,
        identity_resolution_service: Optional[IdentityResolutionService] = None
    ):
        self.octotools_service = octotools_service
        self.nango_service = nango_service
        self.identity_resolution_service = identity_resolution_service or IdentityResolutionService()

        # Map of platform to sync configurations
        # These map to the sync names defined in nango.config.js
        self.platform_sync_configs = {
            "linkedin": {
                "contacts": "linkedin-contacts",
                "companies": "linkedin-companies",
                "posts": "linkedin-posts"
            },
            "twitter": {
                "followers": "twitter-followers",
                "tweets": "twitter-tweets"
            },
            "gmail": {
                "contacts": "gmail-contacts",
                "messages": "gmail-messages"
            },
            "outlook": {
                "contacts": "outlook-contacts",
                "messages": "outlook-messages"
            }
        }

        # Map of platform to tool configurations for OctoTools
        self.platform_tool_configs = {
            "linkedin": [
                {
                    "name": "linkedin_search_people",
                    "description": "Search for people on LinkedIn",
                    "parameters": {
                        "query": "string",
                        "limit": "integer?",
                        "filters": "object?"
                    }
                },
                {
                    "name": "linkedin_send_message",
                    "description": "Send a message to a LinkedIn connection",
                    "parameters": {
                        "connection_id": "string",
                        "message": "string"
                    }
                }
            ],
            "twitter": [
                {
                    "name": "twitter_post_tweet",
                    "description": "Post a tweet",
                    "parameters": {
                        "text": "string",
                        "media_ids": "array?"
                    }
                },
                {
                    "name": "twitter_search",
                    "description": "Search for tweets",
                    "parameters": {
                        "query": "string",
                        "limit": "integer?"
                    }
                }
            ],
            "gmail": [
                {
                    "name": "gmail_send_email",
                    "description": "Send an email via Gmail",
                    "parameters": {
                        "to": "string",
                        "subject": "string",
                        "body": "string",
                        "cc": "string?",
                        "bcc": "string?"
                    }
                },
                {
                    "name": "gmail_search_emails",
                    "description": "Search for emails in Gmail",
                    "parameters": {
                        "query": "string",
                        "limit": "integer?"
                    }
                }
            ],
            "outlook": [
                {
                    "name": "outlook_send_email",
                    "description": "Send an email via Outlook",
                    "parameters": {
                        "to": "string",
                        "subject": "string",
                        "body": "string",
                        "cc": "string?",
                        "bcc": "string?"
                    }
                },
                {
                    "name": "outlook_search_emails",
                    "description": "Search for emails in Outlook",
                    "parameters": {
                        "query": "string",
                        "limit": "integer?"
                    }
                }
            ]
        }

    async def connect_platform(self, user_id: str, platform: str) -> Dict[str, Any]:
        """
        Start the platform connection flow using Nango.

        Args:
            user_id: User ID to connect the platform for
            platform: Platform to connect (e.g., 'linkedin', 'twitter')

        Returns:
            Dict containing the authorization URL and platform
        """
        if platform not in self.platform_sync_configs:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported platform: {platform}"
            )

        connection_id = f"{user_id}-{platform}"
        auth_url = await self.nango_service.get_auth_link(connection_id, user_id, platform)

        return {
            "auth_url": auth_url,
            "platform": platform,
            "connection_id": connection_id
        }

    async def process_nango_callback(self, code: str, state: str) -> Dict[str, Any]:
        """
        Process authentication callback from Nango.

        Args:
            code: Authorization code from the callback
            state: State parameter from the callback

        Returns:
            Dict containing auth result, sync result, and tools registration status
        """
        try:
            # Handle the OAuth callback through Nango
            auth_result = await self.nango_service.handle_callback(code, state)

            # Extract user_id and platform from connection_id
            connection_id = auth_result.get("connection_id")
            if not connection_id or "-" not in connection_id:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid connection ID format"
                )

            connection_parts = connection_id.split("-", 1)
            user_id = connection_parts[0]
            platform = connection_parts[1]

            # Register new tools for this platform with OctoTools
            tools_registered = await self._register_platform_tools(user_id, platform)

            # Trigger initial data syncs through Nango
            sync_results = []
            for sync_type, sync_name in self.platform_sync_configs.get(platform, {}).items():
                try:
                    sync_result = await self.nango_service.trigger_sync(
                        connection_id,
                        platform,
                        sync_name
                    )
                    sync_results.append({
                        "sync_type": sync_type,
                        "sync_name": sync_name,
                        "result": sync_result
                    })
                except Exception as e:
                    logger.error(f"Error triggering sync {sync_name} for {connection_id}: {str(e)}")
                    sync_results.append({
                        "sync_type": sync_type,
                        "sync_name": sync_name,
                        "error": str(e)
                    })

            return {
                "auth_result": auth_result,
                "sync_results": sync_results,
                "tools_registered": tools_registered,
                "user_id": user_id,
                "platform": platform
            }

        except Exception as e:
            logger.error(f"Error processing Nango callback: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing Nango callback: {str(e)}"
            )

    async def _register_platform_tools(self, user_id: str, platform: str) -> bool:
        """
        Register tools for a specific platform with OctoTools.

        Args:
            user_id: User ID to register tools for
            platform: Platform to register tools for

        Returns:
            True if tools were registered successfully, False otherwise
        """
        try:
            tool_configs = self.platform_tool_configs.get(platform, [])

            for tool_config in tool_configs:
                await self.octotools_service.register_tool(
                    user_id=user_id,
                    tool_name=tool_config["name"],
                    description=tool_config["description"],
                    parameters=tool_config["parameters"],
                    platform=platform
                )

            return True
        except Exception as e:
            logger.error(f"Error registering tools for {platform}: {str(e)}")
            return False

    async def list_user_connections(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List all platform connections for a user.

        Args:
            user_id: User ID to list connections for

        Returns:
            List of connection details with sync status
        """
        try:
            # Get connections from Nango
            connections = await self.nango_service.list_connections(user_id)

            # Enhance connection data with sync status
            enhanced_connections = []
            for conn in connections:
                platform = conn.get("provider_config_key")
                connection_id = conn.get("connection_id")

                sync_status = {}
                if platform in self.platform_sync_configs:
                    for sync_type, sync_name in self.platform_sync_configs[platform].items():
                        try:
                            # Get the latest sync record to determine status
                            sync_records = await self.nango_service.get_sync_records(
                                connection_id,
                                platform,
                                sync_name,
                                sync_type,
                                limit=1
                            )

                            if sync_records and "records" in sync_records and sync_records["records"]:
                                sync_status[sync_type] = {
                                    "status": "synced",
                                    "last_synced": sync_records["records"][0].get("created_at")
                                }
                            else:
                                sync_status[sync_type] = {"status": "pending"}
                        except Exception as e:
                            logger.error(f"Error getting sync status for {sync_name}: {str(e)}")
                            sync_status[sync_type] = {"status": "error", "error": str(e)}

                enhanced_connections.append({
                    **conn,
                    "sync_status": sync_status
                })

            return enhanced_connections
        except Exception as e:
            logger.error(f"Error listing connections for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error listing connections: {str(e)}"
            )

    async def disconnect_platform(self, user_id: str, platform: str) -> Dict[str, Any]:
        """
        Disconnect a platform for a user.

        Args:
            user_id: User ID to disconnect the platform for
            platform: Platform to disconnect

        Returns:
            Disconnection result
        """
        try:
            connection_id = f"{user_id}-{platform}"

            # Delete the connection in Nango
            result = await self.nango_service.delete_connection(connection_id, platform)

            # Deregister tools in OctoTools
            tool_configs = self.platform_tool_configs.get(platform, [])
            for tool_config in tool_configs:
                try:
                    await self.octotools_service.deregister_tool(
                        user_id=user_id,
                        tool_name=tool_config["name"]
                    )
                except Exception as e:
                    logger.warning(f"Error deregistering tool {tool_config['name']}: {str(e)}")

            return {
                "success": True,
                "platform": platform,
                "user_id": user_id,
                "connection_id": connection_id,
                "result": result
            }
        except Exception as e:
            logger.error(f"Error disconnecting platform {platform} for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error disconnecting platform: {str(e)}"
            )

    async def trigger_platform_sync(self, user_id: str, platform: str, sync_type: str) -> Dict[str, Any]:
        """
        Trigger a sync for a specific platform and sync type.

        Args:
            user_id: User ID to trigger the sync for
            platform: Platform to trigger the sync for
            sync_type: Type of sync to trigger (e.g., 'contacts', 'messages')

        Returns:
            Sync result
        """
        try:
            if platform not in self.platform_sync_configs:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported platform: {platform}"
                )

            if sync_type not in self.platform_sync_configs[platform]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported sync type for {platform}: {sync_type}"
                )

            connection_id = f"{user_id}-{platform}"
            sync_name = self.platform_sync_configs[platform][sync_type]

            # Trigger the sync through Nango
            result = await self.nango_service.trigger_sync(
                connection_id,
                platform,
                sync_name
            )

            return {
                "success": True,
                "platform": platform,
                "sync_type": sync_type,
                "sync_name": sync_name,
                "user_id": user_id,
                "connection_id": connection_id,
                "result": result
            }
        except Exception as e:
            logger.error(f"Error triggering sync for {platform}/{sync_type} for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error triggering sync: {str(e)}"
            )

    async def get_platform_data(
        self,
        user_id: str,
        platform: str,
        sync_type: str,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get synchronized data for a specific platform and sync type.

        Args:
            user_id: User ID to get data for
            platform: Platform to get data for
            sync_type: Type of data to get (e.g., 'contacts', 'messages')
            limit: Maximum number of records to return
            cursor: Pagination cursor

        Returns:
            Synchronized data with optional identity resolution
        """
        try:
            if platform not in self.platform_sync_configs:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported platform: {platform}"
                )

            if sync_type not in self.platform_sync_configs[platform]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported sync type for {platform}: {sync_type}"
                )

            connection_id = f"{user_id}-{platform}"
            sync_name = self.platform_sync_configs[platform][sync_type]

            # Get the sync records from Nango
            records = await self.nango_service.get_sync_records(
                connection_id,
                platform,
                sync_name,
                sync_type,
                limit=limit,
                cursor=cursor
            )

            # If identity resolution is enabled and this is a contacts sync,
            # perform identity resolution
            if sync_type == "contacts" and self.identity_resolution_service:
                try:
                    if records and "records" in records and records["records"]:
                        resolved_records = await self.identity_resolution_service.resolve_identities(
                            user_id=user_id,
                            platform=platform,
                            contacts=records["records"]
                        )
                        records["records"] = resolved_records
                except Exception as e:
                    logger.error(f"Error resolving identities: {str(e)}")

            return records
        except Exception as e:
            logger.error(f"Error getting data for {platform}/{sync_type} for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error getting platform data: {str(e)}"
            )
