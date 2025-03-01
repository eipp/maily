import os
import logging
from typing import Dict, List, Optional, Any, Union, AsyncIterator
import anthropic
from anthropic import AsyncAnthropic
from pydantic import BaseModel

from .base import BaseModelAdapter, ModelRequest, ModelResponse

logger = logging.getLogger(__name__)


class AnthropicAdapter(BaseModelAdapter):
    """
    Adapter for Anthropic Claude models.

    This adapter implements the BaseModelAdapter interface for Anthropic models,
    providing a standardized way to interact with Anthropic's API.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Anthropic adapter.

        Args:
            api_key: Anthropic API key. If not provided, will use ANTHROPIC_API_KEY environment variable.
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.warning("No Anthropic API key provided. Set ANTHROPIC_API_KEY environment variable.")

        self.client = AsyncAnthropic(api_key=self.api_key)
        self.available_models = [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-3.5-sonnet-20240620",
            "claude-3-5-sonnet-20240620"
        ]

    async def generate(self, request: ModelRequest) -> ModelResponse:
        """
        Generate a response from an Anthropic model.

        Args:
            request: A standardized ModelRequest object.

        Returns:
            A standardized ModelResponse object.
        """
        try:
            response = await self.client.messages.create(
                model=request.model_name,
                messages=[{"role": "user", "content": request.prompt}],
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                stop_sequences=request.stop_sequences
            )

            # Extract the content from the response
            content = response.content[0].text

            # Create a standardized response
            return ModelResponse(
                content=content,
                model_name=request.model_name,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                },
                finish_reason=response.stop_reason,
                metadata=request.metadata
            )
        except Exception as e:
            logger.error(f"Error generating response from Anthropic: {str(e)}")
            raise

    async def stream_generate(self, request: ModelRequest) -> AsyncIterator[ModelResponse]:
        """
        Stream a response from an Anthropic model.

        Args:
            request: A standardized ModelRequest object.

        Returns:
            An async iterator yielding ModelResponse objects.
        """
        try:
            stream = await self.client.messages.create(
                model=request.model_name,
                messages=[{"role": "user", "content": request.prompt}],
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                stop_sequences=request.stop_sequences,
                stream=True
            )

            class ResponseIterator:
                def __init__(self, stream, model_name, metadata):
                    self.stream = stream
                    self.model_name = model_name
                    self.metadata = metadata

                def __aiter__(self):
                    return self

                async def __anext__(self):
                    try:
                        chunk = await self.stream.__anext__()

                        # Check if this is a content delta
                        if not hasattr(chunk, 'delta') or not chunk.delta.text:
                            # This is a non-content message (like a stop reason)
                            # Return an empty content response with the finish reason
                            return ModelResponse(
                                content="",
                                model_name=self.model_name,
                                usage={"total_tokens": 0},
                                finish_reason=getattr(chunk, 'stop_reason', None),
                                metadata=self.metadata
                            )

                        # This is a content delta
                        return ModelResponse(
                            content=chunk.delta.text,
                            model_name=self.model_name,
                            usage={"total_tokens": 0},  # Updated at the end
                            finish_reason=None,
                            metadata=self.metadata
                        )
                    except StopAsyncIteration:
                        raise
                    except Exception as e:
                        logger.error(f"Error streaming response from Anthropic: {str(e)}")
                        raise

            return ResponseIterator(stream, request.model_name, request.metadata)
        except Exception as e:
            logger.error(f"Error setting up stream from Anthropic: {str(e)}")
            raise

    async def embed(self, text: Union[str, List[str]]) -> List[List[float]]:
        """
        Generate embeddings for the provided text using Anthropic.

        Args:
            text: A string or list of strings to generate embeddings for.

        Returns:
            A list of embedding vectors.
        """
        try:
            # Ensure text is a list
            if isinstance(text, str):
                text = [text]

            # Anthropic doesn't have a dedicated embeddings API yet
            # This is a placeholder for when they do
            logger.warning("Anthropic embeddings API not available. Using fallback method.")

            # Return empty embeddings as a placeholder
            # In a real implementation, you might want to use a different provider for embeddings
            return [[0.0] * 1536 for _ in text]
        except Exception as e:
            logger.error(f"Error generating embeddings from Anthropic: {str(e)}")
            raise

    async def check_health(self) -> Dict[str, Any]:
        """
        Check the health of the Anthropic service.

        Returns:
            A dictionary containing health status information.
        """
        try:
            # Simple health check by making a minimal API call
            response = await self.client.messages.create(
                model="claude-3-haiku-20240307",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return {
                "status": "healthy",
                "available_models": len(self.available_models),
                "timestamp": response.id
            }
        except Exception as e:
            logger.error(f"Anthropic health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about available Anthropic models.

        Returns:
            A dictionary containing model information.
        """
        try:
            # Anthropic doesn't have a models.list() endpoint like OpenAI
            # Return the hardcoded list of models
            return {
                "models": self.available_models,
                "count": len(self.available_models),
                "timestamp": None
            }
        except Exception as e:
            logger.error(f"Error getting Anthropic model info: {str(e)}")
            return {
                "error": str(e)
            }
