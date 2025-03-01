"""
Test suite for enhanced AI adapters and orchestrator.
Tests confidence scoring, validation, and other advanced features.
"""
import os
import json
import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from typing import Dict, List, Any

from apps.api.ai.adapters.enhanced_base import (
    EnhancedModelAdapter,
    EnhancedModelRequest,
    EnhancedModelResponse,
    ValidationResult,
    ModelProvider,
    ModelCapability,
    ConfidenceLevel,
    ChainOfThoughtValidationResult
)
from apps.api.ai.adapters.enhanced_openai_adapter import EnhancedOpenAIAdapter
from apps.api.ai.orchestration.enhanced_ai_orchestrator import (
    EnhancedAIOrchestrator,
    OrchestratorConfig,
    RoutingStrategy,
    FallbackConfig
)


# Mock responses for testing
def create_mock_openai_response(content="Test response", confidence=0.9, is_valid=True):
    """Create a mock OpenAI API response"""
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677858242,
        "model": "gpt-4o",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": "stop",
                "index": 0
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    }


# Test fixtures
@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client"""
    mock_client = AsyncMock()

    # Mock completions create
    chat_completions = AsyncMock()
    mock_client.chat.completions.create = chat_completions

    # Mock embeddings create
    embeddings = AsyncMock()
    mock_client.embeddings.create = embeddings

    # Mock models list
    models = AsyncMock()
    mock_client.models.list = models
    models.return_value.data = [
        MagicMock(id="gpt-4o"),
        MagicMock(id="gpt-3.5-turbo"),
        MagicMock(id="text-embedding-3-small")
    ]

    return mock_client


@pytest.fixture
def mock_cache_client():
    """Create a mock cache client"""
    mock_cache = AsyncMock()
    mock_cache.get = AsyncMock(return_value=None)
    mock_cache.set = AsyncMock()
    return mock_cache


@pytest.fixture
def mock_metrics_client():
    """Create a mock metrics client"""
    mock_metrics = AsyncMock()
    mock_metrics.send_metrics = AsyncMock()
    return mock_metrics


@pytest.fixture
def openai_adapter(mock_openai_client):
    """Create an OpenAI adapter with mocked client"""
    with patch('openai.AsyncOpenAI', return_value=mock_openai_client):
        adapter = EnhancedOpenAIAdapter(
            api_key="test-api-key",
            default_model="gpt-4o"
        )
        # Replace the client with our mock
        adapter.client = mock_openai_client
        return adapter


@pytest.fixture
def ai_orchestrator(openai_adapter, mock_cache_client, mock_metrics_client):
    """Create an AI orchestrator with mocked components"""
    config = OrchestratorConfig(
        default_provider=ModelProvider.OPENAI,
        default_model="gpt-4o",
        routing_strategy=RoutingStrategy.FALLBACK_CHAIN,
        fallback=FallbackConfig(
            enabled=True,
            max_attempts=2,
            confidence_threshold=0.7,
            providers=[ModelProvider.OPENAI],
            models=["gpt-4o", "gpt-3.5-turbo"]
        )
    )

    orchestrator = EnhancedAIOrchestrator(
        config=config,
        api_keys={"openai": "test-api-key"},
        cache_client=mock_cache_client,
        metrics_client=mock_metrics_client
    )

    # Replace the adapter with our mocked one
    orchestrator.adapters[ModelProvider.OPENAI] = openai_adapter

    return orchestrator


# Tests for the enhanced OpenAI adapter
class TestEnhancedOpenAIAdapter:

    @pytest.mark.asyncio
    async def test_enhanced_generate_success(self, openai_adapter, mock_openai_client):
        """Test successful enhanced generation"""
        # Setup mock response
        response_obj = create_mock_openai_response(
            content="This is a test response",
            confidence=0.9
        )
        mock_response = AsyncMock()
        mock_response.model_dump.return_value = response_obj
        mock_response.id = response_obj["id"]
        mock_response.created = response_obj["created"]
        mock_response.model = response_obj["model"]
        mock_response.choices = [MagicMock(
            message=MagicMock(
                content=response_obj["choices"][0]["message"]["content"],
                model_dump=MagicMock(return_value=response_obj["choices"][0]["message"])
            ),
            finish_reason=response_obj["choices"][0]["finish_reason"]
        )]
        mock_response.usage = MagicMock(
            prompt_tokens=response_obj["usage"]["prompt_tokens"],
            completion_tokens=response_obj["usage"]["completion_tokens"],
            total_tokens=response_obj["usage"]["total_tokens"]
        )

        mock_openai_client.chat.completions.create.return_value = mock_response

        # Create request
        request = EnhancedModelRequest(
            prompt="Test prompt",
            model_name="gpt-4o",
            provider=ModelProvider.OPENAI,
            temperature=0.7,
            max_tokens=100,
            validation_type="chain_of_thought",
            trace_id="test-trace-id"
        )

        # Test enhanced generate
        response = await openai_adapter.enhanced_generate(request)

        # Assertions
        assert response.content == "This is a test response"
        assert response.model_name == "gpt-4o"
        assert response.provider == ModelProvider.OPENAI
        assert response.prompt_tokens == 10
        assert response.completion_tokens == 20
        assert response.total_tokens == 30
        assert response.trace_id == "test-trace-id"

    @pytest.mark.asyncio
    async def test_validation_json_format(self, openai_adapter, mock_openai_client):
        """Test JSON validation"""
        # Setup mock response with valid JSON
        json_content = '{"name": "Test", "value": 123}'
        response_obj = create_mock_openai_response(content=json_content)
        mock_response = AsyncMock()
        mock_response.model_dump.return_value = response_obj
        mock_response.id = response_obj["id"]
        mock_response.created = response_obj["created"]
        mock_response.model = response_obj["model"]
        mock_response.choices = [MagicMock(
            message=MagicMock(
                content=json_content,
                model_dump=MagicMock(return_value={"content": json_content})
            ),
            finish_reason="stop"
        )]
        mock_response.usage = MagicMock(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30
        )

        mock_openai_client.chat.completions.create.return_value = mock_response

        # Create request with JSON validation
        request = EnhancedModelRequest(
            prompt="Generate JSON",
            model_name="gpt-4o",
            provider=ModelProvider.OPENAI,
            validation_type="json",
            expected_format='{"name": "", "value": 0}'
        )

        # Test enhanced generate with validation
        response = await openai_adapter.enhanced_generate(request)

        # Assertions
        assert response.content == json_content
        assert response.validation.is_valid
        assert response.validation.confidence_score > 0.9
        assert response.validation.confidence_level == ConfidenceLevel.HIGH

    @pytest.mark.asyncio
    async def test_validation_json_format_invalid(self, openai_adapter, mock_openai_client):
        """Test invalid JSON validation"""
        # Setup mock response with invalid JSON
        invalid_json = '{"name": "Test", value: 123'  # Missing quotes around value
        response_obj = create_mock_openai_response(content=invalid_json)
        mock_response = AsyncMock()
        mock_response.model_dump.return_value = response_obj
        mock_response.id = response_obj["id"]
        mock_response.created = response_obj["created"]
        mock_response.model = response_obj["model"]
        mock_response.choices = [MagicMock(
            message=MagicMock(
                content=invalid_json,
                model_dump=MagicMock(return_value={"content": invalid_json})
            ),
            finish_reason="stop"
        )]
        mock_response.usage = MagicMock(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30
        )

        mock_openai_client.chat.completions.create.return_value = mock_response

        # Create request with JSON validation
        request = EnhancedModelRequest(
            prompt="Generate JSON",
            model_name="gpt-4o",
            provider=ModelProvider.OPENAI,
            validation_type="json"
        )

        # Test enhanced generate with validation
        response = await openai_adapter.enhanced_generate(request)

        # Assertions
        assert response.content == invalid_json
        assert not response.validation.is_valid
        assert "Invalid JSON format" in response.validation.errors
        assert response.validation.confidence_score < 0.5
        assert response.validation.confidence_level == ConfidenceLevel.UNCERTAIN

    @pytest.mark.asyncio
    async def test_validation_chain_of_thought(self, openai_adapter, mock_openai_client):
        """Test chain-of-thought validation"""
        # Setup mock response with chain-of-thought reasoning
        cot_content = """
        Let's think step by step.

        Step 1: First, we need to identify the key variables in the problem.
        Step 2: Next, we can apply the formula to calculate the result.
        Step 3: Finally, we check our answer for reasonableness.

        Therefore, the answer is 42.
        """

        response_obj = create_mock_openai_response(content=cot_content)
        mock_response = AsyncMock()
        mock_response.model_dump.return_value = response_obj
        mock_response.id = response_obj["id"]
        mock_response.created = response_obj["created"]
        mock_response.model = response_obj["model"]
        mock_response.choices = [MagicMock(
            message=MagicMock(
                content=cot_content,
                model_dump=MagicMock(return_value={"content": cot_content})
            ),
            finish_reason="stop"
        )]
        mock_response.usage = MagicMock(
            prompt_tokens=15,
            completion_tokens=50,
            total_tokens=65
        )

        mock_openai_client.chat.completions.create.return_value = mock_response

        # Create request with chain-of-thought validation
        request = EnhancedModelRequest(
            prompt="Solve this problem step by step",
            model_name="gpt-4o",
            provider=ModelProvider.OPENAI,
            validation_type="chain_of_thought"
        )

        # Test enhanced generate with validation
        response = await openai_adapter.enhanced_generate(request)

        # Assertions
        assert response.content == cot_content
        assert response.validation.is_valid
        assert response.validation.confidence_score > 0.8
        assert response.validation.reasoning_quality > 0.8
        assert response.reasoning_steps is not None
        assert len(response.reasoning_steps) >= 3


# Tests for the AI orchestrator
class TestEnhancedAIOrchestrator:

    @pytest.mark.asyncio
    async def test_generate_with_caching(self, ai_orchestrator, mock_cache_client):
        """Test generation with caching"""
        # Setup mock cache hit
        cached_response = EnhancedModelResponse(
            content="Cached response",
            model_name="gpt-4o",
            usage={"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
            metadata={"cached": True},
            provider=ModelProvider.OPENAI,
            validation=ValidationResult(
                is_valid=True,
                confidence_score=0.95,
                confidence_level=ConfidenceLevel.HIGH
            )
        )

        # Configure mock cache to return the cached response
        mock_cache_client.get.return_value = json.dumps(cached_response.dict())

        # Generate with a request that should hit cache
        response = await ai_orchestrator.generate(
            prompt="Test prompt",
            model="gpt-4o"
        )

        # Assertions
        assert response.content == "Cached response"
        assert response.metadata.get("cached") is True

        # Verify cache was checked
        mock_cache_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_with_fallback(self, ai_orchestrator, openai_adapter, mock_openai_client):
        """Test generation with fallback on low confidence"""
        # Setup mock responses
        # First response has low confidence
        first_response = create_mock_openai_response(content="Low confidence response")
        first_mock = AsyncMock()
        first_mock.model_dump.return_value = first_response
        first_mock.id = first_response["id"]
        first_mock.created = first_response["created"]
        first_mock.model = first_response["model"]
        first_mock.choices = [MagicMock(
            message=MagicMock(
                content=first_response["choices"][0]["message"]["content"],
                model_dump=MagicMock(return_value=first_response["choices"][0]["message"])
            ),
            finish_reason=first_response["choices"][0]["finish_reason"]
        )]
        first_mock.usage = MagicMock(
            prompt_tokens=first_response["usage"]["prompt_tokens"],
            completion_tokens=first_response["usage"]["completion_tokens"],
            total_tokens=first_response["usage"]["total_tokens"]
        )

        # Second response has high confidence
        second_response = create_mock_openai_response(content="High confidence response")
        second_mock = AsyncMock()
        second_mock.model_dump.return_value = second_response
        second_mock.id = second_response["id"]
        second_mock.created = second_response["created"]
        second_mock.model = second_response["model"]
        second_mock.choices = [MagicMock(
            message=MagicMock(
                content=second_response["choices"][0]["message"]["content"],
                model_dump=MagicMock(return_value=second_response["choices"][0]["message"])
            ),
            finish_reason=second_response["choices"][0]["finish_reason"]
        )]
        second_mock.usage = MagicMock(
            prompt_tokens=second_response["usage"]["prompt_tokens"],
            completion_tokens=second_response["usage"]["completion_tokens"],
            total_tokens=second_response["usage"]["total_tokens"]
        )

        # Configure mock adapter behavior
        mock_openai_client.chat.completions.create.side_effect = [first_mock, second_mock]

        # Override _validate_response for the first call to return low confidence
        original_validate = openai_adapter._validate_response
        validation_results = [
            ValidationResult(
                is_valid=True,
                confidence_score=0.5,  # Low confidence
                confidence_level=ConfidenceLevel.LOW
            ),
            ValidationResult(
                is_valid=True,
                confidence_score=0.95,  # High confidence
                confidence_level=ConfidenceLevel.HIGH
            )
        ]

        async def mock_validate(*args, **kwargs):
            return validation_results.pop(0)

        with patch.object(openai_adapter, '_validate_response', side_effect=mock_validate):
            # Generate with a request that should trigger fallback
            response = await ai_orchestrator.generate(
                prompt="Test prompt",
                model="gpt-4o",
                validation_type="chain_of_thought"
            )

        # Assertions
        assert response.content == "High confidence response"
        assert response.metadata.get("attempts") == 2
        assert response.metadata.get("fallback_used") is True

        # Verify completions.create was called twice
        assert mock_openai_client.chat.completions.create.call_count == 2

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, ai_orchestrator, openai_adapter, mock_openai_client, mock_metrics_client):
        """Test metrics tracking"""
        # Setup mock response
        response_obj = create_mock_openai_response()
        mock_response = AsyncMock()
        mock_response.model_dump.return_value = response_obj
        mock_response.id = response_obj["id"]
        mock_response.created = response_obj["created"]
        mock_response.model = response_obj["model"]
        mock_response.choices = [MagicMock(
            message=MagicMock(
                content=response_obj["choices"][0]["message"]["content"],
                model_dump=MagicMock(return_value=response_obj["choices"][0]["message"])
            ),
            finish_reason=response_obj["choices"][0]["finish_reason"]
        )]
        mock_response.usage = MagicMock(
            prompt_tokens=response_obj["usage"]["prompt_tokens"],
            completion_tokens=response_obj["usage"]["completion_tokens"],
            total_tokens=response_obj["usage"]["total_tokens"]
        )

        mock_openai_client.chat.completions.create.return_value = mock_response

        # Generate response
        response = await ai_orchestrator.generate(
            prompt="Test prompt",
            model="gpt-4o"
        )

        # Get metrics
        metrics = await ai_orchestrator.get_metrics(limit=1)

        # Assertions
        assert len(metrics) == 1
        assert metrics[0]["model"] == "gpt-4o"
        assert metrics[0]["provider"] == ModelProvider.OPENAI
        assert metrics[0]["total_tokens"] == 30
        assert "latency_ms" in metrics[0]

        # Verify metrics client was called
        if ai_orchestrator.config.metrics.export_metrics:
            mock_metrics_client.send_metrics.assert_called_once()
