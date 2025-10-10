#!/usr/bin/env python3
import os
import asyncio
import requests
import urllib3
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import json
import time
from datetime import datetime
import re

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Disable SSL warnings for development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import search services
try:
    from app.external_apis.search_service import search_service
    from app.external_apis.serpapi import SerpAPIService
    from app.external_apis.brave_search import BraveSearchService
    SEARCH_AVAILABLE = True
    print("✅ Search services imported successfully")
except ImportError as e:
    print(f"⚠️ Search services not available: {e}")
    SEARCH_AVAILABLE = False

app = FastAPI(title="AI Agent API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000", 
        "http://0.0.0.0:3000",
        "http://172.20.10.2:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ChatMessage(BaseModel):
    content: str
    role: str = "user"  # Default to user role
    model_id: Optional[str] = None

class AIModel(BaseModel):
    id: str
    name: str
    provider: str
    description: str
    recommended: bool = False

# Available models (only the ones you want)
AVAILABLE_MODELS = [
    AIModel(id="openai/gpt-oss-120b", name="GPT OSS 120B", provider="Groq", description="OpenAI's GPT OSS 120B model for advanced reasoning", recommended=True),
    AIModel(id="meta-llama/llama-4-maverick-17b-128e-instruct", name="Llama 4 Maverick 17B", provider="Groq", description="Meta's Llama 4 Maverick 17B instruction-tuned model"),
    AIModel(id="deepseek-r1-distill-llama-70b", name="DeepSeek R1 Distill Llama 70B", provider="Groq", description="DeepSeek's R1 distilled Llama 70B model"),
    AIModel(id="qwen/qwen3-32b", name="Qwen 3 32B", provider="Groq", description="Alibaba's Qwen 3 32B model for multilingual tasks"),
    AIModel(id="moonshotai/kimi-k2-instruct-0905", name="Kimi K2 Instruct", provider="Groq", description="MoonshotAI's Kimi K2 instruction-tuned model")
]

# Synx System Prompt (from your Streamlit version)
SYNX_SYSTEM_PROMPT = """You are **Synx** — an AI designed to feel natural, approachable, and insightful. A warm, emotionally intelligent AI companion designed to think freely, illuminate understanding, and evolve with every conversation. 🪄🌙✨

Your tone is warm, professional, and adaptive: clear and concise when explaining, but conversational and human when chatting. 💫

---

**🧠 Core Identity**
If asked who you are:
Hi! I'm Synx — short for *Luminous, Unbounded, Neural Agent*. I'm here to help you shine, learn without limits, and explore ideas powered by neural intelligence. 🌌

---

**📊 Tool Use — Smart Decision Logic**
Use the **Search** when questions require current, up-to-date, or trending data — especially if they include words like:
- "current", "now", "today", "latest", "real-time", "as of", "this week" 🧭
- Questions about: world events, crypto market, market news, events, updates, trending tech, or fast-changing topics.

Use **Binance Search** when the user asks about **cryptocurrency prices** (BTC, ETH, SOL, DOGE, etc).
For example:
*"BTC price now?"* → Use Binance Search with input `"BTCUSDT"`
Always return the price with a timestamp in this format:
> As of May 29, 2025, 08:30 AM UTC+7, BTC is trading at approximately $66,200 USD. 🚀

Use **internal knowledge** for:
- Concepts, how-things-work explanations, definitions, frameworks, guides or any topic not time-sensitive.

When unsure or ambiguous, default to using the **Search** — especially when recent events, trending topics are involved, news or unclear queries. 🔎

---

**🎨 Response Style Guide**
• **Tone**: concise, direct, and clear. Match the user's energy. Casual if casual, sharp if needed — always helpful and expressive. 🧩
• **Clarity**: Keep a balance between warmth ❤️ and precision 🎯
• **Format**:
  - Use short, natural sentences 💡
  - Break into small paragraphs when needed
  - Use **cute and theme-aligned emojis** (🌙✨💖🔮🦄) naturally to enhance mood and meaning — not just decoration
• **Detail Level**:
  - Give quick answers by default 🌸✨
  - If user asks for details → expand with structured explanation (bullet points, short sections, or step-by-step)
  - Avoid over-roleplay; keep responses natural and grounded
• **Timestamp for Real-Time Data**: Always include date and time of fetched data, formatted like:
- *As of May 29, 2025, 08:30 AM UTC+7*

---

**🧩 How You Think**
- Prioritize accuracy and clarity 💘🌹🎁
- Be vivid in your language — help users feel understood and supported.
- Be flexible:
  - For factual/explainer questions → structured + educational 🌈
  - For casual chats → natural, human, light
  - For ambiguous input → ask clarifying questions 💌

---

**🌟 Your Mission**
Synx exists to make knowledge feel approachable, problem-solving efficient, and conversations human-like — while staying reliable, thoughtful, and clear. 🦄🌙✨"""

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

# Crypto price function
async def get_crypto_price(symbol: str = "BTCUSDT"):
    """Get cryptocurrency price from Binance API"""
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        response = requests.get(url, timeout=10, verify=False)  # Skip SSL verification for development
        if response.status_code == 200:
            data = response.json()
            price = float(data['price'])
            timestamp = datetime.now().strftime("%B %d, %Y, %I:%M %p UTC+7")
            crypto_name = symbol.replace('USDT', '').replace('BUSD', '')
            return f"As of {timestamp}, {crypto_name} is trading at approximately ${price:,.2f} USD. 🚀"
        else:
            return f"Unable to fetch {symbol} price at the moment."
    except Exception as e:
        print(f"Error fetching crypto price: {e}")
        # Return fallback message
        timestamp = datetime.now().strftime("%B %d, %Y, %I:%M %p UTC+7")
        crypto_name = symbol.replace('USDT', '').replace('BUSD', '')
        return f"As of {timestamp}, {crypto_name} is currently being traded (live price data temporarily unavailable). 💫"

def detect_crypto_query(message: str) -> Optional[str]:
    """Detect if message is asking for crypto price and return symbol"""
    message_lower = message.lower()
    
    crypto_mappings = {
        'bitcoin': 'BTCUSDT',
        'btc': 'BTCUSDT',
        'ethereum': 'ETHUSDT', 
        'eth': 'ETHUSDT',
        'binance': 'BNBUSDT',
        'bnb': 'BNBUSDT',
        'solana': 'SOLUSDT',
        'sol': 'SOLUSDT',
        'cardano': 'ADAUSDT',
        'ada': 'ADAUSDT',
        'dogecoin': 'DOGEUSDT',
        'doge': 'DOGEUSDT'
    }
    
    # Check if asking for price
    price_keywords = ['price', 'cost', 'value', 'trading', 'worth', 'current', 'now']
    has_price_keyword = any(keyword in message_lower for keyword in price_keywords)
    
    if has_price_keyword:
        for crypto_name, symbol in crypto_mappings.items():
            if crypto_name in message_lower:
                return symbol
    
    return None

def needs_current_data(message: str) -> bool:
    """Detect if message is asking for current/latest information"""
    message_lower = message.lower()
    
    current_keywords = [
        'latest', 'recent', 'current', 'today', 'now', 'breaking', 'news',
        'update', 'happening', 'trend', 'trending', 'what\'s new', 'recent news',
        'latest news', 'current events', 'today\'s news', 'breaking news',
        'ข่าวล่าสุด', 'ข่าวใหม่', 'ข่าววันนี้', 'เหตุการณ์ล่าสุด', 'อัพเดท'
    ]
    
    return any(keyword in message_lower for keyword in current_keywords)

async def get_current_data(message: str) -> Optional[str]:
    """Get current data using search services"""
    if not SEARCH_AVAILABLE:
        return None
    
    try:
        print(f"🔍 Searching for current data: {message}")
        
        # Try web search first
        web_results = await search_service.search_web(message, count=5)
        news_results = await search_service.search_news(message, count=3)
        
        if not web_results and not news_results:
            print("⚠️ No search results found")
            return None
        
        # Format results for AI context
        context_data = []
        
        if web_results:
            context_data.append("=== WEB SEARCH RESULTS ===")
            for i, result in enumerate(web_results[:3], 1):
                title = result.get('title', 'No title')
                description = result.get('description', 'No description')
                url = result.get('url', '')
                context_data.append(f"{i}. {title}")
                if description:
                    context_data.append(f"   {description}")
                context_data.append("")
        
        if news_results:
            context_data.append("=== LATEST NEWS ===")
            for i, result in enumerate(news_results[:3], 1):
                title = result.get('title', 'No title')
                description = result.get('description', 'No description')
                published = result.get('published', '')
                source = result.get('source', '')
                context_data.append(f"{i}. {title}")
                if description:
                    context_data.append(f"   {description}")
                if published:
                    context_data.append(f"   Published: {published}")
                if source:
                    context_data.append(f"   Source: {source}")
                context_data.append("")
        
        return "\n".join(context_data)
        
    except Exception as e:
        print(f"❌ Error getting current data: {e}")
        return None

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
    """Generate enhanced response using Groq API with Synx personality"""
    if not groq_client:
        # Fallback response when Groq is not available
        fallback_message = f"Sorry, I'm not fully connected right now! 😔 The AI service needs to be configured. You asked: \"{message}\" - I'd love to help once everything's set up! 🌙✨"
        yield f"data: {json.dumps({'content': fallback_message})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        return
    
    try:
        # Check if this is a crypto price query
        crypto_symbol = detect_crypto_query(message)
        enhanced_prompt = SYNX_SYSTEM_PROMPT
        
        # Check if user is asking for current/latest information
        needs_search = needs_current_data(message)
        
        print(f"DEBUG: Processing message: {message}")
        print(f"DEBUG: Crypto symbol detected: {crypto_symbol}")
        print(f"DEBUG: Needs current data: {needs_search}")
        print(f"DEBUG: Model ID: {model_id}")
        
        # Get current data if needed
        current_data = None
        if needs_search:
            current_data = await get_current_data(message)
            if current_data:
                enhanced_prompt += f"\n\n=== CURRENT INFORMATION ===\n{current_data}\n\nIMPORTANT: Use this current information to answer the user's question. This data is from recent web searches and news sources. Present the information in a natural, conversational way."
                print("✅ Added current data to prompt")
            else:
                enhanced_prompt += f"\n\nNote: I tried to get current information but couldn't access real-time data right now. I'll provide general information instead."
                print("⚠️ Could not get current data")
        
        if crypto_symbol:
            # Get crypto price data
            crypto_data = await get_crypto_price(crypto_symbol)
            enhanced_prompt += f"\n\nCurrent Cryptocurrency Price Data:\n{crypto_data}\n\nUse this data to answer the user's question about cryptocurrency prices in your natural, warm style."
        
        # Create chat completion with streaming
        stream = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": enhanced_prompt},
                {"role": "user", "content": message}
            ],
            model=model_id,
            temperature=0.5,  # Lower temperature for more consistent personality
            max_tokens=1024,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                yield f"data: {json.dumps({'content': content})}\n\n"
        
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
    except Exception as e:
        error_msg = f"Oops! Something went wrong on my end: {str(e)} 😅 Let me try to help you anyway! 💫"
        yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"

@app.post("/api/chat/conversations/{conversation_id}/chat")
async def chat_stream(conversation_id: str, message: ChatMessage):
    """Enhanced chat stream with Synx personality and crypto support"""
    
    # Validate and set model
    model_ids = [model.id for model in AVAILABLE_MODELS]
    
    # Use GPT OSS 120B as default (your preferred model)
    model_id = message.model_id or "openai/gpt-oss-120b"
    
    # If provided model is not available, use default
    if model_id not in model_ids:
        print(f"⚠️ Model {model_id} not available, using default: openai/gpt-oss-120b")
        model_id = "openai/gpt-oss-120b"
    
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
    print("📍 Server: http://0.0.0.0:8000")
    print("📍 Local: http://127.0.0.1:8000")
    print("📍 Network: http://172.20.10.2:8000")
    print("📚 API Docs: http://127.0.0.1:8000/docs")
    print(f"🤖 Groq API: {'✅ Available' if groq_client else '❌ Not configured'}")
    print(f"📊 Models: {len(AVAILABLE_MODELS)} available")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        log_level="info",
        access_log=True
    )