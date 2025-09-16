"""
SQLAlchemy models for the AI agent database.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.connection import Base


class User(Base):
    """User model for authentication."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")


class Conversation(Base):
    """Conversation model for chat sessions."""
    
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    title = Column(String(500), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    metadata_ = Column("metadata", JSONB, default=dict)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Message model for individual chat messages."""
    
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    model_id = Column(String(100), nullable=True)
    context_data = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class Document(Base):
    """Document model for vector storage."""
    
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=True)
    content = Column(Text, nullable=False)
    # Note: embedding column is handled separately via raw SQL due to vector type
    metadata_ = Column("metadata", JSONB, default=dict)
    source = Column(String(255), nullable=True, index=True)
    document_type = Column(String(100), default="text", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# Pydantic models for API serialization
from pydantic import BaseModel, Field
from typing import List, Optional as OptionalType
from datetime import datetime as dt


class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    created_at: dt
    is_active: bool
    
    class Config:
        from_attributes = True


class ConversationBase(BaseModel):
    title: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationCreate(ConversationBase):
    user_id: OptionalType[int] = None


class ConversationResponse(ConversationBase):
    id: str
    user_id: OptionalType[int]
    created_at: dt
    updated_at: dt
    
    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    content: str
    role: str
    model_id: OptionalType[str] = None
    context_data: Dict[str, Any] = Field(default_factory=dict)


class MessageCreate(MessageBase):
    conversation_id: str


class MessageResponse(MessageBase):
    id: str
    conversation_id: str
    created_at: dt
    
    class Config:
        from_attributes = True


class DocumentBase(BaseModel):
    title: OptionalType[str] = None
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source: OptionalType[str] = None
    document_type: str = "text"


class DocumentCreate(DocumentBase):
    pass


class DocumentResponse(DocumentBase):
    id: int
    created_at: dt
    updated_at: dt
    
    class Config:
        from_attributes = True


class VectorSearchResult(BaseModel):
    id: int
    title: OptionalType[str]
    content: str
    metadata: Dict[str, Any]
    similarity_score: float