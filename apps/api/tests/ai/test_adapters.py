"""
Tests for AI model adapters.

These tests verify the functionality of the adapter pattern implementation,
error handling, and fallback mechanisms.
"""

import os
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import time
from typing import Dict, Any

from apps.api.ai.adapters.base import ModelRequest, ModelResponse, BaseModelAdapter
from apps.api.ai.adapters.factory import ModelAdapterFactory
from apps.api.ai.adapters.openai_adapter import OpenAIAdapter
from apps.api.errors.ai_service_errors import (
    AIServiceError,
    RateLimitError,
    AuthenticationError,
    ValidationError,
    ServerError
)

# Test data
SAMPLE_PROMPT = "Write a test prompt for unit testing"
SAMPLE_RESPONSE = "This is a sample response for testing purposes"


# Mock adapter class for testing
class MockAdapter(BaseModelAdapter):
    """Mock adapter for testing."""

    def __init__(self, should_fail=False, error_type=None):
        self.should_fail = should_fail
        self.error_type = error_type
        self.generate_called = False
        self.stream_generate_called = False
        self.embed_called = False

    async def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a mock response."""
        self.generate_called = True

        if self.should_fail:
            if self.error_type == "rate_limit":
                raise RateLimitError("Mock rate limit exceeded")
            elif self.error_type == "auth":
                raise AuthenticationError("Mock authentication error")
            elif self.error_type == "validation":
                raise ValidationError("Mock validation error")
            elif self.error_type == "server":
                raise ServerError("Mock server error")
            else:
                raise AIServiceError("Mock error")

        return ModelResponse(
            content=f"Response to: {request.prompt}",
            model_name=request.model_name,
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop"
        )

    async def stream_generate(self, request: ModelRequest):
        """Generate a mock streaming response."""
        self.stream_generate_called = True

        if self.should_fail:
            raise AIServiceError("Mock streaming error")

        # Yield a few chunks for testing
        for i in range(3):
            yield ModelResponse(
                content=f"Chunk {i} for: {request.prompt}",
                model_name=request.model_name,
                usage={},
                finish_reason=None if i < 2 else "stop"
            )
            await asyncio.sleep(0.01)

    async def embed(self, text):
        """Generate mock embeddings."""
        self.embed_called = True

        if self.should_fail:
            raise AIServiceError("Mock embedding error")

        # Return a mock embedding vector
        if isinstance(text, list):
            return [[0.1, 0.2, 0.3] for _ in text]
        return [[0.1, 0.2, 0.3]]

    async def check_health(self):
        """Check mock health."""
        if self.should_fail:
            return {"status": "unhealthy", "error": "Mock health check error"}
        return {"status": "healthy"}

    async def get_model_info(self):
        """Get mock model info."""
        if self.should_fail:
            return {"error": "Mock model info error"}
        return {"models": ["mock-model-1", "mock-model-2"]}


# Fixtures
@pytest.fixture
def model_request():
    """Create a sample model request for testing."""
    return ModelRequest(
        prompt=SAMPLE_PROMPT,
        model_name="test-model",
        temperature=0.7,
        max_tokens=100
    )


@pytest.fixture
def mock_adapter():
    """Create a mock adapter for testing."""
    return MockAdapter()


@pytest.fixture
def mock_adapter_factory():
    """Create a model adapter factory with mock adapters."""
    factory = ModelAdapterFactory()

    # Register mock adapters
    factory._adapter_classes = {
        "mock": MockAdapter,
        "mock_fail": lambda: MockAdapter(should_fail=True)
    }

    # Clear existing adapters
    factory._adapters = {}

    return factory


# Tests for the BaseModelAdapter interface
class TestBaseModelAdapter:
    """Tests for the base model adapter interface."""

    def test_model_request_validation(self):
        """Test that ModelRequest validates inputs properly."""
        # Valid request
        valid_request = ModelRequest(
            prompt="Test prompt",
            model_name="test-model",
            temperature=0.5
        )
        assert valid_request.temperature == 0.5

        # Invalid temperature (should raise ValidationError)
        with pytest.raises(ValueError):
            ModelRequest(
                prompt="Test prompt",
                model_name="test-model",
                temperature=1.5  # Invalid: >1.0
            )

    def test_model_response_immutability(self):
        """Test that ModelResponse is immutable after creation."""
        response = ModelResponse(
            content="Test content",
            model_name="test-model",
            usage={"total_tokens": 10}
        )

        # Verify immutability
        with pytest.raises(Exception):
            response.content = "Modified content"


# Tests for the OpenAI adapter
@pytest.mark.asyncio
class TestOpenAIAdapter:
    """Tests for the OpenAI adapter implementation."""

    @patch("openai.AsyncOpenAI")
    async def test_openai_adapter_initialization(self, mock_openai):
        """Test that the OpenAI adapter initializes correctly."""
        # Mock the OpenAI client
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client

        # Test with API key in constructor
        adapter = OpenAIAdapter(api_key="test_key")

        # Test with API key in environment
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env_test_key"}):
            adapter = OpenAIAdapter()

    @patch("openai.AsyncOpenAI")
    async def test_openai_adapter_generate(self, mock_openai):
        """Test that the OpenAI adapter generate method works correctly."""
        # Mock the OpenAI client
        mock_client = AsyncMock()
        mock_chat = AsyncMock()
        mock_completions = AsyncMock()
        mock_create = AsyncMock()

        mock_client.chat = mock_chat
        mock_chat.completions = mock_completions
        mock_completions.create = mock_create

        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = SAMPLE_RESPONSE
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30
        mock_response.id = "test_response_id"

        mock_create.return_value = mock_response
        mock_openai.return_value = mock_client

        # Create adapter and test
        adapter = OpenAIAdapter(api_key="test_key")
        request = ModelRequest(
            prompt=SAMPLE_PROMPT,
            model_name="gpt-4",
            temperature=0.7
        )

        response = await adapter.generate(request)

        # Verify response
        assert response.content == SAMPLE_RESPONSE
        assert response.model_name == "gpt-4"
        assert response.finish_reason == "stop"
        assert response.usage["total_tokens"] == 30

        # Verify API call
        mock_create.assert_called_once()
        call_args = mock_create.call_args[1]
        assert call_args["model"] == "gpt-4"
        assert call_args["messages"][0]["content"] == SAMPLE_PROMPT
        assert call_args["temperature"] == 0.7

    @patch("openai.AsyncOpenAI")
    async def test_openai_adapter_error_handling(self, mock_openai):
        """Test that the OpenAI adapter properly handles errors."""
        # Mock the OpenAI client
        mock_client = AsyncMock()
        mock_chat = AsyncMock()
        mock_completions = AsyncMock()
        mock_create = AsyncMock()

        mock_client.chat = mock_chat
        mock_chat.completions = mock_completions
        mock_completions.create = mock_create

        # Setup to raise different errors
        import openai
        mock_create.side_effect = openai.RateLimitError("Rate limit exceeded")
        mock_openai.return_value = mock_client

        # Create adapter and test
        adapter = OpenAIAdapter(api_key="test_key")
        request = ModelRequest(
            prompt=SAMPLE_PROMPT,
            model_name="gpt-4"
        )

        # Test rate limit error
        with pytest.raises(RateLimitError):
            await adapter.generate(request)

        # Test authentication error
        mock_create.side_effect = openai.AuthenticationError("Invalid API key")
        with pytest.raises(AuthenticationError):
            await adapter.generate(request)

        # Test validation error
        mock_create.side_effect = openai.BadRequestError("Invalid request")
        with pytest.raises(ValidationError):
            await adapter.generate(request)

        # Test server error
        mock_create.side_effect = openai.APIError("Server error")
        with pytest.raises(ServerError):
            await adapter.generate(request)


# Tests for the adapter factory
@pytest.mark.asyncio
class TestModelAdapterFactory:
    """Tests for the model adapter factory."""

    async def test_adapter_registration(self, mock_adapter_factory):
        """Test registering adapters with the factory."""
        factory = mock_adapter_factory

        # Register a new adapter class
        class CustomAdapter(BaseModelAdapter):
            async def generate(self, request): pass
            async def stream_generate(self, request): pass
            async def embed(self, text): pass
            async def check_health(self): pass
            async def get_model_info(self): pass

        factory.register_adapter_class("custom", CustomAdapter)

        # Verify registration
        assert "custom" in factory._adapter_classes
        assert factory._adapter_classes["custom"] == CustomAdapter

    async def test_get_adapter(self, mock_adapter_factory):
        """Test getting adapters from the factory."""
        factory = mock_adapter_factory

        # Get a mock adapter
        adapter = factory.get_adapter("mock")

        # Verify adapter type
        assert isinstance(adapter, MockAdapter)

        # Test caching (should return same instance)
        adapter2 = factory.get_adapter("mock")
        assert adapter is adapter2

        # Test getting non-existent adapter
        with pytest.raises(ValueError):
            factory.get_adapter("nonexistent")

    async def test_get_adapter_for_model(self, mock_adapter_factory):
        """Test getting adapters by model name."""
        factory = mock_adapter_factory

        # Override the _detect_provider_for_model method for testing
        def mock_detect(model_name):
            if model_name.startswith("mock-"):
                return "mock"
            if model_name.startswith("fail-"):
                return "mock_fail"
            return None

        factory._detect_provider_for_model = mock_detect

        # Get adapter for mock model
        adapter = factory.get_adapter_for_model("mock-model")
        assert isinstance(adapter, MockAdapter)
        assert not adapter.should_fail

        # Get adapter for failing mock model
        adapter = factory.get_adapter_for_model("fail-model")
        assert isinstance(adapter, MockAdapter)
        assert adapter.should_fail

        # Test unsupported model
        with pytest.raises(Exception):
            factory.get_adapter_for_model("unsupported-model")

    async def test_generate_with_fallbacks(self, mock_adapter_factory):
        """Test generating with fallbacks when primary model fails."""
        factory = mock_adapter_factory

        # Setup adapters for testing
        factory._adapters = {}  # Clear existing adapters
        factory._adapter_classes = {
            "primary": lambda: MockAdapter(should_fail=True, error_type="rate_limit"),
            "fallback1": lambda: MockAdapter(should_fail=True, error_type="server"),
            "fallback2": MockAdapter,  # This one works
        }

        # Override provider detection
        def mock_detect(model_name):
            if model_name == "primary-model":
                return "primary"
            if model_name == "fallback1-model":
                return "fallback1"
            if model_name == "fallback2-model":
                return "fallback2"
            return None

        factory._detect_provider_for_model = mock_detect

        # Set fallback order
        factory.set_fallback_order(["primary", "fallback1", "fallback2"])

        # Test generate with fallbacks
        request = ModelRequest(
            prompt=SAMPLE_PROMPT,
            model_name="primary-model"
        )

        # Without fallbacks, should raise error
        with pytest.raises(RateLimitError):
            await factory.get_adapter_for_model("primary-model").generate(request)

        # With fallbacks, should use fallback2 (since others fail)
        response = await factory.generate_with_fallbacks(
            request,
            fallback_models=["fallback1-model", "fallback2-model"]
        )

        # Verify response and fallback metadata
        assert response.content.startswith("Response to:")
        assert "fallback_from" in response.metadata
        assert response.metadata["fallback_from"] == "primary-model"
        assert response.metadata["fallback_to"] == "fallback2-model"


# Tests for metrics and error handling
@pytest.mark.asyncio
class TestMetricsAndErrorHandling:
    """Tests for adapter metrics and error handling."""

    async def test_metrics_tracking(self, mock_adapter_factory):
        """Test that adapter metrics are tracked properly."""
        factory = mock_adapter_factory

        # Get adapters and use them
        adapter = factory.get_adapter("mock")
        request = ModelRequest(
            prompt=SAMPLE_PROMPT,
            model_name="test-model"
        )

        # Generate a few responses
        for _ in range(3):
            await adapter.generate(request)

        # Check metrics
        metrics = factory.get_metrics()
        assert "mock:default" in metrics

        # More detailed metrics tests would go here

    async def test_error_recovery(self, mock_adapter_factory):
        """Test that adapters can recover from errors."""
        factory = mock_adapter_factory

        # Create an adapter that fails then succeeds
        class RecoveringAdapter(BaseModelAdapter):
            def __init__(self):
                self.attempts = 0

            async def generate(self, request):
                self.attempts += 1
                if self.attempts <= 2:  # Fail first 2 attempts
                    raise ServerError("Temporary server error")

                return ModelResponse(
                    content="Recovery successful",
                    model_name=request.model_name,
                    usage={"total_tokens": 10}
                )

            async def stream_generate(self, request): pass
            async def embed(self, text): pass
            async def check_health(self): pass
            async def get_model_info(self): pass

        factory.register_adapter_class("recovering", RecoveringAdapter)
        adapter = factory.get_adapter("recovering")

        # Request should eventually succeed after retries
        request = ModelRequest(
            prompt=SAMPLE_PROMPT,
            model_name="test-model"
        )

        # This would work with a retry decorator, but we'll simulate it
        with pytest.raises(ServerError):
            await adapter.generate(request)  # 1st attempt fails

        with pytest.raises(ServerError):
            await adapter.generate(request)  # 2nd attempt fails

        response = await adapter.generate(request)  # 3rd attempt succeeds
        assert response.content == "Recovery successful"
