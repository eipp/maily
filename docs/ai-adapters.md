# AI Adapters Documentation

## Overview

The AI adapters in Maily implement the hexagonal architecture pattern to provide a consistent interface for interacting with various AI model providers. This document provides a comprehensive guide to the AI adapter implementation, including code examples and usage patterns.

## Architecture

The AI adapter architecture consists of the following components:

1. **Base Adapter Interface**: Defines the contract that all model adapters must implement
2. **Concrete Adapters**: Implementations for specific AI providers (OpenAI, Anthropic, Google)
3. **Adapter Factory**: Creates and manages adapter instances
4. **Standardized Request/Response Models**: Consistent data models for all adapters

### Component Diagram

```
┌─────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│                 │     │                   │     │                   │
│  Domain Logic   │────▶│  Adapter Factory  │────▶│  Base Adapter     │
│                 │     │                   │     │  Interface        │
└─────────────────┘     └───────────────────┘     └───────────────────┘
                                                          ▲
                                                          │
                         ┌────────────────────────────────┼────────────────────────────┐
                         │                                │                            │
                         │                                │                            │
                ┌────────┴─────────┐           ┌─────────┴──────────┐        ┌────────┴─────────┐
                │                  │           │                    │        │                  │
                │  OpenAI Adapter  │           │ Anthropic Adapter  │        │  Google Adapter  │
                │                  │           │                    │        │                  │
                └──────────────────┘           └────────────────────┘        └──────────────────┘
```

## Base Adapter Interface

The `BaseModelAdapter` abstract class defines the contract that all model adapters must implement:

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, AsyncIterator
from pydantic import BaseModel

class ModelResponse(BaseModel):
    """Standardized model response format."""
    content: str
    model_name: str
    usage: Dict[str, int]
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = {}

class ModelRequest(BaseModel):
    """Standardized model request format."""
    prompt: str
    model_name: str
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: Optional[List[str]] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = {}

class BaseModelAdapter(ABC):
    """
    Base adapter interface for AI model integrations.
    """

    @abstractmethod
    async def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a response from the AI model."""
        pass

    @abstractmethod
    async def stream_generate(self, request: ModelRequest) -> AsyncIterator[ModelResponse]:
        """Stream a response from the AI model."""
        pass

    @abstractmethod
    async def embed(self, text: Union[str, List[str]]) -> List[List[float]]:
        """Generate embeddings for the provided text."""
        pass

    @abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """Check the health of the model service."""
        pass

    @abstractmethod
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model."""
        pass
```

## Concrete Adapter Implementations

### OpenAI Adapter

The `OpenAIAdapter` class implements the `BaseModelAdapter` interface for OpenAI models:

```python
import os
import logging
from typing import Dict, List, Optional, Any, Union, AsyncIterator
import openai
from openai import AsyncOpenAI

from .base import BaseModelAdapter, ModelRequest, ModelResponse

