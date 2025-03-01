"""
Conversation History Module

This module provides services for managing conversation histories,
including storing, retrieving, and manipulating conversation threads.
"""

from .history_manager import (
    ConversationHistoryManager,
    Conversation,
    Message,
    conversation_manager
)

__all__ = [
    "ConversationHistoryManager",
    "Conversation",
    "Message",
    "conversation_manager"
]
