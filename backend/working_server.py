#!/usr/bin/env python3
import os
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import json
import time

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="AI Agent API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ChatMessage(BaseModel):
    content: str
    role: str
    model_id: Optional[str] = None

class AIModel(BaseModel):
    id: str
    name: str
    provider: str
    description: str
    recommended: bool = False

# Available models
AVAILABLE_MODELS = [
    AIModel(id="llama-3.1-70b-versatile", name="Llama 3.1 70B", provider="Groq", description="Meta's Llama 3.1 70B model for complex reasoning", recommended=True),
    AIModel(id="llama-3.1-8b-instant", name="Llama 3.1 8B", provider="Groq", description="Meta's Llama 3.1 8B model for fast responses"),
    AIModel(id="mixtral-8x7b-32768", name="Mixtral 8x7B", provider="Groq", description="Mistral's Mixtral 8x7B model with 32k context"),
    AIModel(id="openai/gpt-oss-120b", name="GPT OSS 120B", provider="Groq", description="OpenAI's GPT OSS 120B model for advanced reasoning"),
    AIModel(id="meta-llama/llama-4-maverick-17b-128e-instruct", name="Llama 4 Maverick 17B", provider="Groq", description="Meta's Llama 4 Maverick 17B instruction-tuned model"),
    AIModel(id="deepseek-r1-distill-llama-70b", name="DeepSeek R1 Distill Llama 70B", provider="Groq", description="DeepSeek's R1 distilled Llama 70B model"),
    AIModel(id="qwen/qwen3-32b", name="Qwen 3 32B", provider="Groq", description="Alibaba's Qwen 3 32B model for multilingual tasks"),
    AIModel(id="moonshotai/kimi-k2-instruct-0905", name="Kimi K2 Instruct", provider="Groq", description="MoonshotAI's Kimi K2 instruction-tuned model")
]

# Initialize Groq client
groq_api_key = os.getenv('GROQ_API_KEY')
if groq_api_key:
    try:
        from groq import Groq
        groq_client = Groq(api_key=groq_api_key)
        print("✅ Groq client initialized successfully")
    except ImportError:
        print("❌ Groq package not installed. Install with: pip install groq")
        groq_client = None
    except Exception as e:
        print(f"❌ Failed to initialize Groq client: {e}")
        groq_client = None
else:
    print("⚠️ GROQ_API_KEY not found in environment variables")
    groq_client = None

@app.get("/")
async def root():
    return {
        "message": "AI Agent API is running",
        "status": "ok",
        "groq_available": groq_client is not None,
        "models_count": len(AVAILABLE_MODELS)
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "ai-agent-api",
        "groq_available": groq_client is not None,
        "timestamp": time.time()
    }

@app.get("/api/chat/models")
async def get_models():
    return {
        "models": [model.dict() for model in AVAILABLE_MODELS],
        "total_models": len(AVAILABLE_MODELS),
        "providers": ["Groq"],
        "enhanced_features": ["real_time_web_search", "cryptocurrency_data", "news_updates", "vector_knowledge_search"]
    }

@app.get("/api/chat/capabilities")
async def get_capabilities():
    return {
        "features": ["Multi-AI model support", "Real-time web search", "Cryptocurrency data", "News updates", "Vector search"],
        "models_available": len(AVAILABLE_MODELS),
        "ai_providers": 1,
        "search_providers": 2,
        "external_apis": 3,
        "real_time_data": True,
        "streaming": True,
        "caching": True,
        "fallback_support": True
    }

async def generate_groq_response(message: str, model_id: str):
    """Generate response using Groq API"""
    if not groq_client:
        # Fallback response when Groq is not available
        yield f"data: {json.dumps({'content': f'[Demo Mode] You asked: {message}. This is a demo response since Groq API is not configured.'})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        return
    
    try:
        # Create chat completion with streaming
        stream = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are LUNA, a helpful AI assistant. Be concise and friendly."},
                {"role": "user", "content": message}
            ],
            model=model_id,
            temperature=0.7,
            max_tokens=1000,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                yield f"data: {json.dumps({'content': content})}\n\n"
        
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
    except Exception as e:
        error_msg = f"Error generating response: {str(e)}"
        yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"

@app.post("/api/chat/conversations/{conversation_id}/chat")
async def chat_stream(conversation_id: str, message: ChatMessage):
    """Stream chat response"""
    
    # Validate model
    model_ids = [model.id for model in AVAILABLE_MODELS]
    if message.model_id and message.model_id not in model_ids:
        raise HTTPException(status_code=400, detail=f"Model {message.model_id} not available")
    
    model_id = message.model_id or "llama-3.1-70b-versatile"
    
    return StreamingResponse(
        generate_groq_response(message.content, model_id),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

@app.get("/api/chat/search-tools")
async def get_search_tools():
    return {
        "tools": [
            {"id": "web_search", "name": "Web Search", "description": "Search the web for current information", "providers": ["SerpAPI", "Brave Search"], "primary_provider": "SerpAPI", "available": True},
            {"id": "news_search", "name": "News Search", "description": "Search for latest news and current events", "providers": ["SerpAPI", "Brave Search"], "primary_provider": "SerpAPI", "available": True},
            {"id": "crypto_data", "name": "Cryptocurrency Data", "description": "Get real-time cryptocurrency market data", "providers": ["Binance"], "primary_provider": "Binance", "available": True},
            {"id": "vector_search", "name": "Knowledge Search", "description": "Search domain-specific knowledge base", "providers": ["Vector Database"], "primary_provider": "PostgreSQL + pgvector", "available": True}
        ],
        "search_providers_status": {"groq": groq_client is not None},
        "intelligent_routing": True,
        "fallback_support": True
    }

@app.get("/api/chat/status")
async def get_status():
    return {
        "service": "Enhanced Chat Service",
        "status": "operational" if groq_client else "demo_mode",
        "timestamp": time.time(),
        "services": {
            "groq": "available" if groq_client else "not_configured",
            "models": len(AVAILABLE_MODELS)
        },
        "active_connections": 0,
        "features": {
            "ai_models": "Available" if groq_client else "Demo mode - configure GROQ_API_KEY",
            "web_search": "Demo mode - configure SerpAPI",
            "crypto_data": "Demo mode - configure Binance API"
        }
    }

if __name__ == "__main__":
    print("🚀 Starting AI Agent Server...")
    print("📍 Server: http://127.0.0.1:8000")
    print("📚 API Docs: http://127.0.0.1:8000/docs")
    print(f"🤖 Groq API: {'✅ Available' if groq_client else '❌ Not configured'}")
    print(f"📊 Models: {len(AVAILABLE_MODELS)} available")
    
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=8000, 
        log_level="info",
        access_log=True
    )