class OpenAIAdapter(BaseModelAdapter):
    """Adapter for OpenAI models."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the OpenAI adapter."""
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model_info_cache = {}

    async def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a response from an OpenAI model."""
        try:
            response = await self.client.chat.completions.create(
                model=request.model_name,
                messages=[{"role": "user", "content": request.prompt}],
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                frequency_penalty=request.frequency_penalty,
                presence_penalty=request.presence_penalty,
                stop=request.stop_sequences,
                user=request.user_id
            )

            return ModelResponse(
                content=response.choices[0].message.content,
                model_name=request.model_name,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                finish_reason=response.choices[0].finish_reason,
                metadata=request.metadata
            )
        except Exception as e:
            logging.error(f"Error generating response from OpenAI: {e}")
            raise
```

### Anthropic Adapter

The `AnthropicAdapter` class implements the `BaseModelAdapter` interface for Anthropic models:

```python
import os
import logging
from typing import Dict, List, Optional, Any, Union, AsyncIterator
import anthropic
from anthropic import AsyncAnthropic

from .base import BaseModelAdapter, ModelRequest, ModelResponse

class AnthropicAdapter(BaseModelAdapter):
    """Adapter for Anthropic models."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Anthropic adapter."""
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.client = AsyncAnthropic(api_key=self.api_key)
        self.model_info_cache = {}

    async def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a response from an Anthropic model."""
        try:
            response = await self.client.messages.create(
                model=request.model_name,
                messages=[{"role": "user", "content": request.prompt}],
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                stop_sequences=request.stop_sequences
            )

            # Anthropic doesn't provide token usage in the same way as OpenAI
            # We estimate it based on the input and output length
            prompt_tokens = len(request.prompt) // 4  # Rough estimate
            completion_tokens = len(response.content[0].text) // 4  # Rough estimate

            return ModelResponse(
                content=response.content[0].text,
                model_name=request.model_name,
                usage={
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens
                },
                finish_reason=response.stop_reason,
                metadata=request.metadata
            )
        except Exception as e:
            logging.error(f"Error generating response from Anthropic: {e}")
            raise
```

## Adapter Factory

The `ModelAdapterFactory` class creates and manages adapter instances:

```python
from typing import Dict, Optional, Type

from .base import BaseModelAdapter
from .openai_adapter import OpenAIAdapter
from .anthropic_adapter import AnthropicAdapter
from .google_adapter import GoogleAIAdapter

class ModelAdapterFactory:
    """Factory class for creating and managing model adapters."""

    def __init__(self):
        """Initialize the factory with empty adapter registry."""
        self._adapters: Dict[str, BaseModelAdapter] = {}
        self._adapter_classes: Dict[str, Type[BaseModelAdapter]] = {
            "openai": OpenAIAdapter,
            "anthropic": AnthropicAdapter,
            "google": GoogleAIAdapter,
        }

    def register_adapter_class(self, provider: str, adapter_class: Type[BaseModelAdapter]) -> None:
        """Register a new adapter class for a provider."""
        self._adapter_classes[provider] = adapter_class

    def get_adapter(self, provider: str, api_key: Optional[str] = None) -> BaseModelAdapter:
        """Get an adapter instance for the specified provider."""
        # Check if we already have an adapter for this provider
        if provider in self._adapters:
            return self._adapters[provider]

        # Check if we have a registered adapter class for this provider
        if provider not in self._adapter_classes:
            raise ValueError(f"Unsupported provider: {provider}")

        # Create a new adapter instance
        adapter_class = self._adapter_classes[provider]
        adapter = adapter_class(api_key=api_key)

        # Store the adapter for future use
        self._adapters[provider] = adapter

        return adapter

    def get_adapter_for_model(self, model_name: str, api_key: Optional[str] = None) -> BaseModelAdapter:
        """Get an adapter instance for the specified model."""
        # Determine the provider based on the model name
        if model_name.startswith(("gpt-", "text-embedding-")):
            return self.get_adapter("openai", api_key)
        elif model_name.startswith("claude-"):
            return self.get_adapter("anthropic", api_key)
        elif model_name.startswith("gemini-"):
            return self.get_adapter("google", api_key)
        else:
            raise ValueError(f"Unsupported model: {model_name}")

# Create a singleton instance of the factory
model_adapter_factory = ModelAdapterFactory()
```

## Usage Examples

### Basic Usage

```python
from apps.api.ai.adapters import model_adapter_factory
from apps.api.ai.adapters.base import ModelRequest

async def generate_email_content(prompt: str, model_name: str = "gpt-4"):
    """Generate email content using an AI model."""
    # Create a standardized request
    request = ModelRequest(
        prompt=prompt,
        model_name=model_name,
        temperature=0.7,
        max_tokens=1000
    )

    # Get the appropriate adapter for the model
    adapter = model_adapter_factory.get_adapter_for_model(model_name)

    # Generate the response
    response = await adapter.generate(request)

    # Return the generated content
    return response.content
```

### Streaming Example

```python
from apps.api.ai.adapters import model_adapter_factory
from apps.api.ai.adapters.base import ModelRequest
from fastapi import WebSocket

async def stream_response(websocket: WebSocket, prompt: str, model_name: str = "gpt-4"):
    """Stream a response to a WebSocket connection."""
    # Create a standardized request
    request = ModelRequest(
        prompt=prompt,
        model_name=model_name,
        temperature=0.7,
        max_tokens=1000
    )

    # Get the appropriate adapter for the model
    adapter = model_adapter_factory.get_adapter_for_model(model_name)

    # Stream the response
    async for chunk in await adapter.stream_generate(request):
        await websocket.send_text(chunk.content)
```

### Embedding Example

```python
from apps.api.ai.adapters import model_adapter_factory

async def get_embeddings(texts: list[str], model_name: str = "text-embedding-ada-002"):
    """Get embeddings for a list of texts."""
    # Get the appropriate adapter for the model
    adapter = model_adapter_factory.get_adapter_for_model(model_name)

    # Generate embeddings
    embeddings = await adapter.embed(texts)

    return embeddings
```

## Adding a New Adapter

To add support for a new AI provider, follow these steps:

1. Create a new adapter class that implements the `BaseModelAdapter` interface:

```python
from .base import BaseModelAdapter, ModelRequest, ModelResponse

class NewProviderAdapter(BaseModelAdapter):
    """Adapter for NewProvider models."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the NewProvider adapter."""
        self.api_key = api_key or os.environ.get("NEW_PROVIDER_API_KEY")
        self.client = NewProviderClient(api_key=self.api_key)

    async def generate(self, request: ModelRequest) -> ModelResponse:
        """Generate a response from a NewProvider model."""
        # Implementation for the new provider
        pass

    # Implement other required methods...
