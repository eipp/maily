import pytest

from ....models import MODEL_REGISTRY, ModelAdapter, ModelInitializationError


def test_model_registry_contents():
    """Test that model registry contains all required models."""
    expected_models = {
        "mock",
        "openai",
        "anthropic",
        "google",
        "xai",
        "replicate",
        "together",
        "huggingface",
        "fireworks",
    }
    assert set(MODEL_REGISTRY.keys()) == expected_models


def test_model_registry_types():
    """Test that all registered models inherit from ModelAdapter."""
    for model_class in MODEL_REGISTRY.values():
        assert issubclass(model_class, ModelAdapter)


def test_model_initialization():
    """Test model initialization with invalid API key."""
    for model_name, model_class in MODEL_REGISTRY.items():
        if model_name == "mock":
            continue  # Skip mock adapter as it doesn't validate API key
        with pytest.raises(ModelInitializationError):
            model_class("invalid-api-key")
