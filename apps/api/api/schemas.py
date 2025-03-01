from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class ErrorResponse(BaseModel):
    """Error response schema."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")


class BaseResponse(BaseModel):
    """Base response schema."""

    status: str = Field(..., example="success")
    error: Optional[ErrorResponse] = None


class ModelConfig(BaseModel):
    """Model configuration schema."""

    provider: str = Field(..., description="Provider of the AI model (e.g., openai, anthropic)")
    model_name: str = Field(..., description="Name of the AI model")
    api_key: str = Field(..., description="API key for the model")

    @validator("provider")
    def validate_provider(cls, v):
        supported_providers = ["openai", "anthropic", "google", "resend", "sendgrid", "mailgun"]
        if v not in supported_providers:
            raise ValueError(f"Provider {v} not supported. Supported providers: {', '.join(supported_providers)}")
        return v


class CampaignRequest(BaseModel):
    """Campaign creation request schema using OctoTools."""

    objective: str = Field(..., description="Campaign objective (e.g., product announcement, newsletter)")
    audience: str = Field(..., description="Target audience description")
    brand_voice: str = Field("professional", description="Brand voice/tone (e.g., professional, friendly, technical)")
    key_points: List[str] = Field(..., description="Key points to include in the email")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="Optional attachments to include")
    personalization: Optional[Dict[str, Any]] = Field(None, description="Optional personalization variables")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")

    @validator("objective")
    def validate_objective(cls, v):
        if len(v) < 5:
            raise ValueError("Objective description too short")
        return v

    @validator("audience")
    def validate_audience(cls, v):
        if len(v) < 5:
            raise ValueError("Audience description too short")
        return v

    @validator("key_points")
    def validate_key_points(cls, v):
        if not v:
            raise ValueError("At least one key point is required")
        return v

    @validator("cache_ttl")
    def validate_cache_ttl(cls, v):
        if v < 0:
            raise ValueError("Cache TTL cannot be negative")
        return v


class CampaignMetadata(BaseModel):
    """Campaign metadata schema."""

    processed_at: datetime
    processor_id: str
    campaign_type: str
    model_used: str
    processing_time: float
    tools_used: Optional[List[str]] = None


class CampaignResponse(BaseResponse):
    """Campaign creation response schema."""

    campaign_id: Optional[int] = None
    result: Optional[Dict[str, Any]] = None
    metadata: Optional[CampaignMetadata] = None


class HealthCheck(BaseModel):
    """Health check response schema."""

    status: str = Field(..., description="Overall health status")
    timestamp: float = Field(..., description="Check timestamp")
    services: Dict[str, Any] = Field(..., description="Service health statuses")


class MetricsResponse(BaseModel):
    """Metrics response schema."""

    requests_total: int
    request_latency_avg: float
    cache_hit_rate: float
