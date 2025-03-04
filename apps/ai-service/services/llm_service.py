import os
import logging
import time
import json
from typing import Dict, Any, List, Optional, Union, Callable, Tuple
from functools import lru_cache
from enum import Enum

import openai
import anthropic
import google.generativeai as genai
import groq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from pydantic import BaseModel

from sqlalchemy.ext.asyncio import AsyncSession
from ai_service.services.content_safety_service import get_content_safety_service, ContentSafetyService
from ai_service.utils.resilience import async_circuit_breaker, CircuitBreakerOpenError
from ai_service.utils.tracing import trace_llm_call

logger = logging.getLogger("ai_service.services.llm_service")

class ModelComplexity(str, Enum):
    LOW = "low"       # Simple tasks like classification, short answers
    MEDIUM = "medium" # Standard tasks like content generation, summarization
    HIGH = "high"     # Complex tasks like analysis, reasoning, multi-step tasks

class ModelConfig(BaseModel):
    """Configuration for a specific LLM model"""
    provider: str
    model_name: str
    default_temperature: float
    default_max_tokens: int
    cost_per_1k_input_tokens: float
    cost_per_1k_output_tokens: float
    api_key_env_var: str
    
    # Capabilities
    streaming_supported: bool = True
    supports_function_calling: bool = False
    supports_json_mode: bool = False
    context_window: int = 16000
    supports_vision: bool = False
    
    # Performance characteristics per complexity level (0-1 score)
    typical_performance: Dict[str, float] = {}

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
    
    def __init__(self):
        self.model_configs = self._initialize_model_configs()
        
        # Cost tracking
        self.cost_tracking = {
            "total": 0.0,
            "models": {},  # model_name -> cost
            "users": {}    # user_id -> cost
        }
        
        # Usage metrics
        self.usage_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "models": {},  # model_name -> calls
            "average_latency": {}  # model_name -> avg_latency in ms
        }
        
        # Model selection cache
        self.model_selection_cache = {}
    
    def _initialize_model_configs(self) -> Dict[str, ModelConfig]:
        """Initialize configurations for all supported models"""
        return {
            # Anthropic models
            "claude-3-7-sonnet": ModelConfig(
                provider="anthropic",
                model_name="claude-3-7-sonnet-20240620",
                default_temperature=0.7,
                default_max_tokens=4096,
                cost_per_1k_input_tokens=0.003,
                cost_per_1k_output_tokens=0.015,
                api_key_env_var="ANTHROPIC_API_KEY",
                supports_json_mode=True,
                context_window=200000,
                supports_vision=True,
                typical_performance={
                    ModelComplexity.LOW.value: 0.96,
                    ModelComplexity.MEDIUM.value: 0.94,
                    ModelComplexity.HIGH.value: 0.90
                }
            ),
            "claude-3-5-sonnet": ModelConfig(
                provider="anthropic",
                model_name="claude-3-5-sonnet-20240620",
                default_temperature=0.7,
                default_max_tokens=4096,
                cost_per_1k_input_tokens=0.003,
                cost_per_1k_output_tokens=0.015,
                api_key_env_var="ANTHROPIC_API_KEY",
                supports_json_mode=True,
                context_window=200000,
                supports_vision=True,
                typical_performance={
                    ModelComplexity.LOW.value: 0.95,
                    ModelComplexity.MEDIUM.value: 0.93,
                    ModelComplexity.HIGH.value: 0.89
                }
            ),
            
            # OpenAI models
            "gpt-4o": ModelConfig(
                provider="openai",
                model_name="gpt-4o-2024-05-13",
                default_temperature=0.7,
                default_max_tokens=4096,
                cost_per_1k_input_tokens=0.005,
                cost_per_1k_output_tokens=0.015,
                api_key_env_var="OPENAI_API_KEY",
                supports_function_calling=True,
                supports_json_mode=True,
                context_window=128000,
                supports_vision=True,
                typical_performance={
                    ModelComplexity.LOW.value: 0.95,
                    ModelComplexity.MEDIUM.value: 0.93,
                    ModelComplexity.HIGH.value: 0.91
                }
            ),
            "gpt-4-turbo": ModelConfig(
                provider="openai",
                model_name="gpt-4-turbo-2024-04-09",
                default_temperature=0.7,
                default_max_tokens=4096,
                cost_per_1k_input_tokens=0.01,
                cost_per_1k_output_tokens=0.03,
                api_key_env_var="OPENAI_API_KEY",
                supports_function_calling=True,
                supports_json_mode=True,
                context_window=128000,
                supports_vision=True,
                typical_performance={
                    ModelComplexity.LOW.value: 0.94,
                    ModelComplexity.MEDIUM.value: 0.92,
                    ModelComplexity.HIGH.value: 0.90
                }
            ),
            
            # Google models
            "gemini-1.5-pro": ModelConfig(
                provider="google",
                model_name="gemini-1.5-pro",
                default_temperature=0.7,
                default_max_tokens=4096,
                cost_per_1k_input_tokens=0.0005,
                cost_per_1k_output_tokens=0.0015,
                api_key_env_var="GOOGLE_AI_API_KEY",
                supports_json_mode=True,
                context_window=1000000,
                supports_vision=True,
                typical_performance={
                    ModelComplexity.LOW.value: 0.93,
                    ModelComplexity.MEDIUM.value: 0.91,
                    ModelComplexity.HIGH.value: 0.87
                }
            ),
            
            # Additional providers can be added here
            "groq-llama3": ModelConfig(
                provider="groq",
                model_name="llama3-8b-8192",
                default_temperature=0.7,
                default_max_tokens=4096,
                cost_per_1k_input_tokens=0.0001,
                cost_per_1k_output_tokens=0.0002,
                api_key_env_var="GROQ_API_KEY",
                context_window=8192,
                typical_performance={
                    ModelComplexity.LOW.value: 0.91,
                    ModelComplexity.MEDIUM.value: 0.88,
                    ModelComplexity.HIGH.value: 0.82
                }
            ),
        }
    
    async def generate_email(
        self,
        prompt: str,
        context: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        task_complexity: str = ModelComplexity.MEDIUM.value,
        formality: str = "formal",
        user_id: Optional[str] = None,
        cost_sensitive: bool = False,
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate an email using the optimal LLM for the task."""
        system_prompt = "You are an expert email composer. Create a professional, well-structured email based on the provided instructions."
        
        # Determine the optimal temperature based on formality
        if temperature is None:
            if formality == "formal":
                temperature = self.recommend_temperature_for_task("email_formal")
            else:
                temperature = self.recommend_temperature_for_task("email_casual")
        
        if context:
            full_prompt = f"{prompt}\n\nAdditional context: {context}"
        else:
            full_prompt = prompt
            
        # Create chat messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt}
        ]
        
        # If no model is specified, let the system automatically select the best model
        # Generate using appropriate provider with intelligent model selection if needed
        response, metadata = await self.chat_completion(
            messages=messages,
            provider=provider,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            task_complexity=task_complexity,
            user_id=user_id,
            cost_sensitive=cost_sensitive
        )
        
        # Add task-specific metadata
        metadata["task"] = "email_generation"
        metadata["prompt_length"] = len(full_prompt)
        metadata["response_length"] = len(response)
        
        return response, metadata
        
    @trace_llm_call
    @retry(
        retry=retry_if_exception_type((openai.RateLimitError, anthropic.RateLimitError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        provider: str = None,
        model: str = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        user_id: Optional[str] = None,
        skip_safety_check: bool = False,
        json_mode: bool = False,
        task_complexity: str = ModelComplexity.MEDIUM.value,
        requires_vision: bool = False,
        requires_function_calling: bool = False,
        cost_sensitive: bool = False,
    ) -> Tuple[str, Dict[str, Any]]:
        """Send a chat completion request to the appropriate provider with enhanced tracking."""
        start_time = time.time()
        metadata = {}
        
        # If no model is specified, select the best model for this task
        if model is None:
            model = self.select_model_for_task(
                task_complexity=task_complexity,
                requires_vision=requires_vision,
                requires_function_calling=requires_function_calling,
                cost_sensitive=cost_sensitive
            )
            metadata["model_selected"] = model
            metadata["auto_selection"] = True
        
        # Get the model configuration
        if model not in self.model_configs:
            raise ValueError(f"Unknown model: {model}")
            
        model_config = self.model_configs[model]
        provider = model_config.provider
        
        # Use provided parameters or fall back to model defaults
        temp = temperature if temperature is not None else model_config.default_temperature
        tokens = max_tokens if max_tokens is not None else model_config.default_max_tokens
        
        # Initialize usage tracking for this model if it doesn't exist
        if model not in self.usage_stats["models"]:
            self.usage_stats["models"][model] = 0
        if model not in self.usage_stats["average_latency"]:
            self.usage_stats["average_latency"][model] = 0
        if model not in self.cost_tracking["models"]:
            self.cost_tracking["models"][model] = 0.0
            
        # Update usage statistics
        self.usage_stats["total_calls"] += 1
        self.usage_stats["models"][model] += 1
        
        # Track user costs if user_id is provided
        if user_id and user_id not in self.cost_tracking["users"]:
            self.cost_tracking["users"][user_id] = 0.0
            
        metadata["provider"] = provider
        metadata["model"] = model
        metadata["temperature"] = temp
        metadata["max_tokens"] = tokens
        
        token_info = self._estimate_token_count(messages)
        metadata["estimated_input_tokens"] = token_info["input_tokens"]
        metadata["estimated_cost"] = self._calculate_cost(
            model_config.cost_per_1k_input_tokens,
            model_config.cost_per_1k_output_tokens,
            token_info["input_tokens"],
            tokens / 2  # Rough estimate of output tokens as half of max_tokens
        )
        
        try:
            # Get response from the appropriate provider with specific optimizations
            if provider == "openai":
                response, response_metadata = await self._openai_completion(
                    messages, model_config, tokens, temp, user_id, json_mode
                )
            elif provider == "anthropic":
                response, response_metadata = await self._anthropic_completion(
                    messages, model_config, tokens, temp, user_id, json_mode
                )
            elif provider == "google":
                response, response_metadata = await self._google_completion(
                    messages, model_config, tokens, temp, user_id, json_mode
                )
            elif provider == "mistral":
                response, response_metadata = await self._mistral_completion(
                    messages, model_config, tokens, temp, user_id, json_mode
                )
            elif provider == "groq":
                response, response_metadata = await self._groq_completion(
                    messages, model_config, tokens, temp, user_id, json_mode
                )
            else:
                raise ValueError(f"Unsupported provider: {provider}")
            
            # Update metadata with response metadata
            metadata.update(response_metadata)
            
            # Calculate and track cost
            if "input_tokens" in metadata and "output_tokens" in metadata:
                cost = self._calculate_cost(
                    model_config.cost_per_1k_input_tokens,
                    model_config.cost_per_1k_output_tokens,
                    metadata["input_tokens"],
                    metadata["output_tokens"]
                )
                metadata["cost"] = cost
                
                # Update cost tracking
                self.cost_tracking["total"] += cost
                self.cost_tracking["models"][model] += cost
                if user_id:
                    self.cost_tracking["users"][user_id] += cost
            
            # Apply content safety filtering if not skipped
            if not skip_safety_check:
                safety_service = get_content_safety_service()
                filtered_response, was_filtered, safety_results = await safety_service.filter_unsafe_content(response)
                
                if was_filtered:
                    logger.warning(f"Content filtered for safety reasons: {json.dumps(safety_results)}")
                    metadata["content_filtered"] = True
                    metadata["safety_results"] = safety_results
                    response = filtered_response
                else:
                    metadata["content_filtered"] = False
            
            # Update success stats
            self.usage_stats["successful_calls"] += 1
            return response, metadata
            
        except Exception as e:
            # Update failure stats
            self.usage_stats["failed_calls"] += 1
            metadata["error"] = str(e)
            logger.error(f"LLM request failed: {str(e)}", exc_info=True)
            raise
            
        finally:
            # Calculate and store latency
            latency = time.time() - start_time
            metadata["latency"] = latency
            
            # Update average latency with exponential moving average
            if model in self.usage_stats["average_latency"]:
                current_avg = self.usage_stats["average_latency"][model]
                call_count = self.usage_stats["models"][model]
                # Weight recent calls more heavily (0.2 weight for newest call)
                self.usage_stats["average_latency"][model] = current_avg * 0.8 + latency * 0.2
            else:
                self.usage_stats["average_latency"][model] = latency
                
            logger.info(
                f"LLM request completed in {latency:.2f}s (provider={provider}, model={model})"
            )
    
    @async_circuit_breaker(
        name="openai",
        failure_threshold=3,
        recovery_timeout=60.0,
        excluded_exceptions=[openai.RateLimitError],
        fallback_function=lambda *args, **kwargs: ("OpenAI service is currently unavailable. Please try again later.", {"error": "circuit_open"})
    )
    async def _openai_completion(
        self, messages, model_config, max_tokens, temperature, user_id, json_mode=False
    ) -> Tuple[str, Dict[str, Any]]:
        """Send a chat completion request to OpenAI with provider-specific optimizations."""
        if not openai_client:
            raise ValueError("OpenAI API key not configured")
            
        model_name = model_config.model_name
        metadata = {}
        
        # Provider-specific optimizations
        api_params = {
            "model": model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        # Add optional parameters based on model capabilities
        if user_id:
            api_params["user"] = user_id
            
        if json_mode and model_config.supports_json_mode:
            api_params["response_format"] = {"type": "json_object"}
            metadata["json_mode"] = True
            
        # Send request with optimized parameters
        response = await openai_client.chat.completions.create(**api_params)
        
        # Extract and track token usage
        if hasattr(response, "usage"):
            metadata["input_tokens"] = response.usage.prompt_tokens
            metadata["output_tokens"] = response.usage.completion_tokens
            metadata["total_tokens"] = response.usage.total_tokens
        
        return response.choices[0].message.content, metadata
    
    @async_circuit_breaker(
        name="anthropic",
        failure_threshold=3,
        recovery_timeout=60.0,
        excluded_exceptions=[anthropic.RateLimitError],
        fallback_function=lambda *args, **kwargs: ("Anthropic service is currently unavailable. Please try again later.", {"error": "circuit_open"})
    )
    async def _anthropic_completion(
        self, messages, model_config, max_tokens, temperature, user_id, json_mode=False
    ) -> Tuple[str, Dict[str, Any]]:
        """Send a chat completion request to Anthropic with provider-specific optimizations."""
        if not anthropic_client:
            raise ValueError("Anthropic API key not configured")
        
        model_name = model_config.model_name
        metadata = {}
            
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
        
        # Provider-specific optimizations
        api_params = {
            "model": model_name,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_prompt,
            "messages": anthropic_messages
        }
        
        # Add Claude-specific optimizations
        if json_mode and model_config.supports_json_mode:
            api_params["response_format"] = {"type": "json"}
            metadata["json_mode"] = True
            
        if user_id:
            api_params["metadata"] = {"user_id": user_id}
        
        response = await anthropic_client.messages.create(**api_params)
        
        # Extract and track token usage
        if hasattr(response, "usage"):
            metadata["input_tokens"] = response.usage.input_tokens
            metadata["output_tokens"] = response.usage.output_tokens
            
        return response.content[0].text, metadata
    
    @async_circuit_breaker(
        name="google",
        failure_threshold=3,
        recovery_timeout=60.0,
        fallback_function=lambda *args, **kwargs: ("Google AI service is currently unavailable. Please try again later.", {"error": "circuit_open"})
    )
    async def _google_completion(
        self, messages, model_config, max_tokens, temperature, user_id, json_mode=False
    ) -> Tuple[str, Dict[str, Any]]:
        """Send a chat completion request to Google AI with provider-specific optimizations."""
        if not GOOGLE_AI_API_KEY:
            raise ValueError("Google AI API key not configured")
        
        model_name = model_config.model_name
        metadata = {}
            
        # Convert messages to Google format
        google_messages = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            google_messages.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })
        
        generation_config = {
            "max_output_tokens": max_tokens,
            "temperature": temperature,
        }
        
        # Add Gemini-specific optimizations
        if json_mode and model_config.supports_json_mode:
            generation_config["response_mime_type"] = "application/json"
            metadata["json_mode"] = True
            
        model_instance = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config
        )
        
        start_time = time.time()
        chat = model_instance.start_chat(history=google_messages)
        response = chat.send_message("")
        
        # Google doesn't provide token usage directly, so we estimate
        metadata["latency"] = time.time() - start_time
        
        # Estimate token counts
        content_length = len(response.text) if response.text else 0
        all_input_text = "".join([msg.get("content", "") for msg in messages])
        
        # Rough estimation: ~4 chars per token
        metadata["estimated_input_tokens"] = len(all_input_text) // 4
        metadata["estimated_output_tokens"] = content_length // 4
        
        return response.text, metadata
    
    @async_circuit_breaker(
        name="mistral",
        failure_threshold=3,
        recovery_timeout=60.0,
        fallback_function=lambda *args, **kwargs: ("Mistral AI service is currently unavailable. Please try again later.", {"error": "circuit_open"})
    )
    async def _mistral_completion(
        self, messages, model_config, max_tokens, temperature, user_id, json_mode=False
    ) -> Tuple[str, Dict[str, Any]]:
        """Send a chat completion request to Mistral AI with provider-specific optimizations."""
        if not mistral_client:
            # Return a mock response for testing if Mistral is not available
            logger.warning("Mistral client not available, returning mock response")
            return "This is a mock response because the Mistral client is not available.", {"mocked": True}
            
        model_name = model_config.model_name
        metadata = {}
        logger.info(f"Using mock Mistral client with model {model_name}")
        
        # Mistral's Python client doesn't support async yet, so wrap in a sync function
        start_time = time.time()
        response = mistral_client.chat(
            model=model_name,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Mistral doesn't provide token usage directly in their simple client
        metadata["latency"] = time.time() - start_time
        
        # Estimate token counts
        content_length = len(response.choices[0].message.content) if response.choices[0].message.content else 0
        all_input_text = "".join([msg.get("content", "") for msg in messages])
        
        # Rough estimation: ~4 chars per token
        metadata["estimated_input_tokens"] = len(all_input_text) // 4
        metadata["estimated_output_tokens"] = content_length // 4
        
        return response.choices[0].message.content, metadata
    
    @async_circuit_breaker(
        name="groq",
        failure_threshold=3,
        recovery_timeout=60.0,
        fallback_function=lambda *args, **kwargs: ("Groq service is currently unavailable. Please try again later.", {"error": "circuit_open"})
    )
    async def _groq_completion(
        self, messages, model_config, max_tokens, temperature, user_id, json_mode=False
    ) -> Tuple[str, Dict[str, Any]]:
        """Send a chat completion request to Groq with provider-specific optimizations."""
        if not groq_client:
            raise ValueError("Groq API key not configured")
            
        model_name = model_config.model_name
        metadata = {}
        
        # Provider-specific optimizations
        api_params = {
            "model": model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        # Add Groq-specific optimizations (they have a similar API to OpenAI)
        if json_mode and model_config.supports_json_mode:
            api_params["response_format"] = {"type": "json_object"}
            metadata["json_mode"] = True
            
        response = await groq_client.chat.completions.create(**api_params)
        
        # Extract token usage if available
        if hasattr(response, "usage"):
            metadata["input_tokens"] = response.usage.prompt_tokens
            metadata["output_tokens"] = response.usage.completion_tokens
            metadata["total_tokens"] = response.usage.total_tokens
        
        return response.choices[0].message.content, metadata
    
    def _estimate_token_count(self, messages: List[Dict[str, str]]) -> Dict[str, int]:
        """Estimate token count for input messages"""
        # Simple estimation: ~4 chars per token on average
        total_chars = sum(len(msg.get("content", "")) for msg in messages)
        estimated_tokens = total_chars // 4
        
        return {
            "input_tokens": estimated_tokens,
            "char_count": total_chars
        }
    
    def _calculate_cost(
        self, 
        input_cost_per_1k: float, 
        output_cost_per_1k: float, 
        input_tokens: int, 
        output_tokens: int
    ) -> float:
        """Calculate the cost of an LLM API call based on token usage"""
        input_cost = (input_tokens / 1000) * input_cost_per_1k
        output_cost = (output_tokens / 1000) * output_cost_per_1k
        return input_cost + output_cost
    
    def select_model_for_task(
        self, 
        task_complexity: str = ModelComplexity.MEDIUM.value,
        requires_vision: bool = False,
        requires_function_calling: bool = False,
        cost_sensitive: bool = False
    ) -> str:
        """Intelligently select the best model for a given task based on requirements and performance"""
        # Cache check for identical requests to avoid recomputation
        cache_key = f"{task_complexity}_{requires_vision}_{requires_function_calling}_{cost_sensitive}"
        if cache_key in self.model_selection_cache:
            return self.model_selection_cache[cache_key]
        
        eligible_models = {}
        
        # Filter by requirements
        for name, config in self.model_configs.items():
            if requires_vision and not config.supports_vision:
                continue
            if requires_function_calling and not config.supports_function_calling:
                continue
            
            # Calculate score based on performance for the given complexity
            score = config.typical_performance.get(task_complexity, 0.5)
            
            # Adjust score based on cost sensitivity
            if cost_sensitive:
                # For cost-sensitive tasks, give bonus to cheaper models
                avg_cost = (config.cost_per_1k_input_tokens + config.cost_per_1k_output_tokens) / 2
                cost_factor = 1.0 - (avg_cost / 0.02)  # Normalize to a 0-1 scale (assuming max cost is 0.02)
                score = score * 0.7 + cost_factor * 0.3  # Weight 70% performance, 30% cost
            
            eligible_models[name] = score
        
        if not eligible_models:
            # Fall back to Claude if no models meet requirements
            selected_model = "claude-3-7-sonnet"
        else:
            # Select highest scoring model
            selected_model = max(eligible_models.items(), key=lambda x: x[1])[0]
        
        # Cache the result
        self.model_selection_cache[cache_key] = selected_model
        return selected_model
    
    def get_cost_tracking(self) -> Dict[str, Any]:
        """Get the current cost tracking information"""
        return self.cost_tracking
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get the current usage statistics"""
        return self.usage_stats
    
    def recommend_temperature_for_task(self, task_type: str) -> float:
        """Recommend optimal temperature setting based on task type"""
        # Map of task types to recommended temperatures
        task_temperature_map = {
            "factual_qa": 0.1,           # Factual Q&A needs deterministic answers
            "summarization": 0.3,        # Summarization should be consistent
            "content_generation": 0.7,   # Standard creative content
            "brainstorming": 0.9,        # High creativity for brainstorming
            "creative_writing": 0.8,     # Creative writing needs variety
            "code_generation": 0.2,      # Code should be consistent
            "classification": 0.0,       # Classifications should be deterministic
            "translation": 0.2,          # Translations should be accurate
            "email_formal": 0.4,         # Formal emails should be somewhat consistent
            "email_casual": 0.7,         # Casual emails can be more varied
        }
        
        return task_temperature_map.get(task_type, 0.7)  # Default to 0.7
        
    async def record_usage(
        self,
        session: AsyncSession,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        user_id: Optional[str] = None,
        cost: Optional[float] = None,
        latency: Optional[float] = None,
        is_success: bool = True,
        task_id: Optional[str] = None,
    ) -> None:
        """Record LLM usage to the database with enhanced metrics"""
        # Calculate cost if not provided
        if cost is None and model in self.model_configs:
            config = self.model_configs[model]
            cost = self._calculate_cost(
                config.cost_per_1k_input_tokens,
                config.cost_per_1k_output_tokens,
                input_tokens,
                output_tokens
            )
        
        # In a full implementation, this would store the usage data in a database
        # For now, we'll just log it with enhanced information
        logger.info(
            f"Usage recorded: provider={provider}, model={model}, "
            f"input_tokens={input_tokens}, output_tokens={output_tokens}, "
            f"cost=${cost:.6f}, latency={latency:.2f}s, success={is_success}, "
            f"user_id={user_id}, task_id={task_id}"
        )
        
        # Update our in-memory tracking as a backup
        if model not in self.cost_tracking["models"]:
            self.cost_tracking["models"][model] = 0.0
        
        if cost is not None:
            self.cost_tracking["total"] += cost
            self.cost_tracking["models"][model] += cost
            if user_id:
                if user_id not in self.cost_tracking["users"]:
                    self.cost_tracking["users"][user_id] = 0.0
                self.cost_tracking["users"][user_id] += cost

@lru_cache()
def get_llm_service() -> LLMService:
    """Get a singleton instance of the LLM service."""
    return LLMService()
