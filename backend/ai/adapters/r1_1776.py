"""R1-1776 model adapter implementation."""

from typing import Optional, Dict, Any, List
from loguru import logger

from .base import BaseModelAdapter
from ..r1_1776 import R11776Model
from ..cache import AICache

class R11776Adapter(BaseModelAdapter):
    """Adapter for R1-1776 language model."""
    
    def __init__(
        self,
        use_onnx: bool = True,
        cache_host: str = "localhost",
        cache_port: int = 6379
    ):
        """
        Initialize R1-1776 adapter.
        
        Args:
            use_onnx: Whether to use ONNX runtime
            cache_host: Redis cache host
            cache_port: Redis cache port
        """
        self._model = R11776Model(
            use_onnx=use_onnx,
            cache_host=cache_host,
            cache_port=cache_port
        )
        
    @property
    def model_name(self) -> str:
        return "r1-1776"
        
    @property
    def model_type(self) -> str:
        return "language_model"
        
    @property
    def endpoint(self) -> str:
        return "local"
        
    def generate(
        self,
        prompt: str,
        max_length: int = 200,
        temperature: float = 0.7,
        **kwargs: Dict[str, Any]
    ) -> Optional[str]:
        """Generate text using R1-1776 model."""
        try:
            response = self._model.generate_text(
                prompt=prompt,
                max_length=max_length,
                temperature=temperature,
                **kwargs
            )
            return self.validate_response(response)
            
        except Exception as e:
            logger.error(f"R1-1776 generation failed: {str(e)}")
            return None
            
    def batch_generate(
        self,
        prompts: List[str],
        max_length: int = 200,
        temperature: float = 0.7,
        **kwargs: Dict[str, Any]
    ) -> List[Optional[str]]:
        """Generate text for multiple prompts."""
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
            "capabilities": ["text-generation"],
            "max_tokens": 2048,
            "input_schema": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "max_length": {"type": "integer"},
                    "temperature": {"type": "number"}
                }
            }
        } 