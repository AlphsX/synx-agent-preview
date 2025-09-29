"""
Analytics API endpoints for conversation insights and metrics.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta

from app.analytics.service import analytics_service
from app.auth.middleware import get_optional_user, get_current_active_user
from app.auth.schemas import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/conversations/{conversation_id}/insights")
async def get_conversation_insights(
    conversation_id: str,
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Get detailed analytics and insights for a specific conversation."""
    try:
        insights = await analytics_service.get_conversation_insights(conversation_id)
        
        if "error" in insights:
            raise HTTPException(status_code=404, detail=insights["error"])
        
        return insights
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}/export")
async def export_conversation_data(
    conversation_id: str,
    format: str = Query("json", description="Export format: json, csv"),
    include_analytics: bool = Query(True, description="Include analytics data"),
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Export conversation data for analysis."""
    try:
        if format not in ["json", "csv"]:
            raise HTTPException(status_code=400, detail="Invalid format. Use 'json' or 'csv'")
        
        export_data = await analytics_service.export_conversation_data(
            conversation_id=conversation_id,
            format=format
        )
        
        if "error" in export_data:
            raise HTTPException(status_code=404, detail=export_data["error"])
        
        # Set appropriate content type and filename
        if format == "json":
            return JSONResponse(
                content=export_data,
                headers={
                    "Content-Disposition": f"attachment; filename=conversation_{conversation_id}_export.json"
                }
            )
        
        # For CSV format, we would need to implement CSV conversion
        # For now, return JSON with a note
        export_data["note"] = "CSV export format not yet implemented. Returning JSON format."
        return JSONResponse(
            content=export_data,
            headers={
                "Content-Disposition": f"attachment; filename=conversation_{conversation_id}_export.json"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting conversation data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/engagement")
async def get_user_engagement_metrics(
    user_id: int,
    period_days: int = Query(30, ge=1, le=365, description="Analysis period in days"),
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Get user engagement metrics and insights."""
    try:
        # Check if user is requesting their own data or is admin
        if current_user and current_user.id != user_id:
            # In a real app, you'd check for admin privileges here
            logger.warning(f"User {current_user.id} requested metrics for user {user_id}")
        
        metrics = await analytics_service.get_user_engagement_metrics(
            user_id=user_id,
            period_days=period_days
        )
        
        if "error" in metrics:
            raise HTTPException(status_code=404, detail=metrics["error"])
        
        return metrics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user engagement metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/me/engagement")
async def get_my_engagement_metrics(
    period_days: int = Query(30, ge=1, le=365, description="Analysis period in days"),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """Get engagement metrics for the current authenticated user."""
    try:
        metrics = await analytics_service.get_user_engagement_metrics(
            user_id=current_user.id,
            period_days=period_days
        )
        
        if "error" in metrics:
            raise HTTPException(status_code=404, detail=metrics["error"])
        
        return metrics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user engagement metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_analytics_dashboard(
    period_hours: int = Query(24, ge=1, le=168, description="Dashboard period in hours"),
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Get system-wide analytics dashboard."""
    try:
        dashboard = await analytics_service.get_system_analytics_dashboard(
            period_hours=period_hours
        )
        
        if "error" in dashboard:
            raise HTTPException(status_code=500, detail=dashboard["error"])
        
        return dashboard
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analytics dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}/quality-score")
async def get_conversation_quality_score(
    conversation_id: str,
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Get quality score and breakdown for a conversation."""
    try:
        insights = await analytics_service.get_conversation_insights(conversation_id)
        
        if "error" in insights:
            raise HTTPException(status_code=404, detail=insights["error"])
        
        quality_metrics = insights.get("quality_metrics", {})
        
        return {
            "conversation_id": conversation_id,
            "quality_score": quality_metrics.get("quality_score", 0),
            "engagement_score": quality_metrics.get("engagement_score", 0),
            "error_rate": quality_metrics.get("error_rate", 0),
            "error_count": quality_metrics.get("error_count", 0),
            "fallback_usage": quality_metrics.get("fallback_usage", 0),
            "score_breakdown": {
                "base_score": 100,
                "error_penalty": quality_metrics.get("error_count", 0) * -10,
                "fallback_penalty": quality_metrics.get("fallback_usage", 0) * -5,
                "context_bonus": min(insights.get("context_usage", {}).get("total_context_requests", 0) * 2, 10),
            },
            "recommendations": self._generate_quality_recommendations(quality_metrics, insights)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation quality score: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/models")
async def get_model_usage_trends(
    period_days: int = Query(7, ge=1, le=30, description="Trend period in days"),
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Get AI model usage trends over time."""
    try:
        # This would typically query time-series data
        # For now, return a simplified version
        dashboard = await analytics_service.get_system_analytics_dashboard(
            period_hours=period_days * 24
        )
        
        if "error" in dashboard:
            raise HTTPException(status_code=500, detail=dashboard["error"])
        
        model_usage = dashboard.get("feature_usage", {}).get("model_usage_distribution", {})
        
        return {
            "period_days": period_days,
            "model_usage_distribution": model_usage,
            "most_popular_model": dashboard.get("feature_usage", {}).get("most_popular_model"),
            "total_model_switches": sum(model_usage.values()),
            "trends": {
                "note": "Detailed time-series trends would be implemented with proper time-series storage",
                "current_distribution": model_usage
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model usage trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/context-usage")
async def get_context_usage_trends(
    period_days: int = Query(7, ge=1, le=30, description="Trend period in days"),
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Get context/search tool usage trends over time."""
    try:
        dashboard = await analytics_service.get_system_analytics_dashboard(
            period_hours=period_days * 24
        )
        
        if "error" in dashboard:
            raise HTTPException(status_code=500, detail=dashboard["error"])
        
        context_usage = dashboard.get("feature_usage", {}).get("context_usage_distribution", {})
        api_usage = dashboard.get("feature_usage", {}).get("api_usage_distribution", {})
        
        return {
            "period_days": period_days,
            "context_type_usage": context_usage,
            "external_api_usage": api_usage,
            "most_used_context": dashboard.get("feature_usage", {}).get("most_used_context"),
            "total_context_requests": sum(context_usage.values()),
            "context_adoption_rate": len(context_usage) / max(len(context_usage) + 1, 1) * 100,  # Simplified metric
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting context usage trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/response-times")
async def get_response_time_analytics(
    period_hours: int = Query(24, ge=1, le=168, description="Analysis period in hours"),
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Get response time performance analytics."""
    try:
        dashboard = await analytics_service.get_system_analytics_dashboard(
            period_hours=period_hours
        )
        
        if "error" in dashboard:
            raise HTTPException(status_code=500, detail=dashboard["error"])
        
        performance = dashboard.get("performance_metrics", {})
        
        return {
            "period_hours": period_hours,
            "avg_response_time_ms": performance.get("avg_response_time_ms", 0),
            "performance_grade": self._calculate_performance_grade(performance.get("avg_response_time_ms", 0)),
            "error_rate": performance.get("error_rate", 0),
            "total_errors": performance.get("total_errors", 0),
            "total_fallbacks": performance.get("total_fallbacks", 0),
            "recommendations": self._generate_performance_recommendations(performance)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting response time analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/{conversation_id}/track-message")
async def track_message_analytics(
    conversation_id: str,
    background_tasks: BackgroundTasks,
    message_id: str = Query(..., description="Message ID to track"),
    processing_time: float = Query(0.0, description="Processing time in milliseconds"),
    tokens_used: int = Query(0, description="Tokens used for this message"),
    had_errors: bool = Query(False, description="Whether errors occurred"),
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Track analytics for a specific message (background task)."""
    try:
        user_id = current_user.id if current_user else None
        
        # Add tracking as background task to not slow down response
        background_tasks.add_task(
            analytics_service.track_message_analytics,
            message_id=message_id,
            conversation_id=conversation_id,
            user_id=user_id,
            processing_time=processing_time,
            tokens_used=tokens_used,
            had_errors=had_errors
        )
        
        return {
            "message": "Analytics tracking queued",
            "message_id": message_id,
            "conversation_id": conversation_id
        }
        
    except Exception as e:
        logger.error(f"Error queuing message analytics tracking: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _generate_quality_recommendations(quality_metrics: Dict[str, Any], insights: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on quality metrics."""
    recommendations = []
    
    quality_score = quality_metrics.get("quality_score", 0)
    error_rate = quality_metrics.get("error_rate", 0)
    
    if quality_score < 50:
        recommendations.append("Consider reviewing conversation flow - quality score is below average")
    
    if error_rate > 0.1:  # More than 10% error rate
        recommendations.append("High error rate detected - check external API configurations")
    
    if quality_metrics.get("fallback_usage", 0) > 3:
        recommendations.append("Frequent fallback usage - verify primary service availability")
    
    context_usage = insights.get("context_usage", {}).get("total_context_requests", 0)
    if context_usage == 0:
        recommendations.append("No context tools used - consider enabling search or data features")
    
    if not recommendations:
        recommendations.append("Conversation quality is good - no specific recommendations")
    
    return recommendations


def _calculate_performance_grade(avg_response_time: float) -> str:
    """Calculate performance grade based on response time."""
    if avg_response_time < 1000:  # < 1 second
        return "A"
    elif avg_response_time < 3000:  # < 3 seconds
        return "B"
    elif avg_response_time < 5000:  # < 5 seconds
        return "C"
    elif avg_response_time < 10000:  # < 10 seconds
        return "D"
    else:
        return "F"


def _generate_performance_recommendations(performance: Dict[str, Any]) -> List[str]:
    """Generate performance recommendations."""
    recommendations = []
    
    avg_time = performance.get("avg_response_time_ms", 0)
    error_rate = performance.get("error_rate", 0)
    
    if avg_time > 5000:  # > 5 seconds
        recommendations.append("Response times are slow - consider optimizing AI model selection or caching")
    
    if error_rate > 0.05:  # > 5% error rate
        recommendations.append("Error rate is elevated - check external service health")
    
    if performance.get("total_fallbacks", 0) > 10:
        recommendations.append("High fallback usage - verify primary service configurations")
    
    if not recommendations:
        recommendations.append("Performance metrics are within acceptable ranges")
    
    return recommendations