from .base import ModelAdapter, ModelError, ModelInitializationError, ModelGenerationError
from .openai_adapter import OpenAIAdapter
from .mock_adapter import MockAdapter
from .replicate_adapter import ReplicateAdapter
from .together_adapter import TogetherAIAdapter
from .anthropic_adapter import AnthropicAdapter
from .huggingface_adapter import HuggingFaceAdapter
from .fireworks_adapter import FireworksAdapter
from .xai_adapter import XAIAdapter
from .google_adapter import GoogleAdapter

MODEL_REGISTRY = {
    "mock": MockAdapter,
    "openai": OpenAIAdapter,
    "anthropic": AnthropicAdapter,
    "google": GoogleAdapter,
    "xai": XAIAdapter,
    "replicate": ReplicateAdapter,
    "together": TogetherAIAdapter,
    "huggingface": HuggingFaceAdapter,
    "fireworks": FireworksAdapter,
}

__all__ = [
    'ModelAdapter',
    'ModelError',
    'ModelInitializationError',
    'ModelGenerationError',
    'OpenAIAdapter',
    'MockAdapter',
    'ReplicateAdapter',
    'TogetherAIAdapter',
    'AnthropicAdapter',
    'HuggingFaceAdapter',
    'FireworksAdapter',
    'XAIAdapter',
    'GoogleAdapter',
    'MODEL_REGISTRY'
] 