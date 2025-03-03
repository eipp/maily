import os
import logging
import time
import json
from typing import Dict, Any, List, Optional, Union, Callable, Tuple
from functools import lru_cache

import openai
import anthropic
import google.generativeai as genai
import groq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from sqlalchemy.ext.asyncio import AsyncSession
from ai_service.services.content_safety_service import get_content_safety_service, ContentSafetyService
from ai_service.utils.resilience import async_circuit_breaker, CircuitBreakerOpenError

logger = logging.getLogger("ai_service.services.llm_service")

# Mock implementation for Mistral
class MistralClient:
    def __init__(self, api_key=None):
        self.api_key = api_key
        
    def chat(self, model, messages, max_tokens=None, temperature=None):
        return MockResponse()

class MockResponse:
    def __init__(self):
        self.choices = [MockChoice()]

class MockChoice:
    def __init__(self):
        self.message = MockMessage()

class MockMessage:
    def __init__(self):
        self.content = "This is a mock response because the Mistral client is not available."

# Initialize API keys from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize clients
openai_client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
anthropic_client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
mistral_client = MistralClient(api_key=MISTRAL_API_KEY) if MISTRAL_API_KEY else None
groq_client = groq.AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Initialize Google AI
if GOOGLE_AI_API_KEY:
    genai.configure(api_key=GOOGLE_AI_API_KEY)

class LLMService:
    """Service for interacting with various LLM providers."""
    
    async def generate_email(
        self,
        provider: str,
        model: str,
        prompt: str,
        context: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """Generate an email using the specified LLM."""
        system_prompt = "You are an expert email composer. Create a professional, well-structured email based on the provided instructions."
        
        if context:
            full_prompt = f"{prompt}\n\nAdditional context: {context}"
        else:
            full_prompt = prompt
            
        # Create chat messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt}
        ]
        
        # Generate using appropriate provider
        response = await self.chat_completion(
            messages=messages,
            provider=provider,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response
        
    @retry(
        retry=retry_if_exception_type((openai.RateLimitError, anthropic.RateLimitError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        provider: str,
        model: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        user_id: Optional[str] = None,
        skip_safety_check: bool = False,
    ) -> str:
        """Send a chat completion request to the appropriate provider."""
        start_time = time.time()
        
        try:
            # Get response from the appropriate provider
            if provider == "openai":
                response = await self._openai_completion(messages, model, max_tokens, temperature, user_id)
            elif provider == "anthropic":
                response = await self._anthropic_completion(messages, model, max_tokens, temperature, user_id)
            elif provider == "google":
                response = await self._google_completion(messages, model, max_tokens, temperature, user_id)
            elif provider == "mistral":
                response = await self._mistral_completion(messages, model, max_tokens, temperature, user_id)
            elif provider == "groq":
                response = await self._groq_completion(messages, model, max_tokens, temperature, user_id)
            else:
                raise ValueError(f"Unsupported provider: {provider}")
            
            # Apply content safety filtering if not skipped
            if not skip_safety_check:
                safety_service = get_content_safety_service()
                filtered_response, was_filtered, safety_results = await safety_service.filter_unsafe_content(response)
                
                if was_filtered:
                    logger.warning(f"Content filtered for safety reasons: {json.dumps(safety_results)}")
                    
                    # You might want to record this in a database for review
                    # You could also implement different handling strategies based on the severity
                    
                    return filtered_response
            
            return response
        finally:
            logger.info(
                f"LLM request completed in {time.time() - start_time:.2f}s (provider={provider}, model={model})"
            )
    
    @async_circuit_breaker(
        name="openai",
        failure_threshold=3,
        recovery_timeout=60.0,
        excluded_exceptions=[openai.RateLimitError],
        fallback_function=lambda *args, **kwargs: "OpenAI service is currently unavailable. Please try again later."
    )
    async def _openai_completion(
        self, messages, model, max_tokens, temperature, user_id
    ) -> str:
        """Send a chat completion request to OpenAI."""
        if not openai_client:
            raise ValueError("OpenAI API key not configured")
            
        response = await openai_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            user=user_id,
        )
        
        return response.choices[0].message.content
    
    @async_circuit_breaker(
        name="anthropic",
        failure_threshold=3,
        recovery_timeout=60.0,
        excluded_exceptions=[anthropic.RateLimitError],
        fallback_function=lambda *args, **kwargs: "Anthropic service is currently unavailable. Please try again later."
    )
    async def _anthropic_completion(
        self, messages, model, max_tokens, temperature, user_id
    ) -> str:
        """Send a chat completion request to Anthropic."""
        if not anthropic_client:
            raise ValueError("Anthropic API key not configured")
            
        # Convert messages to Anthropic format
        system_prompt = ""
        anthropic_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        response = await anthropic_client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=anthropic_messages
        )
        
        return response.content[0].text
    
    @async_circuit_breaker(
        name="google",
        failure_threshold=3,
        recovery_timeout=60.0,
        fallback_function=lambda *args, **kwargs: "Google AI service is currently unavailable. Please try again later."
    )
    async def _google_completion(
        self, messages, model, max_tokens, temperature, user_id
    ) -> str:
        """Send a chat completion request to Google AI."""
        if not GOOGLE_AI_API_KEY:
            raise ValueError("Google AI API key not configured")
            
        # Convert messages to Google format
        google_messages = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            google_messages.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })
            
        model_instance = genai.GenerativeModel(
            model_name=model,
            generation_config={
                "max_output_tokens": max_tokens,
                "temperature": temperature,
            }
        )
        
        chat = model_instance.start_chat(history=google_messages)
        response = chat.send_message("")
        
        return response.text
    
    @async_circuit_breaker(
        name="mistral",
        failure_threshold=3,
        recovery_timeout=60.0,
        fallback_function=lambda *args, **kwargs: "Mistral AI service is currently unavailable. Please try again later."
    )
    async def _mistral_completion(
        self, messages, model, max_tokens, temperature, user_id
    ) -> str:
        """Send a chat completion request to Mistral AI."""
        if not mistral_client:
            # Return a mock response for testing if Mistral is not available
            logger.warning("Mistral client not available, returning mock response")
            return "This is a mock response because the Mistral client is not available."
            
        logger.info(f"Using mock Mistral client with model {model}")
        # Mistral's Python client doesn't support async yet, so wrap in a sync function
        response = mistral_client.chat(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.choices[0].message.content
    
    @async_circuit_breaker(
        name="groq",
        failure_threshold=3,
        recovery_timeout=60.0,
        fallback_function=lambda *args, **kwargs: "Groq service is currently unavailable. Please try again later."
    )
    async def _groq_completion(
        self, messages, model, max_tokens, temperature, user_id
    ) -> str:
        """Send a chat completion request to Groq."""
        if not groq_client:
            raise ValueError("Groq API key not configured")
            
        response = await groq_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        
        return response.choices[0].message.content
    
    async def record_usage(
        self,
        session: AsyncSession,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        user_id: Optional[str] = None,
    ) -> None:
        """Record LLM usage to the database."""
        # In a full implementation, this would store the usage data in a database
        # For now, we'll just log it
        logger.info(
            f"Usage recorded: provider={provider}, model={model}, "
            f"input_tokens={input_tokens}, output_tokens={output_tokens}, "
            f"user_id={user_id}"
        )

@lru_cache()
def get_llm_service() -> LLMService:
    """Get a singleton instance of the LLM service."""
    return LLMService()
