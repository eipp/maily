"""
Enhanced base adapter for AI model integrations with advanced capabilities.
Extends the basic adapter with validation, confidence scoring, and performance metrics.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, Callable, Tuple, AsyncIterator, TypeVar
from enum import Enum
import time
import json
import logging
from pydantic import BaseModel, Field

from apps.api.ai.adapters.base import BaseModelAdapter, ModelRequest, ModelResponse

# Configure logging
logger = logging.getLogger("ai.adapters")

# Model provider types
class ModelProvider(str, Enum):
    """Supported AI model providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    COHERE = "cohere"
    MISTRAL = "mistral"
    LLAMA = "llama"
    CUSTOM = "custom"
    AZURE_OPENAI = "azure_openai"
    HUGGINGFACE = "huggingface"
    BEDROCK = "bedrock"
    TOGETHER = "together"


class ModelCapability(str, Enum):
    """AI model capabilities"""
    TEXT_GENERATION = "text_generation"
    CHAT = "chat"
    EMBEDDINGS = "embeddings"
    IMAGE_GENERATION = "image_generation"
    IMAGE_CLASSIFICATION = "image_classification"
    AUDIO_TRANSCRIPTION = "audio_transcription"
    AUDIO_GENERATION = "audio_generation"
    CODE_GENERATION = "code_generation"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    RAG = "rag"


class ConfidenceLevel(str, Enum):
    """Confidence levels for AI responses"""
    HIGH = "high"          # High confidence (>0.9)
    MEDIUM = "medium"      # Medium confidence (0.7-0.9)
    LOW = "low"            # Low confidence (0.5-0.7)
    UNCERTAIN = "uncertain"  # Uncertain (<0.5)


class ValidationResult(BaseModel):
    """Results of validation checks on AI responses"""
    is_valid: bool = True
    errors: List[str] = []
    warnings: List[str] = []
    confidence_score: float = 1.0  # Between 0.0 and 1.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.HIGH
    reasoning_quality: Optional[float] = None  # Score for chain-of-thought quality
    consistency_score: Optional[float] = None  # Internal consistency
    hallucination_likelihood: Optional[float] = None  # Estimated hallucination probability


class EnhancedModelRequest(ModelRequest):
    """Enhanced model request with additional parameters"""
    provider: ModelProvider = ModelProvider.OPENAI
    model_family: Optional[str] = None  # e.g., "gpt-4", "claude", "gemini"
    required_capabilities: List[ModelCapability] = []
    validation_type: Optional[str] = None  # Type of validation to perform
    expected_format: Optional[str] = None  # Expected output format (JSON, XML, etc.)
    debug_mode: bool = False
    trace_id: Optional[str] = None
    priority: int = 1  # 1 (highest) to 5 (lowest)
    timeout_seconds: float = 30.0
    retry_strategy: Optional[Dict[str, Any]] = None
    fallback_config: Optional[Dict[str, Any]] = None
    tools: List[Dict[str, Any]] = []
    tool_choice: Optional[str] = None


class EnhancedModelResponse(ModelResponse):
    """Enhanced model response with confidence and validation information"""
    validation: ValidationResult = Field(default_factory=ValidationResult)
    raw_response: Optional[Dict[str, Any]] = None
    processing_time_ms: Optional[float] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cost_estimate_usd: Optional[float] = None
    provider: Optional[ModelProvider] = None
    trace_id: Optional[str] = None
    reasoning_steps: Optional[List[Dict[str, Any]]] = None
    function_calls: Optional[List[Dict[str, Any]]] = None


class ChainOfThoughtValidationResult(BaseModel):
    """Detailed results of chain-of-thought validation"""
    valid_structure: bool = True
    reasoning_coherence: float = 1.0
    logical_consistency: float = 1.0
    factual_accuracy: Optional[float] = None
    steps_clarity: float = 1.0
    conclusion_alignment: float = 1.0
    missing_steps: List[str] = []
    logical_errors: List[Dict[str, Any]] = []
    detected_steps: List[Dict[str, str]] = []
    overall_score: float = 1.0


class ModelPerformanceMetrics(BaseModel):
    """Performance metrics for AI model requests"""
    request_timestamp: str
    model_name: str
    provider: ModelProvider
    endpoint: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    success: bool
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    validation_result: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None


