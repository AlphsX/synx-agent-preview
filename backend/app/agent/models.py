from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime


class AIModel(BaseModel):
    """AI Model configuration"""
    id: str
    name: str
    provider: Literal["groq", "openai", "anthropic"]
    description: str
    max_tokens: int
    supports_streaming: bool = True
    available: bool = True
    cost_per_token: Optional[float] = None


class ChatMessage(BaseModel):
    """Chat message model"""
    role: Literal["system", "user", "assistant"]
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    """Chat request model"""
    messages: List[ChatMessage]
    model_id: str
    stream: bool = True
    temperature: float = 0.7
    max_tokens: int = 2000
    top_p: float = 1.0


class ChatResponse(BaseModel):
    """Chat response model"""
    content: str
    model_id: str
    provider: str
    usage: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None


class StreamChunk(BaseModel):
    """Streaming response chunk"""
    content: str
    model_id: str
    provider: str
    finish_reason: Optional[str] = None
    done: bool = False


class ModelAvailability(BaseModel):
    """Model availability status"""
    model_id: str
    available: bool
    error: Optional[str] = None
    last_checked: datetime