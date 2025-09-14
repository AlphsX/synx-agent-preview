from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, AsyncGenerator
import json
import asyncio

from app.chat.schemas import MessageCreate, ConversationCreate, ChatResponse, MessageResponse
from app.chat.services import ChatService
from app.auth.router import oauth2_scheme

router = APIRouter()
chat_service = ChatService()

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
    # Mock conversation creation
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
    # Mock conversations
    return [
        {
            "id": "conv_1",
            "title": "Chat about AI",
            "last_message": "Hello! How can I help you?",
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
    # Mock message creation
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
async def chat_with_ai(
    conversation_id: str,
    message: MessageCreate,
    token: str = Depends(oauth2_scheme)
):
    """Stream AI response for a message"""
    
    async def generate_response():
        # Mock streaming response
        response_chunks = [
            "Hello! I'm an AI assistant inspired by Sync. ",
            "I can help you with various tasks including: ",
            "web search, cryptocurrency data, ",
            "and general conversation. ",
            "What would you like to know?"
        ]
        
        for i, chunk in enumerate(response_chunks):
            data = {
                "type": "content",
                "content": chunk,
                "finished": i == len(response_chunks) - 1
            }
            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.1)  # Simulate typing delay
        
        # Send final completion message
        final_data = {
            "type": "done",
            "content": "",
            "finished": True
        }
        yield f"data: {json.dumps(final_data)}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )

@router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    """WebSocket endpoint for real-time chat"""
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
            
            # Send AI response
            ai_response = f"AI response to: {message_data.get('content', '')}"
            await manager.send_personal_message(
                json.dumps({
                    "type": "ai_message",
                    "content": ai_response,
                    "timestamp": "2024-01-01T00:00:00Z"
                }),
                websocket
            )
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.get("/models")
async def get_available_models():
    """Get list of available AI models"""
    return {
        "models": [
            {
                "id": "gpt-4",
                "name": "GPT-4",
                "provider": "OpenAI",
                "description": "Most capable GPT-4 model"
            },
            {
                "id": "gpt-3.5-turbo",
                "name": "GPT-3.5 Turbo",
                "provider": "OpenAI",
                "description": "Fast and efficient model"
            },
            {
                "id": "claude-3-5-sonnet-20241022",
                "name": "Claude 3.5 Sonnet",
                "provider": "Anthropic",
                "description": "Latest Claude model with enhanced capabilities"
            },
            {
                "id": "groq-llama-3.1-70b",
                "name": "Llama 3.1 70B",
                "provider": "Groq",
                "description": "Ultra-fast inference with Llama 3.1"
            },
            {
                "id": "groq-llama-3.1-8b",
                "name": "Llama 3.1 8B",
                "provider": "Groq",
                "description": "Instant responses with smaller model"
            }
        ]
    }