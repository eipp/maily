from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional


class Provider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    MISTRAL = "mistral"
    GROQ = "groq"


class Model(str, Enum):
    # OpenAI models
    GPT_4O = "gpt-4o"
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    
    # Anthropic models
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    
    # Google models
    GEMINI_PRO = "gemini-pro"
    GEMINI_ULTRA = "gemini-ultra"
    
    # Mistral models
    MISTRAL_LARGE = "mistral-large-latest"
    MISTRAL_MEDIUM = "mistral-medium-latest"
    MISTRAL_SMALL = "mistral-small-latest"
    
    # Groq models
    LLAMA3_70B = "llama3-70b-8192"
    MIXTRAL_8X7B = "mixtral-8x7b-32768"


class EmailGenerationRequest(BaseModel):
    provider: Provider = Field(..., description="The LLM provider to use")
    model: Model = Field(..., description="The LLM model to use")
    prompt: str = Field(..., description="The email generation prompt")
    context: Optional[str] = Field(None, description="Additional context for email generation")
    max_tokens: Optional[int] = Field(2000, description="Maximum number of tokens to generate")
    temperature: Optional[float] = Field(0.7, description="Temperature for generation (0.0-1.0)")
    user_id: Optional[str] = Field(None, description="User ID for tracking purposes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "provider": "openai",
                "model": "gpt-4o",
                "prompt": "Write a follow-up email to a client who hasn't responded in two weeks.",
                "context": "The client is interested in our premium email marketing service. Initial call was positive.",
                "max_tokens": 1500,
                "temperature": 0.7,
                "user_id": "user_123456"
            }
        }


class EmailGenerationResponse(BaseModel):
    email: str = Field(..., description="The generated email content")
    model: Model = Field(..., description="The model used for generation")
    provider: Provider = Field(..., description="The provider used for generation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "Dear Client,\n\nI hope this email finds you well. I'm following up on our conversation two weeks ago about our premium email marketing service...",
                "model": "gpt-4o",
                "provider": "openai"
            }
        } 