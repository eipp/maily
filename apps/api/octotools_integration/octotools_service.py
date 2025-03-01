from typing import Dict, Any, List, Optional, Tuple
import logging
import os
import json
import time
import asyncio
import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Default timeout settings - adjusted for production
DEFAULT_TIMEOUT = float(os.getenv("OCTOTOOLS_TIMEOUT", "30.0"))  # seconds
DEFAULT_CONNECT_TIMEOUT = float(os.getenv("OCTOTOOLS_CONNECT_TIMEOUT", "10.0"))  # seconds

# Retry settings - enhanced for production reliability
MAX_RETRIES = int(os.getenv("OCTOTOOLS_MAX_RETRIES", "3"))
RETRY_BACKOFF_FACTOR = float(os.getenv("OCTOTOOLS_RETRY_BACKOFF", "1.5"))
RETRY_STATUS_CODES = [408, 429, 500, 502, 503, 504]

# Connection pool settings - optimized for production load
MAX_CONNECTIONS = int(os.getenv("OCTOTOOLS_MAX_CONNECTIONS", "100"))
MAX_KEEPALIVE_CONNECTIONS = int(os.getenv("OCTOTOOLS_MAX_KEEPALIVE", "20"))
KEEPALIVE_EXPIRY = int(os.getenv("OCTOTOOLS_KEEPALIVE_EXPIRY", "60"))  # seconds

# Cache settings - configurable for production
CACHE_TTL = int(os.getenv("OCTOTOOLS_CACHE_TTL", "300"))  # seconds
CACHE_ENABLED = os.getenv("OCTOTOOLS_CACHE_ENABLED", "true").lower() == "true"

# Tool execution settings
TOOL_EXECUTION_TIMEOUT = float(os.getenv("OCTOTOOLS_TOOL_TIMEOUT", "60.0"))  # seconds

# Rate limiting settings
MAX_CONCURRENT_REQUESTS = int(os.getenv("OCTOTOOLS_MAX_CONCURRENT", "50"))
REQUEST_RATE_LIMIT = int(os.getenv("OCTOTOOLS_RATE_LIMIT", "100"))  # requests per minute


