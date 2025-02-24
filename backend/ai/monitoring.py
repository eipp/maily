import os
from typing import Optional, Dict, Any
from loguru import logger
from langfuse import Langfuse
from langfuse.model import CreateTrace, CreateGeneration

class AIMonitoring:
    """Langfuse-based monitoring for AI operations."""
    
    def __init__(self):
        """Initialize Langfuse monitoring."""
        try:
            self.api_key = os.getenv("LANGFUSE_API_KEY")
            if not self.api_key:
                raise ValueError("LANGFUSE_API_KEY environment variable not set")
                
            self.langfuse = Langfuse(api_key=self.api_key)
            
            # Register our models
            self._register_models()
            logger.info("Langfuse monitoring initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Langfuse monitoring: {str(e)}")
            raise
            
    def _register_models(self):
        """Register all AI models with Langfuse."""
        try:
            self.langfuse.register_model(
                name="r1-1776",
                model_type="language_model",
                endpoint="local",
                input_schema={
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string"},
                        "max_length": {"type": "integer"},
                        "temperature": {"type": "number"}
                    }
                }
            )
        except Exception as e:
            logger.error(f"Failed to register models: {str(e)}")
            raise
            
    def log_generation(
        self,
        model_name: str,
        prompt: str,
        completion: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a model generation event to Langfuse.
        
        Args:
            model_name: Name of the model used
            prompt: Input prompt
            completion: Generated completion
            metadata: Additional metadata to log
        """
        try:
            trace = self.langfuse.trace(CreateTrace(name=f"{model_name}_generation"))
            
            generation = trace.generation(
                CreateGeneration(
                    name=model_name,
                    model=model_name,
                    prompt=prompt,
                    completion=completion,
                    metadata=metadata or {}
                )
            )
            
            trace.end()
            logger.debug(f"Successfully logged generation event for {model_name}")
            
        except Exception as e:
            logger.error(f"Failed to log generation event: {str(e)}")
            # Don't raise the exception to avoid disrupting the main flow 