class EnhancedModelAdapter(BaseModelAdapter):
    """
    Enhanced model adapter with advanced capabilities.

    This extends the base adapter with:
    - Chain-of-thought validation
    - Confidence scoring
    - Performance metrics
    - Advanced error handling
    - Support for modern model capabilities like tool use
    """

    def __init__(
        self,
        provider: ModelProvider,
        default_model: str,
        api_key: str,
        capabilities: List[ModelCapability] = None,
        config: Dict[str, Any] = None
    ):
        """Initialize the enhanced model adapter"""
        self.provider = provider
        self.default_model = default_model
        self.api_key = api_key
        self.capabilities = capabilities or []
        self.config = config or {}
        self.validators: Dict[str, Callable] = {}
        self.metrics: List[ModelPerformanceMetrics] = []
        self.max_metrics_history = 100

        # Setup validators
        self._setup_default_validators()

    def _setup_default_validators(self):
        """Set up default validators"""
        # Register built-in validators
        self.validators["json"] = self._validate_json_format
        self.validators["chain_of_thought"] = self._validate_chain_of_thought
        self.validators["qa"] = self._validate_qa_format
        self.validators["reasoning"] = self._validate_reasoning

    def register_validator(self, name: str, validator_func: Callable):
        """Register a custom validator function"""
        self.validators[name] = validator_func

    async def _track_performance(
        self,
        model_name: str,
        endpoint: str,
        start_time: float,
        input_tokens: int,
        output_tokens: int,
        success: bool,
        error_type: str = None,
        error_message: str = None,
        request_id: str = None,
        user_id: str = None,
        validation_result: Dict[str, Any] = None,
        confidence_score: float = None
    ):
        """Track model performance metrics"""
        latency = (time.time() - start_time) * 1000  # Convert to ms

        # Calculate estimated cost based on provider and model
        cost = self._estimate_cost(
            self.provider,
            model_name,
            input_tokens,
            output_tokens
        )

        # Create metrics object
        metrics = ModelPerformanceMetrics(
            request_timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            model_name=model_name,
            provider=self.provider,
            endpoint=endpoint,
            latency_ms=latency,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            estimated_cost_usd=cost,
            success=success,
            error_type=error_type,
            error_message=error_message,
            request_id=request_id,
            user_id=user_id,
            validation_result=validation_result,
            confidence_score=confidence_score
        )

        # Add to metrics history (limited size)
        self.metrics.append(metrics)
        if len(self.metrics) > self.max_metrics_history:
            self.metrics.pop(0)

        # Log metrics
        logger.info(f"AI request metrics: {model_name} - {latency:.2f}ms - {input_tokens+output_tokens} tokens - ${cost:.6f}")

        # Could also send to monitoring service here

        return metrics

    def _estimate_cost(
        self,
        provider: ModelProvider,
        model_name: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Estimate the cost of a model request based on token usage"""
        # Default pricing if unknown (conservative estimate)
        input_price_per_1k = 0.01
        output_price_per_1k = 0.03

        # OpenAI pricing (approximate as of Feb 2025)
        if provider == ModelProvider.OPENAI:
            if "gpt-4" in model_name and "vision" in model_name:
                input_price_per_1k = 0.01
                output_price_per_1k = 0.03
            elif "gpt-4" in model_name and "turbo" in model_name:
                input_price_per_1k = 0.01
                output_price_per_1k = 0.03
            elif "gpt-4" in model_name:
                input_price_per_1k = 0.03
                output_price_per_1k = 0.06
            elif "gpt-3.5-turbo" in model_name:
                input_price_per_1k = 0.0005
                output_price_per_1k = 0.0015
            elif "text-embedding" in model_name:
                input_price_per_1k = 0.0001
                output_price_per_1k = 0

        # Anthropic pricing
        elif provider == ModelProvider.ANTHROPIC:
            if "claude-3-opus" in model_name:
                input_price_per_1k = 0.015
                output_price_per_1k = 0.075
            elif "claude-3-sonnet" in model_name:
                input_price_per_1k = 0.003
                output_price_per_1k = 0.015
            elif "claude-3-haiku" in model_name:
                input_price_per_1k = 0.00025
                output_price_per_1k = 0.00125
            elif "claude-2" in model_name:
                input_price_per_1k = 0.008
                output_price_per_1k = 0.024

        # Google pricing
        elif provider == ModelProvider.GOOGLE:
            if "gemini-1.5-pro" in model_name:
                input_price_per_1k = 0.0025
                output_price_per_1k = 0.0075
            elif "gemini-1.0-pro" in model_name:
                input_price_per_1k = 0.001
                output_price_per_1k = 0.002

        # Calculate total cost
        input_cost = (input_tokens / 1000) * input_price_per_1k
        output_cost = (output_tokens / 1000) * output_price_per_1k
        return input_cost + output_cost

    async def _validate_response(
        self,
        request: EnhancedModelRequest,
        response: EnhancedModelResponse
    ) -> ValidationResult:
        """Validate the model response and assign confidence score"""
        validation = ValidationResult()

        # Skip validation if no validation type specified
        if not request.validation_type:
            return validation

        # Find appropriate validator
        validator = self.validators.get(request.validation_type)
        if not validator:
            validation.warnings.append(f"No validator found for type: {request.validation_type}")
            validation.confidence_score = 0.7  # Default medium confidence when no validation
            validation.confidence_level = ConfidenceLevel.MEDIUM
            return validation

        # Run the validator
        try:
            validator_result = await validator(request, response)
            validation = validator_result
        except Exception as e:
            validation.is_valid = False
            validation.errors.append(f"Validation error: {str(e)}")
            validation.confidence_score = 0.3
            validation.confidence_level = ConfidenceLevel.UNCERTAIN

        # Set confidence level based on score
        if validation.confidence_score >= 0.9:
            validation.confidence_level = ConfidenceLevel.HIGH
        elif validation.confidence_score >= 0.7:
            validation.confidence_level = ConfidenceLevel.MEDIUM
        elif validation.confidence_score >= 0.5:
            validation.confidence_level = ConfidenceLevel.LOW
        else:
            validation.confidence_level = ConfidenceLevel.UNCERTAIN

        return validation

    async def _validate_json_format(
        self,
        request: EnhancedModelRequest,
        response: EnhancedModelResponse
    ) -> ValidationResult:
        """Validate JSON format in response"""
        validation = ValidationResult()

        try:
            # Check if response is valid JSON
            if not response.content:
                validation.is_valid = False
                validation.errors.append("Empty response content")
                validation.confidence_score = 0.0
                return validation

            # Try to parse as JSON
            json_data = json.loads(response.content)

            # Check if the expected structure is present
            if request.expected_format:
                expected_keys = json.loads(request.expected_format).keys()
                for key in expected_keys:
                    if key not in json_data:
                        validation.is_valid = False
                        validation.errors.append(f"Missing expected key: {key}")
                        validation.confidence_score = 0.5

            # If valid JSON with expected structure
            if validation.is_valid:
                validation.confidence_score = 0.95
        except json.JSONDecodeError:
            validation.is_valid = False
            validation.errors.append("Invalid JSON format")
            validation.confidence_score = 0.1
        except Exception as e:
            validation.is_valid = False
            validation.errors.append(f"Validation error: {str(e)}")
            validation.confidence_score = 0.3

        return validation

    async def _validate_chain_of_thought(
        self,
        request: EnhancedModelRequest,
        response: EnhancedModelResponse
    ) -> ValidationResult:
        """Validate chain-of-thought reasoning in response"""
        validation = ValidationResult()
        cot_result = ChainOfThoughtValidationResult()

        try:
            content = response.content

            # Check for reasoning pattern indicators
            reasoning_indicators = [
                "let's think step by step",
                "reasoning:",
                "step 1",
                "first,",
                "to solve this",
                "let me analyze",
                "let's break this down"
            ]

            has_reasoning_structure = any(indicator in content.lower() for indicator in reasoning_indicators)
            if not has_reasoning_structure:
                cot_result.valid_structure = False
                cot_result.reasoning_coherence = 0.5
                cot_result.steps_clarity = 0.5
                cot_result.missing_steps.append("No clear reasoning structure detected")
                cot_result.overall_score = 0.5
                validation.confidence_score = 0.5
                validation.reasoning_quality = 0.5
                validation.warnings.append("Response lacks clear reasoning structure")
                return validation

            # Extract reasoning steps
            steps = []
            lines = content.split('\n')
            current_step = ""
            step_num = 1

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Check if this line starts a new step
                starts_new_step = False
                if line.lower().startswith(f"step {step_num}") or line.lower().startswith(f"{step_num}.") or line.lower().startswith(f"{step_num}:"):
                    starts_new_step = True
                    step_num += 1
                elif any(line.lower().startswith(x) for x in ["first:", "second:", "third:", "finally:", "lastly:"]):
                    starts_new_step = True

                # If starting new step and we have a current step, save it
                if starts_new_step and current_step:
                    steps.append({"step": current_step})
                    current_step = line
                else:
                    # Otherwise add to current step
                    if current_step:
                        current_step += " " + line
                    else:
                        current_step = line

            # Add the last step if exists
            if current_step:
                steps.append({"step": current_step})

            # Analyze steps for quality and consistency
            if len(steps) < 2:
                cot_result.reasoning_coherence = 0.6
                cot_result.steps_clarity = 0.7
                cot_result.missing_steps.append("Insufficient reasoning steps")
                cot_result.overall_score = 0.65
                validation.confidence_score = 0.6
                validation.reasoning_quality = 0.6
                validation.warnings.append("Response contains limited reasoning steps")
            else:
                # More sophisticated analysis could be done here
                cot_result.valid_structure = True
                cot_result.reasoning_coherence = 0.9
                cot_result.steps_clarity = 0.85
                cot_result.conclusion_alignment = 0.9
                cot_result.overall_score = 0.88
                cot_result.detected_steps = steps

                validation.confidence_score = 0.85
                validation.reasoning_quality = 0.88

            # Store reasoning steps in response
            response.reasoning_steps = steps

        except Exception as e:
            cot_result.valid_structure = False
            cot_result.overall_score = 0.4
            cot_result.logical_errors.append({"error": str(e)})
            validation.confidence_score = 0.4
            validation.warnings.append(f"Error analyzing reasoning: {str(e)}")

        return validation

    async def _validate_qa_format(
        self,
        request: EnhancedModelRequest,
        response: EnhancedModelResponse
    ) -> ValidationResult:
        """Validate question-answering format"""
        validation = ValidationResult()
        validation.confidence_score = 0.8  # Default for QA

        # Check for answer indicators
        has_answer = any(x in response.content.lower() for x in [
            "the answer is", "to answer your question", "in summary",
            "in conclusion", "therefore", "thus", "hence"
        ])

        if not has_answer:
            validation.warnings.append("Response may not directly answer the question")
            validation.confidence_score = 0.6

        return validation

    async def _validate_reasoning(
        self,
        request: EnhancedModelRequest,
        response: EnhancedModelResponse
    ) -> ValidationResult:
        """Validate general reasoning quality"""
        validation = ValidationResult()

        # For now, basic implementation similar to chain-of-thought
        # but with less strict structural requirements
        content = response.content.lower()

        # Check for reasoning markers
        reasoning_markers = [
            "because", "reason", "therefore", "thus", "hence",
            "since", "as a result", "given that", "considering"
        ]

        reasoning_score = 0.5  # Default
        markers_present = sum(1 for marker in reasoning_markers if marker in content)
        reasoning_score += min(0.4, markers_present * 0.1)  # Up to 0.4 more based on markers

        validation.confidence_score = reasoning_score
        validation.reasoning_quality = reasoning_score

        return validation

    async def generate(self, request: ModelRequest) -> ModelResponse:
        """
        Generate a response from the AI model with validation.
        This method should be implemented by each specific provider adapter.
        """
        # This is an abstract method that should be implemented by subclasses
        pass

    async def enhanced_generate(self, request: EnhancedModelRequest) -> EnhancedModelResponse:
        """
        Enhanced version of generate with validation and metrics.
        This calls the provider-specific generate method and adds the enhancements.
        """
        start_time = time.time()
        input_tokens = 0
        output_tokens = 0
        success = False
        error_type = None
        error_message = None

        try:
            # Convert enhanced request to basic request for backward compatibility
            basic_request = ModelRequest(
                prompt=request.prompt,
                model_name=request.model_name,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                frequency_penalty=request.frequency_penalty,
                presence_penalty=request.presence_penalty,
                stop_sequences=request.stop_sequences,
                user_id=request.user_id
            )

            # Call the provider-specific implementation
            basic_response = await self.generate(basic_request)

            # Convert to enhanced response
            response = EnhancedModelResponse(
                content=basic_response.content,
                model_name=basic_response.model_name,
                usage=basic_response.usage,
                finish_reason=basic_response.finish_reason,
                metadata=basic_response.metadata,
                provider=self.provider,
                trace_id=request.trace_id,
                prompt_tokens=basic_response.usage.get("prompt_tokens"),
                completion_tokens=basic_response.usage.get("completion_tokens"),
                total_tokens=basic_response.usage.get("total_tokens"),
                processing_time_ms=(time.time() - start_time) * 1000
            )

            # Extract token counts
            input_tokens = response.prompt_tokens or 0
            output_tokens = response.completion_tokens or 0

            # Validate the response
            validation = await self._validate_response(request, response)
            response.validation = validation

            success = True

        except Exception as e:
            # Create error response
            error_type = type(e).__name__
            error_message = str(e)

            response = EnhancedModelResponse(
                content="Error generating response",
                model_name=request.model_name,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                metadata={"error": str(e)},
                provider=self.provider,
                trace_id=request.trace_id,
                processing_time_ms=(time.time() - start_time) * 1000,
                validation=ValidationResult(
                    is_valid=False,
                    errors=[str(e)],
                    confidence_score=0.0,
                    confidence_level=ConfidenceLevel.UNCERTAIN
                )
            )

            logger.error(f"Error in AI generation: {str(e)}")

        finally:
            # Track metrics
            await self._track_performance(
                model_name=request.model_name,
                endpoint="generate",
                start_time=start_time,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                success=success,
                error_type=error_type,
                error_message=error_message,
                request_id=request.trace_id,
                user_id=request.user_id,
                validation_result=response.validation.dict() if success else None,
                confidence_score=response.validation.confidence_score if success else 0.0
            )

        return response

    async def get_performance_metrics(
        self,
        limit: int = 100,
        model_name: Optional[str] = None,
        time_period_hours: Optional[int] = None
    ) -> List[ModelPerformanceMetrics]:
        """Get performance metrics history with optional filtering"""
        # Filter metrics based on criteria
        filtered_metrics = self.metrics

        # Filter by model name if specified
        if model_name:
            filtered_metrics = [m for m in filtered_metrics if m.model_name == model_name]

        # Filter by time period if specified
        if time_period_hours:
            import datetime
            cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=time_period_hours)
            cutoff_str = cutoff_time.strftime("%Y-%m-%d %H:%M:%S")
            filtered_metrics = [m for m in filtered_metrics if m.request_timestamp >= cutoff_str]

        # Return limited number of metrics
        return filtered_metrics[-limit:]

    async def get_aggregate_metrics(self) -> Dict[str, Any]:
        """Get aggregate performance metrics"""
        metrics = self.metrics

        if not metrics:
            return {
                "count": 0,
                "success_rate": 0,
                "avg_latency_ms": 0,
                "total_tokens": 0,
                "total_cost_usd": 0
            }

        # Calculate aggregates
        total_requests = len(metrics)
        successful_requests = sum(1 for m in metrics if m.success)
        success_rate = successful_requests / total_requests if total_requests > 0 else 0

        # Latency stats
        latencies = [m.latency_ms for m in metrics]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0

        # Token usage
        total_tokens = sum(m.total_tokens for m in metrics)
        total_cost = sum(m.estimated_cost_usd for m in metrics)

        # Model distribution
        model_counts = {}
        for m in metrics:
            model_counts[m.model_name] = model_counts.get(m.model_name, 0) + 1

        # Confidence distribution
        confidence_scores = [m.confidence_score for m in metrics if m.confidence_score is not None]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else None

        return {
            "count": total_requests,
            "success_rate": success_rate,
            "avg_latency_ms": avg_latency,
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost,
            "model_distribution": model_counts,
            "avg_confidence_score": avg_confidence
        }
