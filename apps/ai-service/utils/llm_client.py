"""
LLM Client Utility for AI Service

This module provides a client for interacting with Large Language Models.
It supports both standard generation and streaming responses for real-time processing.
"""

import logging
import os
import json
import httpx
import asyncio
import time
from typing import Dict, Any, List, Optional, Union, AsyncGenerator, AsyncIterator

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
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0, read=300.0))
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
        system_prompt: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate text from a prompt using the specified model"""
        try:
            # Get adaptive rate limiter
            from .redis_client import get_rate_limiter
            rate_limiter = await get_rate_limiter()
            
            # Determine which provider to use based on model name to create rate limit key
            provider = "unknown"
            if model.startswith("claude"):
                provider = "anthropic"
            elif model.startswith("gpt"):
                provider = "openai"
            elif model.startswith("gemini"):
                provider = "google"
            
            # Create rate limit key including provider, model, and user_id if available
            rate_limit_key = f"llm:{provider}:{model}"
            if user_id:
                rate_limit_key += f":{user_id}"
            
            # Estimate the tokens required for this request
            # This is a simple estimation, not exact
            estimated_prompt_tokens = len(prompt.split()) * 1.3  # rough estimation
            estimated_completion_tokens = max_tokens
            
            # Get tokens per minute (TPM) limit from rate_limits dict or use default
            tpm_limit = self.rate_limits.get(model, {}).get("tpm", 100000)
            rpm_limit = self.rate_limits.get(model, {}).get("rpm", 50)
            
            # Tokens for this request (both prompt and potential max completion)
            request_tokens = estimated_prompt_tokens + estimated_completion_tokens
            
            # Apply adaptive rate limiting
            allowed, info = await rate_limiter.check_rate_limit(
                key=rate_limit_key,
                tokens=int(request_tokens),  # Convert to int as tokens must be whole numbers
                capacity=int(tpm_limit / 3),  # Bucket capacity at 1/3 of monthly TPM limit (shared across all instances)
                refill_rate=int(tpm_limit / (60 * 24 * 30)),  # Tokens per second based on monthly limit
                refill_interval_seconds=1,  # Refill every second
                wait=True  # Wait if rate limited with small delay
            )
            
            # If still not allowed after waiting, the rate limit is severe
            if not allowed:
                raise ValueError(
                    f"Rate limit exceeded for {model}. Please try again in {info.get('wait_time_seconds', 60)} seconds."
                )
            
            # Also respect legacy rate limits for compatibility
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
            
    async def generate_text_stream(
        self,
        prompt: str,
        model: str = "claude-3-7-sonnet",
        temperature: float = 0.7,
        max_tokens: int = 4000,
        system_prompt: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate text from a prompt using the specified model with streaming response"""
        try:
            # Respect rate limits
            await self._respect_rate_limit(model)
            
            # Determine which provider to use based on model name
            if model.startswith("claude"):
                async for chunk in self._stream_with_anthropic(prompt, model, temperature, max_tokens, system_prompt):
                    yield chunk
            elif model.startswith("gpt"):
                async for chunk in self._stream_with_openai(prompt, model, temperature, max_tokens, system_prompt):
                    yield chunk
            elif model.startswith("gemini"):
                async for chunk in self._stream_with_google(prompt, model, temperature, max_tokens, system_prompt):
                    yield chunk
            else:
                raise ValueError(f"Unsupported model: {model}")
                
        except Exception as e:
            logger.error(f"Failed to stream text with {model}: {e}")
            yield {"error": str(e), "text": f"Error: {str(e)}"}
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
            
    async def _stream_with_anthropic(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        system_prompt: Optional[str]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate streaming text using Anthropic Claude API"""
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
                "temperature": temperature,
                "stream": True
            }
            
            # Add system prompt if provided
            if system_prompt:
                payload["system"] = system_prompt
            
            # Start time for tracking
            start_time = time.time()
            accumulated_text = ""
            
            # Make streaming request
            async with self.client.stream("POST", url, headers=headers, json=payload, timeout=300.0) as response:
                # Check for errors
                if response.status_code != 200:
                    error_data = await response.text()
                    raise ValueError(f"Anthropic API error: {response.status_code} - {error_data}")
                
                # Process chunks
                async for chunk in response.aiter_bytes():
                    # Skip empty chunks
                    if not chunk:
                        continue
                    
                    try:
                        # Parse the event
                        chunk_data = chunk.decode("utf-8").strip()
                        if chunk_data.startswith("data: "):
                            data_str = chunk_data[6:]  # Remove "data: " prefix
                            
                            # Skip end event
                            if data_str == "[DONE]":
                                continue
                                
                            # Parse JSON data
                            data = json.loads(data_str)
                            
                            # Extract text content if available
                            delta = ""
                            if "delta" in data and "text" in data["delta"]:
                                delta = data["delta"]["text"]
                            elif "content" in data and len(data["content"]) > 0:
                                # Some Anthropic responses might be structured differently
                                if "text" in data["content"][0]:
                                    delta = data["content"][0]["text"]
                            
                            # Only yield if we have content
                            if delta:
                                accumulated_text += delta
                                yield {
                                    "text": delta,
                                    "model": model,
                                    "provider": "anthropic",
                                    "accumulated_text": accumulated_text,
                                    "finish_reason": None
                                }
                    except json.JSONDecodeError:
                        # Skip invalid JSON
                        continue
                    except Exception as e:
                        logger.error(f"Error processing Anthropic stream chunk: {e}")
                        yield {
                            "error": str(e),
                            "text": "",
                            "model": model,
                            "provider": "anthropic"
                        }
            
            # Final message with metadata
            duration_ms = int((time.time() - start_time) * 1000)
            yield {
                "text": "",
                "model": model,
                "provider": "anthropic",
                "duration_ms": duration_ms,
                "accumulated_text": accumulated_text,
                "finish_reason": "stop",
                "final": True
            }
        
        except Exception as e:
            logger.error(f"Error streaming from Anthropic: {e}")
            yield {
                "error": str(e),
                "text": f"Error: {str(e)}",
                "model": model,
                "provider": "anthropic"
            }
    
    async def _stream_with_openai(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        system_prompt: Optional[str]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate streaming text using OpenAI API"""
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
                "temperature": temperature,
                "stream": True
            }
            
            # Start time for tracking
            start_time = time.time()
            accumulated_text = ""
            
            # Make streaming request
            async with self.client.stream("POST", url, headers=headers, json=payload, timeout=300.0) as response:
                # Check for errors
                if response.status_code != 200:
                    error_data = await response.text()
                    raise ValueError(f"OpenAI API error: {response.status_code} - {error_data}")
                
                # Process chunks
                async for chunk in response.aiter_bytes():
                    # Skip empty chunks
                    if not chunk:
                        continue
                    
                    try:
                        # Parse the event
                        chunk_data = chunk.decode("utf-8").strip()
                        if chunk_data.startswith("data: "):
                            data_str = chunk_data[6:]  # Remove "data: " prefix
                            
                            # Skip end event
                            if data_str == "[DONE]":
                                continue
                                
                            # Parse JSON data
                            data = json.loads(data_str)
                            
                            # Extract delta text
                            if "choices" in data and len(data["choices"]) > 0:
                                choice = data["choices"][0]
                                if "delta" in choice and "content" in choice["delta"]:
                                    delta = choice["delta"]["content"]
                                    accumulated_text += delta
                                    yield {
                                        "text": delta,
                                        "model": model,
                                        "provider": "openai",
                                        "accumulated_text": accumulated_text,
                                        "finish_reason": choice.get("finish_reason")
                                    }
                    except json.JSONDecodeError:
                        # Skip invalid JSON
                        continue
                    except Exception as e:
                        logger.error(f"Error processing OpenAI stream chunk: {e}")
                        yield {
                            "error": str(e),
                            "text": "",
                            "model": model,
                            "provider": "openai"
                        }
            
            # Final message with metadata
            duration_ms = int((time.time() - start_time) * 1000)
            yield {
                "text": "",
                "model": model,
                "provider": "openai",
                "duration_ms": duration_ms,
                "accumulated_text": accumulated_text,
                "finish_reason": "stop",
                "final": True
            }
        
        except Exception as e:
            logger.error(f"Error streaming from OpenAI: {e}")
            yield {
                "error": str(e),
                "text": f"Error: {str(e)}",
                "model": model,
                "provider": "openai"
            }
    
    async def _stream_with_google(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        system_prompt: Optional[str]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate streaming text using Google Gemini API"""
        try:
            api_key = self.api_keys.get("google")
            if not api_key:
                raise ValueError("Google API key not found")
            
            # Prepare request
            url = f"https://generativelanguage.googleapis.com/v1/models/{model}:streamGenerateContent?key={api_key}"
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
            
            # Start time for tracking
            start_time = time.time()
            accumulated_text = ""
            
            # Make streaming request
            async with self.client.stream("POST", url, headers=headers, json=payload, timeout=300.0) as response:
                # Check for errors
                if response.status_code != 200:
                    error_data = await response.text()
                    raise ValueError(f"Google API error: {response.status_code} - {error_data}")
                
                # Process chunks
                buffer = b""
                async for chunk in response.aiter_bytes():
                    # Append chunk to buffer
                    buffer += chunk
                    
                    # Try to parse complete JSON objects from buffer
                    try:
                        # Find a complete JSON object
                        obj_end = buffer.find(b"}\n")
                        while obj_end != -1:
                            obj_data = buffer[:obj_end + 1]
                            buffer = buffer[obj_end + 2:]  # Move past "}\n"
                            
                            # Parse the object
                            data = json.loads(obj_data)
                            
                            # Extract text content
                            if "candidates" in data and len(data["candidates"]) > 0:
                                candidate = data["candidates"][0]
                                if "content" in candidate and "parts" in candidate["content"]:
                                    parts = candidate["content"]["parts"]
                                    for part in parts:
                                        if "text" in part:
                                            delta = part["text"]
                                            accumulated_text += delta
                                            yield {
                                                "text": delta,
                                                "model": model,
                                                "provider": "google",
                                                "accumulated_text": accumulated_text,
                                                "finish_reason": candidate.get("finishReason")
                                            }
                            
                            # Look for next object
                            obj_end = buffer.find(b"}\n")
                    except json.JSONDecodeError:
                        # Not enough data for a complete object
                        continue
                    except Exception as e:
                        logger.error(f"Error processing Google stream chunk: {e}")
                        yield {
                            "error": str(e),
                            "text": "",
                            "model": model,
                            "provider": "google"
                        }
            
            # Final message with metadata
            duration_ms = int((time.time() - start_time) * 1000)
            yield {
                "text": "",
                "model": model,
                "provider": "google",
                "duration_ms": duration_ms,
                "accumulated_text": accumulated_text,
                "finish_reason": "stop",
                "final": True
            }
        
        except Exception as e:
            logger.error(f"Error streaming from Google: {e}")
            yield {
                "error": str(e),
                "text": f"Error: {str(e)}",
                "model": model,
                "provider": "google"
            }
    
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
