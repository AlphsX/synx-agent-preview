from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import json
import asyncio
from .service import AIService
from .models import AIModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Global AI service instance
ai_service = AIService()


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str = Field(..., description="The user message")
    model_id: str = Field(..., description="The AI model to use")
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        default=None, 
        description="Previous messages in the conversation"
    )
    system_message: Optional[str] = Field(
        default=None, 
        description="System prompt to set context"
    )
    stream: bool = Field(default=True, description="Whether to stream the response")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="Sampling temperature")
    max_tokens: int = Field(default=2000, ge=1, le=8192, description="Maximum tokens to generate")


class ChatResponse(BaseModel):
    """Response model for non-streaming chat"""
    content: str
    model_id: str
    provider: str
    finish_reason: Optional[str] = None


class ModelAvailabilityResponse(BaseModel):
    """Response model for model availability check"""
    model_id: str
    available: bool
    provider: Optional[str] = None


class ProviderStatusResponse(BaseModel):
    """Response model for provider status"""
    providers: Dict[str, Dict[str, Any]]


@router.get("/models", response_model=List[AIModel])
async def get_available_models():
    """Get all available AI models"""
    try:
        models = ai_service.get_available_models()
        return models
    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        raise HTTPException(status_code=500, detail="Failed to get available models")


@router.get("/models/{provider}", response_model=List[AIModel])
async def get_models_by_provider(provider: str):
    """Get models for a specific provider"""
    try:
        models = ai_service.get_models_by_provider(provider)
        if not models:
            raise HTTPException(status_code=404, detail=f"No models found for provider: {provider}")
        return models
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting models for provider {provider}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get models for provider")


@router.get("/models/{model_id}/info", response_model=AIModel)
async def get_model_info(model_id: str):
    """Get information about a specific model"""
    try:
        model_info = ai_service.get_model_info(model_id)
        if not model_info:
            raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")
        return model_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model info for {model_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get model information")


@router.get("/models/{model_id}/availability", response_model=ModelAvailabilityResponse)
async def check_model_availability(model_id: str):
    """Check if a specific model is available"""
    try:
        available = await ai_service.check_model_availability(model_id)
        provider = ai_service.router.get_provider_for_model(model_id)
        
        return ModelAvailabilityResponse(
            model_id=model_id,
            available=available,
            provider=provider
        )
    except Exception as e:
        logger.error(f"Error checking availability for {model_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to check model availability")


@router.get("/providers/status", response_model=ProviderStatusResponse)
async def get_provider_status():
    """Get status of all AI providers"""
    try:
        status = ai_service.get_provider_status()
        return ProviderStatusResponse(providers=status)
    except Exception as e:
        logger.error(f"Error getting provider status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get provider status")


@router.get("/recommend/{task_type}")
async def get_recommended_model(task_type: str):
    """Get a recommended model for a specific task type"""
    try:
        model_id = ai_service.get_recommended_model(task_type)
        if not model_id:
            raise HTTPException(status_code=404, detail="No models available for recommendation")
        
        model_info = ai_service.get_model_info(model_id)
        return {
            "recommended_model": model_id,
            "task_type": task_type,
            "model_info": model_info
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendation for {task_type}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get model recommendation")


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Generate AI chat response.
    
    Supports both streaming and non-streaming responses based on the stream parameter.
    """
    try:
        if request.stream:
            # Streaming response
            async def generate_stream():
                try:
                    async for chunk in ai_service.chat_with_context(
                        message=request.message,
                        model_id=request.model_id,
                        conversation_history=request.conversation_history,
                        system_message=request.system_message,
                        stream=True,
                        temperature=request.temperature,
                        max_tokens=request.max_tokens
                    ):
                        # Format as Server-Sent Events
                        yield f"data: {json.dumps({'content': chunk})}\n\n"
                    
                    # Send completion signal
                    yield f"data: {json.dumps({'done': True})}\n\n"
                    
                except Exception as e:
                    logger.error(f"Error in streaming chat: {e}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/plain; charset=utf-8"
                }
            )
        else:
            # Non-streaming response
            content_parts = []
            async for chunk in ai_service.chat_with_context(
                message=request.message,
                model_id=request.model_id,
                conversation_history=request.conversation_history,
                system_message=request.system_message,
                stream=False,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            ):
                content_parts.append(chunk)
            
            full_content = "".join(content_parts)
            provider = ai_service.router.get_provider_for_model(request.model_id)
            
            return ChatResponse(
                content=full_content,
                model_id=request.model_id,
                provider=provider or "unknown",
                finish_reason="stop"
            )
            
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Chat generation failed: {str(e)}")


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Generate streaming AI chat response.
    
    This endpoint always returns a streaming response using Server-Sent Events.
    """
    async def generate_stream():
        try:
            async for chunk in ai_service.chat_with_context(
                message=request.message,
                model_id=request.model_id,
                conversation_history=request.conversation_history,
                system_message=request.system_message,
                stream=True,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            ):
                # Format as Server-Sent Events
                data = {
                    "content": chunk,
                    "model_id": request.model_id,
                    "done": False
                }
                yield f"data: {json.dumps(data)}\n\n"
            
            # Send completion signal
            completion_data = {
                "content": "",
                "model_id": request.model_id,
                "done": True
            }
            yield f"data: {json.dumps(completion_data)}\n\n"
            
        except Exception as e:
            logger.error(f"Error in streaming chat: {e}")
            error_data = {
                "error": str(e),
                "model_id": request.model_id,
                "done": True
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*"
        }
    )


@router.post("/demo/chat")
async def demo_chat(request: ChatRequest):
    """
    Generate demo AI chat response when no real providers are available.
    
    This endpoint provides mock responses for demonstration purposes.
    """
    try:
        if request.stream:
            async def generate_demo_stream():
                try:
                    async for chunk in ai_service.generate_mock_response(
                        message=request.message,
                        model_id=request.model_id,
                        stream=True
                    ):
                        yield f"data: {json.dumps({'content': chunk})}\n\n"
                    
                    yield f"data: {json.dumps({'done': True})}\n\n"
                    
                except Exception as e:
                    logger.error(f"Error in demo streaming: {e}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            return StreamingResponse(
                generate_demo_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive"
                }
            )
        else:
            # Non-streaming demo response
            content_parts = []
            async for chunk in ai_service.generate_mock_response(
                message=request.message,
                model_id=request.model_id,
                stream=False
            ):
                content_parts.append(chunk)
            
            full_content = "".join(content_parts)
            
            return ChatResponse(
                content=full_content,
                model_id=request.model_id,
                provider="demo",
                finish_reason="stop"
            )
            
    except Exception as e:
        logger.error(f"Error in demo chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Demo chat failed: {str(e)}")


@router.post("/cache/clear")
async def clear_cache():
    """Clear AI service cache"""
    try:
        ai_service.clear_cache()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")


@router.get("/health")
async def health_check():
    """Health check endpoint for AI service"""
    try:
        status = ai_service.get_provider_status()
        available_providers = sum(1 for provider_status in status.values() if provider_status["available"])
        total_models = sum(provider_status["models"] for provider_status in status.values())
        
        return {
            "status": "healthy",
            "providers": {
                "available": available_providers,
                "total": len(status)
            },
            "models": {
                "total": total_models
            },
            "service": "ai-model-router"
        }
    except Exception as e:
        logger.error(f"Error in AI health check: {e}")
        raise HTTPException(status_code=500, detail="AI service health check failed")