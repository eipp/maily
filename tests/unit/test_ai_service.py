import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
import json
import os
from datetime import datetime

# Import the AI service components
from apps.api.ai.model_service import ModelService
from apps.api.ai.adapters.base import ModelRequest, ModelResponse
from apps.api.ai.caching import ModelResponseCache
from apps.api.ai.monitoring import AIMetricsService


class TestModelService(unittest.TestCase):
    """Test cases for the ModelService class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock cache service
        self.mock_cache_service = MagicMock()

        # Create a ModelService instance with the mock cache
        self.model_service = ModelService(cache_service=self.mock_cache_service)

        # Mock the environment variables
        self.env_patcher = patch.dict(os.environ, {
            "DEFAULT_MODEL": "gpt-4",
            "DEFAULT_PROVIDER": "openai",
            "OPENAI_API_KEY": "test-openai-key",
            "ANTHROPIC_API_KEY": "test-anthropic-key",
            "GOOGLE_API_KEY": "test-google-key",
            "ENABLE_MODEL_CACHING": "true"
        })
        self.env_patcher.start()

        # Mock the model adapter factory
        self.adapter_factory_patcher = patch('apps.api.ai.model_service.model_adapter_factory')
        self.mock_adapter_factory = self.adapter_factory_patcher.start()

        # Create a mock adapter
        self.mock_adapter = MagicMock()
        self.mock_adapter.generate_text = AsyncMock()
        self.mock_adapter.generate_text.return_value = ModelResponse(
            content="Test response",
            model="gpt-4",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop"
        )

        # Configure the mock adapter factory
        self.mock_adapter_factory.get_adapter.return_value = self.mock_adapter

        # Mock the metrics service
        self.metrics_patcher = patch('apps.api.ai.model_service.ai_metrics_service')
        self.mock_metrics = self.metrics_patcher.start()
        self.mock_metrics.record_model_request = AsyncMock()
        self.mock_metrics.record_model_response = AsyncMock()

    def tearDown(self):
        """Tear down test fixtures."""
        self.env_patcher.stop()
        self.adapter_factory_patcher.stop()
        self.metrics_patcher.stop()

    @pytest.mark.asyncio
    async def test_generate_text(self):
        """Test the generate_text method."""
        # Create a request
        request = ModelRequest(
            prompt="Test prompt",
            model="gpt-4",
            max_tokens=100,
            temperature=0.7
        )

        # Call the method
        response = await self.model_service.generate_text(request)

        # Verify the response
        self.assertEqual(response.content, "Test response")
        self.assertEqual(response.model, "gpt-4")
        self.assertEqual(response.usage["total_tokens"], 30)

        # Verify the adapter was called correctly
        self.mock_adapter_factory.get_adapter.assert_called_once_with("openai")
        self.mock_adapter.generate_text.assert_called_once_with(request)

        # Verify metrics were recorded
        self.mock_metrics.record_model_request.assert_called_once()
        self.mock_metrics.record_model_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_text_with_caching(self):
        """Test the generate_text method with caching."""
        # Configure the mock cache to return a cached response
        cached_response = ModelResponse(
            content="Cached response",
            model="gpt-4",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop"
        )
        self.model_service.response_cache.get = AsyncMock(return_value=cached_response)

        # Create a request
        request = ModelRequest(
            prompt="Test prompt",
            model="gpt-4",
            max_tokens=100,
            temperature=0.7
        )

        # Call the method
        response = await self.model_service.generate_text(request)

        # Verify the response is the cached one
        self.assertEqual(response.content, "Cached response")

        # Verify the adapter was not called
        self.mock_adapter.generate_text.assert_not_called()

        # Verify metrics were recorded
        self.mock_metrics.record_model_request.assert_called_once()
        self.mock_metrics.record_model_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_text_with_error(self):
        """Test the generate_text method with an error."""
        # Configure the mock adapter to raise an exception
        self.mock_adapter.generate_text.side_effect = Exception("Test error")

        # Create a request
        request = ModelRequest(
            prompt="Test prompt",
            model="gpt-4",
            max_tokens=100,
            temperature=0.7
        )

        # Call the method and expect an exception
        with self.assertRaises(Exception):
            await self.model_service.generate_text(request)

        # Verify metrics were recorded
        self.mock_metrics.record_model_request.assert_called_once()
        self.mock_metrics.record_model_error.assert_called_once()


class TestModelResponseCache(unittest.TestCase):
    """Test cases for the ModelResponseCache class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock cache service
        self.mock_cache_service = MagicMock()
        self.mock_cache_service.get = AsyncMock()
        self.mock_cache_service.set = AsyncMock()

        # Create a ModelResponseCache instance
        self.response_cache = ModelResponseCache(self.mock_cache_service)

    @pytest.mark.asyncio
    async def test_get_cached_response(self):
        """Test getting a cached response."""
        # Configure the mock cache to return a cached response
        cached_data = {
            "content": "Cached response",
            "model": "gpt-4",
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            "finish_reason": "stop",
            "timestamp": datetime.now().isoformat()
        }
        self.mock_cache_service.get.return_value = json.dumps(cached_data)

        # Create a request
        request = ModelRequest(
            prompt="Test prompt",
            model="gpt-4",
            max_tokens=100,
            temperature=0.7
        )

        # Get the cached response
        response = await self.response_cache.get(request)

        # Verify the response
        self.assertIsNotNone(response)
        self.assertEqual(response.content, "Cached response")
        self.assertEqual(response.model, "gpt-4")

        # Verify the cache service was called correctly
        self.mock_cache_service.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_cached_response(self):
        """Test setting a cached response."""
        # Create a request and response
        request = ModelRequest(
            prompt="Test prompt",
            model="gpt-4",
            max_tokens=100,
            temperature=0.7
        )
        response = ModelResponse(
            content="Test response",
            model="gpt-4",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop"
        )

        # Set the cached response
        await self.response_cache.set(request, response)

        # Verify the cache service was called correctly
        self.mock_cache_service.set.assert_called_once()


