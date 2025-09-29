"""
Analytics models for conversation tracking and insights.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.connection import Base


class ConversationAnalytics(Base):
    """Analytics tracking for conversations."""
    
    __tablename__ = "conversation_analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    
    # Message counts
    total_messages = Column(Integer, default=0)
    user_messages = Column(Integer, default=0)
    assistant_messages = Column(Integer, default=0)
    
    # Response time metrics (in milliseconds)
    avg_response_time = Column(Float, default=0.0)
    min_response_time = Column(Float, default=0.0)
    max_response_time = Column(Float, default=0.0)
    total_response_time = Column(Float, default=0.0)
    
    # Context usage tracking
    context_types_used = Column(JSONB, default=list)  # ["web_search", "crypto_data", etc.]
    external_apis_called = Column(JSONB, default=list)  # ["SerpAPI", "Binance", etc.]
    context_usage_count = Column(Integer, default=0)
    
    # Model usage
    models_used = Column(JSONB, default=list)  # List of model IDs used
    primary_model = Column(String(100), nullable=True)  # Most used model
    model_switches = Column(Integer, default=0)  # Number of model changes
    
    # Engagement metrics
    conversation_duration = Column(Float, default=0.0)  # Duration in minutes
    user_engagement_score = Column(Float, default=0.0)  # 0-100 score
    conversation_quality_score = Column(Float, default=0.0)  # 0-100 score
    
    # Token usage
    total_tokens_used = Column(Integer, default=0)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    
    # Error tracking
    error_count = Column(Integer, default=0)
    fallback_usage_count = Column(Integer, default=0)
    
    # Timestamps
    first_message_at = Column(DateTime(timezone=True), nullable=True)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    conversation = relationship("Conversation", backref="analytics")
    user = relationship("User", backref="conversation_analytics")


class MessageAnalytics(Base):
    """Analytics tracking for individual messages."""
    
    __tablename__ = "message_analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    
    # Message metrics
    message_length = Column(Integer, default=0)  # Character count
    word_count = Column(Integer, default=0)
    sentence_count = Column(Integer, default=0)
    
    # Processing metrics
    processing_time = Column(Float, default=0.0)  # Time to generate response (ms)
    context_fetch_time = Column(Float, default=0.0)  # Time to fetch external context (ms)
    ai_response_time = Column(Float, default=0.0)  # AI model response time (ms)
    
    # Context usage for this message
    context_data_used = Column(JSONB, default=dict)  # What context was used
    external_apis_used = Column(JSONB, default=list)  # Which APIs were called
    
    # Quality metrics
    user_rating = Column(Integer, nullable=True)  # 1-5 rating from user
    auto_quality_score = Column(Float, default=0.0)  # Automated quality assessment
    
    # Token usage for this message
    tokens_used = Column(Integer, default=0)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    
    # Error tracking
    had_errors = Column(Boolean, default=False)
    error_details = Column(JSONB, default=dict)
    used_fallback = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    message = relationship("Message", backref="analytics")
    conversation = relationship("Conversation")
    user = relationship("User")


class UserEngagementMetrics(Base):
    """User engagement metrics aggregated over time."""
    
    __tablename__ = "user_engagement_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Time period for these metrics
    period_type = Column(String(20), nullable=False)  # "daily", "weekly", "monthly"
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Conversation metrics
    total_conversations = Column(Integer, default=0)
    active_conversations = Column(Integer, default=0)  # Conversations with activity
    avg_conversation_length = Column(Float, default=0.0)  # Average messages per conversation
    
    # Message metrics
    total_messages_sent = Column(Integer, default=0)
    total_messages_received = Column(Integer, default=0)
    avg_message_length = Column(Float, default=0.0)
    
    # Usage patterns
    most_used_model = Column(String(100), nullable=True)
    favorite_context_types = Column(JSONB, default=list)
    peak_usage_hour = Column(Integer, nullable=True)  # 0-23
    
    # Engagement scores
    overall_engagement_score = Column(Float, default=0.0)  # 0-100
    conversation_quality_avg = Column(Float, default=0.0)  # Average quality score
    user_satisfaction_score = Column(Float, default=0.0)  # Based on ratings
    
    # Feature usage
    search_tool_usage = Column(JSONB, default=dict)  # Usage count per search tool
    model_usage = Column(JSONB, default=dict)  # Usage count per model
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="engagement_metrics")


class SystemAnalytics(Base):
    """System-wide analytics and performance metrics."""
    
    __tablename__ = "system_analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    
    # Time period
    period_type = Column(String(20), nullable=False)  # "hourly", "daily", "weekly"
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Usage metrics
    total_conversations = Column(Integer, default=0)
    total_messages = Column(Integer, default=0)
    unique_users = Column(Integer, default=0)
    
    # Performance metrics
    avg_response_time = Column(Float, default=0.0)
    avg_context_fetch_time = Column(Float, default=0.0)
    system_uptime_percentage = Column(Float, default=100.0)
    
    # API usage
    external_api_calls = Column(JSONB, default=dict)  # Calls per API
    api_success_rate = Column(Float, default=100.0)
    api_error_count = Column(Integer, default=0)
    
    # Model usage distribution
    model_usage_distribution = Column(JSONB, default=dict)
    most_popular_model = Column(String(100), nullable=True)
    
    # Context usage
    context_type_usage = Column(JSONB, default=dict)
    search_query_count = Column(Integer, default=0)
    crypto_data_requests = Column(Integer, default=0)
    
    # Error tracking
    total_errors = Column(Integer, default=0)
    error_types = Column(JSONB, default=dict)
    fallback_usage = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Add indexes for performance
    __table_args__ = (
        {"postgresql_partition_by": "RANGE (period_start)"},
    )