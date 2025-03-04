"""Helicone integration for API cost tracking."""

import os
import logging
from typing import Dict, Any, Optional, List, Union
import httpx
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class HeliconeService:
    """Helicone service for API cost tracking."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Helicone service.

        Args:
            api_key: Helicone API key (defaults to HELICONE_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("HELICONE_API_KEY")
        self.base_url = os.getenv("HELICONE_BASE_URL", "https://api.helicone.ai")

        if not self.api_key:
            logger.warning("HELICONE_API_KEY not set. Helicone service will be disabled.")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("Helicone service initialized successfully")

    def get_headers(self, provider: str) -> Dict[str, str]:
        """Get headers for Helicone API requests.

        Args:
            provider: Provider of the model (e.g., openai, anthropic)

        Returns:
            Dictionary of headers
        """
        headers = {
            "Helicone-Auth": f"Bearer {self.api_key}",
            "Helicone-Property-Session": "true"
        }

        if provider == "openai":
            headers["Helicone-OpenAI-Api-Base"] = "https://api.openai.com/v1"
        elif provider == "anthropic":
            headers["Helicone-Anthropic-Api-Base"] = "https://api.anthropic.com"
        elif provider == "google":
            headers["Helicone-Google-Api-Base"] = "https://generativelanguage.googleapis.com"

        return headers

    async def get_cost_metrics(self,
                              start_date: Optional[str] = None,
                              end_date: Optional[str] = None,
                              user_id: Optional[str] = None,
                              model: Optional[str] = None) -> Dict[str, Any]:
        """Get cost metrics from Helicone.

        Args:
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            user_id: Optional user ID
            model: Optional model name

        Returns:
            Dictionary containing cost metrics
        """
        if not self.enabled:
            return {"error": "Helicone service is not enabled"}

        try:
            # Prepare the request
            url = f"{self.base_url}/v1/metrics/cost"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # Set default date range if not provided (last 30 days)
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")

            params = {
                "startDate": start_date,
                "endDate": end_date
            }

            # Add optional parameters if provided
            if user_id:
                params["userId"] = user_id
            if model:
                params["model"] = model

            # Make the request
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return {
                            "error": f"Failed to get cost metrics: {error_text}",
                            "status_code": response.status
                        }

                    # Parse the response
                    data = await response.json()

            return data
        except Exception as e:
            logger.error(f"Failed to get cost metrics from Helicone: {str(e)}")
            return {"error": str(e)}

    async def get_request_metrics(self,
                                 start_date: Optional[str] = None,
                                 end_date: Optional[str] = None,
                                 user_id: Optional[str] = None,
                                 model: Optional[str] = None) -> Dict[str, Any]:
        """Get request metrics from Helicone.

        Args:
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            user_id: Optional user ID
            model: Optional model name

        Returns:
            Dictionary containing request metrics
        """
        if not self.enabled:
            return {"error": "Helicone service is not enabled"}

        try:
            # Prepare the request
            url = f"{self.base_url}/v1/metrics/requests"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # Set default date range if not provided (last 30 days)
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")

            params = {
                "startDate": start_date,
                "endDate": end_date
            }

            # Add optional parameters if provided
            if user_id:
                params["userId"] = user_id
            if model:
                params["model"] = model

            # Make the request
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return {
                            "error": f"Failed to get request metrics: {error_text}",
                            "status_code": response.status
                        }

                    # Parse the response
                    data = await response.json()

            return data
        except Exception as e:
            logger.error(f"Failed to get request metrics from Helicone: {str(e)}")
            return {"error": str(e)}

    async def get_cache_metrics(self) -> Dict[str, Any]:
        """Get cache metrics from Helicone.

        Returns:
            Dictionary containing cache metrics
        """
        if not self.enabled:
            return {"error": "Helicone service is not enabled"}

        try:
            # Prepare the request
            url = f"{self.base_url}/v1/metrics/cache"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # Make the request
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return {
                            "error": f"Failed to get cache metrics: {error_text}",
                            "status_code": response.status
                        }

                    # Parse the response
                    data = await response.json()

            return data
        except Exception as e:
            logger.error(f"Failed to get cache metrics from Helicone: {str(e)}")
            return {"error": str(e)}

    async def get_user_metrics(self,
                              start_date: Optional[str] = None,
                              end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get user metrics from Helicone.

        Args:
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)

        Returns:
            Dictionary containing user metrics
        """
        if not self.enabled:
            return {"error": "Helicone service is not enabled"}

        try:
            # Prepare the request
            url = f"{self.base_url}/v1/metrics/users"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # Set default date range if not provided (last 30 days)
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")

            params = {
                "startDate": start_date,
                "endDate": end_date
            }

            # Make the request
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return {
                            "error": f"Failed to get user metrics: {error_text}",
                            "status_code": response.status
                        }

                    # Parse the response
                    data = await response.json()

            return data
        except Exception as e:
            logger.error(f"Failed to get user metrics from Helicone: {str(e)}")
            return {"error": str(e)}

    async def get_model_metrics(self,
                               start_date: Optional[str] = None,
                               end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get model metrics from Helicone.

        Args:
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)

        Returns:
            Dictionary containing model metrics
        """
        if not self.enabled:
            return {"error": "Helicone service is not enabled"}

        try:
            # Prepare the request
            url = f"{self.base_url}/v1/metrics/models"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # Set default date range if not provided (last 30 days)
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")

            params = {
                "startDate": start_date,
                "endDate": end_date
            }

            # Make the request
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return {
                            "error": f"Failed to get model metrics: {error_text}",
                            "status_code": response.status
                        }

                    # Parse the response
                    data = await response.json()

            return data
        except Exception as e:
            logger.error(f"Failed to get model metrics from Helicone: {str(e)}")
            return {"error": str(e)}

    async def get_cost_by_user(self,
                              start_date: Optional[str] = None,
                              end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get cost by user from Helicone.

        Args:
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)

        Returns:
            Dictionary containing cost by user
        """
        if not self.enabled:
            return {"error": "Helicone service is not enabled"}

        try:
            # Prepare the request
            url = f"{self.base_url}/v1/metrics/cost/by-user"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # Set default date range if not provided (last 30 days)
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")

            params = {
                "startDate": start_date,
                "endDate": end_date
            }

            # Make the request
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return {
                            "error": f"Failed to get cost by user: {error_text}",
                            "status_code": response.status
                        }

                    # Parse the response
                    data = await response.json()

            return data
        except Exception as e:
            logger.error(f"Failed to get cost by user from Helicone: {str(e)}")
            return {"error": str(e)}

    async def get_cost_by_model(self,
                               start_date: Optional[str] = None,
                               end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get cost by model from Helicone.

        Args:
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)

        Returns:
            Dictionary containing cost by model
        """
        if not self.enabled:
            return {"error": "Helicone service is not enabled"}

        try:
            # Prepare the request
            url = f"{self.base_url}/v1/metrics/cost/by-model"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # Set default date range if not provided (last 30 days)
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")

            params = {
                "startDate": start_date,
                "endDate": end_date
            }

            # Make the request
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        return {
                            "error": f"Failed to get cost by model: {error_text}",
                            "status_code": response.status
                        }

                    # Parse the response
                    data = await response.json()

            return data
        except Exception as e:
            logger.error(f"Failed to get cost by model from Helicone: {str(e)}")
            return {"error": str(e)}

# Create a singleton instance
helicone_service = HeliconeService()
