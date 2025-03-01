"""
Unit tests for adapter caching.
"""
import pytest
import time
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

from apps.api.ai.adapters.base import ModelRequest, ModelResponse
from apps.api.ai.adapters.caching import AdapterCache, cached_response


class TestAdapterCache:
    """Tests for AdapterCache class."""

    @pytest.fixture
    def cache(self):
        """Create a cache instance for testing."""
        return AdapterCache(ttl_seconds=10, max_size=5)

    @pytest.fixture
    def model_request(self):
        """Create a model request for testing."""
        return ModelRequest(
            prompt="Test prompt",
            model_name="test-model",
            temperature=0.0,
            max_tokens=100
        )

    @pytest.fixture
    def model_response(self):
        """Create a model response for testing."""
        return ModelResponse(
            content="Test response",
            model_name="test-model",
            usage={"total_tokens": 10},
            finish_reason="stop",
            metadata={}
        )

    @pytest.mark.asyncio
    async def test_cache_miss(self, cache, model_request):
        """Test cache miss."""
        result = await cache.get(model_request)
        assert result is None
        assert cache.misses == 1
        assert cache.hits == 0

    @pytest.mark.asyncio
    async def test_cache_hit(self, cache, model_request, model_response):
        """Test cache hit."""
        await cache.set(model_request, model_response)

        result = await cache.get(model_request)
        assert result is not None
        assert result.content == model_response.content
        assert cache.hits == 1
        assert cache.misses == 0

    @pytest.mark.asyncio
    async def test_cache_expiration(self, cache, model_request, model_response):
        """Test cache expiration."""
        # Set a very short TTL
        cache.ttl_seconds = 0.1

        await cache.set(model_request, model_response)

        # Wait for expiration
        await asyncio.sleep(0.2)

        result = await cache.get(model_request)
        assert result is None
        assert cache.hits == 0
        assert cache.misses == 1

    @pytest.mark.asyncio
    async def test_cache_eviction(self, cache, model_request, model_response):
        """Test cache eviction when full."""
        # Set a small max size
        cache.max_size = 2

        # Add multiple entries
        for i in range(3):
            request = ModelRequest(
                prompt=f"Test prompt {i}",
                model_name="test-model",
                temperature=0.0,
                max_tokens=100
            )
            response = ModelResponse(
                content=f"Test response {i}",
                model_name="test-model",
                usage={"total_tokens": 10},
                finish_reason="stop",
                metadata={}
            )
            await cache.set(request, response)

        # Check cache size
        assert len(cache.cache) == 2

    @pytest.mark.asyncio
    async def test_cache_invalidation(self, cache, model_request, model_response):
        """Test cache invalidation."""
        await cache.set(model_request, model_response)

        # Invalidate all entries
        count = await cache.invalidate()
        assert count == 1
        assert len(cache.cache) == 0

        # Test with pattern
        request1 = ModelRequest(
            prompt="Test prompt 1",
            model_name="model-a",
            temperature=0.0,
            max_tokens=100
        )
        request2 = ModelRequest(
            prompt="Test prompt 2",
            model_name="model-b",
            temperature=0.0,
            max_tokens=100
        )

        await cache.set(request1, model_response)
        await cache.set(request2, model_response)

        # Generate the key for pattern matching
        key1 = cache._generate_key(request1)

        # Invalidate by pattern
        count = await cache.invalidate(key_pattern=key1[:8])
        assert count == 1
        assert len(cache.cache) == 1

    def test_get_stats(self, cache):
        """Test getting cache statistics."""
        cache.hits = 10
        cache.misses = 5

        stats = cache.get_stats()

        assert stats["size"] == 0
        assert stats["max_size"] == 5
        assert stats["ttl_seconds"] == 10
        assert stats["hits"] == 10
        assert stats["misses"] == 5
        assert stats["hit_rate_percent"] == (10 / 15) * 100
        assert stats["total_requests"] == 15


class TestCachedResponseDecorator:
    """Tests for cached_response decorator."""

    @pytest.fixture
    def cache(self):
        """Create a cache instance for testing."""
        return AdapterCache(ttl_seconds=10, max_size=5)

    @pytest.fixture
    def model_request(self):
        """Create a model request for testing."""
        return ModelRequest(
            prompt="Test prompt",
            model_name="test-model",
            temperature=0.0,
            max_tokens=100
        )

    @pytest.fixture
    def model_response(self):
        """Create a model response for testing."""
        return ModelResponse(
            content="Test response",
            model_name="test-model",
            usage={"total_tokens": 10},
            finish_reason="stop",
            metadata={}
        )

    @pytest.mark.asyncio
    async def test_cached_response_hit(self, cache, model_request, model_response):
        """Test cached_response decorator with cache hit."""
        # Mock the original function
        original_func = AsyncMock(return_value=model_response)

        # Create a class with the decorated method
        class TestAdapter:
            @cached_response(cache)
            async def generate(self, request):
                return await original_func(request)

        # Pre-populate the cache
        await cache.set(model_request, model_response)

        # Call the decorated method
        adapter = TestAdapter()
        result = await adapter.generate(model_request)

        # Verify the result and that the original function was not called
        assert result.content == model_response.content
        assert result.metadata["cached"] is True
        original_func.assert_not_called()

    @pytest.mark.asyncio
    async def test_cached_response_miss(self, cache, model_request, model_response):
        """Test cached_response decorator with cache miss."""
        # Mock the original function
        original_func = AsyncMock(return_value=model_response)

        # Create a class with the decorated method
        class TestAdapter:
            @cached_response(cache)
            async def generate(self, request):
                return await original_func(request)

        # Call the decorated method
        adapter = TestAdapter()
        result = await adapter.generate(model_request)

        # Verify the result and that the original function was called
        assert result.content == model_response.content
        assert "cached" not in result.metadata
        original_func.assert_called_once_with(model_request)

        # Verify the response was cached
        cached_result = await cache.get(model_request)
        assert cached_result is not None
        assert cached_result.content == model_response.content

    @pytest.mark.asyncio
    async def test_cached_response_skip_cache(self, cache, model_request, model_response):
        """Test cached_response decorator skipping cache for non-deterministic requests."""
        # Set non-zero temperature to skip cache
        model_request.temperature = 0.7

        # Mock the original function
        original_func = AsyncMock(return_value=model_response)

        # Create a class with the decorated method
        class TestAdapter:
            @cached_response(cache)
            async def generate(self, request):
                return await original_func(request)

        # Call the decorated method
        adapter = TestAdapter()
        result = await adapter.generate(model_request)

        # Verify the result and that the original function was called
        assert result.content == model_response.content
        assert "cached" not in result.metadata
        original_func.assert_called_once_with(model_request)

        # Verify the response was not cached
        cached_result = await cache.get(model_request)
        assert cached_result is None
