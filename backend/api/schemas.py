from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List, Any
from datetime import datetime

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
    model_name: str = Field(..., description="Name of the AI model")
    api_key: str = Field(..., description="API key for the model")
    
    @validator("model_name")
    def validate_model_name(cls, v):
        from ..models import MODEL_REGISTRY
        if v not in MODEL_REGISTRY:
            raise ValueError(f"Model {v} not supported")
        return v

class CampaignRequest(BaseModel):
    """Campaign creation request schema."""
    task: str = Field(..., description="Campaign task description")
    model_name: str = Field(default="gpt-4", description="AI model to use")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    
    @validator("task")
    def validate_task(cls, v):
        if len(v) < 10:
            raise ValueError("Task description too short")
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
    task_type: str
    model_used: str
    processing_time: float

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
    model_latency_avg: Dict[str, float] 