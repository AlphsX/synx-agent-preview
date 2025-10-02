from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.auth.router import router as auth_router
from app.chat.router import router as chat_router
from app.external_apis_router import router as external_apis_router
from app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Checkmate Spec Preview API...")
    print("📡 External APIs: Brave Search, Groq, Binance")
    yield
    # Shutdown
    print("🔄 Shutting down Checkmate Spec Preview API...")

app = FastAPI(
    title="Checkmate Spec Preview API",
    description="Backend API for Checkmate Spec Preview - AI Agent inspired by Sync",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(external_apis_router, prefix="/api/external", tags=["external_apis"])

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
    return {"status": "healthy", "service": "checkmate-spec-preview-api"}

@app.get("/api/status")
async def api_status():
    return {
        "api": "Checkmate Spec Preview",
        "status": "operational",
        "features": [
            "Multi-AI chat (GPT, Claude, Groq)",
            "Real-time web search (Brave Search)",
            "Cryptocurrency data (Binance)",
            "Authentication system",
            "WebSocket chat support"
        ],
        "endpoints": {
            "auth": "/api/auth/*",
            "chat": "/api/chat/*", 
            "external": "/api/external/*",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False
    )