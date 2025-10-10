"""
API Router for AI Model Optimization Features

Provides endpoints for:
1. Model recommendations based on query analysis
2. Performance analytics and monitoring
3. Cost optimization insights
4. Quality assessment and feedback
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

from .enhanced_service import EnhancedAIService
from ..auth.middleware import get_current_user
from ..auth.schemas import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai/optimization", tags=["AI Optimization"])

# Global enhanced AI service instance
enhanced_ai_service = EnhancedAIService()


# Request/Response Models
class QueryAnalysisRequest(BaseModel):
    message: str = Field(..., description="The user query to analyze")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context data")


class ModelRecommendationRequest(BaseModel):
    message: str = Field(..., description="The user query")
    user_preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences for model selection")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context data")


class OptimizationSettingsRequest(BaseModel):
    auto_model_selection: Optional[bool] = Field(None, description="Enable automatic model selection")
    quality_feedback_enabled: Optional[bool] = Field(None, description="Enable quality feedback collection")
    cost_tracking_enabled: Optional[bool] = Field(None, description="Enable cost tracking")
    fallback_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Availability threshold for fallback")
    quality_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum quality score threshold")


class EnhancedChatRequest(BaseModel):
    message: str = Field(..., description="The user message")
    model_id: Optional[str] = Field(None, description="Specific model to use (optional)")
    conversation_history: Optional[List[Dict[str, str]]] = Field(None, description="Previous conversation messages")
    system_message: Optional[str] = Field(None, description="System prompt")
    user_preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    stream: bool = Field(True, description="Whether to stream the response")


# Endpoints
@router.get("/models/recommendation")
async def get_model_recommendation(
    message: str = Query(..., description="The user query to analyze"),
    priority: str = Query("balanced", description="Priority: speed, quality, cost, or balanced"),
    user: Optional[UserResponse] = Depends(get_current_user)
):
    """Get AI model recommendation based on query analysis"""
    try:
        user_preferences = {"priority": priority}
        if user:
            user_preferences["user_id"] = user.id
            user_preferences["user_tier"] = getattr(user, 'tier', 'free')
        
        recommendation = await enhanced_ai_service.get_model_recommendation(
            message=message,
            user_preferences=user_preferences
        )
        
        return {
            "success": True,
            "recommendation": recommendation,
            "user_context": {
                "authenticated": user is not None,
                "user_id": user.id if user else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting model recommendation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/recommendation")
async def get_detailed_model_recommendation(
    request: ModelRecommendationRequest,
    user: Optional[UserResponse] = Depends(get_current_user)
):
    """Get detailed AI model recommendation with context"""
    try:
        user_preferences = request.user_preferences or {}
        if user:
            user_preferences["user_id"] = user.id
            user_preferences["user_tier"] = getattr(user, 'tier', 'free')
        
        recommendation = await enhanced_ai_service.get_model_recommendation(
            message=request.message,
            user_preferences=user_preferences,
            context=request.context
        )
        
        return {
            "success": True,
            "recommendation": recommendation,
            "request_context": {
                "message_length": len(request.message),
                "has_context": request.context is not None,
                "user_authenticated": user is not None
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting detailed model recommendation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics")
async def get_optimization_analytics(
    user: Optional[UserResponse] = Depends(get_current_user)
):
    """Get comprehensive optimization analytics and recommendations"""
    try:
        analytics = await enhanced_ai_service.get_optimization_analytics()
        
        return {
            "success": True,
            "analytics": analytics,
            "user_context": {
                "authenticated": user is not None,
                "can_modify_settings": user is not None  # Only authenticated users can modify settings
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting optimization analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/summary")
async def get_analytics_summary(
    user: Optional[UserResponse] = Depends(get_current_user)
):
    """Get a summary of optimization analytics"""
    try:
        full_analytics = await enhanced_ai_service.get_optimization_analytics()
        
        if "error" in full_analytics:
            return {"success": False, "error": full_analytics["error"]}
        
        # Extract summary information
        analytics = full_analytics.get("analytics", {})
        recommendations = full_analytics.get("recommendations", {})
        
        summary = {
            "total_requests": analytics.get("summary", {}).get("total_requests", 0),
            "total_models_used": analytics.get("summary", {}).get("total_models_used", 0),
            "total_cost": analytics.get("summary", {}).get("total_cost", 0),
            "average_quality_score": analytics.get("summary", {}).get("average_quality_score", 0),
            "top_recommendations": {
                "cost_optimization": recommendations.get("cost_optimization", [])[:3],
                "performance_optimization": recommendations.get("performance_optimization", [])[:3],
                "quality_optimization": recommendations.get("quality_optimization", [])[:3]
            }
        }
        
        return {
            "success": True,
            "summary": summary,
            "has_data": summary["total_requests"] > 0
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/settings")
async def get_optimization_settings(
    user: Optional[UserResponse] = Depends(get_current_user)
):
    """Get current optimization settings"""
    try:
        analytics = await enhanced_ai_service.get_optimization_analytics()
        settings = analytics.get("settings", {})
        
        return {
            "success": True,
            "settings": settings,
            "user_can_modify": user is not None
        }
        
    except Exception as e:
        logger.error(f"Error getting optimization settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings")
async def update_optimization_settings(
    request: OptimizationSettingsRequest,
    user: Optional[UserResponse] = Depends(get_current_user)
):
    """Update optimization settings (requires authentication)"""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required to modify settings")
    
    try:
        # Convert request to dict, excluding None values
        settings_dict = {k: v for k, v in request.dict().items() if v is not None}
        
        if not settings_dict:
            raise HTTPException(status_code=400, detail="No settings provided to update")
        
        result = await enhanced_ai_service.update_optimization_settings(settings_dict)
        
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to update settings"))
        
        return {
            "success": True,
            "updated_settings": result["updated"],
            "message": "Settings updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating optimization settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/performance")
async def get_model_performance(
    model_id: Optional[str] = Query(None, description="Specific model ID to get performance for"),
    user: Optional[UserResponse] = Depends(get_current_user)
):
    """Get performance metrics for models"""
    try:
        analytics = await enhanced_ai_service.get_optimization_analytics()
        
        if "error" in analytics:
            return {"success": False, "error": analytics["error"]}
        
        model_performance = analytics.get("analytics", {}).get("model_performance", {})
        
        if model_id:
            if model_id not in model_performance:
                raise HTTPException(status_code=404, detail=f"No performance data found for model {model_id}")
            
            return {
                "success": True,
                "model_id": model_id,
                "performance": model_performance[model_id]
            }
        else:
            return {
                "success": True,
                "all_models_performance": model_performance,
                "total_models": len(model_performance)
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cost-analysis")
async def get_cost_analysis(
    user: Optional[UserResponse] = Depends(get_current_user)
):
    """Get detailed cost analysis"""
    try:
        analytics = await enhanced_ai_service.get_optimization_analytics()
        
        if "error" in analytics:
            return {"success": False, "error": analytics["error"]}
        
        cost_analysis = analytics.get("analytics", {}).get("cost_analysis", {})
        summary = analytics.get("analytics", {}).get("summary", {})
        
        return {
            "success": True,
            "cost_analysis": cost_analysis,
            "summary": {
                "total_cost": summary.get("total_cost", 0),
                "total_requests": summary.get("total_requests", 0),
                "cost_per_request": cost_analysis.get("cost_per_request", 0),
                "projected_monthly_cost": cost_analysis.get("projected_monthly_cost", 0)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting cost analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/data/export")
async def export_optimization_data(
    user: Optional[UserResponse] = Depends(get_current_user)
):
    """Export optimization data for backup (requires authentication)"""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required to export data")
    
    try:
        data = enhanced_ai_service.export_optimization_data()
        
        return {
            "success": True,
            "data": data,
            "export_info": {
                "user_id": user.id,
                "models_count": len(data.get("model_metrics", {})),
                "export_timestamp": data.get("export_timestamp")
            }
        }
        
    except Exception as e:
        logger.error(f"Error exporting optimization data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/data/import")
async def import_optimization_data(
    data: Dict[str, Any],
    user: Optional[UserResponse] = Depends(get_current_user)
):
    """Import optimization data from backup (requires authentication)"""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required to import data")
    
    try:
        enhanced_ai_service.import_optimization_data(data)
        
        imported_models = len(data.get("model_metrics", {}))
        
        return {
            "success": True,
            "message": f"Successfully imported data for {imported_models} models",
            "import_info": {
                "user_id": user.id,
                "models_imported": imported_models,
                "import_timestamp": data.get("export_timestamp")
            }
        }
        
    except Exception as e:
        logger.error(f"Error importing optimization data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/data/clear")
async def clear_optimization_data(
    user: Optional[UserResponse] = Depends(get_current_user)
):
    """Clear all optimization data (requires authentication)"""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required to clear data")
    
    try:
        enhanced_ai_service.clear_optimization_data()
        
        return {
            "success": True,
            "message": "All optimization data cleared successfully",
            "cleared_by": user.id
        }
        
    except Exception as e:
        logger.error(f"Error clearing optimization data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def optimization_health_check():
    """Health check for optimization service"""
    try:
        # Basic health check
        models = enhanced_ai_service.get_available_models()
        provider_status = enhanced_ai_service.get_provider_status()
        
        return {
            "success": True,
            "status": "healthy",
            "available_models": len(models),
            "providers": provider_status,
            "optimization_features": {
                "auto_model_selection": enhanced_ai_service.auto_model_selection,
                "quality_feedback": enhanced_ai_service.quality_feedback_enabled,
                "cost_tracking": enhanced_ai_service.cost_tracking_enabled
            }
        }
        
    except Exception as e:
        logger.error(f"Optimization health check failed: {e}")
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }