"""
Analytics service for conversation tracking and insights.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
import json
import statistics

from sqlalchemy import func, and_, or_, desc, asc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.connection import get_database_session
from app.analytics.models import (
    ConversationAnalytics, 
    MessageAnalytics, 
    UserEngagementMetrics, 
    SystemAnalytics
)
from app.database.models import Conversation, Message, User

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for tracking and analyzing conversation data."""
    
    def __init__(self):
        self.logger = logger
    
    async def track_message_analytics(
        self,
        message_id: str,
        conversation_id: str,
        user_id: Optional[int] = None,
        processing_time: float = 0.0,
        context_data: Dict[str, Any] = None,
        tokens_used: int = 0,
        had_errors: bool = False,
        error_details: Dict[str, Any] = None
    ) -> bool:
        """Track analytics for a single message."""
        try:
            async with get_database_session() as session:
                # Get message details - handle string IDs from enhanced chat models
                try:
                    # Try to get message using string ID directly
                    from app.enhanced_chat_models import Message as EnhancedMessage
                    message_result = await session.execute(
                        select(EnhancedMessage).filter(EnhancedMessage.id == message_id)
                    )
                    message = message_result.scalar_one_or_none()
                except Exception:
                    # Fallback to UUID conversion if needed
                    try:
                        message = await session.get(Message, UUID(message_id))
                    except Exception:
                        message = None
                
                if not message:
                    logger.warning(f"Message {message_id} not found for analytics tracking")
                    return False
                
                # Calculate message metrics
                message_length = len(message.content)
                word_count = len(message.content.split())
                sentence_count = message.content.count('.') + message.content.count('!') + message.content.count('?')
                
                # Extract context usage
                context_data = context_data or {}
                external_apis_used = []
                context_fetch_time = 0.0
                
                if context_data:
                    if 'web_search' in context_data:
                        external_apis_used.append(context_data['web_search'].get('provider', 'unknown'))
                    if 'crypto_data' in context_data:
                        external_apis_used.append('Binance')
                    if 'news' in context_data:
                        external_apis_used.append(context_data['news'].get('provider', 'unknown'))
                    if 'vector_search' in context_data:
                        external_apis_used.append('Vector Database')
                
                # Create message analytics record - handle string IDs
                try:
                    # Try to convert to UUID if possible
                    msg_uuid = UUID(message_id) if len(message_id) == 36 else None
                    conv_uuid = UUID(conversation_id) if len(conversation_id) == 36 else None
                except (ValueError, TypeError):
                    # Skip analytics if IDs are not valid UUIDs
                    logger.warning(f"Invalid UUID format for message {message_id} or conversation {conversation_id}, skipping analytics")
                    return False
                
                if not msg_uuid or not conv_uuid:
                    logger.warning(f"Could not convert IDs to UUID format, skipping analytics")
                    return False
                
                message_analytics = MessageAnalytics(
                    message_id=msg_uuid,
                    conversation_id=conv_uuid,
                    user_id=user_id,
                    message_length=message_length,
                    word_count=word_count,
                    sentence_count=sentence_count,
                    processing_time=processing_time,
                    context_fetch_time=context_fetch_time,
                    context_data_used=context_data,
                    external_apis_used=external_apis_used,
                    tokens_used=tokens_used,
                    had_errors=had_errors,
                    error_details=error_details or {},
                    used_fallback=bool(error_details and error_details.get('used_fallback'))
                )
                
                session.add(message_analytics)
                await session.commit()
                
                # Update conversation analytics
                await self._update_conversation_analytics(session, conversation_id, user_id)
                
                logger.info(f"Tracked analytics for message {message_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error tracking message analytics: {e}")
            return False
    
    async def _update_conversation_analytics(
        self, 
        session: AsyncSession, 
        conversation_id: str, 
        user_id: Optional[int] = None
    ):
        """Update conversation-level analytics."""
        try:
            # Get or create conversation analytics - handle string IDs
            try:
                conv_uuid = UUID(conversation_id) if len(conversation_id) == 36 else None
            except (ValueError, TypeError):
                logger.warning(f"Invalid conversation ID format: {conversation_id}")
                return
            
            if not conv_uuid:
                logger.warning(f"Could not convert conversation ID to UUID: {conversation_id}")
                return
            
            result = await session.execute(
                select(ConversationAnalytics).filter(
                    ConversationAnalytics.conversation_id == conv_uuid
                )
            )
            conv_analytics = result.scalar_one_or_none()
            
            if not conv_analytics:
                conv_analytics = ConversationAnalytics(
                    conversation_id=conv_uuid,
                    user_id=user_id
                )
                session.add(conv_analytics)
            
            # Get all messages for this conversation
            messages_result = await session.execute(
                select(Message).filter(
                    Message.conversation_id == UUID(conversation_id)
                ).order_by(Message.created_at)
            )
            messages = messages_result.scalars().all()
            
            if not messages:
                return
            
            # Calculate metrics
            total_messages = len(messages)
            user_messages = len([m for m in messages if m.role == 'user'])
            assistant_messages = len([m for m in messages if m.role == 'assistant'])
            
            # Get message analytics for response times
            msg_analytics_result = await session.execute(
                select(MessageAnalytics).filter(
                    MessageAnalytics.conversation_id == UUID(conversation_id)
                )
            )
            msg_analytics = msg_analytics_result.scalars().all()
            
            # Calculate response time metrics
            response_times = [ma.processing_time for ma in msg_analytics if ma.processing_time > 0]
            avg_response_time = statistics.mean(response_times) if response_times else 0.0
            min_response_time = min(response_times) if response_times else 0.0
            max_response_time = max(response_times) if response_times else 0.0
            total_response_time = sum(response_times) if response_times else 0.0
            
            # Extract context usage
            context_types = set()
            external_apis = set()
            context_usage_count = 0
            
            for ma in msg_analytics:
                if ma.context_data_used:
                    context_types.update(ma.context_data_used.keys())
                    context_usage_count += len(ma.context_data_used)
                if ma.external_apis_used:
                    external_apis.update(ma.external_apis_used)
            
            # Extract model usage
            models_used = list(set(m.model_id for m in messages if m.model_id))
            primary_model = max(set(models_used), key=models_used.count) if models_used else None
            
            # Calculate conversation duration
            first_message = messages[0]
            last_message = messages[-1]
            duration = (last_message.created_at - first_message.created_at).total_seconds() / 60.0
            
            # Calculate engagement and quality scores
            engagement_score = self._calculate_engagement_score(messages, msg_analytics)
            quality_score = self._calculate_quality_score(messages, msg_analytics)
            
            # Update analytics
            conv_analytics.total_messages = total_messages
            conv_analytics.user_messages = user_messages
            conv_analytics.assistant_messages = assistant_messages
            conv_analytics.avg_response_time = avg_response_time
            conv_analytics.min_response_time = min_response_time
            conv_analytics.max_response_time = max_response_time
            conv_analytics.total_response_time = total_response_time
            conv_analytics.context_types_used = list(context_types)
            conv_analytics.external_apis_called = list(external_apis)
            conv_analytics.context_usage_count = context_usage_count
            conv_analytics.models_used = models_used
            conv_analytics.primary_model = primary_model
            conv_analytics.conversation_duration = duration
            conv_analytics.user_engagement_score = engagement_score
            conv_analytics.conversation_quality_score = quality_score
            conv_analytics.first_message_at = first_message.created_at
            conv_analytics.last_message_at = last_message.created_at
            conv_analytics.error_count = sum(1 for ma in msg_analytics if ma.had_errors)
            conv_analytics.fallback_usage_count = sum(1 for ma in msg_analytics if ma.used_fallback)
            conv_analytics.total_tokens_used = sum(ma.tokens_used for ma in msg_analytics)
            
            await session.commit()
            
        except Exception as e:
            logger.error(f"Error updating conversation analytics: {e}")
    
    def _calculate_engagement_score(self, messages: List[Message], analytics: List[MessageAnalytics]) -> float:
        """Calculate user engagement score (0-100)."""
        if not messages:
            return 0.0
        
        try:
            # Factors for engagement:
            # 1. Message frequency and consistency
            # 2. Message length and complexity
            # 3. Context tool usage
            # 4. Conversation duration
            
            score = 0.0
            
            # Message frequency (0-30 points)
            user_messages = [m for m in messages if m.role == 'user']
            if len(user_messages) >= 10:
                score += 30
            elif len(user_messages) >= 5:
                score += 20
            elif len(user_messages) >= 2:
                score += 10
            
            # Average message length (0-25 points)
            if user_messages:
                avg_length = sum(len(m.content) for m in user_messages) / len(user_messages)
                if avg_length >= 100:
                    score += 25
                elif avg_length >= 50:
                    score += 15
                elif avg_length >= 20:
                    score += 10
            
            # Context usage (0-25 points)
            context_usage = sum(1 for a in analytics if a.context_data_used)
            if context_usage >= 5:
                score += 25
            elif context_usage >= 3:
                score += 15
            elif context_usage >= 1:
                score += 10
            
            # Conversation duration (0-20 points)
            if len(messages) >= 2:
                duration = (messages[-1].created_at - messages[0].created_at).total_seconds() / 60.0
                if duration >= 30:  # 30+ minutes
                    score += 20
                elif duration >= 15:  # 15+ minutes
                    score += 15
                elif duration >= 5:   # 5+ minutes
                    score += 10
            
            return min(score, 100.0)
            
        except Exception as e:
            logger.error(f"Error calculating engagement score: {e}")
            return 0.0
    
    def _calculate_quality_score(self, messages: List[Message], analytics: List[MessageAnalytics]) -> float:
        """Calculate conversation quality score (0-100)."""
        if not messages:
            return 0.0
        
        try:
            score = 100.0  # Start with perfect score and deduct
            
            # Deduct for errors
            error_count = sum(1 for a in analytics if a.had_errors)
            score -= error_count * 10  # -10 points per error
            
            # Deduct for fallback usage
            fallback_count = sum(1 for a in analytics if a.used_fallback)
            score -= fallback_count * 5  # -5 points per fallback
            
            # Deduct for very slow responses
            slow_responses = sum(1 for a in analytics if a.processing_time > 10000)  # >10 seconds
            score -= slow_responses * 5
            
            # Bonus for context usage
            context_usage = sum(1 for a in analytics if a.context_data_used)
            score += min(context_usage * 2, 10)  # +2 points per context use, max 10
            
            return max(min(score, 100.0), 0.0)
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return 50.0  # Default middle score
    
    async def get_conversation_insights(self, conversation_id: str) -> Dict[str, Any]:
        """Get detailed insights for a specific conversation."""
        try:
            async with get_database_session() as session:
                # Get conversation analytics
                result = await session.execute(
                    select(ConversationAnalytics).filter(
                        ConversationAnalytics.conversation_id == UUID(conversation_id)
                    )
                )
                conv_analytics = result.scalar_one_or_none()
                
                if not conv_analytics:
                    return {"error": "No analytics data found for conversation"}
                
                # Get message analytics
                result = await session.execute(
                    select(MessageAnalytics).filter(
                        MessageAnalytics.conversation_id == UUID(conversation_id)
                    ).order_by(MessageAnalytics.created_at)
                )
                msg_analytics = result.scalars().all()
                
                # Get conversation details
                conversation = await session.get(Conversation, UUID(conversation_id))
                
                insights = {
                    "conversation_id": conversation_id,
                    "title": conversation.title if conversation else "Unknown",
                    "created_at": conversation.created_at.isoformat() if conversation else None,
                    
                    # Message metrics
                    "message_metrics": {
                        "total_messages": conv_analytics.total_messages,
                        "user_messages": conv_analytics.user_messages,
                        "assistant_messages": conv_analytics.assistant_messages,
                        "avg_message_length": statistics.mean([ma.message_length for ma in msg_analytics]) if msg_analytics else 0,
                        "total_words": sum(ma.word_count for ma in msg_analytics),
                    },
                    
                    # Performance metrics
                    "performance_metrics": {
                        "avg_response_time_ms": conv_analytics.avg_response_time,
                        "min_response_time_ms": conv_analytics.min_response_time,
                        "max_response_time_ms": conv_analytics.max_response_time,
                        "total_processing_time_ms": conv_analytics.total_response_time,
                    },
                    
                    # Context usage
                    "context_usage": {
                        "types_used": conv_analytics.context_types_used,
                        "external_apis_called": conv_analytics.external_apis_called,
                        "total_context_requests": conv_analytics.context_usage_count,
                        "context_usage_rate": conv_analytics.context_usage_count / max(conv_analytics.assistant_messages, 1)
                    },
                    
                    # Model usage
                    "model_usage": {
                        "models_used": conv_analytics.models_used,
                        "primary_model": conv_analytics.primary_model,
                        "model_switches": conv_analytics.model_switches,
                    },
                    
                    # Quality metrics
                    "quality_metrics": {
                        "engagement_score": conv_analytics.user_engagement_score,
                        "quality_score": conv_analytics.conversation_quality_score,
                        "error_count": conv_analytics.error_count,
                        "fallback_usage": conv_analytics.fallback_usage_count,
                        "error_rate": conv_analytics.error_count / max(conv_analytics.total_messages, 1)
                    },
                    
                    # Time metrics
                    "time_metrics": {
                        "duration_minutes": conv_analytics.conversation_duration,
                        "first_message_at": conv_analytics.first_message_at.isoformat() if conv_analytics.first_message_at else None,
                        "last_message_at": conv_analytics.last_message_at.isoformat() if conv_analytics.last_message_at else None,
                    },
                    
                    # Token usage
                    "token_usage": {
                        "total_tokens": conv_analytics.total_tokens_used,
                        "avg_tokens_per_message": conv_analytics.total_tokens_used / max(conv_analytics.assistant_messages, 1)
                    }
                }
                
                return insights
                
        except Exception as e:
            logger.error(f"Error getting conversation insights: {e}")
            return {"error": str(e)}
    
    async def get_user_engagement_metrics(
        self, 
        user_id: int, 
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Get user engagement metrics for a specific period."""
        try:
            async with get_database_session() as session:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=period_days)
                
                # Get user's conversation analytics in the period
                result = await session.execute(
                    select(ConversationAnalytics).filter(
                        and_(
                            ConversationAnalytics.user_id == user_id,
                            ConversationAnalytics.created_at >= start_date,
                            ConversationAnalytics.created_at <= end_date
                        )
                    )
                )
                conv_analytics = result.scalars().all()
                
                if not conv_analytics:
                    return {
                        "user_id": user_id,
                        "period_days": period_days,
                        "total_conversations": 0,
                        "message": "No activity in the specified period"
                    }
                
                # Calculate metrics
                total_conversations = len(conv_analytics)
                total_messages = sum(ca.total_messages for ca in conv_analytics)
                total_user_messages = sum(ca.user_messages for ca in conv_analytics)
                total_assistant_messages = sum(ca.assistant_messages for ca in conv_analytics)
                
                avg_engagement = statistics.mean([ca.user_engagement_score for ca in conv_analytics])
                avg_quality = statistics.mean([ca.conversation_quality_score for ca in conv_analytics])
                
                # Context usage analysis
                all_context_types = []
                all_apis = []
                for ca in conv_analytics:
                    all_context_types.extend(ca.context_types_used or [])
                    all_apis.extend(ca.external_apis_called or [])
                
                context_usage_freq = {}
                for context_type in all_context_types:
                    context_usage_freq[context_type] = context_usage_freq.get(context_type, 0) + 1
                
                api_usage_freq = {}
                for api in all_apis:
                    api_usage_freq[api] = api_usage_freq.get(api, 0) + 1
                
                # Model usage analysis
                all_models = []
                for ca in conv_analytics:
                    all_models.extend(ca.models_used or [])
                
                model_usage_freq = {}
                for model in all_models:
                    model_usage_freq[model] = model_usage_freq.get(model, 0) + 1
                
                most_used_model = max(model_usage_freq.items(), key=lambda x: x[1])[0] if model_usage_freq else None
                
                metrics = {
                    "user_id": user_id,
                    "period_days": period_days,
                    "period_start": start_date.isoformat(),
                    "period_end": end_date.isoformat(),
                    
                    "conversation_metrics": {
                        "total_conversations": total_conversations,
                        "avg_messages_per_conversation": total_messages / total_conversations,
                        "avg_duration_minutes": statistics.mean([ca.conversation_duration for ca in conv_analytics]),
                    },
                    
                    "message_metrics": {
                        "total_messages": total_messages,
                        "user_messages": total_user_messages,
                        "assistant_messages": total_assistant_messages,
                        "messages_per_day": total_messages / period_days,
                    },
                    
                    "engagement_metrics": {
                        "avg_engagement_score": avg_engagement,
                        "avg_quality_score": avg_quality,
                        "highly_engaged_conversations": len([ca for ca in conv_analytics if ca.user_engagement_score >= 70]),
                        "high_quality_conversations": len([ca for ca in conv_analytics if ca.conversation_quality_score >= 80]),
                    },
                    
                    "feature_usage": {
                        "context_types_frequency": context_usage_freq,
                        "external_apis_frequency": api_usage_freq,
                        "model_usage_frequency": model_usage_freq,
                        "most_used_model": most_used_model,
                    },
                    
                    "performance_metrics": {
                        "avg_response_time_ms": statistics.mean([ca.avg_response_time for ca in conv_analytics if ca.avg_response_time > 0]),
                        "total_errors": sum(ca.error_count for ca in conv_analytics),
                        "total_fallbacks": sum(ca.fallback_usage_count for ca in conv_analytics),
                        "error_rate": sum(ca.error_count for ca in conv_analytics) / max(total_messages, 1),
                    }
                }
                
                return metrics
                
        except Exception as e:
            logger.error(f"Error getting user engagement metrics: {e}")
            return {"error": str(e)}
    
    async def export_conversation_data(
        self, 
        conversation_id: str, 
        format: str = "json"
    ) -> Dict[str, Any]:
        """Export conversation data for analysis."""
        try:
            async with get_database_session() as session:
                # Get conversation
                conversation = await session.get(Conversation, UUID(conversation_id))
                if not conversation:
                    return {"error": "Conversation not found"}
                
                # Get messages
                messages_result = await session.execute(
                    select(Message).filter(
                        Message.conversation_id == UUID(conversation_id)
                    ).order_by(Message.created_at)
                )
                messages = messages_result.scalars().all()
                
                # Get analytics
                insights = await self.get_conversation_insights(conversation_id)
                
                export_data = {
                    "export_metadata": {
                        "conversation_id": conversation_id,
                        "exported_at": datetime.now().isoformat(),
                        "format": format,
                        "total_messages": len(messages),
                    },
                    
                    "conversation_info": {
                        "id": conversation_id,
                        "title": conversation.title,
                        "created_at": conversation.created_at.isoformat(),
                        "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
                        "user_id": conversation.user_id,
                        "metadata": conversation.metadata_,
                    },
                    
                    "messages": [
                        {
                            "id": str(msg.id),
                            "role": msg.role,
                            "content": msg.content,
                            "model_id": msg.model_id,
                            "context_data": msg.context_data,
                            "created_at": msg.created_at.isoformat(),
                        }
                        for msg in messages
                    ],
                    
                    "analytics": insights,
                }
                
                return export_data
                
        except Exception as e:
            logger.error(f"Error exporting conversation data: {e}")
            return {"error": str(e)}
    
    async def get_system_analytics_dashboard(self, period_hours: int = 24) -> Dict[str, Any]:
        """Get system-wide analytics for dashboard."""
        try:
            async with get_database_session() as session:
                end_time = datetime.now()
                start_time = end_time - timedelta(hours=period_hours)
                
                # Get recent conversation analytics
                result = await session.execute(
                    select(ConversationAnalytics).filter(
                        ConversationAnalytics.created_at >= start_time
                    )
                )
                recent_conversations = result.scalars().all()
                
                # Get recent message analytics
                result = await session.execute(
                    select(MessageAnalytics).filter(
                        MessageAnalytics.created_at >= start_time
                    )
                )
                recent_messages = result.scalars().all()
                
                # Calculate system metrics
                total_conversations = len(recent_conversations)
                total_messages = sum(ca.total_messages for ca in recent_conversations)
                unique_users = len(set(ca.user_id for ca in recent_conversations if ca.user_id))
                
                # Performance metrics
                avg_response_time = statistics.mean([
                    ma.processing_time for ma in recent_messages 
                    if ma.processing_time > 0
                ]) if recent_messages else 0
                
                # API usage
                all_apis = []
                for ca in recent_conversations:
                    all_apis.extend(ca.external_apis_called or [])
                
                api_usage = {}
                for api in all_apis:
                    api_usage[api] = api_usage.get(api, 0) + 1
                
                # Model usage
                all_models = []
                for ca in recent_conversations:
                    all_models.extend(ca.models_used or [])
                
                model_usage = {}
                for model in all_models:
                    model_usage[model] = model_usage.get(model, 0) + 1
                
                # Context usage
                all_context_types = []
                for ca in recent_conversations:
                    all_context_types.extend(ca.context_types_used or [])
                
                context_usage = {}
                for context_type in all_context_types:
                    context_usage[context_type] = context_usage.get(context_type, 0) + 1
                
                dashboard = {
                    "period_hours": period_hours,
                    "period_start": start_time.isoformat(),
                    "period_end": end_time.isoformat(),
                    "generated_at": datetime.now().isoformat(),
                    
                    "usage_metrics": {
                        "total_conversations": total_conversations,
                        "total_messages": total_messages,
                        "unique_users": unique_users,
                        "conversations_per_hour": total_conversations / period_hours,
                        "messages_per_hour": total_messages / period_hours,
                    },
                    
                    "performance_metrics": {
                        "avg_response_time_ms": avg_response_time,
                        "total_errors": sum(ca.error_count for ca in recent_conversations),
                        "total_fallbacks": sum(ca.fallback_usage_count for ca in recent_conversations),
                        "error_rate": sum(ca.error_count for ca in recent_conversations) / max(total_messages, 1),
                    },
                    
                    "feature_usage": {
                        "api_usage_distribution": api_usage,
                        "model_usage_distribution": model_usage,
                        "context_usage_distribution": context_usage,
                        "most_popular_model": max(model_usage.items(), key=lambda x: x[1])[0] if model_usage else None,
                        "most_used_context": max(context_usage.items(), key=lambda x: x[1])[0] if context_usage else None,
                    },
                    
                    "quality_metrics": {
                        "avg_engagement_score": statistics.mean([ca.user_engagement_score for ca in recent_conversations]) if recent_conversations else 0,
                        "avg_quality_score": statistics.mean([ca.conversation_quality_score for ca in recent_conversations]) if recent_conversations else 0,
                        "high_engagement_conversations": len([ca for ca in recent_conversations if ca.user_engagement_score >= 70]),
                        "high_quality_conversations": len([ca for ca in recent_conversations if ca.conversation_quality_score >= 80]),
                    }
                }
                
                return dashboard
                
        except Exception as e:
            logger.error(f"Error getting system analytics dashboard: {e}")
            return {"error": str(e)}


# Global analytics service instance
analytics_service = AnalyticsService()