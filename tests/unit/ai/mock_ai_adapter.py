"""
Mock AI adapter for testing AI-related components.
Provides utilities for mocking AI model responses and errors in tests.
"""
from typing import Dict, List, Optional, Any, Union, AsyncIterator, Pattern, Tuple, Callable
import re
import asyncio
from pydantic import BaseModel

from apps.api.ai.adapters.base import BaseModelAdapter, ModelRequest, ModelResponse


class MockResponseConfig(BaseModel):
    """Configuration for a mock response."""
    prompt_pattern: str
    response: ModelResponse
    delay: float = 0.0


class MockErrorConfig(BaseModel):
    """Configuration for a mock error."""
    prompt_pattern: str
    error: Exception
    delay: float = 0.0


class MockModelAdapter(BaseModelAdapter):
    """
    Mock implementation of BaseModelAdapter for testing.

    This adapter allows setting up predefined responses or errors that
    will be returned for specific prompt patterns, making it easy to test
    AI-dependent components without real API calls.
    """

    def __init__(self):
        self.responses: List[MockResponseConfig] = []
        self.errors: List[MockErrorConfig] = []
        self.calls: List[ModelRequest] = []
        self.embed_responses: Dict[str, List[float]] = {}
        self.health_status: Dict[str, Any] = {"status": "ok"}
        self.model_info: Dict[str, Any] = {
            "name": "mock-model",
            "version": "1.0.0",
            "provider": "mock"
        }

    def mock_response(self, prompt_pattern: str, response: ModelResponse, delay: float = 0.0):
        """
        Set up a mock response for a specific prompt pattern.

        Args:
            prompt_pattern: Regex pattern to match against prompts
            response: ModelResponse to return when pattern matches
            delay: Optional delay in seconds before returning the response
        """
        self.responses.append(
            MockResponseConfig(
                prompt_pattern=prompt_pattern,
                response=response,
                delay=delay
            )
        )

    def mock_error(self, prompt_pattern: str, error: Exception, delay: float = 0.0):
        """
        Set up a mock error for a specific prompt pattern.

        Args:
            prompt_pattern: Regex pattern to match against prompts
            error: Exception to raise when pattern matches
            delay: Optional delay in seconds before raising the error
        """
        self.errors.append(
            MockErrorConfig(
                prompt_pattern=prompt_pattern,
                error=error,
                delay=delay
            )
        )

    def mock_embedding(self, text: str, embedding: List[float]):
        """
        Set up a mock embedding for a specific text.

        Args:
            text: The text to match
            embedding: The embedding vector to return
        """
        self.embed_responses[text] = embedding

    def mock_health_status(self, status: Dict[str, Any]):
        """
        Set the mock health status to return.

        Args:
            status: Health status dictionary
        """
        self.health_status = status

    def mock_model_info(self, info: Dict[str, Any]):
        """
        Set the mock model info to return.

        Args:
            info: Model info dictionary
        """
        self.model_info = info

    def get_calls(self) -> List[ModelRequest]:
        """
        Get the list of all calls made to this adapter.

        Returns:
            A list of ModelRequest objects representing all calls made
        """
        return self.calls.copy()

    def clear(self):
        """Clear all mocked responses, errors, and call history."""
        self.responses = []
        self.errors = []
        self.calls = []
        self.embed_responses = {}

    def _find_match(self, prompt: str) -> Tuple[Optional[MockResponseConfig], Optional[MockErrorConfig]]:
        """Find a matching response or error for the given prompt."""
        # Check for errors first
        for error_config in self.errors:
            if re.search(error_config.prompt_pattern, prompt):
                return None, error_config

        # Then check for responses
        for response_config in self.responses:
            if re.search(response_config.prompt_pattern, prompt):
                return response_config, None

        return None, None

    async def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a response based on configured mock patterns."""
        self.calls.append(request)

        response_config, error_config = self._find_match(request.prompt)

        # Handle delays
        if error_config and error_config.delay > 0:
            await asyncio.sleep(error_config.delay)
        elif response_config and response_config.delay > 0:
            await asyncio.sleep(response_config.delay)

        # Handle errors
        if error_config:
            raise error_config.error

        # Handle responses
        if response_config:
            return response_config.response

        # Default response if no match
        raise ValueError(f"No mock response configured for prompt: {request.prompt[:50]}...")

    async def stream_generate(self, request: ModelRequest) -> AsyncIterator[ModelResponse]:
        """Stream a response based on configured mock patterns."""
        self.calls.append(request)

        response_config, error_config = self._find_match(request.prompt)

        # Handle errors
        if error_config:
            if error_config.delay > 0:
                await asyncio.sleep(error_config.delay)
            raise error_config.error

        # Handle streaming response
        if response_config:
            if response_config.delay > 0:
                await asyncio.sleep(response_config.delay)

            # Create a simple async iterator to yield chunks of the response
            content = response_config.response.content
            chunk_size = max(1, len(content) // 3)  # Split into ~3 chunks

            class ResponseIterator:
                def __init__(self, content, response, chunk_size):
                    self.content = content
                    self.template_response = response
                    self.chunk_size = chunk_size
                    self.position = 0

                def __aiter__(self):
                    return self

                async def __anext__(self):
                    if self.position >= len(self.content):
                        raise StopAsyncIteration

                    end = min(self.position + self.chunk_size, len(self.content))
                    chunk = self.content[self.position:end]
                    self.position = end

                    # Create a new response with just this chunk
                    return ModelResponse(
                        content=chunk,
                        model_name=self.template_response.model_name,
                        usage=self.template_response.usage,
                        finish_reason="continue" if end < len(self.content) else "stop",
                        metadata=self.template_response.metadata
                    )

            return ResponseIterator(content, response_config.response, chunk_size)

        # Default response if no match
        raise ValueError(f"No mock response configured for prompt: {request.prompt[:50]}...")

    async def embed(self, text: Union[str, List[str]]) -> List[List[float]]:
        """Generate embeddings based on configured mock responses."""
        if isinstance(text, str):
            if text in self.embed_responses:
                return [self.embed_responses[text]]
            raise ValueError(f"No mock embedding configured for text: {text[:50]}...")

        result = []
        for t in text:
            if t in self.embed_responses:
                result.append(self.embed_responses[t])
            else:
                raise ValueError(f"No mock embedding configured for text: {t[:50]}...")

        return result

    async def check_health(self) -> Dict[str, Any]:
        """Return the configured mock health status."""
        return self.health_status

    async def get_model_info(self) -> Dict[str, Any]:
        """Return the configured mock model info."""
        return self.model_info


class AITestFactory:
    """Factory for creating preconfigured mock AI adapters for testing."""

    @staticmethod
    def create_default_mock() -> MockModelAdapter:
        """
        Create a mock adapter with common default responses.

        Returns:
            A MockModelAdapter with sensible defaults
        """
        mock = MockModelAdapter()

        # Add some default responses
        mock.mock_response(".*", ModelResponse(
            content="This is a default mock response",
            model_name="mock-model",
            usage={"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18}
        ))

        # Add common embeddings
        mock.mock_embedding("test", [0.1, 0.2, 0.3, 0.4])

        return mock

    @staticmethod
    def create_failing_mock() -> MockModelAdapter:
        """
        Create a mock adapter that simulates API failures.

        Returns:
            A MockModelAdapter configured to simulate various failures
        """
        mock = MockModelAdapter()

        # Configuration for common failure scenarios
        mock.mock_error(".*", Exception("API connection error"))
        mock.mock_health_status({"status": "error", "message": "Service unavailable"})

        return mock
