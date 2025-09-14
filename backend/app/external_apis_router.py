from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import asyncio
from app.external_apis.brave_search import BraveSearchService
from app.external_apis.binance import BinanceService
from app.config import settings

router = APIRouter()

# Initialize services
brave_search = BraveSearchService()
binance_service = BinanceService()

@router.get("/search")
async def search_web(query: str, count: int = 10):
    """Search the web using Brave Search API"""
    try:
        results = await brave_search.search(query, count)
        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/search/news")
async def search_news(query: str, count: int = 5):
    """Search for news using Brave Search API"""
    try:
        results = await brave_search.search_news(query, count)
        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"News search failed: {str(e)}")

@router.get("/crypto/market")
async def get_crypto_market():
    """Get cryptocurrency market data from Binance"""
    try:
        data = await binance_service.get_market_data()
        return {
            "success": True,
            "data": data,
            "timestamp": "2024-01-01T00:00:00Z"  # Would be current timestamp
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Crypto data failed: {str(e)}")

@router.get("/crypto/price/{symbol}")
async def get_crypto_price(symbol: str):
    """Get price for a specific cryptocurrency"""
    try:
        data = await binance_service.get_ticker_price(symbol)
        return {
            "success": True,
            "symbol": symbol,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Price fetch failed: {str(e)}")

@router.get("/crypto/trending")
async def get_trending_crypto():
    """Get top gainers and losers"""
    try:
        data = await binance_service.get_top_gainers_losers()
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trending data failed: {str(e)}")

@router.get("/health")
async def external_apis_health():
    """Check health of external APIs"""
    health_status = {
        "brave_search": False,
        "binance": False,
        "apis_configured": {
            "brave_search": bool(settings.BRAVE_SEARCH_API_KEY),
            "binance": bool(settings.BINANCE_API_KEY)
        }
    }
    
    # Test Brave Search
    try:
        await brave_search.search("test", 1)
        health_status["brave_search"] = True
    except:
        pass
    
    # Test Binance
    try:
        await binance_service.get_ticker_price("BTCUSDT")
        health_status["binance"] = True
    except:
        pass
    
    return health_status