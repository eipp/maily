import os
import logging
import time
import asyncio
from typing import Dict, List, Optional, Any, Union, AsyncIterator
import openai
from openai import AsyncOpenAI
from pydantic import BaseModel
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

from .base import BaseModelAdapter, ModelRequest, ModelResponse
from .adapter_utils import AdapterInitializer, ResponseIteratorFactory, CommonModelHelpers
from packages.error_handling.python.error import (
    AIError as AIServiceError,
    RateLimitExceededError as RateLimitError,
    AuthenticationError,
    ValidationError,
    ServerError,
    NetworkError,
    TimeoutError
)

logger = logging.getLogger(__name__)

# Constants for retry configuration
MAX_RETRIES = 3
MIN_RETRY_WAIT_SECONDS = 1
MAX_RETRY_WAIT_SECONDS = 10

# Constants for model configuration
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"


class OpenAIAdapter(BaseModelAdapter):
    """
    Adapter for OpenAI models.

    This adapter implements the BaseModelAdapter interface for OpenAI models,
    providing a standardized way to interact with OpenAI's API.
    """

    def __init__(self, api_key: Optional[str] = None, timeout: int = 60):
        """
        Initialize the OpenAI adapter.

        Args:
            api_key: OpenAI API key. If not provided, will use OPENAI_API_KEY environment variable.
            timeout: Request timeout in seconds (default: 60)

        Raises:
            AuthenticationError: If no API key is provided and it's not in environment variables
        """
        self.client = AdapterInitializer.initialize_client(
            provider_name="OpenAI",
            api_key_var="OPENAI_API_KEY",
            client_class=AsyncOpenAI,
            api_key=api_key,
            timeout=timeout
        )
        self.model_info_cache = {}
        self.timeout = timeout

        # Verify API key is present
        if not api_key and not os.environ.get("OPENAI_API_KEY"):
            raise AuthenticationError("OpenAI API key is required")

        # Initialize metrics - this would connect to your metrics system
        self._initialize_metrics()

    def _initialize_metrics(self):
        """Initialize metrics for tracking adapter usage and performance."""
        # This would integrate with your metrics/monitoring system
        # For example, with Prometheus:
        # self.request_counter = Counter('openai_requests_total', 'Number of requests to OpenAI API', ['model', 'operation'])
        # self.error_counter = Counter('openai_errors_total', 'Number of OpenAI API errors', ['model', 'error_type'])
        # self.latency_histogram = Histogram('openai_request_duration_seconds', 'OpenAI API request duration', ['model', 'operation'])
        pass

    @retry(
        retry=retry_if_exception_type((NetworkError, ServerError, TimeoutError)),
        wait=wait_exponential(multiplier=1, min=MIN_RETRY_WAIT_SECONDS, max=MAX_RETRY_WAIT_SECONDS),
        stop=stop_after_attempt(MAX_RETRIES),
        before_sleep=lambda retry_state: logger.warning(
            f"Retrying OpenAI request after error: {retry_state.outcome.exception()}. "
            f"Attempt {retry_state.attempt_number}/{MAX_RETRIES}"
        )
    )
    async def generate(self, request: ModelRequest) -> ModelResponse:
        """
        Generate a response from an OpenAI model.

        Args:
            request: A standardized ModelRequest object.

        Returns:
            A standardized ModelResponse object.

        Raises:
            RateLimitError: When API rate limits are exceeded
            AuthenticationError: When authentication fails
            ValidationError: When request parameters are invalid
            ServerError: When the OpenAI service encounters an error
            NetworkError: When network connectivity issues occur
            TimeoutError: When the request times out
            AIServiceError: For other API errors
        """
        start_time = time.time()

        try:
            logger.info(f"Sending request to OpenAI model: {request.model_name}")

            # Map our request to OpenAI's expected format
            openai_request = self._prepare_openai_request(request)

            # Record metrics before the call
            # self.request_counter.labels(model=request.model_name, operation="generate").inc()

            # Send the request with timeout
            response = await asyncio.wait_for(
                self.client.chat.completions.create(**openai_request),
                timeout=self.timeout
            )

            # Extract the content from the response
            content = response.choices[0].message.content

            # Record latency metrics
            latency = time.time() - start_time
            # self.latency_histogram.labels(model=request.model_name, operation="generate").observe(latency)
            logger.debug(f"OpenAI request completed in {latency:.2f}s")

            # Create a standardized response
            return ModelResponse(
                content=content,
                model_name=request.model_name,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                finish_reason=response.choices[0].finish_reason,
                metadata={
                    **request.metadata,
                    "latency_seconds": latency,
                    "openai_request_id": response.id
                }
            )
        except asyncio.TimeoutError as e:
            self._handle_timeout_error(e, request, start_time)
        except openai.RateLimitError as e:
            self._handle_rate_limit_error(e, request, start_time)
        except openai.AuthenticationError as e:
            self._handle_authentication_error(e, request, start_time)
        except openai.BadRequestError as e:
            self._handle_validation_error(e, request, start_time)
        except openai.APIError as e:
            self._handle_server_error(e, request, start_time)
        except (openai.APIConnectionError, ConnectionError) as e:
            self._handle_network_error(e, request, start_time)
        except Exception as e:
            self._handle_general_error(e, request, start_time)

    @retry(
        retry=retry_if_exception_type((NetworkError, ServerError, TimeoutError)),
        wait=wait_exponential(multiplier=1, min=MIN_RETRY_WAIT_SECONDS, max=MAX_RETRY_WAIT_SECONDS),
        stop=stop_after_attempt(MAX_RETRIES),
        before_sleep=lambda retry_state: logger.warning(
            f"Retrying OpenAI streaming request after error: {retry_state.outcome.exception()}. "
            f"Attempt {retry_state.attempt_number}/{MAX_RETRIES}"
        )
    )
    async def stream_generate(self, request: ModelRequest) -> AsyncIterator[ModelResponse]:
        """
        Stream a response from an OpenAI model.

        Args:
            request: A standardized ModelRequest object.

        Returns:
            An async iterator yielding ModelResponse objects as content is generated.

        Raises:
            RateLimitError: When API rate limits are exceeded
            AuthenticationError: When authentication fails
            ValidationError: When request parameters are invalid
            ServerError: When the OpenAI service encounters an error
            NetworkError: When network connectivity issues occur
            TimeoutError: When the request times out
            AIServiceError: For other API errors
        """
        start_time = time.time()

        try:
            logger.info(f"Sending streaming request to OpenAI model: {request.model_name}")

            # Map our request to OpenAI's expected format and add stream=True
            openai_request = self._prepare_openai_request(request)
            openai_request['stream'] = True

            # Record metrics before the call
            # self.request_counter.labels(model=request.model_name, operation="stream_generate").inc()

            # Send the request with timeout for the initial response
            stream = await asyncio.wait_for(
                self.client.chat.completions.create(**openai_request),
                timeout=self.timeout
            )

            # Record initial response latency
            initial_latency = time.time() - start_time
            logger.debug(f"OpenAI streaming request initiated in {initial_latency:.2f}s")

            # Define content extraction function
            def extract_content(chunk):
                return chunk.choices[0].delta.content or ""

            # Define finish reason extraction function
            def extract_finish_reason(chunk):
                return chunk.choices[0].finish_reason

            return ResponseIteratorFactory.create_iterator(
                stream=stream,
                model_name=request.model_name,
                metadata={
                    **request.metadata,
                    "initial_latency_seconds": initial_latency
                },
                extract_content_func=extract_content,
                extract_finish_reason_func=extract_finish_reason
            )

        except asyncio.TimeoutError as e:
            self._handle_timeout_error(e, request, start_time)
        except openai.RateLimitError as e:
            self._handle_rate_limit_error(e, request, start_time)
        except openai.AuthenticationError as e:
            self._handle_authentication_error(e, request, start_time)
        except openai.BadRequestError as e:
            self._handle_validation_error(e, request, start_time)
        except openai.APIError as e:
            self._handle_server_error(e, request, start_time)
        except (openai.APIConnectionError, ConnectionError) as e:
            self._handle_network_error(e, request, start_time)
        except Exception as e:
            self._handle_general_error(e, request, start_time)

    @retry(
        retry=retry_if_exception_type((NetworkError, ServerError, TimeoutError)),
        wait=wait_exponential(multiplier=1, min=MIN_RETRY_WAIT_SECONDS, max=MAX_RETRY_WAIT_SECONDS),
        stop=stop_after_attempt(MAX_RETRIES),
        before_sleep=lambda retry_state: logger.warning(
            f"Retrying OpenAI embedding request after error: {retry_state.outcome.exception()}. "
            f"Attempt {retry_state.attempt_number}/{MAX_RETRIES}"
        )
    )
    async def embed(self, text: Union[str, List[str]]) -> List[List[float]]:
        """
        Generate embeddings for the provided text using OpenAI.

        Args:
            text: A string or list of strings to generate embeddings for.

        Returns:
            A list of embedding vectors.

        Raises:
            RateLimitError: When API rate limits are exceeded
            AuthenticationError: When authentication fails
            ValidationError: When request parameters are invalid
            ServerError: When the OpenAI service encounters an error
            NetworkError: When network connectivity issues occur
            TimeoutError: When the request times out
            AIServiceError: For other API errors
        """
        start_time = time.time()

        try:
            # Ensure text is a list
            if isinstance(text, str):
                text_list = [text]
            else:
                text_list = text

            # Validate input
            if not text_list:
                raise ValidationError("Empty text provided for embedding")

            # Record metrics before the call
            # self.request_counter.labels(model=DEFAULT_EMBEDDING_MODEL, operation="embed").inc()

            logger.info(f"Generating embeddings using {DEFAULT_EMBEDDING_MODEL} for {len(text_list)} text items")

            # Send the request with timeout
            response = await asyncio.wait_for(
                self.client.embeddings.create(
                    model=DEFAULT_EMBEDDING_MODEL,
                    input=text_list
                ),
                timeout=self.timeout
            )

            # Extract embeddings from the response
            embeddings = [item.embedding for item in response.data]

            # Record latency metrics
            latency = time.time() - start_time
            # self.latency_histogram.labels(model=DEFAULT_EMBEDDING_MODEL, operation="embed").observe(latency)
            logger.debug(f"OpenAI embeddings request completed in {latency:.2f}s")

            return embeddings

        except asyncio.TimeoutError as e:
            self._handle_timeout_error(e, None, start_time, operation="embed")
        except openai.RateLimitError as e:
            self._handle_rate_limit_error(e, None, start_time, operation="embed")
        except openai.AuthenticationError as e:
            self._handle_authentication_error(e, None, start_time, operation="embed")
        except openai.BadRequestError as e:
            self._handle_validation_error(e, None, start_time, operation="embed")
        except openai.APIError as e:
            self._handle_server_error(e, None, start_time, operation="embed")
        except (openai.APIConnectionError, ConnectionError) as e:
            self._handle_network_error(e, None, start_time, operation="embed")
        except Exception as e:
            self._handle_general_error(e, None, start_time, operation="embed")

    async def check_health(self) -> Dict[str, Any]:
        """
        Check the health of the OpenAI service.

        Returns:
            A dictionary containing health status information.
        """
        start_time = time.time()

        try:
            # Simple health check by listing models
            models = await self.client.models.list()

            # Record health check latency
            latency = time.time() - start_time

            return {
                "status": "healthy",
                "available_models": len(models.data),
                "latency_seconds": latency,
                "timestamp": models.object
            }
        except Exception as e:
            logger.error(f"OpenAI health check failed: {str(e)}")

            return {
                "status": "unhealthy",
                "error": str(e),
                "latency_seconds": time.time() - start_time
            }

    async def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about available OpenAI models.

        Returns:
            A dictionary containing model information.
        """
        try:
            # Check if cache is expired (1 hour TTL)
            cache_ttl = 3600  # 1 hour in seconds
            if not self.model_info_cache or "timestamp" not in self.model_info_cache or \
               time.time() - self.model_info_cache.get("cache_time", 0) > cache_ttl:

                # Refresh the cache
                models = await self.client.models.list()

                # Group models by category
                categorized_models = self._categorize_models([model.id for model in models.data])

                self.model_info_cache = {
                    "models": [model.id for model in models.data],
                    "categorized": categorized_models,
                    "count": len(models.data),
                    "timestamp": models.object,
                    "cache_time": time.time()
                }

            return self.model_info_cache

        except Exception as e:
            logger.error(f"Error getting OpenAI model info: {str(e)}")
            return {
                "error": str(e),
                "cached_models": self.model_info_cache.get("models", []) if self.model_info_cache else []
            }

    def _categorize_models(self, model_ids: List[str]) -> Dict[str, List[str]]:
        """
        Categorize models by type.

        Args:
            model_ids: List of model IDs

        Returns:
            Dictionary of model categories with corresponding model IDs
        """
        categories = {
            "gpt4": [],
            "gpt35": [],
            "embeddings": [],
            "dall-e": [],
            "whisper": [],
            "other": []
        }

        for model_id in model_ids:
            if model_id.startswith("gpt-4"):
                categories["gpt4"].append(model_id)
            elif model_id.startswith("gpt-3.5"):
                categories["gpt35"].append(model_id)
            elif "embedding" in model_id:
                categories["embeddings"].append(model_id)
            elif model_id.startswith("dall-e"):
                categories["dall-e"].append(model_id)
            elif model_id.startswith("whisper"):
                categories["whisper"].append(model_id)
            else:
                categories["other"].append(model_id)

        return categories

    def _prepare_openai_request(self, request: ModelRequest) -> Dict[str, Any]:
        """
        Prepare the request parameters for OpenAI's API.

        Args:
            request: The ModelRequest to convert

        Returns:
            Dictionary with parameters formatted for OpenAI's API
        """
        return {
            "model": request.model_name,
            "messages": [{"role": "user", "content": request.prompt}],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "frequency_penalty": request.frequency_penalty,
            "presence_penalty": request.presence_penalty,
            "stop": request.stop_sequences,
            "user": request.user_id
        }

    def _handle_timeout_error(self, error: Exception, request: Optional[ModelRequest], start_time: float, operation: str = "generate"):
        """Handle timeout errors with appropriate logging and metrics."""
        latency = time.time() - start_time
        model = request.model_name if request else DEFAULT_EMBEDDING_MODEL

        # self.error_counter.labels(model=model, error_type="timeout").inc()

        logger.error(f"OpenAI request timed out after {latency:.2f}s: {str(error)}",
                    extra={"operation": operation, "model": model, "latency": latency})

        raise TimeoutError(f"OpenAI request timed out after {latency:.2f}s: {str(error)}")

    def _handle_rate_limit_error(self, error: Exception, request: Optional[ModelRequest], start_time: float, operation: str = "generate"):
        """Handle rate limit errors with appropriate logging and metrics."""
        latency = time.time() - start_time
        model = request.model_name if request else DEFAULT_EMBEDDING_MODEL

        # self.error_counter.labels(model=model, error_type="rate_limit").inc()

        logger.warning(f"OpenAI rate limit exceeded: {str(error)}",
                     extra={"operation": operation, "model": model, "latency": latency})

        raise RateLimitError(f"OpenAI rate limit exceeded: {str(error)}")

    def _handle_authentication_error(self, error: Exception, request: Optional[ModelRequest], start_time: float, operation: str = "generate"):
        """Handle authentication errors with appropriate logging and metrics."""
        latency = time.time() - start_time
        model = request.model_name if request else DEFAULT_EMBEDDING_MODEL

        # self.error_counter.labels(model=model, error_type="authentication").inc()

        logger.error(f"OpenAI authentication error: {str(error)}",
                    extra={"operation": operation, "model": model, "latency": latency})

        raise AuthenticationError(f"OpenAI authentication error: {str(error)}")

    def _handle_validation_error(self, error: Exception, request: Optional[ModelRequest], start_time: float, operation: str = "generate"):
        """Handle validation errors with appropriate logging and metrics."""
        latency = time.time() - start_time
        model = request.model_name if request else DEFAULT_EMBEDDING_MODEL

        # self.error_counter.labels(model=model, error_type="validation").inc()

        logger.error(f"OpenAI validation error: {str(error)}",
                    extra={"operation": operation, "model": model, "latency": latency})

        raise ValidationError(f"OpenAI validation error: {str(error)}")

    def _handle_server_error(self, error: Exception, request: Optional[ModelRequest], start_time: float, operation: str = "generate"):
        """Handle server errors with appropriate logging and metrics."""
        latency = time.time() - start_time
        model = request.model_name if request else DEFAULT_EMBEDDING_MODEL

        # self.error_counter.labels(model=model, error_type="server").inc()

        logger.error(f"OpenAI server error: {str(error)}",
                    extra={"operation": operation, "model": model, "latency": latency})

        raise ServerError(f"OpenAI server error: {str(error)}")

    def _handle_network_error(self, error: Exception, request: Optional[ModelRequest], start_time: float, operation: str = "generate"):
        """Handle network errors with appropriate logging and metrics."""
        latency = time.time() - start_time
        model = request.model_name if request else DEFAULT_EMBEDDING_MODEL

        # self.error_counter.labels(model=model, error_type="network").inc()

        logger.error(f"OpenAI network error: {str(error)}",
                    extra={"operation": operation, "model": model, "latency": latency})

        raise NetworkError(f"OpenAI network error: {str(error)}")

    def _handle_general_error(self, error: Exception, request: Optional[ModelRequest], start_time: float, operation: str = "generate"):
        """Handle general errors with appropriate logging and metrics."""
        latency = time.time() - start_time
        model = request.model_name if request else DEFAULT_EMBEDDING_MODEL

        # self.error_counter.labels(model=model, error_type="general").inc()

        logger.error(f"OpenAI general error: {str(error)}",
                    extra={"operation": operation, "model": model, "latency": latency})

        raise AIServiceError(f"OpenAI error: {str(error)}")
