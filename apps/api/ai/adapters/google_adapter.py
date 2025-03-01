import os
import logging
from typing import Dict, List, Optional, Any, Union, AsyncIterator
import google.generativeai as genai
from pydantic import BaseModel

from .base import BaseModelAdapter, ModelRequest, ModelResponse

logger = logging.getLogger(__name__)


class GoogleAIAdapter(BaseModelAdapter):
    """
    Adapter for Google AI models (Gemini).

    This adapter implements the BaseModelAdapter interface for Google AI models,
    providing a standardized way to interact with Google's Generative AI API.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Google AI adapter.

        Args:
            api_key: Google AI API key. If not provided, will use GOOGLE_API_KEY environment variable.
        """
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            logger.warning("No Google AI API key provided. Set GOOGLE_API_KEY environment variable.")

        # Configure the Google AI client
        genai.configure(api_key=self.api_key)

        # Define available models
        self.available_models = [
            "gemini-1.0-pro",
            "gemini-1.0-pro-vision",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "embedding-001"
        ]

        # Cache for model info
        self.model_info_cache = {}

    async def generate(self, request: ModelRequest) -> ModelResponse:
        """
        Generate a response from a Google AI model.

        Args:
            request: A standardized ModelRequest object.

        Returns:
            A standardized ModelResponse object.
        """
        try:
            # Select the model
            model = genai.GenerativeModel(request.model_name)

            # Generate content
            response = await model.generate_content_async(
                request.prompt,
                generation_config={
                    "temperature": request.temperature,
                    "max_output_tokens": request.max_tokens,
                    "top_p": request.top_p
                }
            )

            # Extract the content from the response
            content = response.text

            # Create a standardized response
            return ModelResponse(
                content=content,
                model_name=request.model_name,
                usage={
                    "input_tokens": response.usage.prompt_token_count,
                    "output_tokens": response.usage.candidates_token_count,
                    "total_tokens": response.usage.total_token_count
                },
                finish_reason="stop",  # Google AI doesn't provide specific finish reasons
                metadata=request.metadata
            )
        except Exception as e:
            logger.error(f"Error generating response from Google AI: {str(e)}")
            raise

    async def stream_generate(self, request: ModelRequest) -> AsyncIterator[ModelResponse]:
        """
        Stream a response from a Google AI model.

        Args:
            request: A standardized ModelRequest object.

        Returns:
            An async iterator yielding ModelResponse objects.
        """
        try:
            # Select the model
            model = genai.GenerativeModel(request.model_name)

            # Generate content with streaming
            stream = await model.generate_content_async(
                request.prompt,
                generation_config={
                    "temperature": request.temperature,
                    "max_output_tokens": request.max_tokens,
                    "top_p": request.top_p
                },
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

                        # Check if this is a content chunk
                        if not hasattr(chunk, 'text') or not chunk.text:
                            # This is a non-content message
                            # Return an empty content response
                            return ModelResponse(
                                content="",
                                model_name=self.model_name,
                                usage={"total_tokens": 0},
                                finish_reason=None,
                                metadata=self.metadata
                            )

                        # This is a content chunk
                        return ModelResponse(
                            content=chunk.text,
                            model_name=self.model_name,
                            usage={"total_tokens": 0},  # Updated at the end
                            finish_reason=None,
                            metadata=self.metadata
                        )
                    except StopAsyncIteration:
                        raise
                    except Exception as e:
                        logger.error(f"Error streaming response from Google AI: {str(e)}")
                        raise

            return ResponseIterator(stream, request.model_name, request.metadata)
        except Exception as e:
            logger.error(f"Error setting up stream from Google AI: {str(e)}")
            raise

    async def embed(self, text: Union[str, List[str]]) -> List[List[float]]:
        """
        Generate embeddings for the provided text using Google AI.

        Args:
            text: A string or list of strings to generate embeddings for.

        Returns:
            A list of embedding vectors.
        """
        try:
            # Ensure text is a list
            if isinstance(text, str):
                text = [text]

            # Initialize embedding model
            embedding_model = "embedding-001"

            # Generate embeddings for each text
            embeddings = []
            for t in text:
                result = await genai.embed_content_async(
                    model=embedding_model,
                    content=t,
                    task_type="retrieval_document"
                )
                embeddings.append(result.embedding)

            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings from Google AI: {str(e)}")
            raise

    async def check_health(self) -> Dict[str, Any]:
        """
        Check the health of the Google AI service.

        Returns:
            A dictionary containing health status information.
        """
        try:
            # Simple health check by making a minimal API call
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = await model.generate_content_async("Hello")

            return {
                "status": "healthy",
                "available_models": len(self.available_models),
                "timestamp": str(response.usage.total_token_count)
            }
        except Exception as e:
            logger.error(f"Google AI health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about available Google AI models.

        Returns:
            A dictionary containing model information.
        """
        try:
            # Google AI doesn't have a models.list() endpoint like OpenAI
            # Return the hardcoded list of models
            return {
                "models": self.available_models,
                "count": len(self.available_models),
                "timestamp": None
            }
        except Exception as e:
            logger.error(f"Error getting Google AI model info: {str(e)}")
            return {
                "error": str(e)
            }
