"""
Conversation Router

This module provides endpoints for managing conversation histories,
including creating, retrieving, and manipulating conversation threads.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from pydantic import BaseModel, Field

from ..services.user_service import get_current_user
from ..models.user import User
from ..ai.conversation import (
    conversation_manager,
    Conversation,
    Message
)
from ..dependencies import get_model_service

# Create router
router = APIRouter(prefix="/conversations", tags=["Conversations"])

# Get consolidated service instance
consolidated_ai_service = get_model_service()


# Request/Response Models
class ConversationCreate(BaseModel):
    """Request model for creating a conversation."""
    title: str
    initial_message: Optional[str] = None
    metadata: Dict[str, Any] = {}


class MessageCreate(BaseModel):
    """Request model for creating a message."""
    role: str
    content: str
    metadata: Dict[str, Any] = {}


class ConversationUpdate(BaseModel):
    """Request model for updating a conversation."""
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    """Response model for a message."""
    id: str
    role: str
    content: str
    created_at: str
    metadata: Dict[str, Any]


class ConversationResponse(BaseModel):
    """Response model for a conversation."""
    id: str
    title: str
    user_id: str
    messages: List[MessageResponse]
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]


class ConversationSummaryResponse(BaseModel):
    """Response model for a conversation summary."""
    id: str
    title: str
    user_id: str
    message_count: int
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]


class ChatRequest(BaseModel):
    """Request model for chatting with an AI model."""
    conversation_id: str
    message: str
    model_name: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    metadata: Dict[str, Any] = {}


class ChatResponse(BaseModel):
    """Response model for a chat response."""
    conversation_id: str
    message: MessageResponse
    response: MessageResponse


# Endpoints
@router.post("", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new conversation.

    Args:
        request: The conversation creation request.
        current_user: The current authenticated user.

    Returns:
        The created conversation.
    """
    # Create initial message if provided
    initial_message = None
    if request.initial_message:
        initial_message = Message(
            role="user",
            content=request.initial_message
        )

    # Create conversation
    conversation = conversation_manager.create_conversation(
        title=request.title,
        user_id=str(current_user.id),
        initial_message=initial_message,
        metadata=request.metadata
    )

    # Convert to response format
    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        user_id=conversation.user_id,
        messages=[
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                created_at=m.created_at.isoformat(),
                metadata=m.metadata
            )
            for m in conversation.messages
        ],
        created_at=conversation.created_at.isoformat(),
        updated_at=conversation.updated_at.isoformat(),
        metadata=conversation.metadata
    )


