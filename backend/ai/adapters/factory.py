"""Factory for creating model adapters."""

from typing import Optional, Dict, Any, Type
from loguru import logger

from .base import BaseModelAdapter
from .r1_1776 import R11776Adapter
from .openai import OpenAIAdapter
from .google import GeminiAdapter
from .anthropic import ClaudeAdapter
from ..errors import ModelError

class ModelFactory:
    """Factory for creating model adapters."""
    
    # Registry of available model adapters
    _adapters: Dict[str, Type[BaseModelAdapter]] = {
        # Local models
        "r1-1776": R11776Adapter,
        
        # OpenAI models
        "gpt-4": OpenAIAdapter,
        "gpt-3.5-turbo": OpenAIAdapter,
        
        # Google models
        "gemini-pro": GeminiAdapter,
        "gemini-pro-vision": GeminiAdapter,
        
        # Anthropic models
        "claude-3-opus": ClaudeAdapter,
        "claude-3-sonnet": ClaudeAdapter,
        "claude-3-haiku": ClaudeAdapter,
        "claude-2.1": ClaudeAdapter
    }
    
    @classmethod
    def register_adapter(
        cls,
        model_name: str,
        adapter_class: Type[BaseModelAdapter]
    ) -> None:
        """
        Register a new model adapter.
        
        Args:
            model_name: Name of the model
            adapter_class: Adapter class to register
        """
        cls._adapters[model_name] = adapter_class
        logger.info(f"Registered adapter for model: {model_name}")
        
    @classmethod
    def create_adapter(
        cls,
        model_name: str,
        **kwargs: Dict[str, Any]
    ) -> BaseModelAdapter:
        """
        Create a model adapter instance.
        
        Args:
            model_name: Name of the model to create adapter for
            **kwargs: Additional configuration parameters
            
        Returns:
            Model adapter instance
            
        Raises:
            ModelError: If model adapter is not found
        """
        try:
            # Get the adapter class
            if model_name not in cls._adapters:
                raise ModelError(f"No adapter found for model: {model_name}")
                
            adapter_class = cls._adapters[model_name]
            
            # Create and return the adapter instance
            adapter = adapter_class(
                model_name=model_name,
                **kwargs
            )
            
            logger.info(f"Created adapter for model: {model_name}")
            return adapter
            
        except Exception as e:
            logger.error(f"Failed to create adapter for {model_name}: {str(e)}")
            raise ModelError(f"Adapter creation failed: {str(e)}")
            
    @classmethod
    def list_available_models(cls) -> Dict[str, Type[BaseModelAdapter]]:
        """
        Get list of available model adapters.
        
        Returns:
            Dictionary of model names and their adapter classes
        """
        return cls._adapters.copy() 