"""
Unit tests for AI service.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from apps.api.services.ai_service import AIService
from apps.api.ai.adapters.base import ModelRequest, ModelResponse
from apps.api.schemas.ai import AIModelRequest, AIModelResponse


class TestAIService:
    """Tests for AIService class."""

    @pytest.fixture
    def settings_mock(self):
        """Create a mock settings object."""
        settings = MagicMock()
        settings.AI_CACHE_TTL_SECONDS = 3600
        settings.AI_CACHE_MAX_SIZE = 1000
        return settings

    @pytest.fixture
    def service(self, settings_mock):
        """Create an AI service instance for testing."""
        service = AIService(settings=settings_mock)
        return service

    @pytest.fixture
    def model_request(self):
        """Create a model request for testing."""
        return AIModelRequest(
            prompt="Test prompt",
            model_name="test-model",
            temperature=0.0,
            max_tokens=100,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            stop_sequences=[]
        )

    @pytest.fixture
    def model_response(self):
        """Create a model response for testing."""
        return ModelResponse(
            content="Test response",
            model_name="test-model",
            usage={"total_tokens": 10},
            finish_reason="stop",
            metadata={"latency": 0.1}
        )

    @pytest.mark.asyncio
    async def test_initialize(self, service):
        """Test service initialization."""
        with patch.object(service.logger, 'info') as mock_info:
            await service.initialize()
            mock_info.assert_called_with("AI service initialized with caching enabled")

    @pytest.mark.asyncio
    async def test_get_cache_stats(self, service):
        """Test getting cache statistics."""
        # Mock the cache.get_stats method
        service.cache.get_stats = MagicMock(return_value={
            "size": 10,
            "max_size": 1000,
            "ttl_seconds": 3600,
            "hits": 50,
            "misses": 20,
            "hit_rate_percent": 71.43,
            "total_requests": 70
        })

        stats = await service.get_cache_stats()

        assert stats["size"] == 10
        assert stats["max_size"] == 1000
        assert stats["ttl_seconds"] == 3600
        assert stats["hits"] == 50
        assert stats["misses"] == 20
        assert stats["hit_rate_percent"] == 71.43
        assert stats["total_requests"] == 70

    @pytest.mark.asyncio
    async def test_invalidate_cache(self, service):
        """Test cache invalidation."""
        # Mock the cache.invalidate method
        service.cache.invalidate = AsyncMock(return_value=5)

        # Test invalidating all entries
        count = await service.invalidate_cache()
        service.cache.invalidate.assert_called_with(None)
        assert count == 5

        # Test invalidating entries for a specific model
        service.cache.invalidate.reset_mock()
        count = await service.invalidate_cache(model_name="gpt-4")
        service.cache.invalidate.assert_called_with("model_name:gpt-4")
        assert count == 5

    @pytest.mark.asyncio
    async def test_generate_response_cache_miss(self, service, model_request, model_response):
        """Test generating a response with cache miss."""
        # Mock the adapter
        adapter_mock = AsyncMock()
        adapter_mock.generate = AsyncMock(return_value=model_response)

        # Mock the get_adapter function
        with patch('apps.api.services.ai_service.get_adapter', return_value=adapter_mock):
            # Mock the log_success method
            with patch.object(service, 'log_success') as mock_log_success:
                response = await service.generate_response(model_request)

                # Verify the adapter was called with the correct request
                adapter_mock.generate.assert_called_once()
                actual_request = adapter_mock.generate.call_args[0][0]
                assert actual_request.prompt == model_request.prompt
                assert actual_request.model_name == model_request.model_name

                # Verify the response
                assert response.content == model_response.content
                assert response.model == model_response.model_name
                assert response.usage == model_response.usage
                assert response.finish_reason == model_response.finish_reason
                assert response.cached is False

                # Verify logging
                mock_log_success.assert_called_once()
                call_args = mock_log_success.call_args[1]
                assert call_args["operation"] == "generate_response"
                assert call_args["latency"] == 0.1
                assert call_args["context"]["model"] == model_request.model_name
                assert call_args["context"]["cache_status"] == "cache miss"
                assert call_args["context"]["tokens"] == 10

    @pytest.mark.asyncio
    async def test_generate_response_cache_hit(self, service, model_request, model_response):
        """Test generating a response with cache hit."""
        # Add cached flag to the response
        model_response.metadata["cached"] = True

        # Mock the adapter
        adapter_mock = AsyncMock()
        adapter_mock.generate = AsyncMock(return_value=model_response)

        # Mock the get_adapter function
        with patch('apps.api.services.ai_service.get_adapter', return_value=adapter_mock):
            # Mock the log_success method
            with patch.object(service, 'log_success') as mock_log_success:
                response = await service.generate_response(model_request)

                # Verify the adapter was called
                adapter_mock.generate.assert_called_once()

                # Verify the response
                assert response.content == model_response.content
                assert response.model == model_response.model_name
                assert response.usage == model_response.usage
                assert response.finish_reason == model_response.finish_reason
                assert response.cached is True

                # Verify logging
                mock_log_success.assert_called_once()
                call_args = mock_log_success.call_args[1]
                assert call_args["operation"] == "generate_response"
                assert call_args["latency"] == 0.1
                assert call_args["context"]["model"] == model_request.model_name
                assert call_args["context"]["cache_status"] == "cache hit"
                assert call_args["context"]["tokens"] == 10

    @pytest.mark.asyncio
    async def test_get_model_list(self, service):
        """Test getting the list of available models."""
        models = await service.get_model_list()

        assert len(models) == 2
        assert models[0]["id"] == "gpt-3.5-turbo"
        assert models[0]["name"] == "GPT-3.5 Turbo"
        assert models[0]["provider"] == "openai"
        assert models[1]["id"] == "gpt-4"
        assert models[1]["name"] == "GPT-4"
        assert models[1]["provider"] == "openai"
