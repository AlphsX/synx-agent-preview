from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, AsyncGenerator, Optional, Dict, Any
import json
import asyncio
import logging
from datetime import datetime
import uuid

from app.chat.schemas import MessageCreate, ConversationCreate, ChatResponse, MessageResponse
from app.enhanced_chat_service import EnhancedChatService
from app.auth.middleware import get_optional_user, get_current_active_user, create_user_context
from app.auth.schemas import UserResponse
from app.external_apis.search_service import SearchProvider
from app.streaming import streaming_manager

logger = logging.getLogger(__name__)

router = APIRouter()
enhanced_chat_service = EnhancedChatService()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, connection_id: str, metadata: Dict[str, Any] = None):
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        self.connection_metadata[connection_id] = {
            "connected_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        logger.info(f"WebSocket connection established: {connection_id}")

    def disconnect(self, connection_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        if connection_id in self.connection_metadata:
            del self.connection_metadata[connection_id]
        logger.info(f"WebSocket connection closed: {connection_id}")

    async def send_personal_message(self, message: str, connection_id: str):
        websocket = self.active_connections.get(connection_id)
        if websocket:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                self.disconnect(connection_id)

    async def send_json_message(self, data: Dict[str, Any], connection_id: str):
        await self.send_personal_message(json.dumps(data), connection_id)

    def get_active_connections(self) -> Dict[str, Dict[str, Any]]:
        return {
            conn_id: {
                "metadata": self.connection_metadata.get(conn_id, {}),
                "active": True
            }
            for conn_id in self.active_connections.keys()
        }

manager = ConnectionManager()

@router.post("/conversations", response_model=dict)
async def create_conversation(
    conversation: ConversationCreate,
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Create a new enhanced conversation with context tracking"""
    try:
        user_id = current_user.id if current_user else None
        
        new_conversation = await enhanced_chat_service.create_conversation(
            title=conversation.title,
            user_id=user_id
        )
        
        logger.info(f"Created enhanced conversation: {new_conversation['id']} for user: {current_user.username if current_user else 'anonymous'}")
        return new_conversation
        
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations", response_model=List[dict])
async def get_conversations(
    limit: int = Query(50, ge=1, le=100, description="Number of conversations to retrieve"),
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Get user's enhanced conversations with metadata"""
    try:
        user_id = current_user.id if current_user else None
        
        conversations = await enhanced_chat_service.get_user_conversations(
            user_id=user_id,
            limit=limit
        )
        
        return conversations
        
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    include_messages: bool = Query(False, description="Include conversation messages"),
    message_limit: int = Query(50, ge=1, le=200, description="Number of messages to include"),
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Get conversation details and summary"""
    try:
        if include_messages:
            # Get conversation with messages
            result = await enhanced_chat_service.get_conversation_with_messages(
                conversation_id=conversation_id,
                limit=message_limit
            )
            
            if not result:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            return result
        else:
            # Get conversation details only
            conversation = await enhanced_chat_service.get_conversation(conversation_id)
            
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            # Get summary
            summary = await enhanced_chat_service.get_conversation_summary(conversation_id)
            
            return {
                **conversation,
                "summary": summary
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    limit: int = Query(100, ge=1, le=500, description="Number of messages to retrieve"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
    include_context: bool = Query(False, description="Include context data in messages"),
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Get messages for a conversation"""
    try:
        # Verify conversation exists
        conversation = await enhanced_chat_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get messages from database
        from app.conversation_service import conversation_service
        messages = await conversation_service.get_conversation_messages(
            conversation_id=conversation_id,
            limit=limit,
            offset=offset,
            include_context=include_context
        )
        
        return {
            "conversation_id": conversation_id,
            "messages": messages,
            "count": len(messages),
            "limit": limit,
            "offset": offset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting messages for conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/conversations/{conversation_id}")
async def clear_conversation(
    conversation_id: str,
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Clear conversation history"""
    try:
        success = await enhanced_chat_service.clear_conversation_history(conversation_id)
        return {"success": success, "message": f"Conversation {conversation_id} cleared"}
    except Exception as e:
        logger.error(f"Error clearing conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def create_message(
    conversation_id: str,
    message: MessageCreate,
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Add a message to enhanced conversation"""
    try:
        # Verify conversation exists
        conversation = await enhanced_chat_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Add message to database
        from app.conversation_service import conversation_service
        new_message = await conversation_service.add_message(
            conversation_id=conversation_id,
            content=message.content,
            role=message.role,
            model_id=message.model_id,
            context_data=message.context_data if hasattr(message, 'context_data') else {}
        )
        
        return new_message
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conversations/{conversation_id}/chat")
async def chat_with_enhanced_ai(
    conversation_id: str,
    message: MessageCreate,
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Stream AI response with enhanced capabilities using SSE"""
    
    # Generate unique stream ID
    stream_id = f"chat_{conversation_id}_{uuid.uuid4().hex[:8]}"
    
    # Create user context
    user_context = create_user_context(current_user)
    
    async def enhanced_response_generator():
        """Generator for enhanced AI response with context"""
        try:
            logger.info(f"Starting enhanced chat stream {stream_id} for conversation {conversation_id} by user {user_context.get('username')}")
            
            # Generate response with enhanced context and user information
            async for chunk in enhanced_chat_service.generate_ai_response(
                message=message.content,
                model_id=message.model_id or "openai/gpt-oss-120b",
                conversation_id=conversation_id,
                user_context=user_context
            ):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error in enhanced chat stream {stream_id}: {e}")
            yield f"Error: {str(e)}"
    
    # Create SSE stream with metadata
    metadata = {
        "conversation_id": conversation_id,
        "model_id": message.model_id or "openai/gpt-oss-120b",
        "message_content": message.content[:100] + "..." if len(message.content) > 100 else message.content
    }
    
    return streaming_manager.create_sse_stream(
        stream_id=stream_id,
        generator=enhanced_response_generator(),
        metadata=metadata
    )

@router.post("/conversations/{conversation_id}/chat-stream")
async def chat_with_enhanced_ai_stream(
    conversation_id: str,
    message: MessageCreate,
    stream_type: str = Query("sse", description="Stream type: sse or websocket"),
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Alternative streaming endpoint with configurable stream type"""
    
    if stream_type not in ["sse", "websocket"]:
        raise HTTPException(status_code=400, detail="Invalid stream type. Use 'sse' or 'websocket'")
    
    # For SSE, redirect to main chat endpoint
    if stream_type == "sse":
        return await chat_with_enhanced_ai(conversation_id, message, current_user)
    
    # For WebSocket, return connection info
    return {
        "message": "Use WebSocket endpoint for real-time streaming",
        "websocket_url": f"/api/chat/ws/{conversation_id}",
        "stream_type": "websocket"
    }

@router.websocket("/ws/{conversation_id}")
async def enhanced_websocket_endpoint(websocket: WebSocket, conversation_id: str):
    """Enhanced WebSocket endpoint with streaming manager integration"""
    connection_id = f"ws_{conversation_id}_{uuid.uuid4().hex[:8]}"
    
    await manager.connect(websocket, connection_id, {
        "conversation_id": conversation_id,
        "type": "enhanced_chat"
    })
    
    try:
        # Send welcome message
        await manager.send_json_message({
            "type": "connection_established",
            "connection_id": connection_id,
            "conversation_id": conversation_id,
            "features": [
                "real_time_streaming",
                "intelligent_buffering",
                "web_search",
                "crypto_data",
                "news_updates",
                "vector_search",
                "conversation_history",
                "error_recovery"
            ],
            "timestamp": datetime.now().isoformat()
        }, connection_id)
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Validate message data
            if not message_data.get("content"):
                await manager.send_json_message({
                    "type": "error",
                    "message": "Message content is required",
                    "timestamp": datetime.now().isoformat()
                }, connection_id)
                continue
            
            # Echo back the user message
            await manager.send_json_message({
                "type": "user_message",
                "content": message_data.get("content", ""),
                "model_id": message_data.get("model_id", "openai/gpt-oss-120b"),
                "timestamp": datetime.now().isoformat()
            }, connection_id)
            
            # Generate stream ID for this response
            stream_id = f"ws_stream_{connection_id}_{uuid.uuid4().hex[:8]}"
            
            # Create response generator
            async def websocket_response_generator():
                try:
                    async for chunk in enhanced_chat_service.generate_ai_response(
                        message=message_data.get("content", ""),
                        model_id=message_data.get("model_id", "openai/gpt-oss-120b"),
                        conversation_id=conversation_id
                    ):
                        yield chunk
                except Exception as e:
                    logger.error(f"WebSocket response generation error: {e}")
                    yield f"Error: {str(e)}"
            
            # Stream response using streaming manager
            metadata = {
                "conversation_id": conversation_id,
                "connection_id": connection_id,
                "model_id": message_data.get("model_id", "openai/gpt-oss-120b")
            }
            
            await streaming_manager.stream_to_websocket(
                websocket=websocket,
                stream_id=stream_id,
                generator=websocket_response_generator(),
                metadata=metadata
            )
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
        manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(connection_id)

@router.get("/streams")
async def get_active_streams(current_user: Optional[UserResponse] = Depends(get_optional_user)):
    """Get information about active streaming connections"""
    return {
        "active_streams": streaming_manager.get_active_streams(),
        "websocket_connections": manager.get_active_connections(),
        "total_streams": len(streaming_manager.get_active_streams()),
        "total_websockets": len(manager.get_active_connections())
    }

@router.delete("/streams/{stream_id}")
async def close_stream(stream_id: str, current_user: Optional[UserResponse] = Depends(get_optional_user)):
    """Force close a specific stream"""
    await streaming_manager.close_stream(stream_id)
    return {"message": f"Stream {stream_id} closed", "success": True}

@router.get("/models")
async def get_available_models():
    """Get list of available AI models with enhanced capabilities"""
    try:
        models = await enhanced_chat_service.get_available_models()
        
        return {
            "models": models,
            "total_models": len(models),
            "providers": list(set(model["provider"] for model in models)),
            "enhanced_features": [
                "real_time_web_search",
                "cryptocurrency_data",
                "news_updates", 
                "vector_knowledge_search",
                "conversation_history",
                "intelligent_context_detection"
            ]
        }
    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search-tools")
async def get_search_tools():
    """Get available search tools and their capabilities"""
    try:
        search_status = await enhanced_chat_service.search_service.get_provider_status()
        
        tools = [
            {
                "id": "web_search",
                "name": "Web Search",
                "description": "Search the web for current information",
                "providers": ["SerpAPI", "Brave Search"],
                "primary_provider": "SerpAPI",
                "available": any(
                    provider_info.get("available", False) 
                    for provider_info in search_status.get("providers", {}).values()
                )
            },
            {
                "id": "news_search", 
                "name": "News Search",
                "description": "Search for latest news and current events",
                "providers": ["SerpAPI", "Brave Search"],
                "primary_provider": "SerpAPI",
                "available": any(
                    provider_info.get("available", False)
                    for provider_info in search_status.get("providers", {}).values()
                )
            },
            {
                "id": "crypto_data",
                "name": "Cryptocurrency Data",
                "description": "Get real-time cryptocurrency market data",
                "providers": ["Binance"],
                "primary_provider": "Binance",
                "available": enhanced_chat_service.binance_service.is_available()
            },
            {
                "id": "vector_search",
                "name": "Knowledge Search",
                "description": "Search domain-specific knowledge base",
                "providers": ["Vector Database"],
                "primary_provider": "PostgreSQL + pgvector",
                "available": True  # Assuming vector service is always available
            }
        ]
        
        return {
            "tools": tools,
            "search_providers_status": search_status,
            "intelligent_routing": True,
            "fallback_support": True
        }
        
    except Exception as e:
        logger.error(f"Error getting search tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_service_status():
    """Get comprehensive status of all enhanced chat services"""
    try:
        status = await enhanced_chat_service.get_service_status()
        
        return {
            "service": "Enhanced Chat Service",
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "services": status,
            "active_connections": len(manager.get_active_connections()),
            "features": {
                "ai_models": "Multiple providers with fallback",
                "web_search": "SerpAPI primary, Brave Search fallback",
                "crypto_data": "Real-time Binance integration",
                "news_search": "Multi-provider news aggregation",
                "vector_search": "Semantic knowledge retrieval",
                "conversation_cache": "Redis-based history management",
                "streaming": "WebSocket and SSE support"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting service status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/capabilities")
async def get_chat_capabilities():
    """Get detailed enhanced chat capabilities"""
    try:
        models = await enhanced_chat_service.get_available_models()
        search_status = await enhanced_chat_service.search_service.get_provider_status()
        
        return {
            "features": [
                "Multi-AI model support with intelligent routing",
                "Real-time web search via SerpAPI and Brave Search",
                "Cryptocurrency market data via Binance API",
                "Latest news and current events",
                "Vector database semantic search",
                "Conversation history with Redis caching",
                "Streaming responses (SSE and WebSocket)",
                "Intelligent context detection",
                "Automatic fallback handling",
                "Error recovery and graceful degradation"
            ],
            "models_available": len(models),
            "ai_providers": len(set(model["provider"] for model in models)),
            "search_providers": len(search_status.get("providers", {})),
            "external_apis": 4,  # SerpAPI, Brave, Binance, Vector DB
            "real_time_data": True,
            "streaming": True,
            "caching": True,
            "fallback_support": True
        }
        
    except Exception as e:
        logger.error(f"Error getting capabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/connections")
async def get_active_connections(current_user: Optional[UserResponse] = Depends(get_optional_user)):
    """Get active WebSocket connections (admin endpoint)"""
    return {
        "active_connections": manager.get_active_connections(),
        "total_connections": len(manager.get_active_connections())
    }

# Search tool endpoints
@router.post("/search/web")
async def search_web(
    query: str = Query(..., description="Search query"),
    count: int = Query(10, ge=1, le=20, description="Number of results"),
    provider: Optional[str] = Query(None, description="Specific provider to use"),
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Perform web search using available providers"""
    try:
        search_provider = None
        if provider:
            search_provider = SearchProvider(provider.lower())
        
        results = await enhanced_chat_service.search_service.search_web(
            query=query,
            count=count,
            provider=search_provider or SearchProvider.AUTO
        )
        
        return {
            "query": query,
            "results": results,
            "count": len(results),
            "provider_used": results[0].get("provider") if results else None
        }
        
    except Exception as e:
        logger.error(f"Web search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search/news")
async def search_news(
    query: str = Query(..., description="News search query"),
    count: int = Query(5, ge=1, le=20, description="Number of results"),
    time_period: str = Query("1d", description="Time period (1h, 1d, 1w, 1m, 1y)"),
    provider: Optional[str] = Query(None, description="Specific provider to use"),
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """Search for news using available providers"""
    try:
        search_provider = None
        if provider:
            search_provider = SearchProvider(provider.lower())
        
        results = await enhanced_chat_service.search_service.search_news(
            query=query,
            count=count,
            provider=search_provider or SearchProvider.AUTO,
            time_period=time_period
        )
        
        return {
            "query": query,
            "results": results,
            "count": len(results),
            "time_period": time_period,
            "provider_used": results[0].get("provider") if results else None
        }
        
    except Exception as e:
        logger.error(f"News search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/crypto/market")
async def get_crypto_market_data(current_user: Optional[UserResponse] = Depends(get_optional_user)):
    """Get cryptocurrency market data"""
    try:
        if not enhanced_chat_service.binance_service.is_available():
            raise HTTPException(status_code=503, detail="Cryptocurrency service not available")
        
        market_data = await enhanced_chat_service.binance_service.get_market_data()
        trending_data = await enhanced_chat_service.binance_service.get_top_gainers_losers(limit=10)
        
        return {
            "market_data": market_data,
            "trending": trending_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Crypto market data error: {e}")
        raise HTTPException(status_code=500, detail=str(e))