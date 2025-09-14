from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Preferences
    preferred_model = Column(String, default="groq-llama-3.1-70b")
    theme = Column(String, default="dark")
    api_usage_limit = Column(Integer, default=1000)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    api_usage = relationship("ApiUsage", back_populates="user", cascade="all, delete-orphan")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    
    # Enhanced features
    model_used = Column(String, default="groq-llama-3.1-70b")
    external_apis_used = Column(JSON, default=list)  # Track which external APIs were used
    is_archived = Column(Boolean, default=False)
    is_shared = Column(Boolean, default=False)
    share_token = Column(String, unique=True, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    content = Column(Text, nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    
    # Enhanced features
    model_id = Column(String, nullable=True)  # Which AI model was used
    external_data_used = Column(JSON, default=dict)  # What external data was used
    processing_time = Column(Integer, nullable=True)  # Processing time in milliseconds
    tokens_used = Column(Integer, nullable=True)  # Tokens consumed
    
    # Metadata
    is_edited = Column(Boolean, default=False)
    is_flagged = Column(Boolean, default=False)
    rating = Column(Integer, nullable=True)  # User rating 1-5
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

class ApiUsage(Base):
    __tablename__ = "api_usage"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Usage tracking
    api_type = Column(String, nullable=False)  # "openai", "anthropic", "groq", "brave_search", "binance"
    endpoint = Column(String, nullable=False)
    tokens_used = Column(Integer, default=0)
    cost = Column(String, default="0.00")  # Cost in USD
    
    # Request details
    model_used = Column(String, nullable=True)
    request_data = Column(JSON, default=dict)
    response_status = Column(String, default="success")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="api_usage")

class ExternalApiCache(Base):
    __tablename__ = "external_api_cache"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Cache key and data
    cache_key = Column(String, unique=True, nullable=False, index=True)
    api_type = Column(String, nullable=False)  # "brave_search", "binance", etc.
    query = Column(String, nullable=False)
    response_data = Column(JSON, nullable=False)
    
    # Cache management
    expires_at = Column(DateTime(timezone=True), nullable=False)
    hit_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class SystemSettings(Base):
    __tablename__ = "system_settings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # System configuration
    setting_key = Column(String, unique=True, nullable=False)
    setting_value = Column(JSON, nullable=False)
    description = Column(Text, nullable=True)
    
    # Management
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())