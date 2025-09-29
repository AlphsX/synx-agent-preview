"""
Safe analytics service that handles both UUID and string IDs gracefully.
This service provides analytics tracking without breaking the main chat flow.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
import json
import statistics

logger = logging.getLogger(__name__)


class SafeAnalyticsService:
    """Safe analytics service that doesn't break on ID format issues."""
    
    def __init__(self):
        self.logger = logger
        self.enabled = True
    
    def _safe_uuid_convert(self, id_str: str) -> Optional[UUID]:
        """Safely convert string to UUID, return None if not possible."""
        try:
            if isinstance(id_str, str) and len(id_str) == 36:
                return UUID(id_str)
        except (ValueError, TypeError, AttributeError):
            pass
        return None
    
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
        """Track analytics for a single message safely."""
        if not self.enabled:
            return False
        
        try:
            # Check if we can convert IDs to UUID format
            msg_uuid = self._safe_uuid_convert(message_id)
            conv_uuid = self._safe_uuid_convert(conversation_id)
            
            if not msg_uuid or not conv_uuid:
                # Log for debugging but don't fail
                logger.debug(f"Analytics skipped - ID format not compatible: msg={message_id}, conv={conversation_id}")
                return False
            
            # Try to import and use the full analytics service
            try:
                from app.analytics.service import analytics_service
                return await analytics_service.track_message_analytics(
                    message_id=message_id,
                    conversation_id=conversation_id,
                    user_id=user_id,
                    processing_time=processing_time,
                    context_data=context_data,
                    tokens_used=tokens_used,
                    had_errors=had_errors,
                    error_details=error_details
                )
            except Exception as e:
                logger.debug(f"Full analytics service failed: {e}")
                # Fall back to simple logging
                self._log_analytics_data(
                    message_id, conversation_id, processing_time, 
                    context_data, had_errors
                )
                return True
                
        except Exception as e:
            logger.debug(f"Analytics tracking failed safely: {e}")
            return False
    
    def _log_analytics_data(
        self, 
        message_id: str, 
        conversation_id: str, 
        processing_time: float,
        context_data: Dict[str, Any],
        had_errors: bool
    ):
        """Log analytics data to file as fallback."""
        try:
            analytics_data = {
                "timestamp": datetime.now().isoformat(),
                "message_id": message_id,
                "conversation_id": conversation_id,
                "processing_time": processing_time,
                "context_types": list(context_data.keys()) if context_data else [],
                "had_errors": had_errors
            }
            
            # Log to application logs
            logger.info(f"Analytics: {json.dumps(analytics_data)}")
            
        except Exception as e:
            logger.debug(f"Analytics logging failed: {e}")
    
    async def get_conversation_insights(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation insights safely."""
        try:
            from app.analytics.service import analytics_service
            return await analytics_service.get_conversation_insights(conversation_id)
        except Exception as e:
            logger.debug(f"Analytics insights failed: {e}")
            return {
                "conversation_id": conversation_id,
                "message": "Analytics not available",
                "error": str(e)
            }
    
    def disable_analytics(self):
        """Disable analytics tracking."""
        self.enabled = False
        logger.info("Analytics tracking disabled")
    
    def enable_analytics(self):
        """Enable analytics tracking."""
        self.enabled = True
        logger.info("Analytics tracking enabled")


# Global safe analytics service instance
safe_analytics_service = SafeAnalyticsService()