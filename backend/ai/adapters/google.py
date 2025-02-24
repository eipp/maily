"""Google Gemini model adapter implementation."""

import os
from typing import Optional, Dict, Any, List
from loguru import logger
import google.generativeai as genai

from .base import BaseModelAdapter

class GeminiAdapter(BaseModelAdapter):
    """Adapter for Google Gemini models."""
    
    AVAILABLE_MODELS = {
        "gemini-pro": {
            "max_tokens": 32768,
            "capabilities": ["text-generation", "chat", "function-calling"]
        },
        "gemini-pro-vision": {
            "max_tokens": 32768,
            "capabilities": ["text-generation", "chat", "vision", "function-calling"]
        }
    }
    
    def __init__(
        self,
        model_name: str = "gemini-pro",
        api_key: Optional[str] = None,
        **kwargs: Dict[str, Any]
    ):
        """
        Initialize Gemini adapter.
        
        Args:
            model_name: Gemini model name to use
            api_key: Google API key (defaults to env var)
            **kwargs: Additional configuration parameters
        """
        if model_name not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model name. Available models: {list(self.AVAILABLE_MODELS.keys())}")
            
        self._model_name = model_name
        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            raise ValueError("Google API key not provided")
            
        # Configure the Gemini client
        genai.configure(api_key=api_key)
        
        # Initialize the model
        self._model = genai.GenerativeModel(model_name)
        
        # Store model config
        self._config = self.AVAILABLE_MODELS[model_name]
        
        logger.info(f"Initialized Gemini adapter with model: {model_name}")
        
    @property
    def model_name(self) -> str:
        return self._model_name
        
    @property
    def model_type(self) -> str:
        return "language_model"
        
    @property
    def endpoint(self) -> str:
        return "google"
        
    def generate(
        self,
        prompt: str,
        max_length: int = 200,
        temperature: float = 0.7,
        **kwargs: Dict[str, Any]
    ) -> Optional[str]:
        """Generate text using Gemini model."""
        try:
            # Configure generation parameters
            generation_config = {
                "max_output_tokens": max_length,
                "temperature": temperature,
                **kwargs
            }
            
            # Generate response
            response = self._model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            if response and response.text:
                return self.validate_response(response.text)
            return None
            
        except Exception as e:
            logger.error(f"Gemini generation failed: {str(e)}")
            return None
            
    def batch_generate(
        self,
        prompts: List[str],
        max_length: int = 200,
        temperature: float = 0.7,
        **kwargs: Dict[str, Any]
    ) -> List[Optional[str]]:
        """Generate text for multiple prompts."""
        try:
            # Configure generation parameters
            generation_config = {
                "max_output_tokens": max_length,
                "temperature": temperature,
                **kwargs
            }
            
            # Generate responses in parallel
            responses = self._model.generate_content(
                prompts,
                generation_config=generation_config
            )
            
            # Extract and validate responses
            results = []
            for response in responses:
                text = response.text if response else None
                results.append(self.validate_response(text))
            return results
            
        except Exception as e:
            logger.error(f"Gemini batch generation failed: {str(e)}")
            # Fallback to individual requests
            return [
                self.generate(
                    prompt,
                    max_length=max_length,
                    temperature=temperature,
                    **kwargs
                )
                for prompt in prompts
            ]
            
    def get_model_config(self) -> Dict[str, Any]:
        """Get model configuration for monitoring."""
        return {
            "name": self.model_name,
            "type": self.model_type,
            "endpoint": self.endpoint,
            "capabilities": self._config["capabilities"],
            "max_tokens": self._config["max_tokens"],
            "input_schema": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "max_output_tokens": {"type": "integer"},
                    "temperature": {"type": "number"}
                }
            }
        } 