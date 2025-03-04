"""
Model Fallback Chain for AI Mesh Network

This module implements a model fallback chain for LLM models,
allowing automatic fallback to alternative models if the primary model is unavailable.
"""

import logging
import time
import json
from typing import Dict, Any, List, Optional, Tuple, Union, Callable, Awaitable
import asyncio

from ...utils.llm_client import get_llm_client, LLMClient
from ...utils.concurrent import with_retry, CircuitBreaker

logger = logging.getLogger("ai_service.implementations.models.model_fallback")

# Default model fallback chain
DEFAULT_FALLBACK_CHAIN = ["claude-3-7-sonnet", "gpt-4o", "gemini-2.0"]

class ModelFallbackChain:
    """Model fallback chain for LLM models"""
    
    def __init__(
        self,
        model_chain: List[str] = None,
        max_retries_per_model: int = 2,
        circuit_breaker_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the model fallback chain
        
        Args:
            model_chain: List of models in fallback order
            max_retries_per_model: Maximum number of retries per model
            circuit_breaker_config: Optional configuration for circuit breakers
        """
        self.model_chain = model_chain or DEFAULT_FALLBACK_CHAIN
        self.max_retries_per_model = max_retries_per_model
        self.llm_client = get_llm_client()
        
        # Initialize circuit breakers for each model
        self.circuit_breakers = {}
        cb_config = circuit_breaker_config or {
            "failure_threshold": 3,
            "recovery_timeout": 60.0,
            "half_open_max_trials": 2
        }
        
        for model in self.model_chain:
            self.circuit_breakers[model] = CircuitBreaker(
                name=f"model_{model.replace('-', '_')}",
                failure_threshold=cb_config.get("failure_threshold", 3),
                recovery_timeout=cb_config.get("recovery_timeout", 60.0),
                half_open_max_trials=cb_config.get("half_open_max_trials", 2)
            )
        
        # Performance metrics
        self.model_usage = {model: 0 for model in self.model_chain}
        self.model_success = {model: 0 for model in self.model_chain}
        self.model_failures = {model: 0 for model in self.model_chain}
        self.fallbacks_triggered = 0
        self.total_requests = 0
        self.total_success = 0
        self.total_failures = 0
    
    async def generate_text(
        self,
        prompt: str,
        primary_model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        system_prompt: Optional[str] = None,
        custom_fallback_chain: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate text using a model with fallback
        
        Args:
            prompt: Prompt to send to the model
            primary_model: Primary model to use (defaults to first in chain)
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt
            custom_fallback_chain: Optional custom fallback chain for this request
            
        Returns:
            Dictionary with generation result
        """
        self.total_requests += 1
        start_time = time.time()
        
        # Determine the fallback chain to use
        fallback_chain = custom_fallback_chain or self.model_chain
        
        # If primary model is specified, ensure it's first in the chain
        if primary_model and primary_model in fallback_chain and fallback_chain[0] != primary_model:
            fallback_chain = [primary_model] + [m for m in fallback_chain if m != primary_model]
        
        # Track tried models and errors
        errors = []
        
        # Try each model in the chain with retry
        for i, model in enumerate(fallback_chain):
            try:
                # Skip if circuit breaker is open
                circuit_breaker = self.circuit_breakers.get(model)
                if circuit_breaker and not circuit_breaker.allow_request():
                    logger.warning(f"Circuit breaker for model {model} is open, skipping")
                    errors.append(f"{model}: Circuit breaker open")
                    continue
                
                # Count model usage
                self.model_usage[model] = self.model_usage.get(model, 0) + 1
                
                # Log fallback if not the primary model
                if i > 0:
                    self.fallbacks_triggered += 1
                    logger.info(f"Falling back to model {model} (attempt {i+1}/{len(fallback_chain)})")
                
                # Create retry function for this model
                retry_generate = self._create_retry_function(model, temperature, max_tokens, system_prompt)
                
                # Execute with retry
                model_start_time = time.time()
                result = await retry_generate(prompt)
                
                # Record success
                self.model_success[model] = self.model_success.get(model, 0) + 1
                self.total_success += 1
                
                if circuit_breaker:
                    circuit_breaker.record_success()
                
                # Add metadata about fallback
                generation_time = time.time() - model_start_time
                result["fallback_info"] = {
                    "primary_model": fallback_chain[0],
                    "used_model": model,
                    "fallback_level": i,
                    "models_tried": i + 1,
                    "generation_time": generation_time
                }
                
                # Return successful result
                return result
                
            except Exception as e:
                # Record failure
                self.model_failures[model] = self.model_failures.get(model, 0) + 1
                
                if circuit_breaker:
                    circuit_breaker.record_failure()
                
                # Record error
                error_msg = f"{model}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"Model {model} failed: {e}")
        
        # If we get here, all models failed
        self.total_failures += 1
        error_details = "\n".join(errors)
        logger.error(f"All models in fallback chain failed:\n{error_details}")
        
        # Return fallback response
        return {
            "content": self._create_fallback_content(),
            "model": "fallback",
            "error": f"All models failed: {error_details}",
            "fallback_info": {
                "primary_model": fallback_chain[0],
                "used_model": "fallback",
                "models_tried": len(fallback_chain),
                "errors": errors
            }
        }
    
    def _create_retry_function(
        self,
        model: str,
        temperature: float,
        max_tokens: int,
        system_prompt: Optional[str]
    ) -> Callable[[str], Awaitable[Dict[str, Any]]]:
        """
        Create a retry function for a specific model
        
        Args:
            model: Model to use
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt
            
        Returns:
            Async function that takes a prompt and returns a generation result
        """
        # Create generation function
        async def generate_with_model(prompt: str) -> Dict[str, Any]:
            start_time = time.time()
            try:
                response = await self.llm_client.generate_text(
                    prompt=prompt,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    system_prompt=system_prompt
                )
                duration = time.time() - start_time
                logger.info(f"Generated response with {model} in {duration:.2f}s")
                
                # Add model metadata to response
                response["model"] = model
                response["generation_time"] = duration
                
                return response
            except Exception as e:
                duration = time.time() - start_time
                logger.warning(f"Failed to generate with {model} after {duration:.2f}s: {str(e)}")
                raise
                
        # Create retry function
        async def retry_func(prompt: str) -> Dict[str, Any]:
            return await with_retry(
                generate_with_model,
                prompt,
                retry_count=self.max_retries_per_model,
                initial_backoff=1.0,
                backoff_factor=2.0,
                jitter=True
            )
            
        return retry_func
    
    def _create_fallback_content(self) -> str:
        """
        Create fallback content when all models fail
        
        Returns:
            Fallback content string
        """
        fallback_data = {
            "error": "Service temporarily unavailable",
            "message": "All language models are currently unavailable. Please try again later.",
            "status": "error"
        }
        return json.dumps(fallback_data)
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for the fallback chain
        
        Returns:
            Dictionary with performance metrics
        """
        metrics = {
            "total_requests": self.total_requests,
            "total_success": self.total_success,
            "total_failures": self.total_failures,
            "fallbacks_triggered": self.fallbacks_triggered,
            "fallback_rate": self.fallbacks_triggered / max(1, self.total_requests),
            "success_rate": self.total_success / max(1, self.total_requests),
            "model_metrics": {}
        }
        
        # Add metrics for each model
        for model in self.model_chain:
            usage = self.model_usage.get(model, 0)
            success = self.model_success.get(model, 0)
            failures = self.model_failures.get(model, 0)
            
            # Get circuit breaker status
            cb_stats = None
            if model in self.circuit_breakers:
                cb_stats = self.circuit_breakers[model].get_stats()
            
            metrics["model_metrics"][model] = {
                "usage": usage,
                "success": success,
                "failures": failures,
                "success_rate": success / max(1, usage),
                "circuit_breaker": cb_stats
            }
        
        return metrics
    
    def reset_metrics(self):
        """Reset all performance metrics"""
        self.model_usage = {model: 0 for model in self.model_chain}
        self.model_success = {model: 0 for model in self.model_chain}
        self.model_failures = {model: 0 for model in self.model_chain}
        self.fallbacks_triggered = 0
        self.total_requests = 0
        self.total_success = 0
        self.total_failures = 0

# Singleton instance
_model_fallback_instance = None

def get_model_fallback_chain() -> ModelFallbackChain:
    """Get the singleton instance of ModelFallbackChain"""
    global _model_fallback_instance
    if _model_fallback_instance is None:
        _model_fallback_instance = ModelFallbackChain()
    return _model_fallback_instance