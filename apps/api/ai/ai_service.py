"""
AI Service

This module provides a unified service for AI capabilities, integrating:
- Model adapters for different providers (OpenAI, Anthropic, Google)
- Monitoring and observability tools (Langfuse, Weights & Biases, Arize)
- Caching and throttling mechanisms
- Tool integration for email marketing tasks
"""

import logging
import os
import sys
import time
from typing import Dict, Any, List, Optional, Union, AsyncIterator
import json
import asyncio

from .adapters import model_adapter_factory
from .adapters.base import ModelRequest, ModelResponse, BaseModelAdapter
from .caching import ModelResponseCache
from .monitoring import ai_metrics_service
from .utils.token_counter import count_tokens, estimate_cost

logger = logging.getLogger(__name__)

class AIService:
    """
    Unified AI service for the Maily platform.

    This class provides a comprehensive interface for AI capabilities,
    including text generation, email campaign creation, and more.
    """

    def __init__(self, cache_service=None):
        """Initialize the AI service."""
        self.model_adapters = {}
        self.cache_service = cache_service

        # Initialize monitoring services if available
        self._init_monitoring()

    def _init_monitoring(self):
        """Initialize monitoring services."""
        # Initialize Langfuse if available
        try:
            from langfuse import Langfuse

            langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
            langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY")

            if langfuse_public_key and langfuse_secret_key:
                self.langfuse = Langfuse(
                    public_key=langfuse_public_key,
                    secret_key=langfuse_secret_key
                )
                logger.info("Langfuse monitoring initialized")
            else:
                self.langfuse = None
        except ImportError:
            self.langfuse = None
            logger.info("Langfuse not available")

        # Initialize Weights & Biases if available
        try:
            import wandb

            if os.getenv("WANDB_API_KEY"):
                wandb.init(project="maily-ai-service")
                self.wandb = wandb
                logger.info("Weights & Biases monitoring initialized")
            else:
                self.wandb = None
        except ImportError:
            self.wandb = None
            logger.info("Weights & Biases not available")

    async def generate_text(
        self,
        prompt: str,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        user_id: str = None,
        session_id: str = None,
        metadata: Dict[str, Any] = None,
        tools: List[Dict[str, Any]] = None
    ) -> ModelResponse:
        """
        Generate text using an AI model.

        Args:
            prompt: The prompt to generate text from
            model: The model to use (defaults to the default model)
            temperature: The temperature to use for generation
            max_tokens: The maximum number of tokens to generate
            user_id: Optional user ID for tracking
            session_id: Optional session ID for tracking
            metadata: Optional metadata for tracking
            tools: Optional tools for function calling

        Returns:
            A ModelResponse object containing the generated text
        """
        # Create request
        request = ModelRequest(
            prompt=prompt,
            model=model or "gpt-4",
            temperature=temperature,
            max_tokens=max_tokens,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata or {},
            tools=tools
        )

        # Generate response
        response = await self._generate(request)

        return response

    async def _generate(self, request: ModelRequest) -> ModelResponse:
        """
        Internal method to generate text.

        Args:
            request: The model request

        Returns:
            A ModelResponse object
        """
        # Get adapter for model
        adapter = self._get_adapter_for_model(request.model)

        # Start trace if Langfuse is available
        trace = None
        if self.langfuse and request.user_id:
            trace = self.langfuse.trace(
                name="generate_text",
                user_id=request.user_id,
                metadata=request.metadata
            )

        try:
            # Generate response
            start_time = time.time()
            response = await adapter.generate(request)
            end_time = time.time()

            # Add metrics
            response.latency = end_time - start_time

            # Log to Weights & Biases if available
            if self.wandb:
                self.wandb.log({
                    "prompt": request.prompt,
                    "response": response.content,
                    "model": response.model,
                    "latency": response.latency,
                    "tokens": response.usage.get("total_tokens", 0)
                })

            # Add trace observation if Langfuse is available
            if trace:
                with trace.span(name="model_call"):
                    trace.add_observation(
                        name="generation",
                        value=response.content,
                        metadata={
                            "model": response.model,
                            "latency": response.latency,
                            "tokens": response.usage
                        }
                    )

            return response
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")

            # Add error to trace if Langfuse is available
            if trace:
                trace.error(name="generation_error", message=str(e))

            # Re-raise exception
            raise

    def _get_adapter_for_model(self, model_name: str) -> BaseModelAdapter:
        """
        Get the adapter for a model.

        Args:
            model_name: The name of the model

        Returns:
            A model adapter
        """
        if model_name not in self.model_adapters:
            self.model_adapters[model_name] = model_adapter_factory.get_adapter_for_model(model_name)

        return self.model_adapters[model_name]

    async def generate_embeddings(
        self,
        text: Union[str, List[str]],
        model: str = None,
        user_id: str = None
    ) -> List[List[float]]:
        """
        Generate embeddings for text.

        Args:
            text: The text to generate embeddings for
            model: The model to use (defaults to the default embedding model)
            user_id: Optional user ID for tracking

        Returns:
            A list of embeddings
        """
        # Get adapter for model
        model = model or "text-embedding-3-small"
        adapter = self._get_adapter_for_model(model)

        # Generate embeddings
        embeddings = await adapter.embed(text, user_id=user_id)

        return embeddings

    async def create_email_campaign(
        self,
        campaign_data: Dict[str, Any],
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        Create an email campaign.

        Args:
            campaign_data: The campaign data
            user_id: Optional user ID for tracking

        Returns:
            A dictionary with the campaign results
        """
        # In a real implementation, this would use a specialized service
        # For now, we'll just generate a subject and content

        # Generate subject
        subject_prompt = f"""
        Create an email subject line for a campaign with the following details:
        Objective: {campaign_data.get('objective')}
        Audience: {campaign_data.get('audience')}
        Brand voice: {campaign_data.get('brand_voice', 'professional')}
        Key points: {', '.join(campaign_data.get('key_points', []))}

        The subject line should be attention-grabbing, concise, and relevant.
        """

        subject_response = await self.generate_text(
            prompt=subject_prompt,
            temperature=0.7,
            max_tokens=50,
            user_id=user_id
        )

        # Generate content
        content_prompt = f"""
        Create an email campaign with the following details:
        Objective: {campaign_data.get('objective')}
        Audience: {campaign_data.get('audience')}
        Brand voice: {campaign_data.get('brand_voice', 'professional')}
        Key points: {', '.join(campaign_data.get('key_points', []))}

        The email should be engaging, well-structured, and include a clear call to action.
        """

        content_response = await self.generate_text(
            prompt=content_prompt,
            temperature=0.7,
            max_tokens=1000,
            user_id=user_id
        )

        return {
            "subject": subject_response.content.strip(),
            "content": content_response.content.strip(),
            "preview": content_response.content.strip()[:100] + "...",
            "status": "success"
        }

    async def discover_contacts(
        self,
        discovery_data: Dict[str, Any],
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        Discover contacts based on criteria.

        Args:
            discovery_data: The discovery criteria
            user_id: Optional user ID for tracking

        Returns:
            A dictionary with the discovery results
        """
        # In a real implementation, this would use a specialized service
        # For now, we'll just return mock data

        # Generate mock contacts
        mock_contacts = []
        for i in range(5):
            mock_contacts.append({
                "name": f"Contact {i+1}",
                "email": f"contact{i+1}@example.com",
                "role": "Marketing Director" if i % 2 == 0 else "CEO",
                "company": f"Company {i+1}",
                "industry": discovery_data.get("industry", "Technology"),
                "location": discovery_data.get("location", "San Francisco"),
                "quality_score": 0.8 + (i * 0.03)
            })

        return {
            "results": mock_contacts,
            "status": "success"
        }

    async def segment_audience(
        self,
        audience_data: Dict[str, Any],
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        Segment an audience based on criteria.

        Args:
            audience_data: The audience data and segmentation criteria
            user_id: Optional user ID for tracking

        Returns:
            A dictionary with the segmentation results
        """
        # In a real implementation, this would use a specialized service
        # For now, we'll just return mock data

        # Generate mock segments
        mock_segments = [
            {
                "name": "High Engagement Tech",
                "criteria": "High engagement + Technology industry",
                "count": 25
            },
            {
                "name": "Medium Engagement Tech",
                "criteria": "Medium engagement + Technology industry",
                "count": 42
            },
            {
                "name": "Marketing Professionals",
                "criteria": "Role contains Marketing",
                "count": 18
            }
        ]

        return {
            "segments": mock_segments,
            "status": "success"
        }

    async def check_health(self) -> Dict[str, Any]:
        """
        Check the health of the AI service.

        Returns:
            A dictionary with health information
        """
        health_info = {}
        overall_status = "healthy"

        # Check OpenAI
        try:
            openai_adapter = self._get_adapter_for_model("gpt-3.5-turbo")
            await openai_adapter.check_health()
            health_info["openai"] = {"status": "healthy"}
        except Exception as e:
            health_info["openai"] = {"status": "unhealthy", "error": str(e)}
            overall_status = "degraded"

        # Check Anthropic if available
        try:
            anthropic_adapter = self._get_adapter_for_model("claude-3-opus-20240229")
            await anthropic_adapter.check_health()
            health_info["anthropic"] = {"status": "healthy"}
        except Exception as e:
            health_info["anthropic"] = {"status": "unhealthy", "error": str(e)}
            # Don't degrade overall status if Anthropic is optional

        return {
            "status": overall_status,
            "providers": health_info,
            "timestamp": time.time()
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for the AI service.

        Returns:
            A dictionary with performance metrics
        """
        # In a real implementation, this would fetch metrics from a metrics service
        # For now, we'll just return mock data

        return {
            "latency": {
                "avg_ms": 250,
                "p95_ms": 500,
                "p99_ms": 750
            },
            "success_rate": 99.5,
            "token_usage": {
                "total": 1000000,
                "by_model": {
                    "gpt-4": 500000,
                    "gpt-3.5-turbo": 400000,
                    "claude-3-opus-20240229": 100000
                }
            },
            "cost": {
                "total_usd": 150.25,
                "by_model": {
                    "gpt-4": 100.50,
                    "gpt-3.5-turbo": 25.75,
                    "claude-3-opus-20240229": 24.00
                }
            }
        }

# Create a singleton instance
ai_service = AIService()
