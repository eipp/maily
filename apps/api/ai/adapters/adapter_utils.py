"""
Adapter Utilities Module

Provides common utilities for AI model adapters including initialization,
response handling, and error management functions.
"""

import os
import time
import logging
import traceback
import asyncio
from typing import Dict, List, Optional, Any, Union, AsyncIterator, TypeVar, Generic, Callable
from pydantic import BaseModel
from enum import Enum

from apps.api.errors.ai_service_errors import (
    AIServiceError,
    AuthenticationError,
    ValidationError,
    map_provider_error
)

T = TypeVar('T')

logger = logging.getLogger(__name__)

class AdapterInitializer:
    """
    Utility class for initializing adapters with common patterns.

    Provides standardized methods for creating client instances, validating
    configurations, and handling initialization errors.
    """

    @staticmethod
    def initialize_client(
        provider_name: str,
        api_key_var: str,
        client_class,
        api_key: Optional[str] = None,
        timeout: int = 60,
        **kwargs
    ):
        """
        Initialize a client for an AI provider with proper error handling.

        Args:
            provider_name: Name of the AI provider (for logging)
            api_key_var: Environment variable name for the API key
            client_class: The client class to initialize
            api_key: Optional API key (if not provided, will use environment variable)
            timeout: Request timeout in seconds
            **kwargs: Additional arguments to pass to the client constructor

        Returns:
            Initialized client instance

        Raises:
            AuthenticationError: If no API key is provided and not found in environment
            ValidationError: If client initialization fails due to invalid parameters
            AIServiceError: For other initialization errors
        """
        # Get API key with appropriate fallbacks
        actual_api_key = api_key or os.environ.get(api_key_var)

        # Validate API key exists
        if not actual_api_key:
            error_msg = f"No {provider_name} API key provided. Set {api_key_var} environment variable or pass as parameter."
            logger.error(error_msg)
            raise AuthenticationError(error_msg, provider=provider_name.lower())

        # Create initialization parameters
        init_params = {
            'api_key': actual_api_key,
            **kwargs
        }

        # For OpenAI client, set timeout
        if hasattr(client_class, 'DEFAULT_TIMEOUT'):
            init_params['timeout'] = timeout

        try:
            # Initialize the client
            return client_class(**init_params)
        except Exception as e:
            error_msg = f"Failed to initialize {provider_name} client: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())

            # Determine error type
            if "invalid api key" in str(e).lower() or "unauthorized" in str(e).lower():
                raise AuthenticationError(error_msg, provider=provider_name.lower())
            elif "invalid" in str(e).lower() or "required" in str(e).lower():
                raise ValidationError(error_msg, provider=provider_name.lower())
            else:
                raise AIServiceError(error_msg, provider=provider_name.lower())

class ResponseIteratorFactory:
    """
    Factory for creating standard response iterators.

    Provides utilities for handling streaming responses from different
    AI providers in a consistent way.
    """

    @staticmethod
    def create_iterator(
        stream,
        model_name: str,
        metadata: Dict[str, Any],
        extract_content_func: Callable,
        extract_finish_reason_func: Optional[Callable] = None,
        on_error: Optional[Callable] = None
    ):
        """
        Create a standard response iterator for streaming responses.

        Args:
            stream: The stream object from the provider
            model_name: Name of the model
            metadata: Additional metadata
            extract_content_func: Function to extract content from a chunk
            extract_finish_reason_func: Optional function to extract finish reason
            on_error: Optional function to handle errors during iteration

        Returns:
            An AsyncIterator yielding ModelResponse objects
        """
        from apps.api.ai.adapters.base import ModelResponse

        class ResponseIterator:
            """Inner class implementing the AsyncIterator protocol for streaming responses."""

            def __init__(self, stream, model_name, metadata):
                """Initialize the iterator with the stream and metadata."""
                self.stream = stream
                self.model_name = model_name
                self.metadata = metadata
                self.start_time = time.time()
                self.chunks_received = 0

            def __aiter__(self):
                """Return self as an async iterator."""
                return self

            async def __anext__(self):
                """
                Get the next chunk from the stream and convert it to a ModelResponse.

                Raises:
                    StopAsyncIteration: When the stream is exhausted
                """
                try:
                    # Get next chunk with timeout
                    chunk = await asyncio.wait_for(
                        self.stream.__anext__(),
                        timeout=30  # Timeout for individual chunks
                    )

                    # Extract content and finish reason
                    content = extract_content_func(chunk)

                    finish_reason = None
                    if extract_finish_reason_func:
                        finish_reason = extract_finish_reason_func(chunk)

                    # Update metrics
                    self.chunks_received += 1
                    chunk_latency = time.time() - self.start_time

                    # Create chunk metadata
                    chunk_metadata = {
                        **self.metadata,
                        "chunk_number": self.chunks_received,
                        "chunk_latency_seconds": chunk_latency
                    }

                    # Log debug info for large delays
                    if self.chunks_received > 1 and chunk_latency > 5:
                        logger.debug(
                            f"High latency ({chunk_latency:.2f}s) receiving chunk {self.chunks_received} "
                            f"from {self.model_name}"
                        )

                    # Create and return response
                    return ModelResponse(
                        content=content,
                        model_name=self.model_name,
                        usage={},  # Usage stats usually not available in streaming mode
                        finish_reason=finish_reason,
                        metadata=chunk_metadata
                    )

                except asyncio.TimeoutError:
                    # Handle timeout for individual chunks
                    timeout_message = f"Timeout receiving chunk from {self.model_name} after {time.time() - self.start_time:.2f}s"
                    logger.warning(timeout_message)

                    # Call error handler if provided
                    if on_error:
                        await on_error(timeout_message)

                    # Return error response or re-raise
                    return ModelResponse(
                        content="[Stream timeout occurred]",
                        model_name=self.model_name,
                        usage={},
                        finish_reason="timeout",
                        metadata={
                            **self.metadata,
                            "error": "stream_timeout",
                            "chunks_received": self.chunks_received,
                            "total_latency": time.time() - self.start_time
                        }
                    )

                except StopAsyncIteration:
                    # End of stream
                    logger.debug(
                        f"Stream completed: received {self.chunks_received} chunks in "
                        f"{time.time() - self.start_time:.2f}s from {self.model_name}"
                    )
                    raise StopAsyncIteration

                except Exception as e:
                    # Handle other errors during streaming
                    error_message = f"Error processing stream from {self.model_name}: {str(e)}"
                    logger.error(error_message)
                    logger.debug(traceback.format_exc())

                    # Call error handler if provided
                    if on_error:
                        await on_error(error_message)

                    # Return error response or re-raise
                    return ModelResponse(
                        content=f"[Stream error: {str(e)}]",
                        model_name=self.model_name,
                        usage={},
                        finish_reason="error",
                        metadata={
                            **self.metadata,
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "chunks_received": self.chunks_received,
                            "total_latency": time.time() - self.start_time
                        }
                    )

        return ResponseIterator(stream, model_name, metadata)


