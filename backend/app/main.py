from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging

from app.auth.router import router as auth_router
from app.chat.router import router as chat_router
from app.enhanced_chat_router import router as enhanced_chat_router
from app.external_apis_router import router as external_apis_router
from app.ai.endpoints import router as ai_router
from app.vector.router import router as vector_router
from app.api.health import router as health_router
from app.api.security import router as security_router
from app.database.connection import initialize_database, close_database
from app.database.migrations import run_migrations
from app.vector.service import vector_service
from app.config import settings
from app.core.logging_middleware import LoggingMiddleware
from app.core.error_handling import handle_api_error
from app.core.rate_limiting import RateLimitMiddleware
from app.core.security import SecurityHeadersMiddleware

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Checkmate Spec Preview API...")
    logger.info("📡 External APIs: SerpAPI, Brave Search, Groq, OpenAI, Anthropic, Binance")
    logger.info("🔧 Initializing database connections...")
    await initialize_database()
    logger.info("📊 Running database migrations...")
    await run_migrations()
    logger.info("🤖 Initializing vector service...")
    await vector_service.initialize()
    logger.info("✅ All services initialized successfully")
    logger.info("🔍 Error handling and monitoring system active")
    yield
    # Shutdown
    logger.info("🔄 Shutting down Checkmate Spec Preview API...")
    await close_database()

app = FastAPI(
    title="Checkmate Spec Preview API",
    description="Backend API for Checkmate Spec Preview - AI Agent inspired by Sync",
    version="1.0.0",
    lifespan=lifespan
)

# Add security and logging middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(LoggingMiddleware)

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=settings.RATE_LIMIT_REQUESTS,
    redis_url=settings.REDIS_URL
)

# CORS configuration for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers - Health checks first, then enhanced chat router for priority
app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(security_router, prefix="/api", tags=["security"])
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(ai_router, prefix="/api/ai", tags=["ai_models"])
app.include_router(enhanced_chat_router, prefix="/api/chat", tags=["enhanced_chat"])
app.include_router(external_apis_router, prefix="/api/external", tags=["external_apis"])
app.include_router(vector_router, prefix="/api", tags=["vector"])
# Original chat router as fallback
app.include_router(chat_router, prefix="/api/chat/basic", tags=["basic_chat"])

@app.get("/")
async def root():
    return {
        "message": "Checkmate Spec Preview API - AI Agent inspired by Sync", 
        "version": "1.0.0",
        "docs": "/docs",
        "external_apis": ["brave_search", "groq", "binance"]
    }

@app.get("/health")
async def health_check():
    """Legacy health endpoint for backward compatibility."""
    return {"status": "healthy", "service": "checkmate-spec-preview-api"}

@app.get("/api/status")
async def api_status():
    return {
        "api": "Checkmate Spec Preview - Enhanced",
        "status": "operational",
        "version": "1.0.0",
        "features": [
            "Enhanced Multi-AI chat with intelligent routing",
            "SerpAPI primary web search with Brave Search fallback",
            "Real-time cryptocurrency data via Binance",
            "Latest news aggregation",
            "Vector database semantic search",
            "Conversation history with Redis caching",
            "Server-Sent Events (SSE) streaming",
            "WebSocket real-time communication",
            "Intelligent context detection",
            "Automatic fallback and error recovery",
            "Comprehensive error handling and monitoring",
            "Structured logging for all API calls",
            "Health checks for all services",
            "Retry logic with exponential backoff",
            "Graceful degradation when services fail"
        ],
        "endpoints": {
            "health": "/api/health/*",
            "auth": "/api/auth/*",
            "ai": "/api/ai/*",
            "enhanced_chat": "/api/chat/*",
            "basic_chat": "/api/chat/basic/*",
            "external": "/api/external/*",
            "vector": "/api/vector/*",
            "docs": "/docs"
        },
        "streaming": {
            "sse": "/api/chat/conversations/{id}/chat",
            "websocket": "/api/chat/ws/{id}",
            "stream_management": "/api/chat/streams"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False
    )