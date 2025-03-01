"""
AI Model Adapters Package

This package provides a standardized interface for interacting with various AI models
through the adapter pattern. It includes adapters for different AI providers and a
factory for creating and managing these adapters.

Available adapters:
- OpenAIAdapter: Adapter for OpenAI models (GPT-4, etc.)
- AnthropicAdapter: Adapter for Anthropic models (Claude, etc.)
- GoogleAIAdapter: Adapter for Google AI models (Gemini, etc.)

Usage:
```python
from apps.api.ai.adapters import model_adapter_factory
from apps.api.ai.adapters.base import ModelRequest

# Get an adapter for a specific provider
openai_adapter = model_adapter_factory.get_adapter("openai")

# Or get an adapter based on the model name
adapter = model_adapter_factory.get_adapter_for_model("gpt-4")

# Create a request
request = ModelRequest(
    prompt="Hello, world!",
    model_name="gpt-4",
    temperature=0.7,
    max_tokens=100
)

# Generate a response
response = await adapter.generate(request)
print(response.content)
```
"""

from .base import BaseModelAdapter, ModelRequest, ModelResponse
from .factory import model_adapter_factory
from .openai_adapter import OpenAIAdapter
from .anthropic_adapter import AnthropicAdapter
from .google_adapter import GoogleAIAdapter

__all__ = [
    "BaseModelAdapter",
    "ModelRequest",
    "ModelResponse",
    "model_adapter_factory",
    "OpenAIAdapter",
    "AnthropicAdapter",
    "GoogleAIAdapter",
]
