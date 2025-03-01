from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, AsyncIterator, TypeVar, Generic
from pydantic import BaseModel, Field, validator


class ModelResponse(BaseModel):
    """Standardized model response format."""
    content: str
    model_name: str
    usage: Dict[str, int] = Field(default_factory=dict)
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        frozen = True  # Make the model immutable for better thread safety


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
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        frozen = True  # Make the model immutable for better thread safety

    @validator('temperature')
    def validate_temperature(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Temperature must be between 0 and 1')
        return v

    # Additional validators could be added for other fields as needed

class BaseModelAdapter(ABC):
    """
    Base adapter interface for AI model integrations.

    This abstract class defines the contract that all model adapters must implement,
    ensuring consistent interaction with different AI models regardless of their
    underlying API differences.
    """

    @abstractmethod
    async def generate(self, request: ModelRequest) -> ModelResponse:
        """
        Generate a response from the AI model.

        Args:
            request: A standardized ModelRequest object containing the prompt and parameters.

        Returns:
            A standardized ModelResponse object containing the generated content and metadata.
        """
        pass

    @abstractmethod
    async def stream_generate(self, request: ModelRequest) -> AsyncIterator[ModelResponse]:
        """
        Stream a response from the AI model.

        Args:
            request: A standardized ModelRequest object containing the prompt and parameters.

        Returns:
            An async iterator yielding ModelResponse objects as content is generated.
        """
        pass

    @abstractmethod
    async def embed(self, text: Union[str, List[str]]) -> List[List[float]]:
        """
        Generate embeddings for the provided text.

        Args:
            text: A string or list of strings to generate embeddings for.

        Returns:
            A list of embedding vectors (lists of floats).
        """
        pass

    @abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """
        Check the health of the model service.

        Returns:
            A dictionary containing health status information.
        """
        pass

    @abstractmethod
    async def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model.

        Returns:
            A dictionary containing model information.
        """
        pass

# T is defined inline for clarity
T = TypeVar('T')
