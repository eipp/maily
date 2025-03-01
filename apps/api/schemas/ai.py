"""
Schema models for AI requests and responses.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator


class AIModelRequest(BaseModel):
    """
    Schema for AI model generation request.
    """
    prompt: str = Field(..., description="The prompt to generate a response for")
    model_name: str = Field(..., description="The name of the model to use")
    temperature: float = Field(0.0, description="Controls randomness (0.0-1.0)")
    max_tokens: int = Field(1000, description="Maximum number of tokens to generate")
    top_p: float = Field(1.0, description="Controls diversity via nucleus sampling")
    frequency_penalty: float = Field(0.0, description="Penalizes repeated tokens")
    presence_penalty: float = Field(0.0, description="Penalizes repeated topics")
    stop_sequences: List[str] = Field([], description="Sequences that stop generation")

    @validator("temperature")
    def validate_temperature(cls, v):
        """Validate temperature is between 0 and 1."""
        if v < 0.0 or v > 1.0:
            raise ValueError("Temperature must be between 0.0 and 1.0")
        return v

    @validator("top_p")
    def validate_top_p(cls, v):
        """Validate top_p is between 0 and 1."""
        if v < 0.0 or v > 1.0:
            raise ValueError("Top_p must be between 0.0 and 1.0")
        return v

    @validator("max_tokens")
    def validate_max_tokens(cls, v):
        """Validate max_tokens is positive."""
        if v <= 0:
            raise ValueError("Max tokens must be positive")
        return v


class AIModelResponse(BaseModel):
    """
    Schema for AI model generation response.
    """
    content: str = Field(..., description="The generated text")
    model: str = Field(..., description="The model used for generation")
    usage: Dict[str, int] = Field(..., description="Token usage statistics")
    finish_reason: str = Field(..., description="Reason why generation finished")
    cached: bool = Field(False, description="Whether the response was served from cache")

    class Config:
        schema_extra = {
            "example": {
                "content": "This is a sample response from the AI model.",
                "model": "gpt-3.5-turbo",
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30
                },
                "finish_reason": "stop",
                "cached": True
            }
        }
