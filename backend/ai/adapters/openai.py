"""OpenAI model adapter implementation."""

import os
from typing import Optional, Dict, Any, List
from loguru import logger
import openai

from .base import BaseModelAdapter

class OpenAIAdapter(BaseModelAdapter):
    """Adapter for OpenAI language models."""
    
    def __init__(
        self,
        model_name: str = "gpt-4",
        api_key: Optional[str] = None
    ):
        """
        Initialize OpenAI adapter.
        
        Args:
            model_name: OpenAI model name to use
            api_key: OpenAI API key (defaults to env var)
        """
        self._model_name = model_name
        openai.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not openai.api_key:
            raise ValueError("OpenAI API key not provided")
            
    @property
    def model_name(self) -> str:
        return self._model_name
        
    @property
    def model_type(self) -> str:
        return "language_model"
        
    @property
    def endpoint(self) -> str:
        return "openai"
        
    def generate(
        self,
        prompt: str,
        max_length: int = 200,
        temperature: float = 0.7,
        **kwargs: Dict[str, Any]
    ) -> Optional[str]:
        """Generate text using OpenAI model."""
        try:
            response = openai.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_length,
                temperature=temperature,
                **kwargs
            )
            
            if response.choices:
                return self.validate_response(
                    response.choices[0].message.content
                )
            return None
            
        except Exception as e:
            logger.error(f"OpenAI generation failed: {str(e)}")
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
            # Create messages for each prompt
            messages_list = [
                [{"role": "user", "content": prompt}]
                for prompt in prompts
            ]
            
            # Use OpenAI's native batching
            response = openai.chat.completions.create(
                model=self.model_name,
                messages=messages_list,
                max_tokens=max_length,
                temperature=temperature,
                n=len(prompts),
                **kwargs
            )
            
            # Extract and validate responses
            results = []
            for choice in response.choices:
                text = choice.message.content
                results.append(self.validate_response(text))
            return results
            
        except Exception as e:
            logger.error(f"OpenAI batch generation failed: {str(e)}")
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
            "capabilities": ["text-generation", "chat"],
            "max_tokens": 4096 if "gpt-4" in self.model_name else 2048,
            "input_schema": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "max_tokens": {"type": "integer"},
                    "temperature": {"type": "number"}
                }
            }
        } 