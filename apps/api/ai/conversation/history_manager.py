"""
Conversation History Manager

This module provides a system for managing conversation histories,
including storing, retrieving, and manipulating conversation threads.
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Message(BaseModel):
    """Model for a conversation message."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    role: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = {}


class Conversation(BaseModel):
    """Model for a conversation thread."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    user_id: str
    messages: List[Message] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = {}


class ConversationHistoryManager:
    """
    Manager for conversation histories.

    This class provides methods for storing, retrieving, and manipulating
    conversation threads.
    """

    def __init__(self):
        """Initialize the conversation history manager."""
        self.conversations: Dict[str, Conversation] = {}
        self.user_conversations: Dict[str, List[str]] = {}

    def create_conversation(
        self,
        title: str,
        user_id: str,
        initial_message: Optional[Message] = None,
        metadata: Dict[str, Any] = {}
    ) -> Conversation:
        """
        Create a new conversation.

        Args:
            title: The title of the conversation.
            user_id: The ID of the user who owns the conversation.
            initial_message: Optional initial message to add to the conversation.
            metadata: Optional metadata for the conversation.

        Returns:
            The created conversation.
        """
        # Create conversation
        conversation = Conversation(
            title=title,
            user_id=user_id,
            metadata=metadata
        )

        # Add initial message if provided
        if initial_message:
            conversation.messages.append(initial_message)

        # Store conversation
        self.conversations[conversation.id] = conversation

        # Add to user's conversations
        if user_id not in self.user_conversations:
            self.user_conversations[user_id] = []
        self.user_conversations[user_id].append(conversation.id)

        return conversation

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Get a conversation by ID.

        Args:
            conversation_id: The ID of the conversation to get.

        Returns:
            The conversation, or None if not found.
        """
        return self.conversations.get(conversation_id)

    def list_conversations(self, user_id: str) -> List[Conversation]:
        """
        List all conversations for a user.

        Args:
            user_id: The ID of the user.

        Returns:
            A list of conversations.
        """
        conversation_ids = self.user_conversations.get(user_id, [])
        return [self.conversations[cid] for cid in conversation_ids if cid in self.conversations]

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Dict[str, Any] = {}
    ) -> Optional[Message]:
        """
        Add a message to a conversation.

        Args:
            conversation_id: The ID of the conversation to add the message to.
            role: The role of the message sender (e.g., "user", "assistant").
            content: The content of the message.
            metadata: Optional metadata for the message.

        Returns:
            The added message, or None if the conversation is not found.

        Raises:
            ValueError: If the role is invalid.
        """
        # Validate role
        if role not in ["user", "assistant", "system"]:
            raise ValueError(f"Invalid role: {role}")

        # Get conversation
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None

        # Create message
        message = Message(
            role=role,
            content=content,
            metadata=metadata
        )

        # Add message to conversation
        conversation.messages.append(message)

        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()

        return message

    def get_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
        before_id: Optional[str] = None
    ) -> List[Message]:
        """
        Get messages from a conversation.

        Args:
            conversation_id: The ID of the conversation to get messages from.
            limit: Optional maximum number of messages to return.
            before_id: Optional message ID to get messages before.

        Returns:
            A list of messages, or an empty list if the conversation is not found.
        """
        # Get conversation
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return []

        # Get messages
        messages = conversation.messages

        # Filter by before_id if provided
        if before_id:
            try:
                index = next(i for i, m in enumerate(messages) if m.id == before_id)
                messages = messages[:index]
            except StopIteration:
                # Message not found, return all messages
                pass

        # Apply limit if provided
        if limit is not None and limit > 0:
            messages = messages[-limit:]

        return messages

    def update_conversation(
        self,
        conversation_id: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Conversation]:
        """
        Update a conversation.

        Args:
            conversation_id: The ID of the conversation to update.
            title: Optional new title for the conversation.
            metadata: Optional new metadata for the conversation.

        Returns:
            The updated conversation, or None if not found.
        """
        # Get conversation
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None

        # Update fields
        if title is not None:
            conversation.title = title
        if metadata is not None:
            conversation.metadata = metadata

        # Update timestamp
        conversation.updated_at = datetime.utcnow()

        return conversation

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.

        Args:
            conversation_id: The ID of the conversation to delete.

        Returns:
            True if successful, False otherwise.
        """
        # Check if conversation exists
        if conversation_id not in self.conversations:
            return False

        # Get user ID
        user_id = self.conversations[conversation_id].user_id

        # Remove from user's conversations
        if user_id in self.user_conversations:
            try:
                self.user_conversations[user_id].remove(conversation_id)
            except ValueError:
                pass

        # Remove conversation
        del self.conversations[conversation_id]

        return True

    def clear_conversation(self, conversation_id: str) -> bool:
        """
        Clear all messages from a conversation.

        Args:
            conversation_id: The ID of the conversation to clear.

        Returns:
            True if successful, False otherwise.
        """
        # Get conversation
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return False

        # Clear messages
        conversation.messages = []

        # Update timestamp
        conversation.updated_at = datetime.utcnow()

        return True

    def format_for_prompt(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
        include_system: bool = True
    ) -> str:
        """
        Format a conversation for use in a prompt.

        Args:
            conversation_id: The ID of the conversation to format.
            limit: Optional maximum number of messages to include.
            include_system: Whether to include system messages.

        Returns:
            A formatted string representation of the conversation.
        """
        # Get conversation
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return ""

        # Get messages
        messages = conversation.messages

        # Filter out system messages if not included
        if not include_system:
            messages = [m for m in messages if m.role != "system"]

        # Apply limit if provided
        if limit is not None and limit > 0:
            messages = messages[-limit:]

        # Format messages
        formatted = []
        for message in messages:
            formatted.append(f"{message.role.capitalize()}: {message.content}")

        return "\n\n".join(formatted)

    def get_chat_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
        include_system: bool = True
    ) -> List[Dict[str, str]]:
        """
        Get messages from a conversation in a format suitable for chat models.

        Args:
            conversation_id: The ID of the conversation to get messages from.
            limit: Optional maximum number of messages to include.
            include_system: Whether to include system messages.

        Returns:
            A list of message dictionaries with "role" and "content" keys.
        """
        # Get conversation
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return []

        # Get messages
        messages = conversation.messages

        # Filter out system messages if not included
        if not include_system:
            messages = [m for m in messages if m.role != "system"]

        # Apply limit if provided
        if limit is not None and limit > 0:
            messages = messages[-limit:]

        # Format messages
        return [{"role": m.role, "content": m.content} for m in messages]


# Create a singleton instance
conversation_manager = ConversationHistoryManager()
