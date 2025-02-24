"""Agent-based system for email generation."""

from typing import Optional, Dict, Any, List
from loguru import logger
import autogen

from .adapters.factory import ModelFactory
from .adapters.base import BaseModelAdapter
from .monitoring import AIMonitoring

class DynamicLLM:
    """AutoGen-compatible wrapper for any model adapter."""
    
    def __init__(self, model_adapter: BaseModelAdapter):
        """
        Initialize the LLM wrapper.
        
        Args:
            model_adapter: Model adapter instance
        """
        self.model = model_adapter
        self.monitoring = AIMonitoring()
        
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text using the model adapter.
        
        Args:
            prompt: Input text
            **kwargs: Additional parameters
            
        Returns:
            Generated text
        """
        completion = self.model.generate(prompt, **kwargs)
        
        # Log the generation
        self.monitoring.log_generation(
            model_name=self.model.model_name,
            prompt=prompt,
            completion=completion or "",
            metadata=kwargs
        )
        
        return completion or ""

class EmailAgent:
    """AutoGen agent for email-related tasks."""
    
    def __init__(
        self,
        model_name: str = "r1-1776",
        **model_kwargs: Dict[str, Any]
    ):
        """
        Initialize the email agent system.
        
        Args:
            model_name: Name of the model to use
            **model_kwargs: Additional model configuration
        """
        try:
            # Create model adapter
            model_adapter = ModelFactory.create_adapter(
                model_name,
                **model_kwargs
            )
            
            # Initialize the LLM wrapper
            self.llm = DynamicLLM(model_adapter)
            
            # Create AutoGen agents
            self.content_agent = autogen.AssistantAgent(
                name="EmailContentAgent",
                llm_config={"model": self.llm},
                system_message="""You are an expert at crafting email content.
                Your task is to generate engaging and effective email content
                based on the given requirements."""
            )
            
            self.user_proxy = autogen.UserProxyAgent(
                name="UserProxy",
                human_input_mode="NEVER",
                max_consecutive_auto_reply=1
            )
            
            logger.info(f"Email agent system initialized with model: {model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize email agent system: {str(e)}")
            raise
            
    def generate_subject(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Generate an email subject based on context.
        
        Args:
            context: Dictionary containing email context
            
        Returns:
            Generated subject line or None if generation fails
        """
        try:
            prompt = f"""Generate a compelling email subject line for:
            Purpose: {context.get('purpose', 'N/A')}
            Target Audience: {context.get('audience', 'N/A')}
            Key Message: {context.get('message', 'N/A')}
            Tone: {context.get('tone', 'Professional')}
            """
            
            chat_response = self.user_proxy.initiate_chat(
                self.content_agent,
                message=prompt
            )
            
            # Extract the subject line from the response
            if isinstance(chat_response, str):
                return chat_response.strip()
            return None
            
        except Exception as e:
            logger.error(f"Failed to generate email subject: {str(e)}")
            return None
            
    def generate_body(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Generate email body content based on context.
        
        Args:
            context: Dictionary containing email context
            
        Returns:
            Generated email body or None if generation fails
        """
        try:
            prompt = f"""Generate an email body with the following requirements:
            Subject: {context.get('subject', 'N/A')}
            Purpose: {context.get('purpose', 'N/A')}
            Target Audience: {context.get('audience', 'N/A')}
            Key Message: {context.get('message', 'N/A')}
            Tone: {context.get('tone', 'Professional')}
            Call to Action: {context.get('cta', 'N/A')}
            """
            
            chat_response = self.user_proxy.initiate_chat(
                self.content_agent,
                message=prompt
            )
            
            if isinstance(chat_response, str):
                return chat_response.strip()
            return None
            
        except Exception as e:
            logger.error(f"Failed to generate email body: {str(e)}")
            return None 