```

2. Register the new adapter with the factory:

```python
from .new_provider_adapter import NewProviderAdapter

# Register the new adapter
model_adapter_factory.register_adapter_class("new_provider", NewProviderAdapter)

# Update the model name mapping
def get_adapter_for_model(self, model_name: str, api_key: Optional[str] = None) -> BaseModelAdapter:
    # Add support for the new provider's model naming convention
    if model_name.startswith("new-provider-"):
        return self.get_adapter("new_provider", api_key)
    # Existing mappings...
```

## Testing Adapters

Each adapter should have comprehensive tests to ensure it correctly implements the interface:

```python
import pytest
from unittest.mock import AsyncMock, patch

from apps.api.ai.adapters.base import ModelRequest
from apps.api.ai.adapters.openai_adapter import OpenAIAdapter

@pytest.mark.asyncio
async def test_openai_adapter_generate():
    # Create a mock OpenAI client
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock()]
    mock_response.choices[0].message.content = "Test response"
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 20
    mock_response.usage.total_tokens = 30
    mock_client.chat.completions.create.return_value = mock_response

    # Create the adapter with the mock client
    adapter = OpenAIAdapter(api_key="test_key")
    adapter.client = mock_client

    # Create a test request
    request = ModelRequest(
        prompt="Test prompt",
        model_name="gpt-4",
        temperature=0.7,
        max_tokens=1000
    )

    # Generate a response
    response = await adapter.generate(request)

    # Verify the response
    assert response.content == "Test response"
    assert response.model_name == "gpt-4"
    assert response.usage["prompt_tokens"] == 10
    assert response.usage["completion_tokens"] == 20
    assert response.usage["total_tokens"] == 30
    assert response.finish_reason == "stop"

    # Verify the client was called with the correct parameters
    mock_client.chat.completions.create.assert_called_once_with(
        model="gpt-4",
        messages=[{"role": "user", "content": "Test prompt"}],
        temperature=0.7,
        max_tokens=1000,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        stop=None,
        user=None
    )
```

## Error Handling

The adapters include robust error handling to ensure that errors from the underlying APIs are properly captured and reported:

```python
async def generate(self, request: ModelRequest) -> ModelResponse:
    """Generate a response from an AI model."""
    try:
        # Call the underlying API
        # ...
    except Exception as e:
        logging.error(f"Error generating response: {e}")
        # Determine the type of error
        if isinstance(e, openai.RateLimitError):
            raise RateLimitExceededError(f"Rate limit exceeded: {e}")
        elif isinstance(e, openai.AuthenticationError):
            raise AuthenticationError(f"Authentication failed: {e}")
        elif isinstance(e, openai.APIConnectionError):
            raise ConnectionError(f"API connection error: {e}")
        else:
            raise ModelGenerationError(f"Error generating response: {e}")
```

## Performance Considerations

The adapter implementation includes several performance optimizations:

1. **Singleton Factory**: The factory is implemented as a singleton to avoid creating multiple instances
2. **Adapter Caching**: Adapters are cached in the factory to avoid creating multiple instances
3. **Model Info Caching**: Model information is cached to avoid repeated API calls
4. **Connection Pooling**: The underlying HTTP clients use connection pooling for better performance

## Conclusion

The AI adapter implementation in Maily provides a flexible and extensible way to interact with various AI model providers. By following the hexagonal architecture pattern, the implementation ensures that the core business logic is isolated from the details of specific AI providers, making it easy to add support for new providers or switch between providers as needed.