class TestAIMetricsService(unittest.TestCase):
    """Test cases for the AIMetricsService class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock metrics service
        self.mock_metrics_service = MagicMock()

        # Create an AIMetricsService instance
        self.ai_metrics = AIMetricsService(self.mock_metrics_service)

    @pytest.mark.asyncio
    async def test_record_model_request(self):
        """Test recording a model request."""
        # Create a request
        request = ModelRequest(
            prompt="Test prompt",
            model="gpt-4",
            max_tokens=100,
            temperature=0.7
        )

        # Record the request
        await self.ai_metrics.record_model_request(request, "test-user")

        # Verify the metrics service was called correctly
        self.mock_metrics_service.increment.assert_called_once()
        self.mock_metrics_service.record_timing.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_model_response(self):
        """Test recording a model response."""
        # Create a request and response
        request = ModelRequest(
            prompt="Test prompt",
            model="gpt-4",
            max_tokens=100,
            temperature=0.7
        )
        response = ModelResponse(
            content="Test response",
            model="gpt-4",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop"
        )

        # Record the response
        await self.ai_metrics.record_model_response(request, response, 0.5, "test-user")

        # Verify the metrics service was called correctly
        self.mock_metrics_service.increment.assert_called()
        self.mock_metrics_service.record_timing.assert_called()
        self.mock_metrics_service.record_gauge.assert_called()

    @pytest.mark.asyncio
    async def test_record_model_error(self):
        """Test recording a model error."""
        # Create a request and error
        request = ModelRequest(
            prompt="Test prompt",
            model="gpt-4",
            max_tokens=100,
            temperature=0.7
        )
        error = Exception("Test error")

        # Record the error
        await self.ai_metrics.record_model_error(request, error, "test-user")

        # Verify the metrics service was called correctly
        self.mock_metrics_service.increment.assert_called_once()