class OctoToolsService:
    """
    Service for integrating with OctoTools to register and manage AI tools.

    This service provides methods for registering, deregistering, and invoking
    tools with the OctoTools framework.
    """

    def __init__(self):
        """Initialize the OctoTools service."""
        # Use production URL from environment with secure fallback
        self.base_url = os.getenv("OCTOTOOLS_API_URL", "https://octotools.justmaily.com/api")
        self.api_key = os.getenv("OCTOTOOLS_API_KEY")

        if not self.api_key:
            logger.warning("OCTOTOOLS_API_KEY environment variable not set")

        # Set up rate limiting
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        self.request_timestamps = []

        # Configure connection pool limits
        limits = httpx.Limits(
            max_connections=MAX_CONNECTIONS,
            max_keepalive_connections=MAX_KEEPALIVE_CONNECTIONS,
            keepalive_expiry=KEEPALIVE_EXPIRY
        )

        # Configure timeouts
        timeout = httpx.Timeout(
            timeout=DEFAULT_TIMEOUT,
            connect=DEFAULT_CONNECT_TIMEOUT
        )

        # Create HTTP client with optimized settings
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}" if self.api_key else "",
                "Content-Type": "application/json",
                "User-Agent": "Maily/1.0 OctoToolsClient/Production"
            },
            timeout=timeout,
            limits=limits,
            follow_redirects=True,
            http2=True  # Enable HTTP/2 for better performance
        )

        # In-memory cache for tool responses
        self.response_cache = {}
        self.cache_timestamps = {}

        # Tool execution metrics
        self.execution_metrics = {
            "total_invocations": 0,
            "successful_invocations": 0,
            "failed_invocations": 0,
            "cached_responses": 0,
            "average_latency_ms": 0,
            "tool_latencies": {},
            "error_counts": {},
            "rate_limited_requests": 0,
            "concurrent_executions_max": 0
        }

        # Active tool executions
        self.active_executions = {}

        # Start background tasks
        asyncio.create_task(self._cache_cleanup_task())
        asyncio.create_task(self._metrics_reporting_task())

        logger.info(f"OctoTools service initialized with base URL: {self.base_url}")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
        logger.info("OctoTools service shut down")

    async def register_tool(
        self,
        user_id: str,
        tool_name: str,
        description: str,
        parameters: Dict[str, str],
        platform: str
    ) -> Dict[str, Any]:
        """
        Register a tool with OctoTools.

        Args:
            user_id: User ID to register the tool for
            tool_name: Name of the tool
            description: Description of the tool
            parameters: Parameters for the tool
            platform: Platform the tool is for

        Returns:
            Registration result
        """
        try:
            # Convert parameters to OctoTools format
            octotools_parameters = []
            for param_name, param_type in parameters.items():
                is_required = True
                if param_type.endswith("?"):
                    is_required = False
                    param_type = param_type[:-1]

                octotools_parameters.append({
                    "name": param_name,
                    "type": param_type,
                    "required": is_required,
                    "description": f"{param_name} parameter for {tool_name}"
                })

            payload = {
                "user_id": user_id,
                "tool_name": tool_name,
                "description": description,
                "parameters": octotools_parameters,
                "metadata": {
                    "platform": platform,
                    "source": "maily_integration",
                    "registered_at": time.time()
                }
            }

            # Use retry logic for registration
            for attempt in range(MAX_RETRIES):
                try:
                    response = await self.client.post(
                        "/tools/register",
                        json=payload,
                        timeout=httpx.Timeout(timeout=DEFAULT_TIMEOUT * (attempt + 1))
                    )

                    if response.status_code == 200:
                        return response.json()

                    # Retry on specific status codes
                    if response.status_code in RETRY_STATUS_CODES and attempt < MAX_RETRIES - 1:
                        backoff_time = RETRY_BACKOFF_FACTOR ** attempt
                        logger.warning(f"Retrying tool registration after {backoff_time:.2f}s (attempt {attempt+1}/{MAX_RETRIES})")
                        await asyncio.sleep(backoff_time)
                        continue

                    logger.error(f"Error registering tool {tool_name}: {response.text}")
                    return {
                        "success": False,
                        "error": f"Error registering tool: {response.text}"
                    }
                except httpx.TimeoutException:
                    if attempt < MAX_RETRIES - 1:
                        backoff_time = RETRY_BACKOFF_FACTOR ** attempt
                        logger.warning(f"Timeout registering tool, retrying after {backoff_time:.2f}s")
                        await asyncio.sleep(backoff_time)
                    else:
                        logger.error(f"Timeout registering tool {tool_name} after {MAX_RETRIES} attempts")
                        return {
                            "success": False,
                            "error": f"Timeout registering tool after {MAX_RETRIES} attempts"
                        }
                except Exception as e:
                    logger.error(f"Error registering tool {tool_name}: {str(e)}")
                    return {
                        "success": False,
                        "error": f"Error registering tool: {str(e)}"
                    }
        except Exception as e:
            logger.error(f"Error preparing tool registration {tool_name}: {str(e)}")
            return {
                "success": False,
                "error": f"Error preparing tool registration: {str(e)}"
            }

    async def deregister_tool(self, user_id: str, tool_name: str) -> Dict[str, Any]:
        """
        Deregister a tool from OctoTools.

        Args:
            user_id: User ID to deregister the tool for
            tool_name: Name of the tool

        Returns:
            Deregistration result
        """
        try:
            payload = {
                "user_id": user_id,
                "tool_name": tool_name
            }

            # Use retry logic for deregistration
            for attempt in range(MAX_RETRIES):
                try:
                    response = await self.client.post(
                        "/tools/deregister",
                        json=payload,
                        timeout=httpx.Timeout(timeout=DEFAULT_TIMEOUT * (attempt + 1))
                    )

                    if response.status_code == 200:
                        # Clear any cached responses for this tool
                        cache_keys_to_remove = []
                        for key in self.response_cache:
                            if f"{user_id}:{tool_name}" in key:
                                cache_keys_to_remove.append(key)

                        for key in cache_keys_to_remove:
                            del self.response_cache[key]
                            if key in self.cache_timestamps:
                                del self.cache_timestamps[key]

                        return response.json()

                    # Retry on specific status codes
                    if response.status_code in RETRY_STATUS_CODES and attempt < MAX_RETRIES - 1:
                        backoff_time = RETRY_BACKOFF_FACTOR ** attempt
                        logger.warning(f"Retrying tool deregistration after {backoff_time:.2f}s (attempt {attempt+1}/{MAX_RETRIES})")
                        await asyncio.sleep(backoff_time)
                        continue

                    logger.error(f"Error deregistering tool {tool_name}: {response.text}")
                    return {
                        "success": False,
                        "error": f"Error deregistering tool: {response.text}"
                    }
                except httpx.TimeoutException:
                    if attempt < MAX_RETRIES - 1:
                        backoff_time = RETRY_BACKOFF_FACTOR ** attempt
                        logger.warning(f"Timeout deregistering tool, retrying after {backoff_time:.2f}s")
                        await asyncio.sleep(backoff_time)
                    else:
                        logger.error(f"Timeout deregistering tool {tool_name} after {MAX_RETRIES} attempts")
                        return {
                            "success": False,
                            "error": f"Timeout deregistering tool after {MAX_RETRIES} attempts"
                        }
                except Exception as e:
                    logger.error(f"Error deregistering tool {tool_name}: {str(e)}")
                    return {
                        "success": False,
                        "error": f"Error deregistering tool: {str(e)}"
                    }
        except Exception as e:
            logger.error(f"Error preparing tool deregistration {tool_name}: {str(e)}")
            return {
                "success": False,
                "error": f"Error preparing tool deregistration: {str(e)}"
            }

    async def invoke_tool(
        self,
        user_id: str,
        tool_name: str,
        parameters: Dict[str, Any],
        use_cache: bool = True,
        execution_timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Invoke a tool with OctoTools.

        Args:
            user_id: User ID to invoke the tool for
            tool_name: Name of the tool
            parameters: Parameters for the tool invocation
            use_cache: Whether to use cached responses
            execution_timeout: Custom timeout for this execution

        Returns:
            Tool invocation result
        """
        # Update metrics
        self.execution_metrics["total_invocations"] += 1

        # Generate cache key if caching is enabled
        cache_key = None
        if CACHE_ENABLED and use_cache:
            # Create a deterministic cache key
            param_str = json.dumps(parameters, sort_keys=True)
            cache_key = f"{user_id}:{tool_name}:{param_str}"

            # Check cache
            if cache_key in self.response_cache:
                # Check if cache entry is still valid
                if time.time() - self.cache_timestamps[cache_key] < CACHE_TTL:
                    logger.info(f"Cache hit for tool {tool_name}")
                    self.execution_metrics["cached_responses"] += 1
                    return self.response_cache[cache_key]

        # Track execution start time
        start_time = time.time()
        execution_id = f"{user_id}:{tool_name}:{start_time}"
        self.active_executions[execution_id] = {
            "user_id": user_id,
            "tool_name": tool_name,
            "parameters": parameters,
            "start_time": start_time,
            "status": "running"
        }

        try:
            payload = {
                "user_id": user_id,
                "tool_name": tool_name,
                "parameters": parameters
            }

            # Use retry logic for invocation
            timeout = execution_timeout or TOOL_EXECUTION_TIMEOUT

            for attempt in range(MAX_RETRIES):
                try:
                    response = await self.client.post(
                        "/tools/invoke",
                        json=payload,
                        timeout=httpx.Timeout(timeout=timeout * (attempt + 1))
                    )

                    if response.status_code == 200:
                        result = response.json()

                        # Update metrics
                        self.execution_metrics["successful_invocations"] += 1

                        # Calculate and store latency
                        latency_ms = (time.time() - start_time) * 1000
                        if tool_name not in self.execution_metrics["tool_latencies"]:
                            self.execution_metrics["tool_latencies"][tool_name] = []

                        self.execution_metrics["tool_latencies"][tool_name].append(latency_ms)

                        # Update average latency
                        total_successful = self.execution_metrics["successful_invocations"]
                        current_avg = self.execution_metrics["average_latency_ms"]
                        self.execution_metrics["average_latency_ms"] = (
                            (current_avg * (total_successful - 1) + latency_ms) / total_successful
                        )

                        # Cache the result if caching is enabled
                        if CACHE_ENABLED and use_cache and cache_key:
                            self.response_cache[cache_key] = result
                            self.cache_timestamps[cache_key] = time.time()

                        # Update active execution status
                        self.active_executions[execution_id]["status"] = "completed"
                        self.active_executions[execution_id]["end_time"] = time.time()

                        return result

                    # Retry on specific status codes
                    if response.status_code in RETRY_STATUS_CODES and attempt < MAX_RETRIES - 1:
                        backoff_time = RETRY_BACKOFF_FACTOR ** attempt
                        logger.warning(f"Retrying tool invocation after {backoff_time:.2f}s (attempt {attempt+1}/{MAX_RETRIES})")
                        await asyncio.sleep(backoff_time)
                        continue

                    # Update error metrics
                    self.execution_metrics["failed_invocations"] += 1
                    error_type = f"HTTP {response.status_code}"
                    if error_type not in self.execution_metrics["error_counts"]:
                        self.execution_metrics["error_counts"][error_type] = 0
                    self.execution_metrics["error_counts"][error_type] += 1

                    logger.error(f"Error invoking tool {tool_name}: {response.text}")

                    # Update active execution status
                    self.active_executions[execution_id]["status"] = "failed"
                    self.active_executions[execution_id]["end_time"] = time.time()
                    self.active_executions[execution_id]["error"] = response.text

                    return {
                        "success": False,
                        "error": f"Error invoking tool: {response.text}"
                    }
                except httpx.TimeoutException:
                    if attempt < MAX_RETRIES - 1:
                        backoff_time = RETRY_BACKOFF_FACTOR ** attempt
                        logger.warning(f"Timeout invoking tool, retrying after {backoff_time:.2f}s")
                        await asyncio.sleep(backoff_time)
                    else:
                        # Update error metrics
                        self.execution_metrics["failed_invocations"] += 1
                        if "timeout" not in self.execution_metrics["error_counts"]:
                            self.execution_metrics["error_counts"]["timeout"] = 0
                        self.execution_metrics["error_counts"]["timeout"] += 1

                        logger.error(f"Timeout invoking tool {tool_name} after {MAX_RETRIES} attempts")

                        # Update active execution status
                        self.active_executions[execution_id]["status"] = "timeout"
                        self.active_executions[execution_id]["end_time"] = time.time()

                        return {
                            "success": False,
                            "error": f"Timeout invoking tool after {MAX_RETRIES} attempts"
                        }
                except Exception as e:
                    # Update error metrics
                    self.execution_metrics["failed_invocations"] += 1
                    error_type = e.__class__.__name__
                    if error_type not in self.execution_metrics["error_counts"]:
                        self.execution_metrics["error_counts"][error_type] = 0
                    self.execution_metrics["error_counts"][error_type] += 1

                    logger.error(f"Error invoking tool {tool_name}: {str(e)}")

                    # Update active execution status
                    self.active_executions[execution_id]["status"] = "error"
                    self.active_executions[execution_id]["end_time"] = time.time()
                    self.active_executions[execution_id]["error"] = str(e)

                    return {
                        "success": False,
                        "error": f"Error invoking tool: {str(e)}"
                    }
        except Exception as e:
            # Update error metrics
            self.execution_metrics["failed_invocations"] += 1
            error_type = e.__class__.__name__
            if error_type not in self.execution_metrics["error_counts"]:
                self.execution_metrics["error_counts"][error_type] = 0
            self.execution_metrics["error_counts"][error_type] += 1

            logger.error(f"Error preparing tool invocation {tool_name}: {str(e)}")

            # Update active execution status
            self.active_executions[execution_id]["status"] = "error"
            self.active_executions[execution_id]["end_time"] = time.time()
            self.active_executions[execution_id]["error"] = str(e)

            return {
                "success": False,
                "error": f"Error preparing tool invocation: {str(e)}"
            }

    async def list_tools(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List all tools registered for a user.

        Args:
            user_id: User ID to list tools for

        Returns:
            List of tools
        """
        try:
            # Use retry logic for listing tools
            for attempt in range(MAX_RETRIES):
                try:
                    response = await self.client.get(
                        f"/tools/list/{user_id}",
                        timeout=httpx.Timeout(timeout=DEFAULT_TIMEOUT * (attempt + 1))
                    )

                    if response.status_code == 200:
                        return response.json().get("tools", [])

                    # Retry on specific status codes
                    if response.status_code in RETRY_STATUS_CODES and attempt < MAX_RETRIES - 1:
                        backoff_time = RETRY_BACKOFF_FACTOR ** attempt
                        logger.warning(f"Retrying tool listing after {backoff_time:.2f}s (attempt {attempt+1}/{MAX_RETRIES})")
                        await asyncio.sleep(backoff_time)
                        continue

                    logger.error(f"Error listing tools for user {user_id}: {response.text}")
                    return []
                except httpx.TimeoutException:
                    if attempt < MAX_RETRIES - 1:
                        backoff_time = RETRY_BACKOFF_FACTOR ** attempt
                        logger.warning(f"Timeout listing tools, retrying after {backoff_time:.2f}s")
                        await asyncio.sleep(backoff_time)
                    else:
                        logger.error(f"Timeout listing tools for user {user_id} after {MAX_RETRIES} attempts")
                        return []
                except Exception as e:
                    logger.error(f"Error listing tools for user {user_id}: {str(e)}")
                    return []
        except Exception as e:
            logger.error(f"Error preparing tool listing for user {user_id}: {str(e)}")
            return []

    def get_execution_metrics(self) -> Dict[str, Any]:
        """
        Get execution metrics for tools.

        Returns:
            Dictionary of execution metrics
        """
        # Calculate per-tool metrics
        tool_metrics = {}
        for tool_name, latencies in self.execution_metrics["tool_latencies"].items():
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                max_latency = max(latencies)
                min_latency = min(latencies)
                p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) >= 20 else None

                tool_metrics[tool_name] = {
                    "avg_latency_ms": avg_latency,
                    "max_latency_ms": max_latency,
                    "min_latency_ms": min_latency,
                    "p95_latency_ms": p95_latency,
                    "invocation_count": len(latencies)
                }

        # Return all metrics
        return {
            **self.execution_metrics,
            "tool_metrics": tool_metrics,
            "active_executions_count": len([e for e in self.active_executions.values() if e["status"] == "running"]),
            "cache_size": len(self.response_cache),
            "timestamp": time.time()
        }

    def clear_cache(self) -> int:
        """
        Clear the response cache.

        Returns:
            Number of cleared cache entries
        """
        cache_size = len(self.response_cache)
        self.response_cache.clear()
        self.cache_timestamps.clear()
        return cache_size

    async def _cache_cleanup_task(self) -> None:
        """Background task to clean up expired cache entries."""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute

                # Find expired cache entries
                current_time = time.time()
                expired_keys = [
                    key for key, timestamp in self.cache_timestamps.items()
                    if current_time - timestamp > CACHE_TTL
                ]

                # Remove expired entries
                for key in expired_keys:
                    del self.response_cache[key]
                    del self.cache_timestamps[key]

                if expired_keys:
                    logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

                # Clean up old completed executions (keep last 1000)
                completed_executions = [
                    execution_id for execution_id, execution in self.active_executions.items()
                    if execution["status"] != "running" and "end_time" in execution
                ]

                if len(completed_executions) > 1000:
                    # Sort by end time, oldest first
                    completed_executions.sort(
                        key=lambda execution_id: self.active_executions[execution_id]["end_time"]
                    )

                    # Remove oldest executions
                    for execution_id in completed_executions[:-1000]:
                        del self.active_executions[execution_id]

                    logger.debug(f"Cleaned up {len(completed_executions) - 1000} old execution records")
            except Exception as e:
                logger.error(f"Error in cache cleanup task: {str(e)}")

    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the OctoTools service.

        Returns:
            Health check result
        """
        try:
            start_time = time.time()
            response = await self.client.get("/health", timeout=5.0)
            latency_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "latency_ms": latency_ms,
                    "api_status": response.json(),
                    "cache_size": len(self.response_cache),
                    "active_executions": len([e for e in self.active_executions.values() if e["status"] == "running"]),
                    "timestamp": time.time()
                }
            else:
                return {
                    "status": "unhealthy",
                    "latency_ms": latency_ms,
                    "error": f"Unexpected status code: {response.status_code}",
                    "timestamp": time.time()
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
