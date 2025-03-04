import os
import logging
import time
import asyncio
from typing import Dict, List, Optional, Any, Union, AsyncIterator
import openai
from openai import AsyncOpenAI
from pydantic import BaseModel
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

from .base import BaseModelAdapter, ModelRequest, ModelResponse
from .adapter_utils import AdapterInitializer, ResponseIteratorFactory, CommonModelHelpers
from apps.api.errors.ai_service_errors import (
    AIServiceError,
    RateLimitError,
    AuthenticationError,
    ValidationError,
    ServerError,
    NetworkError,
    TimeoutError
)

logger = logging.getLogger(__name__)

# Constants for retry configuration
MAX_RETRIES = 3
MIN_RETRY_WAIT_SECONDS = 1
MAX_RETRY_WAIT_SECONDS = 10

# Constants for model configuration
DEFAULT_CHAT_MODEL = "deepseek-chat"
DEFAULT_REASONING_MODEL = "deepseek-reasoner"
DEFAULT_EMBEDDING_MODEL = "deepseek-embedding"


class DeepSeekAdapter(BaseModelAdapter):
    """
    Adapter for DeepSeek models.

    This adapter implements the BaseModelAdapter interface for DeepSeek models,
    which use the OpenAI-compatible API format with additional features like reasoning.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.deepseek.com", timeout: int = 60):
        """
        Initialize the DeepSeek adapter.

        Args:
            api_key: DeepSeek API key
            base_url: DeepSeek API base URL
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DeepSeek API key is required")
            
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=base_url,
            timeout=timeout
        )
        self.timeout = timeout
        self._initialize_metrics()
        logger.info("DeepSeek adapter initialized")

    def _initialize_metrics(self):
        """Initialize metrics for monitoring."""
        # Initialize metrics here if needed
        self.total_requests = 0
        self.failed_requests = 0
        self.total_tokens = 0
        self.response_times = []

    @retry(
        retry=retry_if_exception_type((NetworkError, ServerError, TimeoutError)),
        wait=wait_exponential(multiplier=1, min=MIN_RETRY_WAIT_SECONDS, max=MAX_RETRY_WAIT_SECONDS),
        stop=stop_after_attempt(MAX_RETRIES),
        before_sleep=lambda retry_state: logger.warning(
            f"Retrying DeepSeek request after error: {retry_state.outcome.exception()}. "
            f"Attempt {retry_state.attempt_number}/{MAX_RETRIES}"
        )
    )
    async def generate(self, request: ModelRequest) -> ModelResponse:
        """
        Generate text with DeepSeek model.

        Args:
            request: Model request

        Returns:
            ModelResponse: Generated text response
        """
        start_time = time.time()
        self.total_requests += 1
        
        try:
            openai_request = self._prepare_openai_request(request)
            is_reasoning = request.model == DEFAULT_REASONING_MODEL
            
            response = await self.client.chat.completions.create(**openai_request)
            
            content = response.choices[0].message.content
            
            # Handle reasoning content if available and model is deepseek-reasoner
            reasoning_content = None
            if is_reasoning and hasattr(response.choices[0].message, 'reasoning_content'):
                reasoning_content = response.choices[0].message.reasoning_content
            
            # Get token usage
            input_tokens = response.usage.prompt_tokens if hasattr(response.usage, 'prompt_tokens') else 0
            output_tokens = response.usage.completion_tokens if hasattr(response.usage, 'completion_tokens') else 0
            total_tokens = response.usage.total_tokens if hasattr(response.usage, 'total_tokens') else 0
            
            self.total_tokens += total_tokens
            
            model_response = ModelResponse(
                text=content,
                model=request.model,
                metadata={
                    "reasoning": reasoning_content,
                    "finish_reason": response.choices[0].finish_reason,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "response_time": time.time() - start_time
                }
            )
            
            self.response_times.append(time.time() - start_time)
            return model_response
            
        except openai.RateLimitError as e:
            return self._handle_rate_limit_error(e, request, start_time)
        except openai.AuthenticationError as e:
            return self._handle_authentication_error(e, request, start_time)
        except openai.BadRequestError as e:
            return self._handle_validation_error(e, request, start_time)
        except openai.APIStatusError as e:
            return self._handle_server_error(e, request, start_time)
        except (openai.APIConnectionError, openai.APITimeoutError) as e:
            return self._handle_network_error(e, request, start_time)
        except asyncio.TimeoutError as e:
            return self._handle_timeout_error(e, request, start_time)
        except Exception as e:
            return self._handle_general_error(e, request, start_time)

    @retry(
        retry=retry_if_exception_type((NetworkError, ServerError, TimeoutError)),
        wait=wait_exponential(multiplier=1, min=MIN_RETRY_WAIT_SECONDS, max=MAX_RETRY_WAIT_SECONDS),
        stop=stop_after_attempt(MAX_RETRIES),
        before_sleep=lambda retry_state: logger.warning(
            f"Retrying DeepSeek streaming request after error: {retry_state.outcome.exception()}. "
            f"Attempt {retry_state.attempt_number}/{MAX_RETRIES}"
        )
    )
    async def stream_generate(self, request: ModelRequest) -> AsyncIterator[ModelResponse]:
        """
        Stream text generation with DeepSeek model.

        Args:
            request: Model request

        Returns:
            AsyncIterator[ModelResponse]: Stream of generated text responses
        """
        start_time = time.time()
        self.total_requests += 1
        
        try:
            openai_request = self._prepare_openai_request(request)
            openai_request["stream"] = True
            is_reasoning = request.model == DEFAULT_REASONING_MODEL
            
            stream = await self.client.chat.completions.create(**openai_request)
            
            # Variables to accumulate values throughout the stream
            accumulated_content = ""
            accumulated_reasoning = ""
            finish_reason = None
            input_tokens = 0
            output_tokens = 0
            
            def extract_content(chunk):
                if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                    return chunk.choices[0].delta.content
                return ""
                
            def extract_reasoning(chunk):
                if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content:
                    return chunk.choices[0].delta.reasoning_content
                return ""
                
            def extract_finish_reason(chunk):
                if hasattr(chunk.choices[0], 'finish_reason') and chunk.choices[0].finish_reason:
                    return chunk.choices[0].finish_reason
                return None
            
            async for chunk in stream:
                content_delta = extract_content(chunk)
                accumulated_content += content_delta
                
                reasoning_delta = ""
                if is_reasoning:
                    reasoning_delta = extract_reasoning(chunk)
                    accumulated_reasoning += reasoning_delta
                
                # Update finish reason if available
                current_finish_reason = extract_finish_reason(chunk)
                if current_finish_reason:
                    finish_reason = current_finish_reason
                
                # Count tokens (approximate)
                output_tokens += len(content_delta.split()) // 4 + 1 if content_delta else 0
                
                # Yield a response for each chunk
                metadata = {
                    "finish_reason": finish_reason,
                    "is_final": False,
                    "response_time": time.time() - start_time
                }
                
                if is_reasoning and reasoning_delta:
                    metadata["reasoning"] = reasoning_delta
                
                yield ModelResponse(
                    text=content_delta,
                    model=request.model,
                    metadata=metadata
                )
            
            # Add final completion marker
            self.total_tokens += input_tokens + output_tokens
            self.response_times.append(time.time() - start_time)
            
            yield ModelResponse(
                text="",
                model=request.model,
                metadata={
                    "finish_reason": finish_reason or "unknown",
                    "reasoning": accumulated_reasoning if is_reasoning else None,
                    "is_final": True,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens,
                    "response_time": time.time() - start_time
                }
            )
            
        except openai.RateLimitError as e:
            yield self._handle_rate_limit_error(e, request, start_time)
        except openai.AuthenticationError as e:
            yield self._handle_authentication_error(e, request, start_time)
        except openai.BadRequestError as e:
            yield self._handle_validation_error(e, request, start_time)
        except openai.APIStatusError as e:
            yield self._handle_server_error(e, request, start_time)
        except (openai.APIConnectionError, openai.APITimeoutError) as e:
            yield self._handle_network_error(e, request, start_time)
        except asyncio.TimeoutError as e:
            yield self._handle_timeout_error(e, request, start_time)
        except Exception as e:
            yield self._handle_general_error(e, request, start_time)
            
    async def check_health(self) -> Dict[str, Any]:
        """
        Check the health of the DeepSeek service.
        
        Returns:
            Dict[str, Any]: Health status information
        """
        start_time = time.time()
        
        try:
            # Make a simple API call to check if the service is responsive
            test_request = ModelRequest(
                model=DEFAULT_CHAT_MODEL,
                prompt="Hello, are you available?",
                max_tokens=5
            )
            openai_request = self._prepare_openai_request(test_request)
            await self.client.chat.completions.create(**openai_request)
            
            return {
                "status": "healthy",
                "latency": time.time() - start_time,
                "provider": "deepseek",
                "timestamp": time.time()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "provider": "deepseek",
                "timestamp": time.time()
            }

    async def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about available DeepSeek models.
        
        Returns:
            Dict[str, Any]: Model information
        """
        # DeepSeek doesn't have a models listing endpoint, so we return static info
        models = [
            {
                "id": "deepseek-chat",
                "name": "DeepSeek Chat",
                "description": "General-purpose chat model from DeepSeek",
                "capabilities": ["chat", "completion"],
                "max_tokens": 4096,
                "pricing": {
                    "input": 0.0001,  # Cost per 1K tokens (adjust as needed)
                    "output": 0.0002  # Cost per 1K tokens (adjust as needed)
                }
            },
            {
                "id": "deepseek-reasoner",
                "name": "DeepSeek Reasoner",
                "description": "Advanced reasoning model from DeepSeek with step-by-step reasoning capabilities",
                "capabilities": ["chat", "completion", "reasoning"],
                "max_tokens": 4096,
                "pricing": {
                    "input": 0.0002,  # Cost per 1K tokens (adjust as needed)
                    "output": 0.0004  # Cost per 1K tokens (adjust as needed)
                }
            }
        ]
        
        categorized_models = self._categorize_models([model["id"] for model in models])
        
        return {
            "provider": "deepseek",
            "models": models,
            "categorized_models": categorized_models,
            "default_model": DEFAULT_CHAT_MODEL,
            "default_reasoning_model": DEFAULT_REASONING_MODEL,
            "total_models": len(models)
        }
        
    def _categorize_models(self, model_ids: List[str]) -> Dict[str, List[str]]:
        """
        Categorize models by capabilities.
        
        Args:
            model_ids: List of model IDs
            
        Returns:
            Dict[str, List[str]]: Categorized models
        """
        categories = {
            "chat": [],
            "reasoning": [],
            "embedding": []
        }
        
        for model_id in model_ids:
            if "chat" in model_id:
                categories["chat"].append(model_id)
            if "reasoner" in model_id:
                categories["reasoning"].append(model_id)
            if "embedding" in model_id:
                categories["embedding"].append(model_id)
        
        return categories
        
    def _prepare_openai_request(self, request: ModelRequest) -> Dict[str, Any]:
        """
        Prepare request for OpenAI API format that DeepSeek uses.
        
        Args:
            request: Model request
            
        Returns:
            Dict[str, Any]: DeepSeek API request
        """
        messages = []
        
        # Add system message if provided
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
            
        # Add prompt as user message
        messages.append({"role": "user", "content": request.prompt})
        
        # Add conversation history if provided
        if request.conversation:
            for entry in request.conversation:
                messages.append({
                    "role": "assistant" if entry.get("is_assistant", False) else "user",
                    "content": entry.get("content", "")
                })
        
        return {
            "model": request.model or DEFAULT_CHAT_MODEL,
            "messages": messages,
            "max_tokens": request.max_tokens or 1024,
            "temperature": request.temperature or 0.7,
            "top_p": request.top_p or 1.0,
            "n": 1,
            "presence_penalty": request.presence_penalty or 0,
            "frequency_penalty": request.frequency_penalty or 0
        }

    # Error handling methods - reusing the same implementation patterns as OpenAI Adapter
    def _handle_timeout_error(self, error: Exception, request: Optional[ModelRequest], start_time: float, operation: str = "generate"):
        self.failed_requests += 1
        logger.error(f"Timeout error in DeepSeek {operation}: {str(error)}")
        raise TimeoutError(f"Request to DeepSeek timed out after {self.timeout} seconds: {str(error)}")

    def _handle_rate_limit_error(self, error: Exception, request: Optional[ModelRequest], start_time: float, operation: str = "generate"):
        self.failed_requests += 1
        logger.error(f"Rate limit error in DeepSeek {operation}: {str(error)}")
        raise RateLimitError(f"DeepSeek rate limit exceeded: {str(error)}")

    def _handle_authentication_error(self, error: Exception, request: Optional[ModelRequest], start_time: float, operation: str = "generate"):
        self.failed_requests += 1
        logger.error(f"Authentication error in DeepSeek {operation}: {str(error)}")
        raise AuthenticationError(f"DeepSeek authentication failed: {str(error)}")

    def _handle_validation_error(self, error: Exception, request: Optional[ModelRequest], start_time: float, operation: str = "generate"):
        self.failed_requests += 1
        logger.error(f"Validation error in DeepSeek {operation}: {str(error)}")
        raise ValidationError(f"DeepSeek validation error: {str(error)}")

    def _handle_server_error(self, error: Exception, request: Optional[ModelRequest], start_time: float, operation: str = "generate"):
        self.failed_requests += 1
        logger.error(f"Server error in DeepSeek {operation}: {str(error)}")
        raise ServerError(f"DeepSeek server error: {str(error)}")

    def _handle_network_error(self, error: Exception, request: Optional[ModelRequest], start_time: float, operation: str = "generate"):
        self.failed_requests += 1
        logger.error(f"Network error in DeepSeek {operation}: {str(error)}")
        raise NetworkError(f"Network error when connecting to DeepSeek: {str(error)}")

    def _handle_general_error(self, error: Exception, request: Optional[ModelRequest], start_time: float, operation: str = "generate"):
        self.failed_requests += 1
        logger.error(f"General error in DeepSeek {operation}: {str(error)}")
        raise AIServiceError(f"Unexpected error with DeepSeek: {str(error)}")

    # Embedding is not currently supported by DeepSeek, but implement for completeness
    async def embed(self, text: Union[str, List[str]]) -> List[List[float]]:
        """
        Generate embeddings for text (not supported yet in DeepSeek).
        
        Args:
            text: Text to embed
            
        Returns:
            List[List[float]]: List of embedding vectors
        """
        raise NotImplementedError("Embedding is not currently supported by DeepSeek adapter") 