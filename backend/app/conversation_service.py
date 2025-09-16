"""
Conversation persistence and history management service.
Handles CRUD operations for conversations and messages using database models.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_
from sqlalchemy.orm import selectinload

from app.database.connection import db_manager
from app.enhanced_chat_models import Conversation, Message
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime as dt


class ConversationResponse(BaseModel):
    id: str
    title: str
    user_id: Optional[str]
    created_at: dt
    updated_at: Optional[dt]
    metadata: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    content: str
    role: str
    model_id: Optional[str] = None
    context_data: Dict[str, Any] = {}
    created_at: dt
    
    class Config:
        from_attributes = True

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing conversation persistence and history."""
    
    async def create_conversation(
        self, 
        title: str, 
        user_id: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ) -> ConversationResponse:
        """Create a new conversation."""
        try:
            async with db_manager.get_session() as session:
                # Create conversation with enhanced chat model schema
                conversation = Conversation(
                    title=title,
                    user_id=user_id or "anonymous",  # Enhanced model requires user_id
                    model_used="enhanced-chat",
                    external_apis_used=[],
                    is_archived=False,
                    is_shared=False
                )
                
                session.add(conversation)
                await session.commit()
                await session.refresh(conversation)
                
                logger.info(f"Created conversation {conversation.id} with title: {title}")
                
                return ConversationResponse(
                    id=str(conversation.id),
                    title=conversation.title,
                    user_id=conversation.user_id,
                    created_at=conversation.created_at,
                    updated_at=conversation.updated_at,
                    metadata=metadata or {}
                )
                
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            raise
    
    async def get_conversation(self, conversation_id: str) -> Optional[ConversationResponse]:
        """Get a conversation by ID."""
        try:
            async with db_manager.get_session() as session:
                stmt = select(Conversation).where(Conversation.id == conversation_id)
                result = await session.execute(stmt)
                conversation = result.scalar_one_or_none()
                
                if not conversation:
                    return None
                
                return ConversationResponse(
                    id=str(conversation.id),
                    title=conversation.title,
                    user_id=conversation.user_id,
                    created_at=conversation.created_at,
                    updated_at=conversation.updated_at,
                    metadata={}  # Enhanced model doesn't have metadata field
                )
                
        except Exception as e:
            logger.error(f"Error getting conversation {conversation_id}: {e}")
            raise
    
    async def get_user_conversations(
        self, 
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ConversationResponse]:
        """Get conversations for a user."""
        try:
            async with db_manager.get_session() as session:
                stmt = select(Conversation)
                
                if user_id is not None:
                    stmt = stmt.where(Conversation.user_id == user_id)
                
                stmt = stmt.order_by(desc(Conversation.updated_at)).limit(limit).offset(offset)
                
                result = await session.execute(stmt)
                conversations = result.scalars().all()
                
                return [
                    ConversationResponse(
                        id=str(conv.id),
                        title=conv.title,
                        user_id=conv.user_id,
                        created_at=conv.created_at,
                        updated_at=conv.updated_at,
                        metadata={}  # Enhanced model doesn't have metadata field
                    )
                    for conv in conversations
                ]
                
        except Exception as e:
            logger.error(f"Error getting user conversations: {e}")
            raise
    
    async def update_conversation(
        self, 
        conversation_id: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[ConversationResponse]:
        """Update a conversation."""
        try:
            async with db_manager.get_session() as session:
                stmt = select(Conversation).where(Conversation.id == conversation_id)
                result = await session.execute(stmt)
                conversation = result.scalar_one_or_none()
                
                if not conversation:
                    return None
                
                if title is not None:
                    conversation.title = title
                
                if metadata is not None:
                    # Enhanced model doesn't have metadata field, but we can update other fields
                    if metadata.get("model_used"):
                        conversation.model_used = metadata["model_used"]
                    if metadata.get("external_apis_used"):
                        conversation.external_apis_used = metadata["external_apis_used"]
                
                await session.commit()
                await session.refresh(conversation)
                
                logger.info(f"Updated conversation {conversation_id}")
                
                return ConversationResponse(
                    id=str(conversation.id),
                    title=conversation.title,
                    user_id=conversation.user_id,
                    created_at=conversation.created_at,
                    updated_at=conversation.updated_at,
                    metadata={}  # Enhanced model doesn't have metadata field
                )
                
        except Exception as e:
            logger.error(f"Error updating conversation {conversation_id}: {e}")
            raise
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its messages."""
        try:
            async with db_manager.get_session() as session:
                stmt = select(Conversation).where(Conversation.id == conversation_id)
                result = await session.execute(stmt)
                conversation = result.scalar_one_or_none()
                
                if not conversation:
                    return False
                
                await session.delete(conversation)
                await session.commit()
                
                logger.info(f"Deleted conversation {conversation_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id}: {e}")
            raise
    
    async def add_message(
        self,
        conversation_id: str,
        content: str,
        role: str,
        model_id: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None
    ) -> MessageResponse:
        """Add a message to a conversation."""
        try:
            async with db_manager.get_session() as session:
                # Verify conversation exists
                conv_stmt = select(Conversation).where(Conversation.id == conversation_id)
                conv_result = await session.execute(conv_stmt)
                conversation = conv_result.scalar_one_or_none()
                
                if not conversation:
                    raise ValueError(f"Conversation {conversation_id} not found")
                
                message = Message(
                    conversation_id=conversation_id,
                    content=content,
                    role=role,
                    model_id=model_id,
                    external_data_used=context_data or {}
                )
                
                session.add(message)
                
                # Update conversation timestamp
                conversation.updated_at = datetime.utcnow()
                
                await session.commit()
                await session.refresh(message)
                
                logger.info(f"Added message {message.id} to conversation {conversation_id}")
                
                return MessageResponse(
                    id=str(message.id),
                    conversation_id=str(message.conversation_id),
                    content=message.content,
                    role=message.role,
                    model_id=message.model_id,
                    context_data=message.external_data_used or {},
                    created_at=message.created_at
                )
                
        except Exception as e:
            logger.error(f"Error adding message to conversation {conversation_id}: {e}")
            raise
    
    async def get_conversation_messages(
        self,
        conversation_id: str,
        limit: int = 100,
        offset: int = 0,
        include_context: bool = False
    ) -> List[MessageResponse]:
        """Get messages for a conversation."""
        try:
            async with db_manager.get_session() as session:
                stmt = select(Message).where(Message.conversation_id == conversation_id)
                stmt = stmt.order_by(Message.created_at).limit(limit).offset(offset)
                
                result = await session.execute(stmt)
                messages = result.scalars().all()
                
                return [
                    MessageResponse(
                        id=str(msg.id),
                        conversation_id=str(msg.conversation_id),
                        content=msg.content,
                        role=msg.role,
                        model_id=msg.model_id,
                        context_data=msg.external_data_used if include_context else {},
                        created_at=msg.created_at
                    )
                    for msg in messages
                ]
                
        except Exception as e:
            logger.error(f"Error getting messages for conversation {conversation_id}: {e}")
            raise
    
    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get conversation history in chat format for AI context."""
        try:
            messages = await self.get_conversation_messages(
                conversation_id=conversation_id,
                limit=limit,
                include_context=False
            )
            
            # Convert to chat format
            history = []
            for msg in messages:
                history.append({
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat() if msg.created_at else None
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting conversation history {conversation_id}: {e}")
            raise
    
    async def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation summary and statistics."""
        try:
            async with db_manager.get_session() as session:
                # Get conversation
                conv_stmt = select(Conversation).where(Conversation.id == conversation_id)
                conv_result = await session.execute(conv_stmt)
                conversation = conv_result.scalar_one_or_none()
                
                if not conversation:
                    return {"error": "Conversation not found"}
                
                # Get message statistics
                msg_count_stmt = select(func.count(Message.id)).where(
                    Message.conversation_id == conversation_id
                )
                msg_count_result = await session.execute(msg_count_stmt)
                total_messages = msg_count_result.scalar() or 0
                
                # Get user and assistant message counts
                user_msg_stmt = select(func.count(Message.id)).where(
                    and_(Message.conversation_id == conversation_id, Message.role == "user")
                )
                user_msg_result = await session.execute(user_msg_stmt)
                user_messages = user_msg_result.scalar() or 0
                
                assistant_msg_stmt = select(func.count(Message.id)).where(
                    and_(Message.conversation_id == conversation_id, Message.role == "assistant")
                )
                assistant_msg_result = await session.execute(assistant_msg_stmt)
                assistant_messages = assistant_msg_result.scalar() or 0
                
                # Get unique models used
                models_stmt = select(Message.model_id).where(
                    and_(Message.conversation_id == conversation_id, Message.model_id.isnot(None))
                ).distinct()
                models_result = await session.execute(models_stmt)
                models_used = [row[0] for row in models_result.fetchall()]
                
                # Get last message timestamp
                last_msg_stmt = select(Message.created_at).where(
                    Message.conversation_id == conversation_id
                ).order_by(desc(Message.created_at)).limit(1)
                last_msg_result = await session.execute(last_msg_stmt)
                last_message_time = last_msg_result.scalar()
                
                return {
                    "conversation_id": conversation_id,
                    "title": conversation.title,
                    "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
                    "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
                    "total_messages": total_messages,
                    "user_messages": user_messages,
                    "assistant_messages": assistant_messages,
                    "models_used": models_used,
                    "last_message_at": last_message_time.isoformat() if last_message_time else None,
                    "metadata": {
                        "model_used": conversation.model_used,
                        "external_apis_used": conversation.external_apis_used,
                        "is_archived": conversation.is_archived,
                        "is_shared": conversation.is_shared
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting conversation summary {conversation_id}: {e}")
            raise
    
    async def search_conversations(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 20
    ) -> List[ConversationResponse]:
        """Search conversations by title or content."""
        try:
            async with db_manager.get_session() as session:
                # Search in conversation titles and message content
                stmt = select(Conversation).distinct()
                
                if user_id is not None:
                    stmt = stmt.where(Conversation.user_id == user_id)
                
                # Join with messages for content search
                stmt = stmt.outerjoin(Message)
                
                # Search in titles and message content
                search_condition = (
                    Conversation.title.ilike(f"%{query}%") |
                    Message.content.ilike(f"%{query}%")
                )
                
                stmt = stmt.where(search_condition)
                stmt = stmt.order_by(desc(Conversation.updated_at)).limit(limit)
                
                result = await session.execute(stmt)
                conversations = result.scalars().all()
                
                return [
                    ConversationResponse(
                        id=str(conv.id),
                        title=conv.title,
                        user_id=conv.user_id,
                        created_at=conv.created_at,
                        updated_at=conv.updated_at,
                        metadata={}  # Enhanced model doesn't have metadata field
                    )
                    for conv in conversations
                ]
                
        except Exception as e:
            logger.error(f"Error searching conversations: {e}")
            raise
    
    async def get_conversation_with_messages(
        self,
        conversation_id: str,
        message_limit: int = 50
    ) -> Optional[Dict[str, Any]]:
        """Get conversation with its messages."""
        try:
            async with db_manager.get_session() as session:
                # Get conversation with messages
                stmt = select(Conversation).options(
                    selectinload(Conversation.messages)
                ).where(Conversation.id == conversation_id)
                
                result = await session.execute(stmt)
                conversation = result.scalar_one_or_none()
                
                if not conversation:
                    return None
                
                # Sort messages by creation time and limit
                messages = sorted(conversation.messages, key=lambda m: m.created_at)[-message_limit:]
                
                return {
                    "conversation": ConversationResponse(
                        id=str(conversation.id),
                        title=conversation.title,
                        user_id=conversation.user_id,
                        created_at=conversation.created_at,
                        updated_at=conversation.updated_at,
                        metadata={}  # Enhanced model doesn't have metadata field
                    ),
                    "messages": [
                        MessageResponse(
                            id=str(msg.id),
                            conversation_id=str(msg.conversation_id),
                            content=msg.content,
                            role=msg.role,
                            model_id=msg.model_id,
                            context_data=msg.external_data_used or {},
                            created_at=msg.created_at
                        )
                        for msg in messages
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error getting conversation with messages {conversation_id}: {e}")
            raise


# Global conversation service instance
conversation_service = ConversationService()