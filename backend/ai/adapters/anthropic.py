"""Anthropic Claude model adapter implementation."""

import os
from typing import Optional, Dict, Any, List
from loguru import logger
import anthropic

from .base import BaseModelAdapter

class ClaudeAdapter(BaseModelAdapter):
    """Adapter for Anthropic Claude models."""
    
    AVAILABLE_MODELS = {
        "claude-3-opus": {
            "max_tokens": 200000,
            "capabilities": ["text-generation", "chat", "function-calling", "vision"]
        },
        "claude-3-sonnet": {
            "max_tokens": 200000,
            "capabilities": ["text-generation", "chat", "function-calling", "vision"]
        },
        "claude-3-haiku": {
            "max_tokens": 200000,
            "capabilities": ["text-generation", "chat", "function-calling", "vision"]
        },
        "claude-2.1": {
            "max_tokens": 100000,
            "capabilities": ["text-generation", "chat", "function-calling"]
        }
    }
    
    def __init__(
        self,
        model_name: str = "claude-3-opus",
        api_key: Optional[str] = None,
        **kwargs: Dict[str, Any]
    ):
        """
        Initialize Claude adapter.
        
        Args:
            model_name: Claude model name to use
            api_key: Anthropic API key (defaults to env var)
            **kwargs: Additional configuration parameters
        """
        if model_name not in self.AVAILABLE_MODELS:
            raise ValueError(f"Invalid model name. Available models: {list(self.AVAILABLE_MODELS.keys())}")
            
        self._model_name = model_name
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        
        if not api_key:
            raise ValueError("Anthropic API key not provided")
            
        # Initialize the client
        self._client = anthropic.Anthropic(api_key=api_key)
        
        # Store model config
        self._config = self.AVAILABLE_MODELS[model_name]
        
        logger.info(f"Initialized Claude adapter with model: {model_name}")
        
    @property
    def model_name(self) -> str:
        return self._model_name
        
    @property
    def model_type(self) -> str:
        return "language_model"
        
    @property
    def endpoint(self) -> str:
        return "anthropic"
        
    def generate(
        self,
        prompt: str,
        max_length: int = 200,
        temperature: float = 0.7,
        **kwargs: Dict[str, Any]
    ) -> Optional[str]:
        """Generate text using Claude model."""
        try:
            # Create message
            response = self._client.messages.create(
                model=self.model_name,
                max_tokens=max_length,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                **kwargs
            )
            
            if response and response.content:
                return self.validate_response(response.content[0].text)
            return None
            
        except Exception as e:
            logger.error(f"Claude generation failed: {str(e)}")
            return None
            
    def batch_generate(
        self,
        prompts: List[str],
        max_length: int = 200,
        temperature: float = 0.7,
        **kwargs: Dict[str, Any]
    ) -> List[Optional[str]]:
        """Generate text for multiple prompts."""
        # Claude doesn't support native batching, so we process sequentially
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
                    "max_tokens": {"type": "integer"},
                    "temperature": {"type": "number"}
                }
            }
        } 