class CommonModelHelpers:
    """
    Common helper methods for AI model interactions.

    Provides utilities for handling common tasks like error responses,
    token usage estimation, and validation.
    """

    @staticmethod
    def prepare_error_response(
        model_name: str,
        error: Exception,
        metadata: Optional[Dict[str, Any]] = None,
        operation: str = "generate"
    ):
        """
        Create a standardized error response.

        Args:
            model_name: Name of the model
            error: The exception that occurred
            metadata: Additional metadata
            operation: The operation that failed

        Returns:
            A ModelResponse with error information
        """
        from apps.api.ai.adapters.base import ModelResponse

        error_metadata = metadata or {}

        # Determine error category
        error_category = type(error).__name__

        # Determine error message
        if hasattr(error, 'message'):
            error_message = error.message
        else:
            error_message = str(error)

        # Update metadata with error details
        error_metadata.update({
            "error": error_message,
            "error_type": error_category,
            "operation": operation,
            "model": model_name,
            "timestamp": time.time()
        })

        # Log the error
        logger.error(
            f"AI model error ({model_name}/{operation}): {error_message}",
            extra={"error_type": error_category, "model": model_name}
        )

        # Return a standardized error response
        return ModelResponse(
            content=f"Error: {error_message}",
            model_name=model_name,
            usage={"error": 1},
            finish_reason="error",
            metadata=error_metadata
        )

    @staticmethod
    def estimate_token_count(text: str, model_name: str = "gpt-4") -> int:
        """
        Estimate the number of tokens in a text.

        This is a simplified estimation. For more accurate counts, use the tiktoken library.

        Args:
            text: The text to estimate token count for
            model_name: The model to use for estimation

        Returns:
            Estimated token count
        """
        # Simple estimation based on words (very approximate)
        # For production, use tiktoken for accuracy
        words = text.split()

        # Different models have different tokenization
        if "gpt-4" in model_name or "gpt-3.5" in model_name:
            # GPT models average ~1.3 tokens per word
            return int(len(words) * 1.3) + 10
        elif "claude" in model_name:
            # Claude models average ~1.4 tokens per word
            return int(len(words) * 1.4) + 10
        else:
            # Default approximation
            return int(len(words) * 1.5) + 10

    @staticmethod
    def validate_model_compatibility(model_name: str, provider: str) -> bool:
        """
        Validate that a model is compatible with a provider.

        Args:
            model_name: The name of the model
            provider: The provider name

        Returns:
            True if compatible, False otherwise
        """
        provider = provider.lower()
        model_name = model_name.lower()

        # OpenAI models
        if provider == "openai":
            return (
                model_name.startswith("gpt-") or
                model_name.startswith("text-embedding-") or
                model_name.startswith("text-davinci-") or
                model_name.startswith("dall-e")
            )

        # Anthropic models
        elif provider == "anthropic":
            return model_name.startswith("claude-")

        # Google models
        elif provider == "google":
            return model_name.startswith("gemini-")

        # If provider is unknown, always return False
        return False
