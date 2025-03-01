"""
AI Service Router

This module provides FastAPI endpoints for interacting with the AI service,
including text generation, embeddings, model management, and advanced features.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Body, Path
from pydantic import BaseModel, Field, validator

from ..ai import (
    ConsolidatedAIService,
    ModelProvider,
    ModelCapability,
    count_tokens,
    estimate_cost
)
from ..services.user_service import get_current_user
from ..models.user import User
from ..dependencies import get_model_service
from apps.api.services.ai_service import AIService, get_ai_service
from apps.api.schemas.ai import AIModelRequest, AIModelResponse

# Create router
router = APIRouter(prefix="/ai", tags=["AI"])

# Get consolidated service instance
consolidated_ai_service = get_model_service()


# Request/Response Models
class GenerateRequest(BaseModel):
    """Request model for text generation."""
    prompt: str
    model_name: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: Optional[List[str]] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    bypass_cache: bool = False

    @validator('temperature')
    def validate_temperature(cls, v):
        if v < 0 or v > 2:
            raise ValueError('Temperature must be between 0 and 2')
        return v

    @validator('max_tokens')
    def validate_max_tokens(cls, v):
        if v < 1 or v > 32000:
            raise ValueError('max_tokens must be between 1 and 32000')
        return v


class GenerateResponse(BaseModel):
    """Response model for text generation."""
    content: str
    model_name: str
    usage: Dict[str, int]
    finish_reason: Optional[str] = None
    cached: bool = False
    token_count: int
    estimated_cost: float
    latency_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EmbeddingRequest(BaseModel):
    """Request model for text embedding."""
    text: Union[str, List[str]]
    model_name: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EmbeddingResponse(BaseModel):
    """Response model for text embedding."""
    embeddings: List[List[float]]
    model_name: str
    usage: Dict[str, int]
    token_count: int
    estimated_cost: float
    latency_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ModelInfoResponse(BaseModel):
    """Response model for model information."""
    providers: Dict[str, Any]
    models_count: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    providers: Dict[str, Dict[str, Any]]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RoutingRequest(BaseModel):
    """Request model for model routing."""
    prompt: str
    task_type: str
    complexity: int = Field(default=2, ge=1, le=5)
    max_tokens: int = 1000
    temperature: float = 0.7
    top_p: float = 1.0
    requirements: Optional[Dict[str, Any]] = None
    override_model: Optional[str] = None
    timeout: float = 30.0


class RoutingResponse(BaseModel):
    """Response model for model routing."""
    content: str
    model: str
    model_tier: str
    success: bool
    meta: Dict[str, Any]
    used_fallback: bool = False
    primary_model: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PerformanceMetricsResponse(BaseModel):
    """Response model for performance metrics."""
    metrics: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TokenCountRequest(BaseModel):
    """Request model for token counting."""
    text: str
    model_name: Optional[str] = None


class TokenCountResponse(BaseModel):
    """Response model for token counting."""
    token_count: int
    character_count: int
    estimated_cost: float
    model_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Endpoints
@router.post("/generate", response_model=AIModelResponse)
async def generate_response(
    request: AIModelRequest,
    ai_service: AIService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a response from an AI model.

    This endpoint uses caching for improved performance with deterministic requests.
    """
    return await ai_service.generate_response(request)


@router.get("/models", response_model=List[Dict[str, Any]])
async def get_models(
    ai_service: AIService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user)
):
    """Get a list of available AI models."""
    return await ai_service.get_model_list()


