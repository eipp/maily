"""
Enhanced OpenAI adapter implementation with validation and confidence scoring.
Uses the OpenAI API with additional capabilities for monitoring, validation, and confidence assessment.
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any, Union, AsyncIterator
import time
import asyncio
from openai import AsyncOpenAI

from apps.api.ai.adapters.base import (
    EnhancedModelAdapter,
    EnhancedModelRequest,
    EnhancedModelResponse,
    ModelRequest,
    ModelResponse,
    ValidationResult,
    ModelProvider,
    ModelCapability,
    ConfidenceLevel
)

# Configure logging
logger = logging.getLogger("ai.adapters.openai")

class EnhancedOpenAIAdapter(EnhancedModelAdapter):
    """
    Enhanced OpenAI adapter with validation and confidence scoring.

    Features:
    - Support for all OpenAI models including GPT-4, GPT-3.5
    - Tool use and function calling support
    - Response validation and confidence scoring
    - Detailed performance metrics
    - Automatic token counting and cost estimation
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = "gpt-4o",
        organization: Optional[str] = None,
        base_url: Optional[str] = None,
        config: Dict[str, Any] = None
    ):
        """Initialize the OpenAI adapter"""
        # Get API key from environment if not provided
        if api_key is None:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key is required. Provide it directly or set OPENAI_API_KEY environment variable.")

        # Initialize the base class
        super().__init__(
            provider=ModelProvider.OPENAI,
            default_model=default_model,
            api_key=api_key,
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CHAT,
                ModelCapability.EMBEDDINGS,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.CODE_GENERATION,
                ModelCapability.VISION,
            ],
            config=config or {}
        )

        # Initialize the OpenAI client
        self.client = AsyncOpenAI(
            api_key=api_key,
            organization=organization,
            base_url=base_url,
        )

        # Store additional config
        self.organization = organization
        self.base_url = base_url

        # Set up model family mapping
        self.model_families = {
            "gpt-4": ["gpt-4", "gpt-4-32k", "gpt-4-turbo", "gpt-4o", "gpt-4-vision"],
            "gpt-3.5": ["gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-3.5-turbo-instruct"],
            "embedding": ["text-embedding-ada-002", "text-embedding-3-small", "text-embedding-3-large"],
        }

        logger.info(f"Initialized EnhancedOpenAIAdapter with default model: {default_model}")

    def _prepare_messages(self, prompt: str, system_message: Optional[str] = None) -> List[Dict[str, str]]:
        """Prepare messages for the OpenAI chat API"""
        messages = []

        # Add system message if provided
        if system_message:
            messages.append({"role": "system", "content": system_message})

        # Add user message
        messages.append({"role": "user", "content": prompt})

        return messages

    def _prepare_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare tools for the OpenAI API"""
        if not tools:
            return None

        formatted_tools = []
        for tool in tools:
            if "function" in tool:
                formatted_tools.append({
                    "type": "function",
                    "function": tool["function"]
                })
            elif "name" in tool and "description" in tool and "parameters" in tool:
                formatted_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool["parameters"]
                    }
                })

        return formatted_tools if formatted_tools else None

    def _extract_function_calls(self, response_message: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract function calls from response message"""
        function_calls = []

        if "tool_calls" in response_message:
            for tool_call in response_message["tool_calls"]:
                if tool_call["type"] == "function":
                    function_call = tool_call["function"]
                    try:
                        arguments = json.loads(function_call["arguments"])
                    except json.JSONDecodeError:
                        arguments = function_call["arguments"]

                    function_calls.append({
                        "name": function_call["name"],
                        "arguments": arguments,
                        "id": tool_call["id"]
                    })

        return function_calls

    async def generate(self, request: ModelRequest) -> ModelResponse:
        """
        Generate a response from the OpenAI model.
        This implements the base abstract method from BaseModelAdapter.
        """
        model = request.model_name
        system_message = request.metadata.get("system_message")

        try:
            # Prepare messages
            messages = self._prepare_messages(request.prompt, system_message)

            # Make API call
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                frequency_penalty=request.frequency_penalty,
                presence_penalty=request.presence_penalty,
                stop=request.stop_sequences,
                user=request.user_id,
                stream=False
            )

            # Extract response content
            content = response.choices[0].message.content or ""

            # Build usage dictionary
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }

            # Create response
            return ModelResponse(
                content=content,
                model_name=model,
                usage=usage,
                finish_reason=response.choices[0].finish_reason,
                metadata={
                    "id": response.id,
                    "created": response.created,
                    "model": response.model
                }
            )

        except Exception as e:
            logger.error(f"Error in OpenAI generate: {str(e)}")
            raise

    async def enhanced_generate(self, request: EnhancedModelRequest) -> EnhancedModelResponse:
        """
        Enhanced generation with validation and confidence scoring.
        This method extends the basic generate method with additional capabilities.
        """
        start_time = time.time()
        model = request.model_name
        system_message = request.metadata.get("system_message")

        # Default to the configured default model if not specified
        if not model:
            model = self.default_model

        try:
            # Prepare messages
            messages = self._prepare_messages(request.prompt, system_message)

            # Prepare tools if provided
            tools = self._prepare_tools(request.tools)
            tool_choice = request.tool_choice if request.tool_choice else "auto"

            # Make API call
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                frequency_penalty=request.frequency_penalty,
                presence_penalty=request.presence_penalty,
                stop=request.stop_sequences,
                user=request.user_id,
                tools=tools,
                tool_choice=tool_choice if tools else None,
                stream=False
            )

            # Extract response content
            content = response.choices[0].message.content or ""

            # Extract function calls if any
            function_calls = self._extract_function_calls(response.choices[0].message.model_dump())

            # Create enhanced response
            enhanced_response = EnhancedModelResponse(
                content=content,
                model_name=model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                finish_reason=response.choices[0].finish_reason,
                metadata={
                    "id": response.id,
                    "created": response.created,
                    "model": response.model,
                    "response_format": request.expected_format
                },
                provider=ModelProvider.OPENAI,
                trace_id=request.trace_id,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                processing_time_ms=(time.time() - start_time) * 1000,
                function_calls=function_calls if function_calls else None,
                raw_response=response.model_dump()
            )

            # Validate response if validation type is specified
            if request.validation_type:
                validation = await self._validate_response(request, enhanced_response)
                enhanced_response.validation = validation

            # Calculate cost estimate
            enhanced_response.cost_estimate_usd = self._estimate_cost(
                ModelProvider.OPENAI,
                model,
                response.usage.prompt_tokens,
                response.usage.completion_tokens
            )

            return enhanced_response

        except Exception as e:
            logger.error(f"Error in OpenAI enhanced_generate: {str(e)}")

            # Create error response with zero confidence
            error_response = EnhancedModelResponse(
                content=f"Error: {str(e)}",
                model_name=model,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                finish_reason="error",
                metadata={"error": str(e)},
                provider=ModelProvider.OPENAI,
                trace_id=request.trace_id,
                processing_time_ms=(time.time() - start_time) * 1000,
                validation=ValidationResult(
                    is_valid=False,
                    errors=[str(e)],
                    confidence_score=0.0,
                    confidence_level=ConfidenceLevel.UNCERTAIN
                )
            )

            # Track metrics for the failed request
            await self._track_performance(
                model_name=model,
                endpoint="enhanced_generate",
                start_time=start_time,
                input_tokens=0,
                output_tokens=0,
                success=False,
                error_type=type(e).__name__,
                error_message=str(e),
                request_id=request.trace_id,
                user_id=request.user_id
            )

            return error_response

    async def stream_generate(self, request: ModelRequest) -> AsyncIterator[ModelResponse]:
        """
        Stream a response from the OpenAI model.
        This implements the base abstract method from BaseModelAdapter.
        """
        model = request.model_name
        system_message = request.metadata.get("system_message")

        try:
            # Prepare messages
            messages = self._prepare_messages(request.prompt, system_message)

            # Start streaming
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                frequency_penalty=request.frequency_penalty,
                presence_penalty=request.presence_penalty,
                stop=request.stop_sequences,
                user=request.user_id,
                stream=True
            )

            # Iterate through stream and yield responses
            accumulated_content = ""
            prompt_tokens = 0
            completion_tokens = 0

            class ResponseIterator:
                def __init__(self, stream, model_name):
                    self.stream = stream
                    self.model_name = model_name
                    self.accumulated_content = ""
                    self.prompt_tokens = 0
                    self.completion_tokens = 0
                    self.finish_reason = None

                def __aiter__(self):
                    return self

                async def __anext__(self):
                    # Get next chunk
                    try:
                        chunk = await anext(self.stream)
                        delta_content = chunk.choices[0].delta.content or ""
                        self.accumulated_content += delta_content
                        self.finish_reason = chunk.choices[0].finish_reason

                        # Estimate token counts - will be refined with actual counts later
                        if delta_content:
                            self.completion_tokens += len(delta_content.split()) // 3  # Rough estimate

                        # Create response
                        return ModelResponse(
                            content=delta_content,
                            model_name=self.model_name,
                            usage={
                                "prompt_tokens": self.prompt_tokens,
                                "completion_tokens": self.completion_tokens,
                                "total_tokens": self.prompt_tokens + self.completion_tokens
                            },
                            finish_reason=self.finish_reason or "incomplete",
                            metadata={
                                "accumulated_content": self.accumulated_content,
                                "is_streaming": True
                            }
                        )
                    except StopAsyncIteration:
                        raise StopAsyncIteration
                    except Exception as e:
                        logger.error(f"Error in OpenAI stream: {str(e)}")
                        raise StopAsyncIteration

            return ResponseIterator(stream, model)

        except Exception as e:
            logger.error(f"Error setting up OpenAI stream: {str(e)}")
            raise

    async def embed(self, text: Union[str, List[str]]) -> List[List[float]]:
        """
        Generate embeddings for the provided text.
        This implements the base abstract method from BaseModelAdapter.
        """
        try:
            # Handle single string vs list of strings
            input_texts = [text] if isinstance(text, str) else text

            # Make API call
            response = await self.client.embeddings.create(
                model="text-embedding-3-small",  # Default model
                input=input_texts
            )

            # Extract embeddings
            embeddings = [data.embedding for data in response.data]

            return embeddings

        except Exception as e:
            logger.error(f"Error in OpenAI embed: {str(e)}")
            raise

    async def check_health(self) -> Dict[str, Any]:
        """
        Check the health of the OpenAI service.
        This implements the base abstract method from BaseModelAdapter.
        """
        try:
            # Make a simple API call to check health
            start_time = time.time()
            await self.client.models.list()
            latency = (time.time() - start_time) * 1000  # ms

            return {
                "status": "ok",
                "provider": "openai",
                "latency_ms": latency,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            logger.error(f"OpenAI health check failed: {str(e)}")
            return {
                "status": "error",
                "provider": "openai",
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }

    async def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the available OpenAI models.
        This implements the base abstract method from BaseModelAdapter.
        """
        try:
            # Get list of models
            models = await self.client.models.list()

            # Filter and organize models
            model_info = {
                "provider": "openai",
                "default_model": self.default_model,
                "available_models": [model.id for model in models.data],
                "model_families": self.model_families,
                "capabilities": {
                    "text_generation": True,
                    "chat": True,
                    "embeddings": True,
                    "function_calling": True,
                    "code_generation": True,
                    "vision": True
                }
            }

            return model_info

        except Exception as e:
            logger.error(f"Error getting OpenAI model info: {str(e)}")
            return {
                "provider": "openai",
                "error": str(e),
                "default_model": self.default_model,
                "model_families": self.model_families
            }
