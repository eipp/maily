"""LiteLLM integration for model routing."""

import os
import logging
from typing import Dict, Any, Optional, List, Union
import json
import asyncio

logger = logging.getLogger(__name__)

class LiteLLMService:
    """LiteLLM service for model routing."""

    def __init__(self):
        """Initialize the LiteLLM service."""
        try:
            # Import LiteLLM
            import litellm

            # Configure LiteLLM
            litellm.drop_params = True

            # Set API keys from environment variables
            litellm.openai_api_key = os.getenv("OPENAI_API_KEY")
            litellm.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
            litellm.google_api_key = os.getenv("GOOGLE_API_KEY")

            # Configure Helicone if API key is available
            helicone_api_key = os.getenv("HELICONE_API_KEY")
            if helicone_api_key:
                litellm.helicone_api_key = helicone_api_key

            # Configure model cost map
            litellm.model_cost = {
                # OpenAI models
                "gpt-4o": {"input_cost_per_token": 0.00001, "output_cost_per_token": 0.00003},
                "gpt-4-turbo": {"input_cost_per_token": 0.00001, "output_cost_per_token": 0.00003},
                "gpt-4": {"input_cost_per_token": 0.00003, "output_cost_per_token": 0.00006},
                "gpt-3.5-turbo": {"input_cost_per_token": 0.0000015, "output_cost_per_token": 0.000002},

                # Anthropic models
                "claude-3-opus-20240229": {"input_cost_per_token": 0.00001, "output_cost_per_token": 0.00003},
                "claude-3-sonnet-20240229": {"input_cost_per_token": 0.000003, "output_cost_per_token": 0.000015},
                "claude-3-haiku-20240307": {"input_cost_per_token": 0.00000025, "output_cost_per_token": 0.00000125},

                # Google models
                "gemini-pro": {"input_cost_per_token": 0.000000125, "output_cost_per_token": 0.000000375},
                "gemini-ultra": {"input_cost_per_token": 0.00000075, "output_cost_per_token": 0.00000225}
            }

            # Configure model aliases
            litellm.model_alias_map = {
                "fastest": "claude-3-haiku-20240307",
                "balanced": "gpt-3.5-turbo",
                "smartest": "claude-3-opus-20240229",
                "cheapest": "gemini-pro"
            }

            self.enabled = True
            logger.info("LiteLLM service initialized successfully")
        except ImportError:
            logger.error("LiteLLM not installed. Please install with 'pip install litellm'.")
            self.enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize LiteLLM service: {str(e)}")
            self.enabled = False

    async def generate_completion(self,
                                 prompt: str,
                                 model: Optional[str] = None,
                                 max_tokens: int = 1000,
                                 temperature: float = 0.7,
                                 fallbacks: Optional[List[str]] = None,
                                 metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a completion using LiteLLM.

        Args:
            prompt: Prompt to send to the model
            model: Model to use (defaults to auto-routing)
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            fallbacks: Optional list of fallback models
            metadata: Optional metadata

        Returns:
            Dictionary containing the generated completion
        """
        if not self.enabled:
            return {"error": "LiteLLM service is not enabled"}

        try:
            # Import LiteLLM
            import litellm

            # Prepare the request
            params = {
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature
            }

            # Add model if provided
            if model:
                params["model"] = model

            # Add metadata if provided
            if metadata:
                params["metadata"] = metadata

            # Generate the completion
            if fallbacks:
                response = await litellm.acompletion_with_fallbacks(
                    fallbacks=fallbacks,
                    **params
                )
            else:
                response = await litellm.acompletion(**params)

            # Extract the content
            content = response.choices[0].message.content

            return {
                "content": content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "id": response.id
            }
        except Exception as e:
            logger.error(f"Failed to generate completion with LiteLLM: {str(e)}")
            return {"error": str(e)}

    async def route_request(self,
                           prompt: str,
                           task_type: str,
                           max_tokens: int = 1000,
                           temperature: float = 0.7,
                           metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Route a request to the appropriate model based on task type.

        Args:
            prompt: Prompt to send to the model
            task_type: Type of task (e.g., creative, analytical, summarization)
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            metadata: Optional metadata

        Returns:
            Dictionary containing the generated completion
        """
        if not self.enabled:
            return {"error": "LiteLLM service is not enabled"}

        try:
            # Determine the model based on task type
            model = None
            fallbacks = None

            if task_type == "creative":
                model = "anthropic/claude-3-opus-20240229"
                fallbacks = ["openai/gpt-4o", "google/gemini-pro"]
                temperature = max(temperature, 0.7)  # Ensure temperature is at least 0.7 for creative tasks
            elif task_type == "analytical":
                model = "openai/gpt-4o"
                fallbacks = ["anthropic/claude-3-opus-20240229", "google/gemini-pro"]
                temperature = min(temperature, 0.3)  # Ensure temperature is at most 0.3 for analytical tasks
            elif task_type == "summarization":
                model = "anthropic/claude-3-haiku-20240307"
                fallbacks = ["openai/gpt-3.5-turbo", "google/gemini-pro"]
            else:
                # Default to auto-routing
                model = None
                fallbacks = ["anthropic/claude-3-opus-20240229", "openai/gpt-4o", "google/gemini-pro"]

            # Generate the completion
            return await self.generate_completion(
                prompt=prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                fallbacks=fallbacks,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Failed to route request with LiteLLM: {str(e)}")
            return {"error": str(e)}

    async def generate_chat_completion(self,
                                      messages: List[Dict[str, str]],
                                      model: Optional[str] = None,
                                      max_tokens: int = 1000,
                                      temperature: float = 0.7,
                                      fallbacks: Optional[List[str]] = None,
                                      metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a chat completion using LiteLLM.

        Args:
            messages: List of messages in the conversation
            model: Model to use (defaults to auto-routing)
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            fallbacks: Optional list of fallback models
            metadata: Optional metadata

        Returns:
            Dictionary containing the generated chat completion
        """
        if not self.enabled:
            return {"error": "LiteLLM service is not enabled"}

        try:
            # Import LiteLLM
            import litellm

            # Prepare the request
            params = {
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }

            # Add model if provided
            if model:
                params["model"] = model

            # Add metadata if provided
            if metadata:
                params["metadata"] = metadata

            # Generate the completion
            if fallbacks:
                response = await litellm.acompletion_with_fallbacks(
                    fallbacks=fallbacks,
                    **params
                )
            else:
                response = await litellm.acompletion(**params)

            # Extract the content
            content = response.choices[0].message.content

            return {
                "content": content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "id": response.id
            }
        except Exception as e:
            logger.error(f"Failed to generate chat completion with LiteLLM: {str(e)}")
            return {"error": str(e)}

    async def get_embedding(self,
                           text: str,
                           model: str = "text-embedding-ada-002") -> Dict[str, Any]:
        """Get an embedding for text using LiteLLM.

        Args:
            text: Text to get embedding for
            model: Model to use for embedding

        Returns:
            Dictionary containing the embedding
        """
        if not self.enabled:
            return {"error": "LiteLLM service is not enabled"}

        try:
            # Import LiteLLM
            import litellm

            # Get the embedding
            response = await litellm.aembedding(
                model=model,
                input=text
            )

            return {
                "embedding": response.data[0].embedding,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except Exception as e:
            logger.error(f"Failed to get embedding with LiteLLM: {str(e)}")
            return {"error": str(e)}

    async def get_token_count(self,
                             text: str,
                             model: str = "gpt-4") -> Dict[str, Any]:
        """Get the token count for text using LiteLLM.

        Args:
            text: Text to get token count for
            model: Model to use for tokenization

        Returns:
            Dictionary containing the token count
        """
        if not self.enabled:
            return {"error": "LiteLLM service is not enabled"}

        try:
            # Import LiteLLM
            import litellm

            # Get the token count
            token_count = litellm.token_counter(
                model=model,
                text=text
            )

            return {
                "token_count": token_count,
                "model": model
            }
        except Exception as e:
            logger.error(f"Failed to get token count with LiteLLM: {str(e)}")
            return {"error": str(e)}

    async def get_cost_estimate(self,
                               prompt: str,
                               model: str,
                               max_tokens: int = 1000) -> Dict[str, Any]:
        """Get a cost estimate for a completion using LiteLLM.

        Args:
            prompt: Prompt to send to the model
            model: Model to use
            max_tokens: Maximum tokens to generate

        Returns:
            Dictionary containing the cost estimate
        """
        if not self.enabled:
            return {"error": "LiteLLM service is not enabled"}

        try:
            # Import LiteLLM
            import litellm

            # Get the token count for the prompt
            prompt_tokens = litellm.token_counter(
                model=model,
                text=prompt
            )

            # Estimate the cost
            cost = litellm.completion_cost(
                model=model,
                prompt=prompt,
                completion="",  # Empty completion for estimation
                prompt_tokens=prompt_tokens,
                completion_tokens=max_tokens
            )

            return {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": max_tokens,
                "total_tokens": prompt_tokens + max_tokens,
                "estimated_cost": cost,
                "model": model
            }
        except Exception as e:
            logger.error(f"Failed to get cost estimate with LiteLLM: {str(e)}")
            return {"error": str(e)}

# Create a singleton instance
litellm_service = LiteLLMService()
