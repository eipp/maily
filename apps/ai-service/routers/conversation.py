import logging
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional

from ai_service.utils.database import get_session
from ai_service.services.llm_service import get_llm_service, LLMService

logger = logging.getLogger("ai_service.routers.conversation")
router = APIRouter()

@router.post("/chat")
async def chat_conversation(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    llm_service: LLMService = Depends(get_llm_service),
):
    """Process a chat conversation request."""
    try:
        logger.info(f"Processing chat request")
        
        # Validate required fields
        if "messages" not in request:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Messages are required",
            )
            
        if "provider" not in request:
            request["provider"] = "openai"  # Default provider
            
        if "model" not in request:
            request["model"] = "gpt-4o"  # Default model
        
        # Process chat request
        response = await llm_service.chat_completion(
            messages=request["messages"],
            provider=request["provider"],
            model=request["model"],
            temperature=request.get("temperature", 0.7),
            max_tokens=request.get("max_tokens", 1000),
            user_id=request.get("user_id"),
        )
        
        # Record usage asynchronously
        background_tasks.add_task(
            llm_service.record_usage,
            session=session,
            provider=request["provider"],
            model=request["model"],
            input_tokens=sum(len(msg.get("content", "")) for msg in request["messages"]),
            output_tokens=len(response),
            user_id=request.get("user_id"),
        )
        
        return {
            "response": response,
            "model": request["model"],
            "provider": request["provider"],
        }
        
    except Exception as e:
        logger.error(f"Chat conversation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat conversation failed: {str(e)}",
        )

@router.get("/sessions")
async def list_conversation_sessions(
    user_id: str,
    session: AsyncSession = Depends(get_session),
):
    """List conversation sessions for a user."""
    try:
        # In a real implementation, this would query the database
        # For demo purposes, we'll return a mock response
        return {
            "sessions": [
                {
                    "id": "sess_123456",
                    "title": "Email marketing campaign discussion",
                    "created_at": "2023-09-15T14:30:00Z",
                    "updated_at": "2023-09-15T15:45:00Z",
                    "message_count": 12
                },
                {
                    "id": "sess_789012",
                    "title": "Customer support template creation",
                    "created_at": "2023-09-10T09:15:00Z",
                    "updated_at": "2023-09-10T10:30:00Z",
                    "message_count": 8
                }
            ]
        }
    except Exception as e:
        logger.error(f"Failed to list conversation sessions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list conversation sessions: {str(e)}",
        ) 