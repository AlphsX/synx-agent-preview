"""
Database models for real-time collaboration features.
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Integer, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

Base = declarative_base()

class CollaborationRole(enum.Enum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"
    COMMENTER = "commenter"

class PresenceStatus(enum.Enum):
    ONLINE = "online"
    AWAY = "away"
    BUSY = "busy"
    OFFLINE = "offline"

class SharedConversation(Base):
    """Model for shared conversation spaces that multiple users can access."""
    
    __tablename__ = "shared_conversations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Sharing configuration
    share_token = Column(String, unique=True, nullable=False, index=True)
    is_public = Column(Boolean, default=False)
    allow_anonymous = Column(Boolean, default=False)
    max_participants = Column(Integer, default=10)
    
    # Permissions
    default_role = Column(Enum(CollaborationRole), default=CollaborationRole.VIEWER)
    allow_branching = Column(Boolean, default=True)
    allow_editing = Column(Boolean, default=False)
    
    # Metadata
    description = Column(Text, nullable=True)
    tags = Column(JSON, default=list)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    participants = relationship("ConversationParticipant", back_populates="shared_conversation", cascade="all, delete-orphan")
    branches = relationship("ConversationBranch", back_populates="shared_conversation", cascade="all, delete-orphan")

class ConversationParticipant(Base):
    """Model for users participating in shared conversations."""
    
    __tablename__ = "conversation_participants"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    shared_conversation_id = Column(String, ForeignKey("shared_conversations.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # Null for anonymous users
    
    # Participant info
    display_name = Column(String, nullable=False)
    avatar_color = Column(String, default="#3B82F6")  # Default blue
    role = Column(Enum(CollaborationRole), default=CollaborationRole.VIEWER)
    
    # Session info
    session_id = Column(String, nullable=False, index=True)
    is_anonymous = Column(Boolean, default=False)
    
    # Status
    presence_status = Column(Enum(PresenceStatus), default=PresenceStatus.ONLINE)
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    is_typing = Column(Boolean, default=False)
    typing_updated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Permissions
    can_edit = Column(Boolean, default=False)
    can_branch = Column(Boolean, default=True)
    can_invite = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    shared_conversation = relationship("SharedConversation", back_populates="participants")

class ConversationBranch(Base):
    """Model for conversation branches created during collaboration."""
    
    __tablename__ = "conversation_branches"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    shared_conversation_id = Column(String, ForeignKey("shared_conversations.id"), nullable=False)
    parent_message_id = Column(String, nullable=False)  # Message where branch starts
    creator_id = Column(String, ForeignKey("users.id"), nullable=True)
    
    # Branch info
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    branch_type = Column(String, default="alternative")  # alternative, experiment, correction
    
    # Status
    is_active = Column(Boolean, default=True)
    is_merged = Column(Boolean, default=False)
    merged_at = Column(DateTime(timezone=True), nullable=True)
    merged_by = Column(String, ForeignKey("users.id"), nullable=True)
    
    # Metadata
    tags = Column(JSON, default=list)
    vote_score = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    shared_conversation = relationship("SharedConversation", back_populates="branches")
    messages = relationship("BranchMessage", back_populates="branch", cascade="all, delete-orphan")

class BranchMessage(Base):
    """Model for messages within conversation branches."""
    
    __tablename__ = "branch_messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    branch_id = Column(String, ForeignKey("conversation_branches.id"), nullable=False)
    author_id = Column(String, ForeignKey("users.id"), nullable=True)
    
    # Message content
    content = Column(Text, nullable=False)
    role = Column(String, nullable=False)  # "user", "assistant", "system"
    model_id = Column(String, nullable=True)
    
    # Metadata
    external_data_used = Column(JSON, default=dict)
    processing_time = Column(Integer, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    
    # Collaboration features
    is_suggestion = Column(Boolean, default=False)
    parent_message_id = Column(String, nullable=True)  # For threaded discussions
    vote_score = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    branch = relationship("ConversationBranch", back_populates="messages")

class TypingIndicator(Base):
    """Model for real-time typing indicators."""
    
    __tablename__ = "typing_indicators"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, nullable=False, index=True)  # Can be regular or shared conversation
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    session_id = Column(String, nullable=False, index=True)
    
    # Typing info
    display_name = Column(String, nullable=False)
    is_typing = Column(Boolean, default=True)
    typing_text = Column(String, nullable=True)  # Preview of what they're typing
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)  # Auto-expire after inactivity

class CollaborationEvent(Base):
    """Model for tracking collaboration events and activity."""
    
    __tablename__ = "collaboration_events"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    shared_conversation_id = Column(String, ForeignKey("shared_conversations.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    
    # Event details
    event_type = Column(String, nullable=False)  # join, leave, message, branch, merge, etc.
    event_data = Column(JSON, default=dict)
    description = Column(Text, nullable=True)
    
    # Metadata
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ConversationInvite(Base):
    """Model for conversation invitations."""
    
    __tablename__ = "conversation_invites"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    shared_conversation_id = Column(String, ForeignKey("shared_conversations.id"), nullable=False)
    inviter_id = Column(String, ForeignKey("users.id"), nullable=False)
    invitee_email = Column(String, nullable=True)
    invitee_id = Column(String, ForeignKey("users.id"), nullable=True)
    
    # Invite details
    invite_token = Column(String, unique=True, nullable=False, index=True)
    role = Column(Enum(CollaborationRole), default=CollaborationRole.VIEWER)
    message = Column(Text, nullable=True)
    
    # Status
    is_accepted = Column(Boolean, default=False)
    is_expired = Column(Boolean, default=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())