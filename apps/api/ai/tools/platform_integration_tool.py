"""Platform integration tool for OctoTools."""

import logging
import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, List, Optional

from octotools import ToolCard

from ai.config import PLATFORM_INTEGRATION_TOOL_CONFIG

logger = logging.getLogger(__name__)

class PlatformIntegrationTool(ToolCard):
    """Tool for integrating with external platforms."""

    def __init__(self):
        """Initialize the platform integration tool."""
        super().__init__(
            tool_name="Platform_Integration_Tool",
            tool_description="A tool that interacts with connected platforms to retrieve data and perform actions.",
            input_types={
                "platform": "str - The platform to interact with (e.g., 'linkedin', 'twitter')",
                "action": "str - The action to perform (e.g., 'get_contacts', 'get_company_info')",
                "parameters": "dict - Additional parameters for the action"
            },
            output_type="dict - Contains the result of the platform interaction",
            demo_commands=[
                {
                    "command": 'execution = tool.execute(platform="linkedin", action="get_contacts", parameters={"limit": 10})',
                    "description": "Get 10 contacts from LinkedIn"
                }
            ],
            user_metadata={
                "limitations": [
                    "Requires prior connection and authentication with the platform",
                    "Subject to rate limits and quotas of the platform",
                    "Some platforms may restrict data access"
                ],
                "best_practices": [
                    "Use specific parameters to limit data retrieval to what's needed",
                    "Cache results when appropriate to avoid excessive API calls",
                    "Handle platform errors gracefully with appropriate fallbacks"
                ]
            }
        )

        # Initialize configuration
        self.config = PLATFORM_INTEGRATION_TOOL_CONFIG

        # Initialize cache
        self.cache = {}
        self.cache_timestamps = {}

    async def execute(
        self,
        platform: str,
        action: str,
        parameters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Interact with a connected platform.

        Args:
            platform: The platform to interact with
            action: The action to perform
            parameters: Additional parameters for the action

        Returns:
            Dictionary containing the result of the interaction
        """
        logger.info(f"Executing platform integration: {platform}/{action}")

        parameters = parameters or {}

        try:
            # Validate inputs
            self._validate_inputs(platform, action, parameters)

            # Check if platform is connected
            if not await self._is_platform_connected(platform):
                return {
                    "error": f"Platform {platform} is not connected",
                    "status": "error",
                    "data": None
                }

            # Check cache if applicable
            cache_key = self._get_cache_key(platform, action, parameters)
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                logger.info(f"Using cached result for {platform}/{action}")
                return cached_result

            # Route the action to the appropriate handler
            if action == "get_contacts":
                result = await self._get_platform_contacts(platform, parameters)
            elif action == "get_company_info":
                result = await self._get_company_info(platform, parameters)
            elif action == "search_profiles":
                result = await self._search_profiles(platform, parameters)
            elif action == "get_message_history":
                result = await self._get_message_history(platform, parameters)
            elif action == "send_message":
                result = await self._send_message(platform, parameters)
            elif action == "create_campaign":
                result = await self._create_campaign(platform, parameters)
            elif action == "get_analytics":
                result = await self._get_analytics(platform, parameters)
            else:
                return {
                    "error": f"Unsupported action: {action}",
                    "status": "error",
                    "data": None
                }

            # Cache the result if applicable
            if self._is_cacheable(action):
                self._add_to_cache(cache_key, result)

            return result
        except Exception as e:
            logger.error(f"Platform integration failed: {str(e)}")
            return {
                "error": str(e),
                "status": "error",
                "data": None,
                "platform": platform,
                "action": action
            }

    def _validate_inputs(self, platform, action, parameters):
        """Validate input parameters."""
        if platform not in self.config["supported_platforms"]:
            raise ValueError(f"Platform must be one of: {', '.join(self.config['supported_platforms'])}")

        valid_actions = [
            "get_contacts", "get_company_info", "search_profiles", "get_message_history",
            "send_message", "create_campaign", "get_analytics"
        ]
        if action not in valid_actions:
            raise ValueError(f"Action must be one of: {', '.join(valid_actions)}")

        # Validate action-specific parameters
        if action == "get_contacts" and "limit" in parameters:
            limit = parameters["limit"]
            if not isinstance(limit, int) or limit <= 0 or limit > self.config["max_batch_size"]:
                raise ValueError(f"Limit must be a positive integer not exceeding {self.config['max_batch_size']}")

        if action == "search_profiles" and "query" not in parameters:
            raise ValueError("Query parameter is required for search_profiles action")

        if action == "send_message" and ("recipient" not in parameters or "content" not in parameters):
            raise ValueError("Recipient and content parameters are required for send_message action")

    async def _is_platform_connected(self, platform):
        """Check if the platform is connected."""
        # In a real implementation, this would check against a database
        # For now, we'll simulate that LinkedIn and Gmail are connected
        return platform in ["linkedin", "gmail"]

    def _get_cache_key(self, platform, action, parameters):
        """Generate a cache key for the request."""
        # Create a deterministic string representation of parameters
        param_str = json.dumps(parameters, sort_keys=True) if parameters else "{}"
        return f"{platform}:{action}:{param_str}"

    def _get_from_cache(self, cache_key):
        """Get a result from the cache if it exists and is not expired."""
        if cache_key in self.cache and cache_key in self.cache_timestamps:
            # Check if the cache entry is expired
            timestamp = self.cache_timestamps[cache_key]
            if time.time() - timestamp < self.config["cache_ttl"]:
                return self.cache[cache_key]

        return None

    def _add_to_cache(self, cache_key, result):
        """Add a result to the cache."""
        self.cache[cache_key] = result
        self.cache_timestamps[cache_key] = time.time()

    def _is_cacheable(self, action):
        """Determine if an action's result should be cached."""
        # Only cache read operations, not write operations
        return action in ["get_contacts", "get_company_info", "search_profiles", "get_message_history", "get_analytics"]

    async def _get_platform_contacts(self, platform, parameters):
        """Get contacts from the platform."""
        # Simulate API calls to the platform
        await asyncio.sleep(0.8)  # Simulate API call

        limit = parameters.get("limit", 10)

        if platform == "linkedin":
            # Sample LinkedIn contacts
            contacts = [
                {
                    "id": f"linkedin_{i}",
                    "name": f"LinkedIn Contact {i}",
                    "title": "Software Engineer",
                    "company": "Tech Company",
                    "email": f"contact{i}@example.com",
                    "connected_date": "2023-01-15",
                    "location": "San Francisco, CA",
                    "industry": "Technology"
                }
                for i in range(1, min(limit + 1, 20))
            ]

            return {
                "status": "success",
                "data": {
                    "contacts": contacts,
                    "total_count": 150,  # Total available contacts
                    "page": parameters.get("page", 1),
                    "limit": limit
                },
                "platform": platform,
                "action": "get_contacts"
            }
        elif platform == "gmail":
            # Sample Gmail contacts
            contacts = [
                {
                    "id": f"gmail_{i}",
                    "name": f"Gmail Contact {i}",
                    "email": f"gmail{i}@example.com",
                    "last_interaction": "2023-05-20",
                    "interaction_count": 5,
                    "labels": ["Important", "Work"]
                }
                for i in range(1, min(limit + 1, 20))
            ]

            return {
                "status": "success",
                "data": {
                    "contacts": contacts,
                    "total_count": 250,  # Total available contacts
                    "page": parameters.get("page", 1),
                    "limit": limit
                },
                "platform": platform,
                "action": "get_contacts"
            }
        elif platform == "twitter":
            # Sample Twitter contacts
            contacts = [
                {
                    "id": f"twitter_{i}",
                    "username": f"twitter_user_{i}",
                    "name": f"Twitter Contact {i}",
                    "followers_count": 1000 + i * 100,
                    "following": True,
                    "last_interaction": "2023-06-10"
                }
                for i in range(1, min(limit + 1, 20))
            ]

            return {
                "status": "success",
                "data": {
                    "contacts": contacts,
                    "total_count": 180,  # Total available contacts
                    "page": parameters.get("page", 1),
                    "limit": limit
                },
                "platform": platform,
                "action": "get_contacts"
            }
        elif platform == "outlook":
            # Sample Outlook contacts
            contacts = [
                {
                    "id": f"outlook_{i}",
                    "name": f"Outlook Contact {i}",
                    "email": f"outlook{i}@example.com",
                    "job_title": "Product Manager",
                    "company": "Enterprise Corp",
                    "last_email_date": "2023-04-05"
                }
                for i in range(1, min(limit + 1, 20))
            ]

            return {
                "status": "success",
                "data": {
                    "contacts": contacts,
                    "total_count": 200,  # Total available contacts
                    "page": parameters.get("page", 1),
                    "limit": limit
                },
                "platform": platform,
                "action": "get_contacts"
            }
        else:
            return {
                "status": "error",
                "error": f"Unsupported platform: {platform}",
                "data": None,
                "platform": platform,
                "action": "get_contacts"
            }

    async def _get_company_info(self, platform, parameters):
        """Get company information from the platform."""
        # Simulate API calls to the platform
        await asyncio.sleep(0.7)  # Simulate API call

        company_id = parameters.get("company_id")
        company_name = parameters.get("company_name")

        if not company_id and not company_name:
            return {
                "status": "error",
                "error": "Either company_id or company_name is required",
                "data": None,
                "platform": platform,
                "action": "get_company_info"
            }

        if platform == "linkedin":
            # Sample LinkedIn company info
            company_info = {
                "id": company_id or "linkedin_company_123",
                "name": company_name or "Tech Solutions Inc",
                "industry": "Information Technology",
                "size": "1001-5000 employees",
                "founded": 2005,
                "headquarters": "San Francisco, CA",
                "website": "https://techsolutions.example.com",
                "description": "A leading technology solutions provider.",
                "specialties": ["Software Development", "Cloud Computing", "AI"],
                "followers_count": 25000
            }

            return {
                "status": "success",
                "data": {
                    "company": company_info
                },
                "platform": platform,
                "action": "get_company_info"
            }
        else:
            return {
                "status": "error",
                "error": f"Company info not available for platform: {platform}",
                "data": None,
                "platform": platform,
                "action": "get_company_info"
            }

    async def _search_profiles(self, platform, parameters):
        """Search for profiles on the platform."""
        # Simulate API calls to the platform
        await asyncio.sleep(0.9)  # Simulate API call

        query = parameters.get("query", "")
        limit = parameters.get("limit", 10)

        if platform == "linkedin":
            # Sample LinkedIn search results
            profiles = [
                {
                    "id": f"linkedin_profile_{i}",
                    "name": f"LinkedIn Profile {i}",
                    "title": "Software Engineer",
                    "company": "Tech Company",
                    "location": "San Francisco, CA",
                    "connection_degree": 2,
                    "mutual_connections": 5
                }
                for i in range(1, min(limit + 1, 20))
            ]

            return {
                "status": "success",
                "data": {
                    "profiles": profiles,
                    "total_count": 120,  # Total available profiles
                    "query": query,
                    "page": parameters.get("page", 1),
                    "limit": limit
                },
                "platform": platform,
                "action": "search_profiles"
            }
        elif platform == "twitter":
            # Sample Twitter search results
            profiles = [
                {
                    "id": f"twitter_profile_{i}",
                    "username": f"twitter_user_{i}",
                    "name": f"Twitter Profile {i}",
                    "bio": f"Bio for Twitter Profile {i}",
                    "followers_count": 1000 + i * 100,
                    "following_count": 500 + i * 50,
                    "verified": i % 5 == 0  # Every 5th profile is verified
                }
                for i in range(1, min(limit + 1, 20))
            ]

            return {
                "status": "success",
                "data": {
                    "profiles": profiles,
                    "total_count": 150,  # Total available profiles
                    "query": query,
                    "page": parameters.get("page", 1),
                    "limit": limit
                },
                "platform": platform,
                "action": "search_profiles"
            }
        else:
            return {
                "status": "error",
                "error": f"Profile search not available for platform: {platform}",
                "data": None,
                "platform": platform,
                "action": "search_profiles"
            }

    async def _get_message_history(self, platform, parameters):
        """Get message history from the platform."""
        # Simulate API calls to the platform
        await asyncio.sleep(0.6)  # Simulate API call

        contact_id = parameters.get("contact_id")
        limit = parameters.get("limit", 10)

        if not contact_id:
            return {
                "status": "error",
                "error": "contact_id is required",
                "data": None,
                "platform": platform,
                "action": "get_message_history"
            }

        if platform == "linkedin":
            # Sample LinkedIn message history
            messages = [
                {
                    "id": f"linkedin_message_{i}",
                    "sender_id": i % 2 == 0 and "me" or contact_id,  # Alternate between me and contact
                    "content": f"LinkedIn message {i} content",
                    "timestamp": f"2023-06-{20-i:02d}T10:{i:02d}:00Z",
                    "read": True
                }
                for i in range(1, min(limit + 1, 20))
            ]

            return {
                "status": "success",
                "data": {
                    "messages": messages,
                    "total_count": 35,  # Total available messages
                    "contact_id": contact_id,
                    "page": parameters.get("page", 1),
                    "limit": limit
                },
                "platform": platform,
                "action": "get_message_history"
            }
        elif platform == "gmail":
            # Sample Gmail message history
            messages = [
                {
                    "id": f"gmail_message_{i}",
                    "sender": i % 2 == 0 and "me@example.com" or f"contact{contact_id}@example.com",
                    "subject": f"Email subject {i}",
                    "snippet": f"Preview of email content {i}...",
                    "timestamp": f"2023-06-{20-i:02d}T10:{i:02d}:00Z",
                    "has_attachments": i % 3 == 0  # Every 3rd message has attachments
                }
                for i in range(1, min(limit + 1, 20))
            ]

            return {
                "status": "success",
                "data": {
                    "messages": messages,
                    "total_count": 45,  # Total available messages
                    "contact_id": contact_id,
                    "page": parameters.get("page", 1),
                    "limit": limit
                },
                "platform": platform,
                "action": "get_message_history"
            }
        else:
            return {
                "status": "error",
                "error": f"Message history not available for platform: {platform}",
                "data": None,
                "platform": platform,
                "action": "get_message_history"
            }

    async def _send_message(self, platform, parameters):
        """Send a message on the platform."""
        # Simulate API calls to the platform
        await asyncio.sleep(1.0)  # Simulate API call

        recipient = parameters.get("recipient")
        content = parameters.get("content")

        if not recipient or not content:
            return {
                "status": "error",
                "error": "recipient and content are required",
                "data": None,
                "platform": platform,
                "action": "send_message"
            }

        if platform == "linkedin":
            # Sample LinkedIn message send result
            return {
                "status": "success",
                "data": {
                    "message_id": f"linkedin_message_{int(time.time())}",
                    "recipient": recipient,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "status": "sent"
                },
                "platform": platform,
                "action": "send_message"
            }
        elif platform == "gmail":
            # Sample Gmail message send result
            return {
                "status": "success",
                "data": {
                    "message_id": f"gmail_message_{int(time.time())}",
                    "recipient": recipient,
                    "subject": parameters.get("subject", "No Subject"),
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "status": "sent"
                },
                "platform": platform,
                "action": "send_message"
            }
        elif platform == "twitter":
            # Sample Twitter message send result
            return {
                "status": "success",
                "data": {
                    "message_id": f"twitter_message_{int(time.time())}",
                    "recipient": recipient,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "status": "sent"
                },
                "platform": platform,
                "action": "send_message"
            }
        else:
            return {
                "status": "error",
                "error": f"Sending messages not available for platform: {platform}",
                "data": None,
                "platform": platform,
                "action": "send_message"
            }

    async def _create_campaign(self, platform, parameters):
        """Create a campaign on the platform."""
        # Simulate API calls to the platform
        await asyncio.sleep(1.2)  # Simulate API call

        name = parameters.get("name")
        content = parameters.get("content")
        recipients = parameters.get("recipients", [])

        if not name or not content or not recipients:
            return {
                "status": "error",
                "error": "name, content, and recipients are required",
                "data": None,
                "platform": platform,
                "action": "create_campaign"
            }

        if platform == "linkedin":
            # Sample LinkedIn campaign creation result
            return {
                "status": "success",
                "data": {
                    "campaign_id": f"linkedin_campaign_{int(time.time())}",
                    "name": name,
                    "recipient_count": len(recipients),
                    "status": "scheduled",
                    "scheduled_time": parameters.get("scheduled_time", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
                },
                "platform": platform,
                "action": "create_campaign"
            }
        elif platform == "gmail":
            # Sample Gmail campaign creation result
            return {
                "status": "success",
                "data": {
                    "campaign_id": f"gmail_campaign_{int(time.time())}",
                    "name": name,
                    "subject": parameters.get("subject", "No Subject"),
                    "recipient_count": len(recipients),
                    "status": "scheduled",
                    "scheduled_time": parameters.get("scheduled_time", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
                },
                "platform": platform,
                "action": "create_campaign"
            }
        else:
            return {
                "status": "error",
                "error": f"Campaign creation not available for platform: {platform}",
                "data": None,
                "platform": platform,
                "action": "create_campaign"
            }

    async def _get_analytics(self, platform, parameters):
        """Get analytics from the platform."""
        # Simulate API calls to the platform
        await asyncio.sleep(0.8)  # Simulate API call

        metric = parameters.get("metric")
        time_range = parameters.get("time_range", "last_30_days")

        if platform == "linkedin":
            # Sample LinkedIn analytics
            if metric == "profile_views":
                data = {
                    "total_views": 250,
                    "unique_viewers": 180,
                    "view_trend": "+15%",
                    "top_viewer_industries": ["Technology", "Finance", "Healthcare"],
                    "top_viewer_titles": ["CEO", "CTO", "VP of Engineering"]
                }
            elif metric == "post_engagement":
                data = {
                    "total_posts": 12,
                    "total_impressions": 5600,
                    "total_reactions": 320,
                    "total_comments": 45,
                    "total_shares": 28,
                    "engagement_rate": "5.7%",
                    "top_performing_post": {
                        "id": "linkedin_post_123",
                        "impressions": 1200,
                        "reactions": 85
                    }
                }
            else:
                data = {
                    "profile_views": {
                        "total": 250,
                        "trend": "+15%"
                    },
                    "post_engagement": {
                        "total_impressions": 5600,
                        "engagement_rate": "5.7%"
                    },
                    "connection_growth": {
                        "new_connections": 45,
                        "trend": "+8%"
                    }
                }

            return {
                "status": "success",
                "data": data,
                "platform": platform,
                "action": "get_analytics",
                "metric": metric,
                "time_range": time_range
            }
        elif platform == "twitter":
            # Sample Twitter analytics
            if metric == "profile_views":
                data = {
                    "total_views": 1200,
                    "unique_viewers": 950,
                    "view_trend": "+22%"
                }
            elif metric == "tweet_engagement":
                data = {
                    "total_tweets": 28,
                    "total_impressions": 15600,
                    "total_likes": 780,
                    "total_retweets": 210,
                    "total_replies": 95,
                    "engagement_rate": "6.9%",
                    "top_performing_tweet": {
                        "id": "twitter_tweet_456",
                        "impressions": 3200,
                        "likes": 145
                    }
                }
            else:
                data = {
                    "profile_views": {
                        "total": 1200,
                        "trend": "+22%"
                    },
                    "tweet_engagement": {
                        "total_impressions": 15600,
                        "engagement_rate": "6.9%"
                    },
                    "follower_growth": {
                        "new_followers": 85,
                        "trend": "+12%"
                    }
                }

            return {
                "status": "success",
                "data": data,
                "platform": platform,
                "action": "get_analytics",
                "metric": metric,
                "time_range": time_range
            }
        else:
            return {
                "status": "error",
                "error": f"Analytics not available for platform: {platform}",
                "data": None,
                "platform": platform,
                "action": "get_analytics"
            }
