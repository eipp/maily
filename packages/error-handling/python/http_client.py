"""
Standardized HTTP client for use across all services.

This module provides a unified HTTP client with resilience, tracing,
and standardized error handling. It is built on httpx, which offers
both sync and async APIs with modern HTTP features.
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, cast
from functools import wraps
import asyncio
import os

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError,
)

# Use absolute imports to allow standalone imports
try:
    # First try relative import (for normal package structure)
    from .errors import (
        NetworkError,
        TimeoutError,
        InfrastructureError,
        BadRequestError,
        UnauthorizedError,
        ForbiddenError,
        NotFoundError,
        ConflictError,
        RateLimitExceededError,
        ServerError,
        ValidationError,
    )
except ImportError:
    # Fallback to absolute import (for direct module import)
    from errors import (
        NetworkError,
        TimeoutError,
        InfrastructureError,
        BadRequestError,
        UnauthorizedError,
        ForbiddenError,
        NotFoundError,
        ConflictError,
        RateLimitExceededError,
        ServerError,
        ValidationError,
    )

T = TypeVar('T')

# Configure logger
logger = logging.getLogger(__name__)

# Default timeout in seconds
DEFAULT_TIMEOUT = 30.0

# Default retry settings
DEFAULT_MAX_RETRIES = 3
DEFAULT_MIN_RETRY_WAIT = 0.1  # 100ms
DEFAULT_MAX_RETRY_WAIT = 2.0  # 2s

# Environment configurations
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", str(DEFAULT_TIMEOUT)))
HTTP_MAX_RETRIES = int(os.getenv("HTTP_MAX_RETRIES", str(DEFAULT_MAX_RETRIES)))
HTTP_MIN_RETRY_WAIT = float(os.getenv("HTTP_MIN_RETRY_WAIT", str(DEFAULT_MIN_RETRY_WAIT)))
HTTP_MAX_RETRY_WAIT = float(os.getenv("HTTP_MAX_RETRY_WAIT", str(DEFAULT_MAX_RETRY_WAIT)))


def map_status_code_to_error(
    status_code: int,
    response_text: str,
    url: str,
    provider: Optional[str] = None,
    request_id: Optional[str] = None,
) -> Optional[Exception]:
    """
    Map HTTP status code to appropriate error type.

    Args:
        status_code: HTTP status code
        response_text: Response body text
        url: Request URL
        provider: Optional service provider name
        request_id: Optional request ID for tracing

    Returns:
        Mapped exception or None if status code is successful
    """
    # Extract more details from the response if possible
    details = {}
    try:
        response_json = json.loads(response_text)
        details = {"response": response_json}
    except (ValueError, TypeError):
        details = {"response_text": response_text}

    # Add request context
    details["url"] = url

    # Return proper error type based on status code
    if 200 <= status_code < 300:
        return None
    elif status_code == 400:
        return BadRequestError(
            message=f"Bad request: {response_text[:100]}...",
            details=details,
            provider=provider,
            request_id=request_id,
        )
    elif status_code == 401:
        return UnauthorizedError(
            message="Authentication required",
            details=details,
            provider=provider,
            request_id=request_id,
        )
    elif status_code == 403:
        return ForbiddenError(
            message="Operation not permitted",
            details=details,
            provider=provider,
            request_id=request_id,
        )
    elif status_code == 404:
        return NotFoundError(
            message=f"Resource not found: {url}",
            details=details,
            provider=provider,
            request_id=request_id,
        )
    elif status_code == 409:
        return ConflictError(
            message="Resource conflict",
            details=details,
            provider=provider,
            request_id=request_id,
        )
    elif status_code == 422:
        return ValidationError(
            message=f"Validation failed: {response_text[:100]}...",
            details=details,
            provider=provider,
            request_id=request_id,
        )
    elif status_code == 429:
        return RateLimitExceededError(
            message="Too many requests, rate limit exceeded",
            details=details,
            provider=provider,
            request_id=request_id,
        )
    elif 500 <= status_code < 600:
        return ServerError(
            message=f"Server error ({status_code}): {response_text[:100]}...",
            details=details,
            provider=provider,
            request_id=request_id,
        )
    else:
        return InfrastructureError(
            message=f"Unexpected status code: {status_code}",
            details=details,
            provider=provider,
            request_id=request_id,
        )


class HttpClient:
    """
    Standardized HTTP client with resilience and error mapping.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        headers: Optional[Dict[str, str]] = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_codes: Optional[List[int]] = None,
        provider_name: Optional[str] = None,
    ):
        """
        Initialize the HTTP client.

        Args:
            base_url: Optional base URL for all requests
            timeout: Request timeout in seconds (default: 30s)
            headers: Default headers to include in all requests
            max_retries: Maximum number of retry attempts for failed requests
            retry_codes: HTTP status codes to retry (default: 5xx and some 4xx)
            provider_name: Name of the service provider for error context
        """
        self.base_url = base_url
        self.timeout = timeout or HTTP_TIMEOUT
        self.headers = headers or {}
        self.max_retries = max_retries
        self.retry_codes = retry_codes or [408, 429, 500, 502, 503, 504]
        self.provider_name = provider_name

        # Add standard headers
        if "User-Agent" not in self.headers:
            self.headers["User-Agent"] = "Maily-HttpClient/1.0"

        # Initialize the sync client with proper arguments
        client_args = {"headers": self.headers, "follow_redirects": True}
        if base_url is not None:
            client_args["base_url"] = base_url
        if timeout is not None:
            client_args["timeout"] = timeout
            
        self.sync_client = httpx.Client(**client_args)

        # The async client will be created when needed
        self._async_client = None

    @property
    async def async_client(self) -> httpx.AsyncClient:
        """
        Lazy-loaded async HTTP client.

        Returns:
            Configured async HTTP client
        """
        if self._async_client is None:
            # Initialize the async client with proper arguments
            client_args = {"headers": self.headers, "follow_redirects": True}
            if self.base_url is not None:
                client_args["base_url"] = self.base_url
            if self.timeout is not None:
                client_args["timeout"] = self.timeout
                
            self._async_client = httpx.AsyncClient(**client_args)
        return self._async_client

    async def close(self) -> None:
        """Close the HTTP client connections."""
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None

        # Also close the sync client
        self.sync_client.close()

    def _prepare_url(self, url: str) -> str:
        """
        Prepare the full URL by combining base_url and path if needed.

        Args:
            url: URL path or full URL

        Returns:
            Full URL
        """
        if self.base_url and not url.startswith(("http://", "https://")):
            # Handle trailing/leading slashes properly
            if self.base_url.endswith("/") and url.startswith("/"):
                url = url[1:]
            elif not self.base_url.endswith("/") and not url.startswith("/"):
                url = f"/{url}"
            return f"{self.base_url}{url}"
        return url

    def _prepare_headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Combine default headers with request-specific headers.

        Args:
            headers: Request-specific headers

        Returns:
            Combined headers dictionary
        """
        result = self.headers.copy()
        if headers:
            result.update(headers)
        return result

    def _handle_sync_response(
        self, response: httpx.Response, raise_for_status: bool = True
    ) -> httpx.Response:
        """
        Handle synchronous response and map errors if needed.

        Args:
            response: HTTP response
            raise_for_status: Whether to raise an exception for non-2xx status codes

        Returns:
            Response object

        Raises:
            Mapped exception if status code indicates an error
        """
        if raise_for_status and not (200 <= response.status_code < 300):
            error = map_status_code_to_error(
                response.status_code,
                response.text,
                str(response.url),
                provider=self.provider_name,
                request_id=response.headers.get("X-Request-ID"),
            )
            if error:
                raise error
        return response

    async def _handle_async_response(
        self, response: httpx.Response, raise_for_status: bool = True
    ) -> httpx.Response:
        """
        Handle asynchronous response and map errors if needed.

        Args:
            response: HTTP response
            raise_for_status: Whether to raise an exception for non-2xx status codes

        Returns:
            Response object

        Raises:
            Mapped exception if status code indicates an error
        """
        if raise_for_status and not (200 <= response.status_code < 300):
            error = map_status_code_to_error(
                response.status_code,
                response.text,
                str(response.url),
                provider=self.provider_name,
                request_id=response.headers.get("X-Request-ID"),
            )
            if error:
                raise error
        return response

    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        raise_for_status: bool = True,
    ) -> httpx.Response:
        """
        Make a synchronous GET request.

        Args:
            url: URL path or full URL
            params: Query parameters
            headers: Request headers
            timeout: Request timeout in seconds
            raise_for_status: Whether to raise an exception for non-2xx status codes

        Returns:
            Response object

        Raises:
            NetworkError: Network-related errors
            TimeoutError: Request timeout
            Various mapped exceptions based on status code
        """
        full_url = self._prepare_url(url)
        request_headers = self._prepare_headers(headers)

        try:
            # Use tenacity for retry logic
            @retry(
                retry=retry_if_exception_type(
                    (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout)
                ),
                stop=stop_after_attempt(self.max_retries),
                wait=wait_exponential(
                    multiplier=HTTP_MIN_RETRY_WAIT, max=HTTP_MAX_RETRY_WAIT
                ),
            )
            def _get_with_retry():
                return self.sync_client.get(
                    full_url,
                    params=params,
                    headers=request_headers,
                    timeout=timeout or self.timeout,
                )

            # Make the request with retries
            response = _get_with_retry()
            return self._handle_sync_response(response, raise_for_status)

        except RetryError as e:
            logger.error(f"Max retries exceeded for GET {full_url}: {str(e)}")
            if isinstance(e.last_attempt.exception(), httpx.TimeoutException):
                raise TimeoutError(
                    message=f"Request timed out: {full_url}",
                    details={"url": full_url, "params": params},
                    provider=self.provider_name,
                ) from e
            else:
                raise NetworkError(
                    message=f"Network error: {str(e.last_attempt.exception())}",
                    details={"url": full_url, "params": params},
                    provider=self.provider_name,
                ) from e
        except httpx.TimeoutException as e:
            logger.error(f"Timeout during GET {full_url}: {str(e)}")
            raise TimeoutError(
                message=f"Request timed out: {full_url}",
                details={"url": full_url, "params": params},
                provider=self.provider_name,
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during GET {full_url}: {str(e)}")
            raise NetworkError(
                message=f"HTTP error: {str(e)}",
                details={"url": full_url, "params": params},
                provider=self.provider_name,
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error during GET {full_url}: {str(e)}")
            raise InfrastructureError(
                message=f"Unexpected error: {str(e)}",
                details={"url": full_url, "params": params},
                provider=self.provider_name,
            ) from e

    async def async_get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        raise_for_status: bool = True,
    ) -> httpx.Response:
        """
        Make an asynchronous GET request.

        Args:
            url: URL path or full URL
            params: Query parameters
            headers: Request headers
            timeout: Request timeout in seconds
            raise_for_status: Whether to raise an exception for non-2xx status codes

        Returns:
            Response object

        Raises:
            NetworkError: Network-related errors
            TimeoutError: Request timeout
            Various mapped exceptions based on status code
        """
        full_url = self._prepare_url(url)
        request_headers = self._prepare_headers(headers)
        client = await self.async_client

        try:
            # Implement retry logic manually for async
            max_attempts = self.max_retries
            attempt = 0
            last_exception = None

            while attempt < max_attempts:
                try:
                    attempt += 1
                    response = await client.get(
                        full_url,
                        params=params,
                        headers=request_headers,
                        timeout=timeout or self.timeout,
                    )

                    # If it's a status code we want to retry, do so
                    if response.status_code in self.retry_codes and attempt < max_attempts:
                        logger.warning(
                            f"Retrying GET request to {full_url} due to status code {response.status_code} "
                            f"(attempt {attempt}/{max_attempts})"
                        )
                        # Exponential backoff
                        backoff = min(
                            HTTP_MIN_RETRY_WAIT * (2 ** (attempt - 1)),
                            HTTP_MAX_RETRY_WAIT,
                        )
                        await asyncio.sleep(backoff)
                        continue

                    return await self._handle_async_response(response, raise_for_status)

                except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout) as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"Retrying GET request to {full_url} due to {str(e)} "
                            f"(attempt {attempt}/{max_attempts})"
                        )
                        # Exponential backoff
                        backoff = min(
                            HTTP_MIN_RETRY_WAIT * (2 ** (attempt - 1)),
                            HTTP_MAX_RETRY_WAIT,
                        )
                        await asyncio.sleep(backoff)
                    else:
                        break

            # If we get here, we've exhausted our retries
            if isinstance(last_exception, httpx.TimeoutException):
                raise TimeoutError(
                    message=f"Request timed out after {max_attempts} attempts: {full_url}",
                    details={"url": full_url, "params": params, "attempts": max_attempts},
                    provider=self.provider_name,
                ) from last_exception
            else:
                raise NetworkError(
                    message=f"Network error after {max_attempts} attempts: {str(last_exception)}",
                    details={"url": full_url, "params": params, "attempts": max_attempts},
                    provider=self.provider_name,
                ) from last_exception

        except httpx.TimeoutException as e:
            logger.error(f"Timeout during async GET {full_url}: {str(e)}")
            raise TimeoutError(
                message=f"Request timed out: {full_url}",
                details={"url": full_url, "params": params},
                provider=self.provider_name,
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during async GET {full_url}: {str(e)}")
            raise NetworkError(
                message=f"HTTP error: {str(e)}",
                details={"url": full_url, "params": params},
                provider=self.provider_name,
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error during async GET {full_url}: {str(e)}")
            raise InfrastructureError(
                message=f"Unexpected error: {str(e)}",
                details={"url": full_url, "params": params},
                provider=self.provider_name,
            ) from e

    def post(
        self,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        raise_for_status: bool = True,
    ) -> httpx.Response:
        """
        Make a synchronous POST request.

        Args:
            url: URL path or full URL
            json: JSON body
            data: Form data
            params: Query parameters
            headers: Request headers
            timeout: Request timeout in seconds
            raise_for_status: Whether to raise an exception for non-2xx status codes

        Returns:
            Response object

        Raises:
            NetworkError: Network-related errors
            TimeoutError: Request timeout
            Various mapped exceptions based on status code
        """
        full_url = self._prepare_url(url)
        request_headers = self._prepare_headers(headers)

        try:
            # Use tenacity for retry logic
            @retry(
                retry=retry_if_exception_type(
                    (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout)
                ),
                stop=stop_after_attempt(self.max_retries),
                wait=wait_exponential(
                    multiplier=HTTP_MIN_RETRY_WAIT, max=HTTP_MAX_RETRY_WAIT
                ),
            )
            def _post_with_retry():
                return self.sync_client.post(
                    full_url,
                    json=json,
                    data=data,
                    params=params,
                    headers=request_headers,
                    timeout=timeout or self.timeout,
                )

            # Make the request with retries
            response = _post_with_retry()
            return self._handle_sync_response(response, raise_for_status)

        except RetryError as e:
            logger.error(f"Max retries exceeded for POST {full_url}: {str(e)}")
            if isinstance(e.last_attempt.exception(), httpx.TimeoutException):
                raise TimeoutError(
                    message=f"Request timed out: {full_url}",
                    details={"url": full_url, "params": params},
                    provider=self.provider_name,
                ) from e
            else:
                raise NetworkError(
                    message=f"Network error: {str(e.last_attempt.exception())}",
                    details={"url": full_url, "params": params},
                    provider=self.provider_name,
                ) from e
        except httpx.TimeoutException as e:
            logger.error(f"Timeout during POST {full_url}: {str(e)}")
            raise TimeoutError(
                message=f"Request timed out: {full_url}",
                details={"url": full_url, "params": params},
                provider=self.provider_name,
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during POST {full_url}: {str(e)}")
            raise NetworkError(
                message=f"HTTP error: {str(e)}",
                details={"url": full_url, "params": params},
                provider=self.provider_name,
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error during POST {full_url}: {str(e)}")
            raise InfrastructureError(
                message=f"Unexpected error: {str(e)}",
                details={"url": full_url, "params": params},
                provider=self.provider_name,
            ) from e

    async def async_post(
        self,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        raise_for_status: bool = True,
    ) -> httpx.Response:
        """
        Make an asynchronous POST request.

        Args:
            url: URL path or full URL
            json: JSON body
            data: Form data
            params: Query parameters
            headers: Request headers
            timeout: Request timeout in seconds
            raise_for_status: Whether to raise an exception for non-2xx status codes

        Returns:
            Response object

        Raises:
            NetworkError: Network-related errors
            TimeoutError: Request timeout
            Various mapped exceptions based on status code
        """
        full_url = self._prepare_url(url)
        request_headers = self._prepare_headers(headers)
        client = await self.async_client

        try:
            # Implement retry logic manually for async
            max_attempts = self.max_retries
            attempt = 0
            last_exception = None

            while attempt < max_attempts:
                try:
                    attempt += 1
                    response = await client.post(
                        full_url,
                        json=json,
                        data=data,
                        params=params,
                        headers=request_headers,
                        timeout=timeout or self.timeout,
                    )

                    # If it's a status code we want to retry, do so
                    if response.status_code in self.retry_codes and attempt < max_attempts:
                        logger.warning(
                            f"Retrying POST request to {full_url} due to status code {response.status_code} "
                            f"(attempt {attempt}/{max_attempts})"
                        )
                        # Exponential backoff
                        backoff = min(
                            HTTP_MIN_RETRY_WAIT * (2 ** (attempt - 1)),
                            HTTP_MAX_RETRY_WAIT,
                        )
                        await asyncio.sleep(backoff)
                        continue

                    return await self._handle_async_response(response, raise_for_status)

                except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout) as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"Retrying POST request to {full_url} due to {str(e)} "
                            f"(attempt {attempt}/{max_attempts})"
                        )
                        # Exponential backoff
                        backoff = min(
                            HTTP_MIN_RETRY_WAIT * (2 ** (attempt - 1)),
                            HTTP_MAX_RETRY_WAIT,
                        )
                        await asyncio.sleep(backoff)
                    else:
                        break

            # If we get here, we've exhausted our retries
            if isinstance(last_exception, httpx.TimeoutException):
                raise TimeoutError(
                    message=f"Request timed out after {max_attempts} attempts: {full_url}",
                    details={"url": full_url, "params": params, "attempts": max_attempts},
                    provider=self.provider_name,
                ) from last_exception
            else:
                raise NetworkError(
                    message=f"Network error after {max_attempts} attempts: {str(last_exception)}",
                    details={"url": full_url, "params": params, "attempts": max_attempts},
                    provider=self.provider_name,
                ) from last_exception

        except httpx.TimeoutException as e:
            logger.error(f"Timeout during async POST {full_url}: {str(e)}")
            raise TimeoutError(
                message=f"Request timed out: {full_url}",
                details={"url": full_url, "params": params},
                provider=self.provider_name,
            ) from e
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during async POST {full_url}: {str(e)}")
            raise NetworkError(
                message=f"HTTP error: {str(e)}",
                details={"url": full_url, "params": params},
                provider=self.provider_name,
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error during async POST {full_url}: {str(e)}")
            raise InfrastructureError(
                message=f"Unexpected error: {str(e)}",
                details={"url": full_url, "params": params},
                provider=self.provider_name,
            ) from e

    # Define similar methods for other HTTP methods (PUT, DELETE, PATCH)
    # These follow the same pattern as GET and POST but with different HTTP methods

    def put(
        self,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        raise_for_status: bool = True,
    ) -> httpx.Response:
        """Make a synchronous PUT request."""
        full_url = self._prepare_url(url)
        request_headers = self._prepare_headers(headers)

        try:
            @retry(
                retry=retry_if_exception_type(
                    (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout)
                ),
                stop=stop_after_attempt(self.max_retries),
                wait=wait_exponential(
                    multiplier=HTTP_MIN_RETRY_WAIT, max=HTTP_MAX_RETRY_WAIT
                ),
            )
            def _put_with_retry():
                return self.sync_client.put(
                    full_url,
                    json=json,
                    data=data,
                    params=params,
                    headers=request_headers,
                    timeout=timeout or self.timeout,
                )

            response = _put_with_retry()
            return self._handle_sync_response(response, raise_for_status)
        except Exception as e:
            # Error handling similar to GET/POST methods
            logger.error(f"Error during PUT {full_url}: {str(e)}")
            raise NetworkError(
                message=f"Error during PUT request: {str(e)}",
                details={"url": full_url},
                provider=self.provider_name,
            ) from e

    async def async_put(
        self,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        raise_for_status: bool = True,
    ) -> httpx.Response:
        """Make an asynchronous PUT request."""
        # Implementation similar to async_post but with PUT method
        full_url = self._prepare_url(url)
        request_headers = self._prepare_headers(headers)
        client = await self.async_client

        try:
            # Retry logic similar to async_post
            response = await client.put(
                full_url,
                json=json,
                data=data,
                params=params,
                headers=request_headers,
                timeout=timeout or self.timeout,
            )
            return await self._handle_async_response(response, raise_for_status)
        except Exception as e:
            logger.error(f"Error during async PUT {full_url}: {str(e)}")
            raise NetworkError(
                message=f"Error during PUT request: {str(e)}",
                details={"url": full_url},
                provider=self.provider_name,
            ) from e

    def delete(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        raise_for_status: bool = True,
    ) -> httpx.Response:
        """Make a synchronous DELETE request."""
        full_url = self._prepare_url(url)
        request_headers = self._prepare_headers(headers)

        try:
            @retry(
                retry=retry_if_exception_type(
                    (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout)
                ),
                stop=stop_after_attempt(self.max_retries),
                wait=wait_exponential(
                    multiplier=HTTP_MIN_RETRY_WAIT, max=HTTP_MAX_RETRY_WAIT
                ),
            )
            def _delete_with_retry():
                return self.sync_client.delete(
                    full_url,
                    params=params,
                    headers=request_headers,
                    timeout=timeout or self.timeout,
                )

            response = _delete_with_retry()
            return self._handle_sync_response(response, raise_for_status)
        except Exception as e:
            logger.error(f"Error during DELETE {full_url}: {str(e)}")
            raise NetworkError(
                message=f"Error during DELETE request: {str(e)}",
                details={"url": full_url},
                provider=self.provider_name,
            ) from e

    async def async_delete(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        raise_for_status: bool = True,
    ) -> httpx.Response:
        """Make an asynchronous DELETE request."""
        full_url = self._prepare_url(url)
        request_headers = self._prepare_headers(headers)
        client = await self.async_client

        try:
            response = await client.delete(
                full_url,
                params=params,
                headers=request_headers,
                timeout=timeout or self.timeout,
            )
            return await self._handle_async_response(response, raise_for_status)
        except Exception as e:
            logger.error(f"Error during async DELETE {full_url}: {str(e)}")
            raise NetworkError(
                message=f"Error during DELETE request: {str(e)}",
                details={"url": full_url},
                provider=self.provider_name,
            ) from e

    def patch(
        self,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        raise_for_status: bool = True,
    ) -> httpx.Response:
        """Make a synchronous PATCH request."""
        full_url = self._prepare_url(url)
        request_headers = self._prepare_headers(headers)

        try:
            @retry(
                retry=retry_if_exception_type(
                    (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout)
                ),
                stop=stop_after_attempt(self.max_retries),
                wait=wait_exponential(
                    multiplier=HTTP_MIN_RETRY_WAIT, max=HTTP_MAX_RETRY_WAIT
                ),
            )
            def _patch_with_retry():
                return self.sync_client.patch(
                    full_url,
                    json=json,
                    data=data,
                    params=params,
                    headers=request_headers,
                    timeout=timeout or self.timeout,
                )

            response = _patch_with_retry()
            return self._handle_sync_response(response, raise_for_status)
        except Exception as e:
            logger.error(f"Error during PATCH {full_url}: {str(e)}")
            raise NetworkError(
                message=f"Error during PATCH request: {str(e)}",
                details={"url": full_url},
                provider=self.provider_name,
            ) from e

    async def async_patch(
        self,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        raise_for_status: bool = True,
    ) -> httpx.Response:
        """Make an asynchronous PATCH request."""
        full_url = self._prepare_url(url)
        request_headers = self._prepare_headers(headers)
        client = await self.async_client

        try:
            response = await client.patch(
                full_url,
                json=json,
                data=data,
                params=params,
                headers=request_headers,
                timeout=timeout or self.timeout,
            )
            return await self._handle_async_response(response, raise_for_status)
        except Exception as e:
            logger.error(f"Error during async PATCH {full_url}: {str(e)}")
            raise NetworkError(
                message=f"Error during PATCH request: {str(e)}",
                details={"url": full_url},
                provider=self.provider_name,
            ) from e


# Create singleton instance for global use
try:
    http_client = HttpClient()
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"Failed to initialize HTTP client: {e}")
    http_client = None

# Convenience functions
async def get(url: str, **kwargs) -> httpx.Response:
    """Convenience function for async GET request."""
    if http_client is None:
        client = HttpClient()
        return await client.async_get(url, **kwargs)
    return await http_client.async_get(url, **kwargs)

async def post(url: str, **kwargs) -> httpx.Response:
    """Convenience function for async POST request."""
    if http_client is None:
        client = HttpClient()
        return await client.async_post(url, **kwargs)
    return await http_client.async_post(url, **kwargs)

async def put(url: str, **kwargs) -> httpx.Response:
    """Convenience function for async PUT request."""
    if http_client is None:
        client = HttpClient()
        return await client.async_put(url, **kwargs)
    return await http_client.async_put(url, **kwargs)

async def delete(url: str, **kwargs) -> httpx.Response:
    """Convenience function for async DELETE request."""
    if http_client is None:
        client = HttpClient()
        return await client.async_delete(url, **kwargs)
    return await http_client.async_delete(url, **kwargs)

async def patch(url: str, **kwargs) -> httpx.Response:
    """Convenience function for async PATCH request."""
    if http_client is None:
        client = HttpClient()
        return await client.async_patch(url, **kwargs)
    return await http_client.async_patch(url, **kwargs)

def create_client(base_url: str, **kwargs) -> HttpClient:
    """
    Create a new HTTP client with the given base URL and options.
    
    Args:
        base_url: Base URL for all requests
        **kwargs: Additional client options
        
    Returns:
        Configured HTTP client
    """
    return HttpClient(base_url=base_url, **kwargs)