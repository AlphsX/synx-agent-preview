"""
Real-time collaboration service for shared conversations.
"""

import logging
import asyncio
import json
from typing import List, Optional, Dict, Any, Set
from datetime import datetime, timedelta
from uuid import uuid4
import secrets

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_, or_, delete
from sqlalchemy.orm import selectinload

from app.database.connection import db_manager
from app.collaboration.models import (
    SharedConversation, ConversationParticipant, ConversationBranch,
    BranchMessage, TypingIndicator, CollaborationEvent, ConversationInvite,
    CollaborationRole, PresenceStatus
)
from app.enhanced_chat_models import Conversation, Message, User

logger = logging.getLogger(__name__)

class CollaborationService:
    """Service for managing real-time collaboration features."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[str]] = {}  # conversation_id -> set of session_ids
        self.typing_sessions: Dict[str, Dict[str, datetime]] = {}  # conversation_id -> {session_id: last_update}
    
    # Shared Conversation Management
    
    async def create_shared_conversation(
        self,
        conversation_id: str,
        owner_id: str,
        title: str = None,
        description: str = None,
        is_public: bool = False,
        allow_anonymous: bool = False,
        max_participants: int = 10,
        default_role: CollaborationRole = CollaborationRole.VIEWER
    ) -> Dict[str, Any]:
        """Create a shared conversation space."""
        try:
            async with db_manager.get_session() as session:
                # Verify conversation exists
                conv_stmt = select(Conversation).where(Conversation.id == conversation_id)
                conv_result = await session.execute(conv_stmt)
                conversation = conv_result.scalar_one_or_none()
                
                if not conversation:
                    raise ValueError(f"Conversation {conversation_id} not found")
                
                # Generate unique share token
                share_token = secrets.token_urlsafe(32)
                
                shared_conv = SharedConversation(
                    conversation_id=conversation_id,
                    owner_id=owner_id,
                    share_token=share_token,
                    is_public=is_public,
                    allow_anonymous=allow_anonymous,
                    max_participants=max_participants,
                    default_role=default_role,
                    description=description or f"Shared conversation: {conversation.title}"
                )
                
                session.add(shared_conv)
                await session.commit()
                await session.refresh(shared_conv)
                
                # Add owner as first participant
                await self._add_participant(
                    session,
                    shared_conv.id,
                    owner_id,
                    "Owner",
                    CollaborationRole.OWNER,
                    str(uuid4())
                )
                
                await session.commit()
                
                # Log event
                await self._log_collaboration_event(
                    session,
                    shared_conv.id,
                    owner_id,
                    "conversation_shared",
                    {"share_token": share_token, "is_public": is_public}
                )
                
                logger.info(f"Created shared conversation {shared_conv.id} for conversation {conversation_id}")
                
                return {
                    "id": shared_conv.id,
                    "conversation_id": conversation_id,
                    "share_token": share_token,
                    "share_url": f"/shared/{share_token}",
                    "is_public": is_public,
                    "allow_anonymous": allow_anonymous,
                    "max_participants": max_participants,
                    "created_at": shared_conv.created_at.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error creating shared conversation: {e}")
            raise
    
    async def join_shared_conversation(
        self,
        share_token: str,
        user_id: Optional[str] = None,
        display_name: str = None,
        session_id: str = None
    ) -> Dict[str, Any]:
        """Join a shared conversation."""
        try:
            async with db_manager.get_session() as session:
                # Find shared conversation
                stmt = select(SharedConversation).where(SharedConversation.share_token == share_token)
                result = await session.execute(stmt)
                shared_conv = result.scalar_one_or_none()
                
                if not shared_conv:
                    raise ValueError("Invalid share token")
                
                if shared_conv.expires_at and shared_conv.expires_at < datetime.utcnow():
                    raise ValueError("Share link has expired")
                
                # Check if anonymous users are allowed
                if not user_id and not shared_conv.allow_anonymous:
                    raise ValueError("Anonymous users not allowed in this conversation")
                
                # Check participant limit
                participant_count = await self._get_participant_count(session, shared_conv.id)
                if participant_count >= shared_conv.max_participants:
                    raise ValueError("Conversation has reached maximum participants")
                
                # Generate session ID if not provided
                if not session_id:
                    session_id = str(uuid4())
                
                # Set display name
                if not display_name:
                    if user_id:
                        user_stmt = select(User).where(User.id == user_id)
                        user_result = await session.execute(user_stmt)
                        user = user_result.scalar_one_or_none()
                        display_name = user.username if user else f"User {user_id[:8]}"
                    else:
                        display_name = f"Anonymous {session_id[:8]}"
                
                # Check if user is already a participant
                existing_participant = await self._get_participant_by_user(session, shared_conv.id, user_id, session_id)
                
                if existing_participant:
                    # Update existing participant
                    existing_participant.presence_status = PresenceStatus.ONLINE
                    existing_participant.last_seen = datetime.utcnow()
                    participant = existing_participant
                else:
                    # Add new participant
                    participant = await self._add_participant(
                        session,
                        shared_conv.id,
                        user_id,
                        display_name,
                        shared_conv.default_role,
                        session_id,
                        is_anonymous=user_id is None
                    )
                
                await session.commit()
                
                # Track active connection
                if shared_conv.conversation_id not in self.active_connections:
                    self.active_connections[shared_conv.conversation_id] = set()
                self.active_connections[shared_conv.conversation_id].add(session_id)
                
                # Log event
                await self._log_collaboration_event(
                    session,
                    shared_conv.id,
                    user_id,
                    "user_joined",
                    {"display_name": display_name, "session_id": session_id}
                )
                
                logger.info(f"User {display_name} joined shared conversation {shared_conv.id}")
                
                return {
                    "shared_conversation_id": shared_conv.id,
                    "conversation_id": shared_conv.conversation_id,
                    "participant_id": participant.id,
                    "session_id": session_id,
                    "display_name": display_name,
                    "role": participant.role.value,
                    "permissions": {
                        "can_edit": participant.can_edit,
                        "can_branch": participant.can_branch,
                        "can_invite": participant.can_invite
                    }
                }
                
        except Exception as e:
            logger.error(f"Error joining shared conversation: {e}")
            raise
    
    async def leave_shared_conversation(
        self,
        shared_conversation_id: str,
        session_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """Leave a shared conversation."""
        try:
            async with db_manager.get_session() as session:
                # Find participant
                participant = await self._get_participant_by_session(session, shared_conversation_id, session_id)
                
                if not participant:
                    return False
                
                # Update presence status
                participant.presence_status = PresenceStatus.OFFLINE
                participant.last_seen = datetime.utcnow()
                participant.is_typing = False
                
                await session.commit()
                
                # Remove from active connections
                shared_conv_stmt = select(SharedConversation).where(SharedConversation.id == shared_conversation_id)
                shared_conv_result = await session.execute(shared_conv_stmt)
                shared_conv = shared_conv_result.scalar_one_or_none()
                
                if shared_conv and shared_conv.conversation_id in self.active_connections:
                    self.active_connections[shared_conv.conversation_id].discard(session_id)
                
                # Clean up typing indicators
                if shared_conv and shared_conv.conversation_id in self.typing_sessions:
                    self.typing_sessions[shared_conv.conversation_id].pop(session_id, None)
                
                # Log event
                await self._log_collaboration_event(
                    session,
                    shared_conversation_id,
                    user_id,
                    "user_left",
                    {"session_id": session_id}
                )
                
                logger.info(f"Session {session_id} left shared conversation {shared_conversation_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error leaving shared conversation: {e}")
            raise
    
    # Typing Indicators and Presence
    
    async def update_typing_status(
        self,
        conversation_id: str,
        session_id: str,
        user_id: Optional[str] = None,
        display_name: str = "Anonymous",
        is_typing: bool = True,
        typing_text: str = None
    ) -> Dict[str, Any]:
        """Update typing indicator for a user."""
        try:
            async with db_manager.get_session() as session:
                now = datetime.utcnow()
                expires_at = now + timedelta(seconds=30)  # Auto-expire after 30 seconds
                
                # Find or create typing indicator
                stmt = select(TypingIndicator).where(
                    and_(
                        TypingIndicator.conversation_id == conversation_id,
                        TypingIndicator.session_id == session_id
                    )
                )
                result = await session.execute(stmt)
                indicator = result.scalar_one_or_none()
                
                if indicator:
                    # Update existing indicator
                    indicator.is_typing = is_typing
                    indicator.typing_text = typing_text
                    indicator.updated_at = now
                    indicator.expires_at = expires_at
                else:
                    # Create new indicator
                    indicator = TypingIndicator(
                        conversation_id=conversation_id,
                        user_id=user_id,
                        session_id=session_id,
                        display_name=display_name,
                        is_typing=is_typing,
                        typing_text=typing_text,
                        expires_at=expires_at
                    )
                    session.add(indicator)
                
                await session.commit()
                
                # Update in-memory tracking
                if conversation_id not in self.typing_sessions:
                    self.typing_sessions[conversation_id] = {}
                
                if is_typing:
                    self.typing_sessions[conversation_id][session_id] = now
                else:
                    self.typing_sessions[conversation_id].pop(session_id, None)
                
                return {
                    "conversation_id": conversation_id,
                    "session_id": session_id,
                    "display_name": display_name,
                    "is_typing": is_typing,
                    "typing_text": typing_text,
                    "updated_at": now.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error updating typing status: {e}")
            raise
    
    async def get_typing_indicators(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get current typing indicators for a conversation."""
        try:
            async with db_manager.get_session() as session:
                now = datetime.utcnow()
                
                # Clean up expired indicators
                delete_stmt = delete(TypingIndicator).where(
                    and_(
                        TypingIndicator.conversation_id == conversation_id,
                        TypingIndicator.expires_at < now
                    )
                )
                await session.execute(delete_stmt)
                
                # Get active indicators
                stmt = select(TypingIndicator).where(
                    and_(
                        TypingIndicator.conversation_id == conversation_id,
                        TypingIndicator.is_typing == True,
                        TypingIndicator.expires_at >= now
                    )
                ).order_by(TypingIndicator.updated_at.desc())
                
                result = await session.execute(stmt)
                indicators = result.scalars().all()
                
                await session.commit()
                
                return [
                    {
                        "session_id": indicator.session_id,
                        "display_name": indicator.display_name,
                        "typing_text": indicator.typing_text,
                        "started_at": indicator.started_at.isoformat(),
                        "updated_at": indicator.updated_at.isoformat()
                    }
                    for indicator in indicators
                ]
                
        except Exception as e:
            logger.error(f"Error getting typing indicators: {e}")
            return []
    
    async def update_presence_status(
        self,
        shared_conversation_id: str,
        session_id: str,
        status: PresenceStatus
    ) -> bool:
        """Update presence status for a participant."""
        try:
            async with db_manager.get_session() as session:
                participant = await self._get_participant_by_session(session, shared_conversation_id, session_id)
                
                if not participant:
                    return False
                
                participant.presence_status = status
                participant.last_seen = datetime.utcnow()
                
                await session.commit()
                
                logger.info(f"Updated presence status for session {session_id} to {status.value}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating presence status: {e}")
            return False
    
    async def get_participants(self, shared_conversation_id: str) -> List[Dict[str, Any]]:
        """Get all participants in a shared conversation."""
        try:
            async with db_manager.get_session() as session:
                stmt = select(ConversationParticipant).where(
                    ConversationParticipant.shared_conversation_id == shared_conversation_id
                ).order_by(ConversationParticipant.created_at)
                
                result = await session.execute(stmt)
                participants = result.scalars().all()
                
                return [
                    {
                        "id": p.id,
                        "user_id": p.user_id,
                        "display_name": p.display_name,
                        "avatar_color": p.avatar_color,
                        "role": p.role.value,
                        "presence_status": p.presence_status.value,
                        "last_seen": p.last_seen.isoformat() if p.last_seen else None,
                        "is_typing": p.is_typing,
                        "is_anonymous": p.is_anonymous,
                        "permissions": {
                            "can_edit": p.can_edit,
                            "can_branch": p.can_branch,
                            "can_invite": p.can_invite
                        },
                        "joined_at": p.created_at.isoformat()
                    }
                    for p in participants
                ]
                
        except Exception as e:
            logger.error(f"Error getting participants: {e}")
            return []
    
    # Conversation Branching
    
    async def create_branch(
        self,
        shared_conversation_id: str,
        parent_message_id: str,
        creator_id: Optional[str],
        title: str,
        description: str = None,
        branch_type: str = "alternative"
    ) -> Dict[str, Any]:
        """Create a new conversation branch."""
        try:
            async with db_manager.get_session() as session:
                # Verify shared conversation exists
                shared_conv_stmt = select(SharedConversation).where(SharedConversation.id == shared_conversation_id)
                shared_conv_result = await session.execute(shared_conv_stmt)
                shared_conv = shared_conv_result.scalar_one_or_none()
                
                if not shared_conv:
                    raise ValueError("Shared conversation not found")
                
                if not shared_conv.allow_branching:
                    raise ValueError("Branching is not allowed in this conversation")
                
                # Create branch
                branch = ConversationBranch(
                    shared_conversation_id=shared_conversation_id,
                    parent_message_id=parent_message_id,
                    creator_id=creator_id,
                    title=title,
                    description=description,
                    branch_type=branch_type
                )
                
                session.add(branch)
                await session.commit()
                await session.refresh(branch)
                
                # Log event
                await self._log_collaboration_event(
                    session,
                    shared_conversation_id,
                    creator_id,
                    "branch_created",
                    {
                        "branch_id": branch.id,
                        "title": title,
                        "parent_message_id": parent_message_id
                    }
                )
                
                logger.info(f"Created branch {branch.id} in shared conversation {shared_conversation_id}")
                
                return {
                    "id": branch.id,
                    "title": title,
                    "description": description,
                    "branch_type": branch_type,
                    "parent_message_id": parent_message_id,
                    "creator_id": creator_id,
                    "is_active": True,
                    "created_at": branch.created_at.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error creating branch: {e}")
            raise
    
    async def get_branches(self, shared_conversation_id: str) -> List[Dict[str, Any]]:
        """Get all branches for a shared conversation."""
        try:
            async with db_manager.get_session() as session:
                stmt = select(ConversationBranch).where(
                    ConversationBranch.shared_conversation_id == shared_conversation_id
                ).order_by(ConversationBranch.created_at.desc())
                
                result = await session.execute(stmt)
                branches = result.scalars().all()
                
                return [
                    {
                        "id": branch.id,
                        "title": branch.title,
                        "description": branch.description,
                        "branch_type": branch.branch_type,
                        "parent_message_id": branch.parent_message_id,
                        "creator_id": branch.creator_id,
                        "is_active": branch.is_active,
                        "is_merged": branch.is_merged,
                        "vote_score": branch.vote_score,
                        "created_at": branch.created_at.isoformat(),
                        "merged_at": branch.merged_at.isoformat() if branch.merged_at else None
                    }
                    for branch in branches
                ]
                
        except Exception as e:
            logger.error(f"Error getting branches: {e}")
            return []
    
    async def merge_branch(
        self,
        branch_id: str,
        merger_id: Optional[str],
        merge_strategy: str = "append"
    ) -> Dict[str, Any]:
        """Merge a branch back into the main conversation."""
        try:
            async with db_manager.get_session() as session:
                # Get branch with messages
                stmt = select(ConversationBranch).options(
                    selectinload(ConversationBranch.messages)
                ).where(ConversationBranch.id == branch_id)
                
                result = await session.execute(stmt)
                branch = result.scalar_one_or_none()
                
                if not branch:
                    raise ValueError("Branch not found")
                
                if branch.is_merged:
                    raise ValueError("Branch is already merged")
                
                # Get shared conversation
                shared_conv_stmt = select(SharedConversation).where(SharedConversation.id == branch.shared_conversation_id)
                shared_conv_result = await session.execute(shared_conv_stmt)
                shared_conv = shared_conv_result.scalar_one_or_none()
                
                if not shared_conv:
                    raise ValueError("Shared conversation not found")
                
                # Merge messages based on strategy
                merged_messages = []
                
                if merge_strategy == "append":
                    # Add all branch messages to main conversation
                    for branch_msg in branch.messages:
                        main_message = Message(
                            conversation_id=shared_conv.conversation_id,
                            content=branch_msg.content,
                            role=branch_msg.role,
                            model_id=branch_msg.model_id,
                            external_data_used=branch_msg.external_data_used or {}
                        )
                        session.add(main_message)
                        merged_messages.append(main_message)
                
                elif merge_strategy == "replace":
                    # Replace messages from parent message onwards
                    # This is more complex and would require careful message ordering
                    pass
                
                # Mark branch as merged
                branch.is_merged = True
                branch.merged_at = datetime.utcnow()
                branch.merged_by = merger_id
                
                await session.commit()
                
                # Log event
                await self._log_collaboration_event(
                    session,
                    branch.shared_conversation_id,
                    merger_id,
                    "branch_merged",
                    {
                        "branch_id": branch_id,
                        "merge_strategy": merge_strategy,
                        "messages_merged": len(merged_messages)
                    }
                )
                
                logger.info(f"Merged branch {branch_id} with {len(merged_messages)} messages")
                
                return {
                    "branch_id": branch_id,
                    "merged_at": branch.merged_at.isoformat(),
                    "merged_by": merger_id,
                    "messages_merged": len(merged_messages),
                    "merge_strategy": merge_strategy
                }
                
        except Exception as e:
            logger.error(f"Error merging branch: {e}")
            raise
    
    # Helper Methods
    
    async def _add_participant(
        self,
        session: AsyncSession,
        shared_conversation_id: str,
        user_id: Optional[str],
        display_name: str,
        role: CollaborationRole,
        session_id: str,
        is_anonymous: bool = False
    ) -> ConversationParticipant:
        """Add a participant to a shared conversation."""
        participant = ConversationParticipant(
            shared_conversation_id=shared_conversation_id,
            user_id=user_id,
            display_name=display_name,
            role=role,
            session_id=session_id,
            is_anonymous=is_anonymous,
            can_edit=role in [CollaborationRole.OWNER, CollaborationRole.EDITOR],
            can_branch=role != CollaborationRole.VIEWER,
            can_invite=role in [CollaborationRole.OWNER, CollaborationRole.EDITOR]
        )
        
        session.add(participant)
        return participant
    
    async def _get_participant_by_user(
        self,
        session: AsyncSession,
        shared_conversation_id: str,
        user_id: Optional[str],
        session_id: str
    ) -> Optional[ConversationParticipant]:
        """Get participant by user ID or session ID."""
        if user_id:
            stmt = select(ConversationParticipant).where(
                and_(
                    ConversationParticipant.shared_conversation_id == shared_conversation_id,
                    ConversationParticipant.user_id == user_id
                )
            )
        else:
            stmt = select(ConversationParticipant).where(
                and_(
                    ConversationParticipant.shared_conversation_id == shared_conversation_id,
                    ConversationParticipant.session_id == session_id
                )
            )
        
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _get_participant_by_session(
        self,
        session: AsyncSession,
        shared_conversation_id: str,
        session_id: str
    ) -> Optional[ConversationParticipant]:
        """Get participant by session ID."""
        stmt = select(ConversationParticipant).where(
            and_(
                ConversationParticipant.shared_conversation_id == shared_conversation_id,
                ConversationParticipant.session_id == session_id
            )
        )
        
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _get_participant_count(self, session: AsyncSession, shared_conversation_id: str) -> int:
        """Get the number of active participants."""
        stmt = select(func.count(ConversationParticipant.id)).where(
            and_(
                ConversationParticipant.shared_conversation_id == shared_conversation_id,
                ConversationParticipant.presence_status != PresenceStatus.OFFLINE
            )
        )
        
        result = await session.execute(stmt)
        return result.scalar() or 0
    
    async def _log_collaboration_event(
        self,
        session: AsyncSession,
        shared_conversation_id: str,
        user_id: Optional[str],
        event_type: str,
        event_data: Dict[str, Any]
    ):
        """Log a collaboration event."""
        event = CollaborationEvent(
            shared_conversation_id=shared_conversation_id,
            user_id=user_id,
            event_type=event_type,
            event_data=event_data,
            description=f"{event_type}: {json.dumps(event_data)}"
        )
        
        session.add(event)
    
    # Cleanup Methods
    
    async def cleanup_expired_typing_indicators(self):
        """Clean up expired typing indicators (background task)."""
        try:
            async with db_manager.get_session() as session:
                now = datetime.utcnow()
                
                delete_stmt = delete(TypingIndicator).where(
                    TypingIndicator.expires_at < now
                )
                
                result = await session.execute(delete_stmt)
                await session.commit()
                
                if result.rowcount > 0:
                    logger.info(f"Cleaned up {result.rowcount} expired typing indicators")
                
        except Exception as e:
            logger.error(f"Error cleaning up typing indicators: {e}")
    
    async def cleanup_inactive_participants(self, inactive_threshold_minutes: int = 30):
        """Clean up participants who have been inactive for too long."""
        try:
            async with db_manager.get_session() as session:
                threshold = datetime.utcnow() - timedelta(minutes=inactive_threshold_minutes)
                
                # Update participants to offline if they've been inactive
                stmt = select(ConversationParticipant).where(
                    and_(
                        ConversationParticipant.last_seen < threshold,
                        ConversationParticipant.presence_status != PresenceStatus.OFFLINE
                    )
                )
                
                result = await session.execute(stmt)
                inactive_participants = result.scalars().all()
                
                for participant in inactive_participants:
                    participant.presence_status = PresenceStatus.OFFLINE
                    participant.is_typing = False
                
                await session.commit()
                
                if inactive_participants:
                    logger.info(f"Marked {len(inactive_participants)} participants as offline due to inactivity")
                
        except Exception as e:
            logger.error(f"Error cleaning up inactive participants: {e}")

# Global collaboration service instance
collaboration_service = CollaborationService()