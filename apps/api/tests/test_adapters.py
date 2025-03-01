"""Unit tests for model adapters."""

import re
from typing import Any, Dict

import pytest

from backend.ai.adapters import (
    ClaudeAdapter,
    GeminiAdapter,
    ModelFactory,
    OpenAIAdapter,
    R11776Adapter,
)
from backend.ai.errors import ModelError


def test_model_factory_registration():
    """Test model adapter registration."""
    # Get initial adapter count
    initial_count = len(ModelFactory._adapters)

    # Create a test adapter
    class TestAdapter(R11776Adapter):
        pass

    # Register new adapter
    ModelFactory.register_adapter("test-model", TestAdapter)

    # Verify registration
    assert len(ModelFactory._adapters) == initial_count + 1
    assert "test-model" in ModelFactory._adapters
    assert ModelFactory._adapters["test-model"] == TestAdapter


def test_model_factory_invalid_model():
    """Test error handling for invalid model names."""
    with pytest.raises(ModelError):
        ModelFactory.create_adapter("non-existent-model")


def test_adapter_initialization(mock_env):
    """Test initialization of all adapters."""
    adapters = {
        "r1-1776": R11776Adapter,
        "gpt-4": OpenAIAdapter,
        "gemini-pro": GeminiAdapter,
        "claude-3-opus": ClaudeAdapter,
    }

    for model_name, adapter_class in adapters.items():
        adapter = ModelFactory.create_adapter(model_name)
        assert isinstance(adapter, adapter_class)
        assert adapter.model_name == model_name
        assert adapter.model_type == "language_model"


def test_adapter_generation(mock_env, test_prompts):
    """Test text generation with all adapters."""
    adapters = [
        ("r1-1776", R11776Adapter()),
        ("gpt-4", OpenAIAdapter()),
        ("gemini-pro", GeminiAdapter()),
        ("claude-3-opus", ClaudeAdapter()),
    ]

    for model_name, adapter in adapters:
        # Test single generation
        response = adapter.generate(test_prompts["email_subject"]["prompt"])
        assert isinstance(response, str)
        assert len(response) > 0

        # Test batch generation
        prompts = [
            test_prompts["email_subject"]["prompt"],
            test_prompts["email_body"]["prompt"],
        ]
        responses = adapter.batch_generate(prompts)
        assert len(responses) == len(prompts)
        assert all(isinstance(r, str) for r in responses)


def test_response_validation():
    """Test response validation logic."""
    adapter = R11776Adapter()  # Use any adapter for validation testing

    # Test valid responses
    assert adapter.validate_response("Valid response") == "Valid response"
    assert adapter.validate_response(" Padded response ") == "Padded response"

    # Test invalid responses
    assert adapter.validate_response(None) is None
    assert adapter.validate_response("") is None
    assert adapter.validate_response(" ") is None
    assert adapter.validate_response("Error: Something went wrong") is None


def test_model_config():
    """Test model configuration retrieval."""
    adapters = [R11776Adapter(), OpenAIAdapter(), GeminiAdapter(), ClaudeAdapter()]

    required_fields = {
        "name",
        "type",
        "endpoint",
        "capabilities",
        "max_tokens",
        "input_schema",
    }

    for adapter in adapters:
        config = adapter.get_model_config()

        # Check required fields
        assert all(field in config for field in required_fields)

        # Check input schema
        schema = config["input_schema"]
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "prompt" in schema["properties"]


def test_adapter_error_handling(mock_env):
    """Test error handling in adapters."""
    adapters = [R11776Adapter(), OpenAIAdapter(), GeminiAdapter(), ClaudeAdapter()]

    # Test with invalid prompts
    invalid_prompts = [None, "", " ", "a" * 100000]  # Very long prompt

    for adapter in adapters:
        for prompt in invalid_prompts:
            response = adapter.generate(prompt)
            assert response is None


def test_response_patterns(mock_env, test_prompts):
    """Test if responses match expected patterns."""
    adapter = OpenAIAdapter()  # Use any adapter

    # Test email subject generation
    subject = adapter.generate(test_prompts["email_subject"]["prompt"])
    if subject:  # Skip if generation failed
        patterns = test_prompts["email_subject"]["patterns"]
        assert any(re.search(pattern, subject, re.IGNORECASE) for pattern in patterns)

    # Test email body generation
    body = adapter.generate(test_prompts["email_body"]["prompt"])
    if body:  # Skip if generation failed
        patterns = test_prompts["email_body"]["patterns"]
        assert any(re.search(pattern, body, re.IGNORECASE) for pattern in patterns)