@router.get("/cache/stats", response_model=Dict[str, Any])
async def get_cache_stats(
    ai_service: AIService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get cache statistics.

    Returns information about cache size, hits, misses, and hit rate.
    """
    return await ai_service.get_cache_stats()


@router.post("/cache/invalidate", response_model=Dict[str, int])
async def invalidate_cache(
    model_name: str = None,
    ai_service: AIService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user)
):
    """
    Invalidate cache entries.

    If model_name is provided, only invalidates entries for that model.
    Otherwise, invalidates all entries.
    """
    count = await ai_service.invalidate_cache(model_name)
    return {"invalidated_entries": count}


@router.post("/embed", response_model=EmbeddingResponse)
async def embed_text(
    request: EmbeddingRequest,
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Generate embeddings for the provided text.

    This endpoint generates vector embeddings for the provided text,
    which can be used for semantic search, clustering, or other NLP tasks.

    Args:
        request: The embedding request parameters
        current_user: The current authenticated user

    Returns:
        An EmbeddingResponse object containing the embeddings and metadata
    """
    try:
        # Set user_id if authenticated
        if current_user and not request.user_id:
            request.user_id = str(current_user.id)

        # Track start time for latency calculation
        start_time = datetime.utcnow()

        # Generate embeddings
        embeddings = await consolidated_ai_service.generate_embeddings(
            text=request.text,
            model=request.model_name,
            user_id=request.user_id
        )

        # Calculate latency
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Count tokens
        if isinstance(request.text, str):
            token_count = count_tokens(request.text, request.model_name)
            text_list = [request.text]
        else:
            token_count = sum(count_tokens(t, request.model_name) for t in request.text)
            text_list = request.text

        # Estimate cost
        estimated_cost = estimate_cost(token_count, 0, request.model_name or "text-embedding-3-small")

        return EmbeddingResponse(
            embeddings=embeddings,
            model_name=request.model_name or "text-embedding-3-small",
            usage={"prompt_tokens": token_count, "completion_tokens": 0, "total_tokens": token_count},
            token_count=token_count,
            estimated_cost=estimated_cost,
            latency_ms=latency_ms
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def check_health():
    """
    Check the health of the AI service.

    This endpoint checks the health of all registered model providers
    and returns their status.

    Returns:
        A HealthResponse object containing health status information
    """
    try:
        # Check health
        health_info = await consolidated_ai_service.check_health()

        # Determine overall status
        overall_status = "healthy"
        for provider, info in health_info.items():
            if info.get("status") != "healthy":
                overall_status = "degraded"
                break

        return HealthResponse(
            status=overall_status,
            providers=health_info
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/route", response_model=RoutingResponse)
async def route_request(
    request: RoutingRequest,
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Route a request to the optimal model based on task characteristics.

    This endpoint uses the model routing service to select the optimal model
    for the given task and generate a response.

    Args:
        request: The routing request parameters
        current_user: The current authenticated user

    Returns:
        A RoutingResponse object containing the generated text and metadata
    """
    try:
        from ..ai.routing.model_routing_service import ModelRoutingService
        from ..adapters import model_adapter_factory

        # Create routing service if not already created
        routing_service = ModelRoutingService(
            model_adapters={
                model_id: model_adapter_factory.get_adapter_for_model(model_id)
                for model_id in model_adapter_factory.list_models()
            }
        )

        # Generate response
        result = await routing_service.generate_response(
            prompt=request.prompt,
            task_type=request.task_type,
            complexity=request.complexity,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            requirements=request.requirements,
            override_model=request.override_model,
            timeout=request.timeout
        )

        return RoutingResponse(
            content=result["content"],
            model=result["model"],
            model_tier=result["model_tier"],
            success=result["success"],
            meta=result["meta"],
            used_fallback=result.get("used_fallback", False),
            primary_model=result.get("primary_model")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=PerformanceMetricsResponse)
async def get_performance_metrics():
    """
    Get performance metrics for AI operations.

    This endpoint returns performance metrics for AI operations,
    including latency, success rates, and cost information.

    Returns:
        A PerformanceMetricsResponse object containing performance metrics
    """
    try:
        # Get metrics
        metrics = consolidated_ai_service.get_performance_metrics()

        return PerformanceMetricsResponse(
            metrics=metrics
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/count-tokens", response_model=TokenCountResponse)
async def count_tokens_endpoint(request: TokenCountRequest):
    """
    Count tokens in text and estimate cost.

    This endpoint counts the number of tokens in the provided text
    and estimates the cost of processing it with the specified model.

    Args:
        request: The token counting request parameters

    Returns:
        A TokenCountResponse object containing token count and cost information
    """
    try:
        # Count tokens
        token_count = count_tokens(request.text, request.model_name)

        # Estimate cost (assuming this is for completion, not embedding)
        estimated_cost = estimate_cost(token_count, token_count, request.model_name or "gpt-3.5-turbo")

        return TokenCountResponse(
            token_count=token_count,
            character_count=len(request.text),
            estimated_cost=estimated_cost,
            model_name=request.model_name or "gpt-3.5-turbo"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
