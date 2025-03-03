import logging
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional

from ai_service.utils.database import get_session
from ai_service.services.llm_service import get_llm_service, LLMService
from ai_service.models.generation import (
    EmailGenerationRequest,
    EmailGenerationResponse,
    Model,
    Provider,
)

logger = logging.getLogger("ai_service.routers.generation")
router = APIRouter()

@router.post("/email", response_model=EmailGenerationResponse)
async def generate_email(
    request: EmailGenerationRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    llm_service: LLMService = Depends(get_llm_service),
):
    """Generate an email based on the provided input."""
    try:
        logger.info(f"Processing email generation request with provider {request.provider} and model {request.model}")
        
        # Generate email content
        email_content = await llm_service.generate_email(
            provider=request.provider,
            model=request.model,
            prompt=request.prompt,
            context=request.context,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )
        
        # Record usage asynchronously
        background_tasks.add_task(
            llm_service.record_usage,
            session=session,
            provider=request.provider,
            model=request.model,
            input_tokens=len(request.prompt) + len(request.context or ""),
            output_tokens=len(email_content),
            user_id=request.user_id,
        )
        
        return EmailGenerationResponse(
            email=email_content,
            model=request.model,
            provider=request.provider,
        )
        
    except Exception as e:
        logger.error(f"Email generation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email generation failed: {str(e)}",
        )

@router.get("/models", response_model=List[Dict[str, Any]])
async def list_available_models():
    """List all available models and providers."""
    return [
        {"name": Model.GPT_4O, "provider": Provider.OPENAI, "description": "GPT-4o model from OpenAI", "capabilities": ["email", "code", "summarization"]},
        {"name": Model.GPT_4, "provider": Provider.OPENAI, "description": "GPT-4 model from OpenAI", "capabilities": ["email", "code", "summarization"]},
        {"name": Model.CLAUDE_3_OPUS, "provider": Provider.ANTHROPIC, "description": "Claude 3 Opus from Anthropic", "capabilities": ["email", "document_analysis", "creative_writing"]},
        {"name": Model.CLAUDE_3_SONNET, "provider": Provider.ANTHROPIC, "description": "Claude 3 Sonnet from Anthropic", "capabilities": ["email", "document_analysis"]},
        {"name": Model.GEMINI_PRO, "provider": Provider.GOOGLE, "description": "Gemini Pro from Google", "capabilities": ["email", "summarization"]},
        {"name": Model.MISTRAL_LARGE, "provider": Provider.MISTRAL, "description": "Mistral Large", "capabilities": ["email", "summarization"]},
    ] 