"""
LLM Client Utility for AI Service

This module provides a client for interacting with Large Language Models.
"""

import logging
import os
import json
import httpx
import asyncio
import time
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger("ai_service.utils.llm_client")

class LLMClient:
    """Client for interacting with Large Language Models"""
    
    def __init__(self, api_keys: Optional[Dict[str, str]] = None):
        """Initialize LLM client"""
        self.api_keys = api_keys or {
            "claude": os.environ.get("ANTHROPIC_API_KEY", ""),
            "openai": os.environ.get("OPENAI_API_KEY", ""),
            "google": os.environ.get("GOOGLE_API_KEY", "")
        }
        self.client = httpx.AsyncClient(timeout=60.0)
        self.rate_limits = {
            "claude-3-7-sonnet": {"tpm": 100000, "rpm": 500},
            "gpt-4o": {"tpm": 80000, "rpm": 500},
            "gemini-2.0": {"tpm": 60000, "rpm": 300}
        }
        self.last_request_time = {}
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def _respect_rate_limit(self, model: str):
        """Respect rate limits for the model"""
        if model not in self.rate_limits:
            return
        
        # Check if we need to wait
        now = time.time()
        if model in self.last_request_time:
            last_time = self.last_request_time[model]
            # Calculate minimum time between requests based on RPM
            min_interval = 60.0 / self.rate_limits[model]["rpm"]
            elapsed = now - last_time
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
        
        # Update last request time
        self.last_request_time[model] = time.time()
    
    async def generate_text(
        self,
        prompt: str,
        model: str = "claude-3-7-sonnet",
        temperature: float = 0.7,
        max_tokens: int = 4000,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate text from a prompt using the specified model"""
        try:
            # Respect rate limits
            await self._respect_rate_limit(model)
            
            # Determine which provider to use based on model name
            if model.startswith("claude"):
                return await self._generate_with_anthropic(prompt, model, temperature, max_tokens, system_prompt)
            elif model.startswith("gpt"):
                return await self._generate_with_openai(prompt, model, temperature, max_tokens, system_prompt)
            elif model.startswith("gemini"):
                return await self._generate_with_google(prompt, model, temperature, max_tokens, system_prompt)
            else:
                raise ValueError(f"Unsupported model: {model}")
                
        except Exception as e:
            logger.error(f"Failed to generate text with {model}: {e}")
            raise
    
    async def _generate_with_anthropic(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        system_prompt: Optional[str]
    ) -> Dict[str, Any]:
        """Generate text using Anthropic Claude API"""
        try:
            api_key = self.api_keys.get("claude")
            if not api_key:
                raise ValueError("Anthropic API key not found")
            
            # Prepare request
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            
            # Prepare payload
            payload = {
                "model": model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            # Add system prompt if provided
            if system_prompt:
                payload["system"] = system_prompt
            
            # Make request
            response = await self.client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            
            # Extract content
            content = result["content"][0]["text"]
            
            return {
                "content": content,
                "model": model,
                "provider": "anthropic",
                "usage": {
                    "prompt_tokens": result.get("usage", {}).get("input_tokens", 0),
                    "completion_tokens": result.get("usage", {}).get("output_tokens", 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate text with Anthropic: {e}")
            raise
    
    async def _generate_with_openai(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        system_prompt: Optional[str]
    ) -> Dict[str, Any]:
        """Generate text using OpenAI API"""
        try:
            api_key = self.api_keys.get("openai")
            if not api_key:
                raise ValueError("OpenAI API key not found")
            
            # Prepare request
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Prepare messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Prepare payload
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            # Make request
            response = await self.client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            
            # Extract content
            content = result["choices"][0]["message"]["content"]
            
            return {
                "content": content,
                "model": model,
                "provider": "openai",
                "usage": result.get("usage", {})
            }
            
        except Exception as e:
            logger.error(f"Failed to generate text with OpenAI: {e}")
            raise
    
    async def _generate_with_google(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        system_prompt: Optional[str]
    ) -> Dict[str, Any]:
        """Generate text using Google Gemini API"""
        try:
            api_key = self.api_keys.get("google")
            if not api_key:
                raise ValueError("Google API key not found")
            
            # Prepare request
            url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={api_key}"
            headers = {
                "Content-Type": "application/json"
            }
            
            # Prepare content parts
            content_parts = []
            if system_prompt:
                content_parts.append({"text": f"System: {system_prompt}"})
            content_parts.append({"text": prompt})
            
            # Prepare payload
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": content_parts
                    }
                ],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                    "topP": 0.95,
                    "topK": 40
                }
            }
            
            # Make request
            response = await self.client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            
            # Extract content
            content = result["candidates"][0]["content"]["parts"][0]["text"]
            
            return {
                "content": content,
                "model": model,
                "provider": "google",
                "usage": {}  # Google doesn't provide token usage info
            }
            
        except Exception as e:
            logger.error(f"Failed to generate text with Google: {e}")
            raise
    
    async def get_embedding(
        self,
        text: str,
        model: str = "text-embedding-3-small"
    ) -> Dict[str, Any]:
        """
        Generate embedding vector for text
        
        Args:
            text: The text to generate embedding for
            model: Embedding model name
            
        Returns:
            Dictionary with embedding vector and metadata
        """
        try:
            # Currently we only support OpenAI embeddings
            # We could add support for other providers in the future
            return await self._get_embedding_openai(text, model)
        except Exception as e:
            logger.error(f"Failed to generate embedding with {model}: {e}")
            # Try fallback model
            if model != "text-embedding-ada-002":
                logger.info("Trying fallback embedding model")
                try:
                    return await self._get_embedding_openai(text, "text-embedding-ada-002")
                except Exception as fallback_error:
                    logger.error(f"Fallback embedding also failed: {fallback_error}")
            raise
    
    async def _get_embedding_openai(
        self,
        text: str,
        model: str
    ) -> Dict[str, Any]:
        """
        Generate embedding using OpenAI API
        
        Args:
            text: Text to get embedding for
            model: OpenAI embedding model name
            
        Returns:
            Dictionary with embedding vector and metadata
        """
        try:
            api_key = self.api_keys.get("openai")
            if not api_key:
                raise ValueError("OpenAI API key not found")
            
            # Prepare request
            url = "https://api.openai.com/v1/embeddings"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Prepare payload
            payload = {
                "model": model,
                "input": text,
                "encoding_format": "float"
            }
            
            # Make request
            response = await self.client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            
            # Extract embedding
            embedding = result["data"][0]["embedding"]
            
            return {
                "embedding": embedding,
                "model": model,
                "provider": "openai",
                "usage": result.get("usage", {})
            }
            
        except Exception as e:
            logger.error(f"Failed to generate embedding with OpenAI: {e}")
            raise
    
    async def check_health(self) -> Dict[str, Any]:
        """Check health of LLM providers"""
        results = {}
        
        # Check Anthropic
        if self.api_keys.get("claude"):
            try:
                # Simple ping to Anthropic API
                url = "https://api.anthropic.com/v1/models"
                headers = {
                    "x-api-key": self.api_keys["claude"],
                    "anthropic-version": "2023-06-01"
                }
                response = await self.client.get(url, headers=headers)
                results["anthropic"] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "status_code": response.status_code
                }
            except Exception as e:
                results["anthropic"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        # Check OpenAI
        if self.api_keys.get("openai"):
            try:
                # Simple ping to OpenAI API
                url = "https://api.openai.com/v1/models"
                headers = {
                    "Authorization": f"Bearer {self.api_keys['openai']}"
                }
                response = await self.client.get(url, headers=headers)
                results["openai"] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "status_code": response.status_code
                }
            except Exception as e:
                results["openai"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        # Check Google
        if self.api_keys.get("google"):
            try:
                # Simple ping to Google API
                model = "gemini-2.0"
                url = f"https://generativelanguage.googleapis.com/v1/models/{model}?key={self.api_keys['google']}"
                response = await self.client.get(url)
                results["google"] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "status_code": response.status_code
                }
            except Exception as e:
                results["google"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        # Overall status
        overall_status = "healthy"
        for provider, status in results.items():
            if status["status"] != "healthy":
                overall_status = "degraded"
                break
        
        return {
            "status": overall_status,
            "providers": results,
            "timestamp": time.time()
        }

# Singleton instance
_llm_client_instance = None

def get_llm_client() -> LLMClient:
    """Get the singleton instance of LLMClient"""
    global _llm_client_instance
    if _llm_client_instance is None:
        _llm_client_instance = LLMClient()
    return _llm_client_instance

async def init_llm_client():
    """Initialize LLM client"""
    client = get_llm_client()
    # No specific initialization needed for LLM client
    return client

async def close_llm_client():
    """Close LLM client"""
    global _llm_client_instance
    if _llm_client_instance is not None:
        await _llm_client_instance.close()
        _llm_client_instance = None