@router.get("", response_model=List[ConversationSummaryResponse])
async def list_conversations(
    current_user: User = Depends(get_current_user)
):
    """
    List all conversations for the current user.

    Args:
        current_user: The current authenticated user.

    Returns:
        A list of conversation summaries.
    """
    # Get conversations
    conversations = conversation_manager.list_conversations(str(current_user.id))

    # Convert to response format
    return [
        ConversationSummaryResponse(
            id=c.id,
            title=c.title,
            user_id=c.user_id,
            message_count=len(c.messages),
            created_at=c.created_at.isoformat(),
            updated_at=c.updated_at.isoformat(),
            metadata=c.metadata
        )
        for c in conversations
    ]


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str = Path(..., description="The ID of the conversation to get"),
    current_user: User = Depends(get_current_user)
):
    """
    Get a conversation by ID.

    Args:
        conversation_id: The ID of the conversation to get.
        current_user: The current authenticated user.

    Returns:
        The conversation.

    Raises:
        HTTPException: If the conversation is not found or does not belong to the user.
    """
    # Get conversation
    conversation = conversation_manager.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")

    # Check ownership
    if conversation.user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="You do not have permission to access this conversation")

    # Convert to response format
    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        user_id=conversation.user_id,
        messages=[
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                created_at=m.created_at.isoformat(),
                metadata=m.metadata
            )
            for m in conversation.messages
        ],
        created_at=conversation.created_at.isoformat(),
        updated_at=conversation.updated_at.isoformat(),
        metadata=conversation.metadata
    )


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    request: ConversationUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update a conversation.

    Args:
        conversation_id: The ID of the conversation to update.
        request: The conversation update request.
        current_user: The current authenticated user.

    Returns:
        The updated conversation.

    Raises:
        HTTPException: If the conversation is not found or does not belong to the user.
    """
    # Get conversation
    conversation = conversation_manager.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")

    # Check ownership
    if conversation.user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="You do not have permission to update this conversation")

    # Update conversation
    updated = conversation_manager.update_conversation(
        conversation_id=conversation_id,
        title=request.title,
        metadata=request.metadata
    )

    # Convert to response format
    return ConversationResponse(
        id=updated.id,
        title=updated.title,
        user_id=updated.user_id,
        messages=[
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                created_at=m.created_at.isoformat(),
                metadata=m.metadata
            )
            for m in updated.messages
        ],
        created_at=updated.created_at.isoformat(),
        updated_at=updated.updated_at.isoformat(),
        metadata=updated.metadata
    )


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a conversation.

    Args:
        conversation_id: The ID of the conversation to delete.
        current_user: The current authenticated user.

    Returns:
        A success message.

    Raises:
        HTTPException: If the conversation is not found or does not belong to the user.
    """
    # Get conversation
    conversation = conversation_manager.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")

    # Check ownership
    if conversation.user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="You do not have permission to delete this conversation")

    # Delete conversation
    success = conversation_manager.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete conversation")

    return {"status": "success", "message": f"Conversation {conversation_id} deleted"}


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def add_message(
    conversation_id: str,
    request: MessageCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Add a message to a conversation.

    Args:
        conversation_id: The ID of the conversation to add the message to.
        request: The message creation request.
        current_user: The current authenticated user.

    Returns:
        The added message.

    Raises:
        HTTPException: If the conversation is not found or does not belong to the user.
    """
    # Get conversation
    conversation = conversation_manager.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")

    # Check ownership
    if conversation.user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="You do not have permission to add messages to this conversation")

    try:
        # Add message
        message = conversation_manager.add_message(
            conversation_id=conversation_id,
            role=request.role,
            content=request.content,
            metadata=request.metadata
        )

        if not message:
            raise HTTPException(status_code=500, detail="Failed to add message")

        # Convert to response format
        return MessageResponse(
            id=message.id,
            role=message.role,
            content=message.content,
            created_at=message.created_at.isoformat(),
            metadata=message.metadata
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: str,
    limit: Optional[int] = Query(None, description="Maximum number of messages to return"),
    before_id: Optional[str] = Query(None, description="Get messages before this message ID"),
    current_user: User = Depends(get_current_user)
):
    """
    Get messages from a conversation.

    Args:
        conversation_id: The ID of the conversation to get messages from.
        limit: Optional maximum number of messages to return.
        before_id: Optional message ID to get messages before.
        current_user: The current authenticated user.

    Returns:
        A list of messages.

    Raises:
        HTTPException: If the conversation is not found or does not belong to the user.
    """
    # Get conversation
    conversation = conversation_manager.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")

    # Check ownership
    if conversation.user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="You do not have permission to access this conversation")

    # Get messages
    messages = conversation_manager.get_messages(
        conversation_id=conversation_id,
        limit=limit,
        before_id=before_id
    )

    # Convert to response format
    return [
        MessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            created_at=m.created_at.isoformat(),
            metadata=m.metadata
        )
        for m in messages
    ]


@router.post("/{conversation_id}/chat", response_model=ChatResponse)
async def chat(
    conversation_id: str,
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Chat with an AI model in a conversation.

    This endpoint adds a user message to the conversation and generates
    an AI response, which is also added to the conversation.

    Args:
        conversation_id: The ID of the conversation to chat in.
        request: The chat request.
        current_user: The current authenticated user.

    Returns:
        The user message and AI response.

    Raises:
        HTTPException: If the conversation is not found or does not belong to the user.
    """
    # Get conversation
    conversation = conversation_manager.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")

    # Check ownership
    if conversation.user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="You do not have permission to chat in this conversation")

    try:
        # Add user message
        user_message = conversation_manager.add_message(
            conversation_id=conversation_id,
            role="user",
            content=request.message,
            metadata=request.metadata
        )

        if not user_message:
            raise HTTPException(status_code=500, detail="Failed to add user message")

        # Get chat history
        chat_messages = conversation_manager.get_chat_messages(
            conversation_id=conversation_id,
            limit=10,  # Limit to last 10 messages for context
            include_system=True
        )

        # Generate AI response
        ai_response = await consolidated_ai_service.generate_text(
            prompt=request.message,
            model_name=request.model_name,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            metadata={
                "conversation_id": conversation_id,
                "user_id": str(current_user.id),
                **request.metadata
            }
        )

        # Add AI response to conversation
        assistant_message = conversation_manager.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=ai_response.content,
            metadata={
                "model_name": ai_response.model_name,
                "usage": ai_response.usage,
                "finish_reason": ai_response.finish_reason,
                **request.metadata
            }
        )

        if not assistant_message:
            raise HTTPException(status_code=500, detail="Failed to add assistant message")

        # Convert to response format
        return ChatResponse(
            conversation_id=conversation_id,
            message=MessageResponse(
                id=user_message.id,
                role=user_message.role,
                content=user_message.content,
                created_at=user_message.created_at.isoformat(),
                metadata=user_message.metadata
            ),
            response=MessageResponse(
                id=assistant_message.id,
                role=assistant_message.role,
                content=assistant_message.content,
                created_at=assistant_message.created_at.isoformat(),
                metadata=assistant_message.metadata
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conversation_id}/clear")
async def clear_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Clear all messages from a conversation.

    Args:
        conversation_id: The ID of the conversation to clear.
        current_user: The current authenticated user.

    Returns:
        A success message.

    Raises:
        HTTPException: If the conversation is not found or does not belong to the user.
    """
    # Get conversation
    conversation = conversation_manager.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")

    # Check ownership
    if conversation.user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="You do not have permission to clear this conversation")

    # Clear conversation
    success = conversation_manager.clear_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to clear conversation")

    return {"status": "success", "message": f"Conversation {conversation_id} cleared"}
