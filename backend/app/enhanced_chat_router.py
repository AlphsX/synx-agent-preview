from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, AsyncGenerator
import json
import asyncio

from app.chat.schemas import MessageCreate, ConversationCreate, ChatResponse, MessageResponse
from app.enhanced_chat_service import EnhancedChatService
from app.auth.router import oauth2_scheme

router = APIRouter()
enhanced_chat_service = EnhancedChatService()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

manager = ConnectionManager()

@router.post("/conversations", response_model=dict)
async def create_conversation(
    conversation: ConversationCreate,
    token: str = Depends(oauth2_scheme)
):
    """Create a new conversation"""
    new_conversation = {
        "id": f"conv_{len(str(conversation.title))}",
        "title": conversation.title,
        "user_id": "mock-user-id",
        "created_at": "2024-01-01T00:00:00Z"
    }
    return new_conversation

@router.get("/conversations", response_model=List[dict])
async def get_conversations(token: str = Depends(oauth2_scheme)):
    """Get user's conversations"""
    return [
        {
            "id": "conv_1",
            "title": "Chat with Checkmate Spec Preview",
            "last_message": "Hello! I'm your enhanced AI assistant with real-time capabilities.",
            "created_at": "2024-01-01T00:00:00Z"
        }
    ]

@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def create_message(
    conversation_id: str,
    message: MessageCreate,
    token: str = Depends(oauth2_scheme)
):
    """Add a message to conversation"""
    new_message = {
        "id": f"msg_{len(message.content)}",
        "conversation_id": conversation_id,
        "content": message.content,
        "role": message.role,
        "model_id": message.model_id,
        "created_at": "2024-01-01T00:00:00Z"
    }
    return MessageResponse(**new_message)

@router.post("/conversations/{conversation_id}/chat")
async def chat_with_enhanced_ai(
    conversation_id: str,
    message: MessageCreate,
    token: str = Depends(oauth2_scheme)
):
    """Stream AI response with enhanced capabilities (web search, crypto data)"""
    
    async def generate_enhanced_response():
        try:
            # Use enhanced chat service with external API integration
            async for chunk in enhanced_chat_service.generate_ai_response(
                message=message.content,
                model_id=message.model_id or "groq-llama-3.1-70b",
                conversation_history=[]  # Would get from database
            ):
                data = {
                    "type": "content",
                    "content": chunk,
                    "finished": False
                }
                yield f"data: {json.dumps(data)}\\n\\n"
                await asyncio.sleep(0.01)  # Small delay for streaming effect
            
            # Send completion message
            final_data = {
                "type": "done",
                "content": "",
                "finished": True,
                "enhanced_features": [
                    "Real-time web search",
                    "Cryptocurrency data",
                    "News updates",
                    "Multi-AI model support"
                ]
            }
            yield f"data: {json.dumps(final_data)}\\n\\n"
            
        except Exception as e:
            error_data = {
                "type": "error",
                "content": f"Error: {str(e)}",
                "finished": True
            }
            yield f"data: {json.dumps(error_data)}\\n\\n"
    
    return StreamingResponse(
        generate_enhanced_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )

@router.websocket("/ws/{conversation_id}")
async def enhanced_websocket_endpoint(websocket: WebSocket, conversation_id: str):
    """Enhanced WebSocket endpoint for real-time chat with external data"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Echo back the user message
            await manager.send_personal_message(
                json.dumps({
                    "type": "user_message",
                    "content": message_data.get("content", ""),
                    "timestamp": "2024-01-01T00:00:00Z"
                }),
                websocket
            )
            
            # Generate enhanced AI response
            response_content = ""
            async for chunk in enhanced_chat_service.generate_ai_response(
                message=message_data.get("content", ""),
                model_id=message_data.get("model_id", "groq-llama-3.1-70b"),
                conversation_history=[]
            ):
                response_content += chunk
                # Send chunk in real-time
                await manager.send_personal_message(
                    json.dumps({
                        "type": "ai_chunk",
                        "content": chunk,
                        "timestamp": "2024-01-01T00:00:00Z"
                    }),
                    websocket
                )
            
            # Send final complete message
            await manager.send_personal_message(
                json.dumps({
                    "type": "ai_message_complete",
                    "content": response_content,
                    "features_used": ["Enhanced AI", "External APIs"],
                    "timestamp": "2024-01-01T00:00:00Z"
                }),
                websocket
            )
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.get("/models")
async def get_available_models():
    """Get list of available AI models with enhanced capabilities"""
    return {
        "models": [
            {
                "id": "gpt-4",
                "name": "GPT-4",
                "provider": "OpenAI",
                "description": "Most capable GPT-4 model with web search",
                "features": ["web_search", "crypto_data"]
            },
            {
                "id": "gpt-3.5-turbo",
                "name": "GPT-3.5 Turbo",
                "provider": "OpenAI",
                "description": "Fast and efficient model with real-time data",
                "features": ["web_search", "crypto_data"]
            },
            {
                "id": "claude-3-5-sonnet-20241022",
                "name": "Claude 3.5 Sonnet",
                "provider": "Anthropic",
                "description": "Latest Claude model with enhanced capabilities",
                "features": ["web_search", "crypto_data", "news"]
            },
            {
                "id": "groq-llama-3.1-70b",
                "name": "Llama 3.1 70B (Groq)",
                "provider": "Groq",
                "description": "Ultra-fast inference with real-time data",
                "features": ["web_search", "crypto_data", "ultra_fast"],
                "recommended": True
            },
            {
                "id": "groq-llama-3.1-8b",
                "name": "Llama 3.1 8B (Groq)",
                "provider": "Groq",
                "description": "Instant responses with external data",
                "features": ["web_search", "crypto_data", "instant"]
            }
        ],
        "external_apis": {
            "brave_search": "Real-time web search",
            "binance": "Cryptocurrency market data",
            "news": "Latest news updates"
        }
    }

@router.get("/capabilities")
async def get_chat_capabilities():
    """Get enhanced chat capabilities"""
    return {
        "features": [
            "Multi-AI model support",
            "Real-time web search via Brave Search",
            "Cryptocurrency market data via Binance",
            "News and current events",
            "Streaming responses",
            "WebSocket real-time chat",
            "Context-aware responses"
        ],
        "models_available": 5,
        "external_apis": 3,
        "real_time_data": True,
        "streaming": True
    }