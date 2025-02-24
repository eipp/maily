"""Base adapter interface for language models."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

from ..errors import ModelError

class BaseModelAdapter(ABC):
    """Abstract base class for model adapters."""
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get the name of the model."""
        pass
        
    @property
    @abstractmethod
    def model_type(self) -> str:
        """Get the type of the model (e.g., 'language_model', 'embedding_model')."""
        pass
        
    @property
    @abstractmethod
    def endpoint(self) -> str:
        """Get the endpoint where the model is hosted."""
        pass
        
    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_length: int = 200,
        temperature: float = 0.7,
        **kwargs: Dict[str, Any]
    ) -> Optional[str]:
        """
        Generate text using the model.
        
        Args:
            prompt: Input text
            max_length: Maximum length of generated text
            temperature: Sampling temperature
            **kwargs: Additional model-specific parameters
            
        Returns:
            Generated text or None if generation fails
        """
        pass
        
    @abstractmethod
    def batch_generate(
        self,
        prompts: List[str],
        max_length: int = 200,
        temperature: float = 0.7,
        **kwargs: Dict[str, Any]
    ) -> List[Optional[str]]:
        """
        Generate text for multiple prompts in batch.
        
        Args:
            prompts: List of input texts
            max_length: Maximum length of generated text
            temperature: Sampling temperature
            **kwargs: Additional model-specific parameters
            
        Returns:
            List of generated texts (None for failed generations)
        """
        pass
        
    @abstractmethod
    def get_model_config(self) -> Dict[str, Any]:
        """
        Get model configuration for registration with monitoring systems.
        
        Returns:
            Dictionary containing model configuration
        """
        pass
        
    def validate_response(self, response: Optional[str]) -> Optional[str]:
        """
        Validate and clean up model response.
        
        Args:
            response: Raw model response
            
        Returns:
            Validated and cleaned response
        """
        if response is None:
            return None
            
        # Remove any obvious error patterns
        if "error" in response.lower() or "exception" in response.lower():
            return None
            
        # Remove any empty or whitespace-only responses
        cleaned = response.strip()
        if not cleaned:
            return None
            
        return cleaned 