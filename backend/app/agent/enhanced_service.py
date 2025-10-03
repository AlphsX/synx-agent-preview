"""
Enhanced AI Service with Advanced Model Management and Optimization

This service extends the base AI service with:
1. Dynamic model selection based on query complexity
2. Performance monitoring and automatic fallback
3. Cost optimization and usage tracking
4. Quality assessment and feedback loops
"""

import asyncio
import time
from typing import List, AsyncGenerator, Dict, Any, Optional
import logging

from .service import AIService
from .optimization_service import AIOptimizationService, QueryComplexity, ModelTier
from .models import AIModel, ChatMessage

logger = logging.getLogger(__name__)


class EnhancedAIService:
    """Enhanced AI service with optimization and intelligent model selection"""
    
    def __init__(self):
        self.base_service = AIService()
        self.optimization_service = AIOptimizationService(self.base_service)
        
        # Configuration
        self.auto_model_selection = True
        self.quality_feedback_enabled = True
        self.cost_tracking_enabled = True
        
        logger.info("Enhanced AI Service initialized with optimization capabilities")
    
    def get_available_models(self) -> List[AIModel]:
        """Get all available AI models"""
        return self.base_service.get_available_models()
    
    def get_models_by_provider(self, provider: str) -> List[AIModel]:
        """Get models for a specific provider"""
        return self.base_service.get_models_by_provider(provider)
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all AI providers"""
        return self.base_service.get_provider_status()
    
    async def chat_with_optimization(
        self,
        message: str,
        model_id: Optional[str] = None,
        conversation_history: List[Dict[str, str]] = None,
        system_message: str = None,
        user_preferences: Dict[str, Any] = None,
        context: Dict[str, Any] = None,
        stream: bool = True,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate chat response with intelligent model selection and optimization.
        
        Args:
            message: The user message
            model_id: Specific model to use (optional, will auto-select if None)
            conversation_history: Previous messages in the conversation
            system_message: System prompt to set context
            user_preferences: User preferences for model selection
            context: Additional context data
            stream: Whether to stream the response
            **kwargs: Additional parameters
            
        Yields:
            Dict containing response chunks and metadata
        """
        start_time = time.time()
        
        try:
            # Analyze the query
            query_analysis = await self.optimization_service.analyze_query(message, context)
            
            # Get available models
            available_models = self.get_available_models()
            available_models = [m for m in available_models if m.available]
            
            if not available_models:
                yield {
                    "type": "error",
                    "content": "No AI models are currently available",
                    "error": "no_models_available"
                }
                return
            
            # Select model (use provided model_id or auto-select)
            selected_model_id = model_id
            recommendation = None
            
            if not selected_model_id and self.auto_model_selection:
                try:
                    recommendation = await self.optimization_service.recommend_model(
                        query_analysis, available_models, user_preferences
                    )
                    selected_model_id = recommendation.model_id
                    
                    # Yield model selection info
                    yield {
                        "type": "model_selection",
                        "model_id": selected_model_id,
                        "reasoning": recommendation.reasoning,
                        "confidence": recommendation.confidence,
                        "estimated_cost": recommendation.estimated_cost,
                        "estimated_response_time": recommendation.estimated_response_time,
                        "tier": recommendation.tier.value,
                        "query_analysis": {
                            "complexity": query_analysis.complexity.value,
                            "domain": query_analysis.domain,
                            "requires_real_time_data": query_analysis.requires_real_time_data,
                            "estimated_tokens": query_analysis.estimated_tokens
                        }
                    }
                    
                except Exception as e:
                    logger.warning(f"Model recommendation failed: {e}, using fallback")
                    selected_model_id = available_models[0].id
            
            elif not selected_model_id:
                # Fallback to first available model
                selected_model_id = available_models[0].id
            
            # Prepare messages
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            
            if conversation_history:
                messages.extend(conversation_history[-10:])  # Last 10 messages
            
            messages.append({"role": "user", "content": message})
            
            # Generate response with performance tracking
            response_start_time = time.time()
            response_content = ""
            token_count = 0
            success = True
            error_message = None
            
            try:
                async for chunk in self.base_service.chat(
                    messages=messages,
                    model_id=selected_model_id,
                    stream=stream,
                    **kwargs
                ):
                    response_content += chunk
                    token_count += len(chunk.split())  # Rough token estimation
                    
                    # Yield response chunk
                    yield {
                        "type": "response",
                        "content": chunk,
                        "model_id": selected_model_id,
                        "partial_response": response_content
                    }
                    
            except Exception as e:
                success = False
                error_message = str(e)
                logger.error(f"Error generating response with {selected_model_id}: {e}")
                
                # Try fallback model if available
                fallback_attempted = False
                if self.auto_model_selection and len(available_models) > 1:
                    fallback_models = [m for m in available_models if m.id != selected_model_id]
                    if fallback_models:
                        fallback_model_id = fallback_models[0].id
                        logger.info(f"Attempting fallback to {fallback_model_id}")
                        
                        try:
                            fallback_attempted = True
                            async for chunk in self.base_service.chat(
                                messages=messages,
                                model_id=fallback_model_id,
                                stream=stream,
                                **kwargs
                            ):
                                response_content += chunk
                                token_count += len(chunk.split())
                                
                                yield {
                                    "type": "response",
                                    "content": chunk,
                                    "model_id": fallback_model_id,
                                    "partial_response": response_content,
                                    "fallback_used": True,
                                    "original_model": selected_model_id
                                }
                            
                            success = True
                            selected_model_id = fallback_model_id  # Update for tracking
                            
                        except Exception as fallback_error:
                            logger.error(f"Fallback model also failed: {fallback_error}")
                            error_message = f"Primary model failed: {e}. Fallback failed: {fallback_error}"
                
                if not success:
                    yield {
                        "type": "error",
                        "content": f"AI generation failed: {error_message}",
                        "model_id": selected_model_id,
                        "fallback_attempted": fallback_attempted
                    }
                    return
            
            response_time = time.time() - response_start_time
            total_time = time.time() - start_time
            
            # Calculate cost
            cost = 0.0
            if self.cost_tracking_enabled and recommendation:
                cost = recommendation.estimated_cost
            
            # Assess response quality
            quality_score = None
            if self.quality_feedback_enabled and success and response_content:
                try:
                    quality_score = await self.optimization_service.assess_response_quality(
                        message, response_content, context
                    )
                except Exception as e:
                    logger.warning(f"Quality assessment failed: {e}")
            
            # Track performance
            if success:
                await self.optimization_service.track_model_performance(
                    model_id=selected_model_id,
                    response_time=response_time,
                    success=success,
                    tokens_used=token_count,
                    cost=cost,
                    quality_score=quality_score
                )
            
            # Yield completion metadata
            yield {
                "type": "completion",
                "model_id": selected_model_id,
                "response_time": response_time,
                "total_time": total_time,
                "token_count": token_count,
                "estimated_cost": cost,
                "quality_score": quality_score,
                "success": success,
                "query_complexity": query_analysis.complexity.value,
                "query_domain": query_analysis.domain
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced chat: {e}")
            yield {
                "type": "error",
                "content": f"System error: {str(e)}",
                "error": "system_error"
            }
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model_id: str,
        stream: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        track_performance: bool = True,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Generate chat response with performance tracking (compatible with base service).
        
        This method maintains compatibility with the base AIService interface
        while adding performance tracking capabilities.
        """
        start_time = time.time()
        response_content = ""
        token_count = 0
        success = True
        
        try:
            async for chunk in self.base_service.chat(
                messages=messages,
                model_id=model_id,
                stream=stream,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            ):
                response_content += chunk
                token_count += len(chunk.split())
                yield chunk
                
        except Exception as e:
            success = False
            logger.error(f"Error in chat: {e}")
            yield f"Error: {str(e)}"
        
        # Track performance if enabled
        if track_performance:
            response_time = time.time() - start_time
            
            # Estimate cost (rough calculation)
            cost_info = self.optimization_service.cost_per_token.get(model_id, {"input": 0.001, "output": 0.001})
            estimated_cost = (cost_info["input"] + cost_info["output"]) * token_count / 2000  # Rough estimate
            
            await self.optimization_service.track_model_performance(
                model_id=model_id,
                response_time=response_time,
                success=success,
                tokens_used=token_count,
                cost=estimated_cost
            )
    
    async def get_model_recommendation(
        self,
        message: str,
        user_preferences: Dict[str, Any] = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get model recommendation for a specific query"""
        
        try:
            # Analyze query
            query_analysis = await self.optimization_service.analyze_query(message, context)
            
            # Get available models
            available_models = [m for m in self.get_available_models() if m.available]
            
            if not available_models:
                return {"error": "No models available"}
            
            # Get recommendation
            recommendation = await self.optimization_service.recommend_model(
                query_analysis, available_models, user_preferences
            )
            
            return {
                "recommended_model": recommendation.model_id,
                "confidence": recommendation.confidence,
                "reasoning": recommendation.reasoning,
                "estimated_cost": recommendation.estimated_cost,
                "estimated_response_time": recommendation.estimated_response_time,
                "tier": recommendation.tier.value,
                "query_analysis": {
                    "complexity": query_analysis.complexity.value,
                    "domain": query_analysis.domain,
                    "requires_real_time_data": query_analysis.requires_real_time_data,
                    "estimated_tokens": query_analysis.estimated_tokens,
                    "confidence": query_analysis.confidence,
                    "reasoning": query_analysis.reasoning
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting model recommendation: {e}")
            return {"error": str(e)}
    
    async def get_optimization_analytics(self) -> Dict[str, Any]:
        """Get comprehensive optimization analytics"""
        try:
            analytics = await self.optimization_service.get_model_analytics()
            recommendations = await self.optimization_service.get_optimization_recommendations()
            
            return {
                "analytics": analytics,
                "recommendations": recommendations,
                "settings": {
                    "auto_model_selection": self.auto_model_selection,
                    "quality_feedback_enabled": self.quality_feedback_enabled,
                    "cost_tracking_enabled": self.cost_tracking_enabled,
                    "fallback_threshold": self.optimization_service.fallback_threshold,
                    "quality_threshold": self.optimization_service.quality_threshold
                }
            }
        except Exception as e:
            logger.error(f"Error getting optimization analytics: {e}")
            return {"error": str(e)}
    
    async def update_optimization_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update optimization settings"""
        try:
            updated = {}
            
            if "auto_model_selection" in settings:
                self.auto_model_selection = bool(settings["auto_model_selection"])
                updated["auto_model_selection"] = self.auto_model_selection
            
            if "quality_feedback_enabled" in settings:
                self.quality_feedback_enabled = bool(settings["quality_feedback_enabled"])
                updated["quality_feedback_enabled"] = self.quality_feedback_enabled
            
            if "cost_tracking_enabled" in settings:
                self.cost_tracking_enabled = bool(settings["cost_tracking_enabled"])
                updated["cost_tracking_enabled"] = self.cost_tracking_enabled
            
            if "fallback_threshold" in settings:
                threshold = float(settings["fallback_threshold"])
                if 0.0 <= threshold <= 1.0:
                    self.optimization_service.fallback_threshold = threshold
                    updated["fallback_threshold"] = threshold
            
            if "quality_threshold" in settings:
                threshold = float(settings["quality_threshold"])
                if 0.0 <= threshold <= 1.0:
                    self.optimization_service.quality_threshold = threshold
                    updated["quality_threshold"] = threshold
            
            logger.info(f"Updated optimization settings: {updated}")
            return {"updated": updated, "success": True}
            
        except Exception as e:
            logger.error(f"Error updating optimization settings: {e}")
            return {"error": str(e), "success": False}
    
    def clear_optimization_data(self):
        """Clear all optimization data (useful for testing)"""
        self.optimization_service.clear_metrics()
        logger.info("Optimization data cleared")
    
    def export_optimization_data(self) -> Dict[str, Any]:
        """Export optimization data for backup"""
        return self.optimization_service.export_metrics()
    
    def import_optimization_data(self, data: Dict[str, Any]):
        """Import optimization data from backup"""
        self.optimization_service.import_metrics(data)
        logger.info("Optimization data imported")
    
    async def check_model_availability(self, model_id: str, force_check: bool = False) -> bool:
        """Check if a specific model is available"""
        return await self.base_service.check_model_availability(model_id, force_check)
    
    def get_model_info(self, model_id: str) -> Optional[AIModel]:
        """Get information about a specific model"""
        return self.base_service.get_model_info(model_id)
    
    def get_recommended_model(self, task_type: str = "general") -> Optional[str]:
        """Get a recommended model for a specific task type (legacy method)"""
        return self.base_service.get_recommended_model(task_type)