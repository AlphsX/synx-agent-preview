"""
Real-time collaboration module for AI agent conversations.

This module provides:
- Shared conversation spaces for multiple users
- Real-time typing indicators and presence status
- Conversation sharing and collaboration permissions
- Conversation branching and merge capabilities
"""

from .service import collaboration_service
from .websocket_manager import collaboration_websocket_manager
from .router import router as collaboration_router
from .models import (
    SharedConversation,
    ConversationParticipant,
    ConversationBranch,
    BranchMessage,
    TypingIndicator,
    CollaborationEvent,
    ConversationInvite,
    CollaborationRole,
    PresenceStatus
)

__all__ = [
    "collaboration_service",
    "collaboration_websocket_manager", 
    "collaboration_router",
    "SharedConversation",
    "ConversationParticipant",
    "ConversationBranch",
    "BranchMessage",
    "TypingIndicator",
    "CollaborationEvent",
    "ConversationInvite",
    "CollaborationRole",
    "PresenceStatus"
]