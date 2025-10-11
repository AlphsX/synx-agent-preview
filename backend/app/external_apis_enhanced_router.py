"""
Enhanced External APIs Router

This router provides endpoints for all external API integrations including:
- Weather data
- Stock market data  
- Sentiment analysis
- Plugin system
- Unified data access
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, Any, List, Optional
import logging
from .external_apis import (
    WeatherService, StockService, SentimentAnalysisService,
    PluginManager, unified_service
)
from .external_apis.groq_compound_service import groq_compound_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/external", tags=["external-apis-enhanced"])

# Service instances
weather_service = WeatherService()
stock_service = StockService()
sentiment_service = SentimentAnalysisService()
plugin_manager = PluginManager()


@router.get("/weather/current")
async def get_current_weather(
    location: str = Query(..., description="Location for weather data"),
    units: str = Query("metric", description="Temperature units (metric, imperial, kelvin)")
) -> Dict[str, Any]:
    """Get current weather for a location."""
    try:
        result = await weather_service.get_current_weather(location, units)
        return result
    except Exception as e:
        logger.error(f"Weather API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Weather service error: {str(e)}")


@router.get("/weather/forecast")
async def get_weather_forecast(
    location: str = Query(..., description="Location for weather forecast"),
    days: int = Query(5, ge=1, le=5, description="Number of forecast days"),
    units: str = Query("metric", description="Temperature units")
) -> Dict[str, Any]:
    """Get weather forecast for a location."""
    try:
        result = await weather_service.get_weather_forecast(location, days, units)
        return result
    except Exception as e:
        logger.error(f"Weather forecast API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Weather forecast service error: {str(e)}")


@router.get("/weather/alerts")
async def get_weather_alerts(
    location: str = Query(..., description="Location for weather alerts")
) -> Dict[str, Any]:
    """Get weather alerts for a location."""
    try:
        result = await weather_service.get_weather_alerts(location)
        return result
    except Exception as e:
        logger.error(f"Weather alerts API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Weather alerts service error: {str(e)}")


@router.get("/stocks/quote")
async def get_stock_quote(
    symbol: str = Query(..., description="Stock symbol (e.g., AAPL)")
) -> Dict[str, Any]:
    """Get real-time stock quote."""
    try:
        result = await stock_service.get_stock_quote(symbol.upper())
        return result
    except Exception as e:
        logger.error(f"Stock quote API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Stock service error: {str(e)}")


@router.get("/stocks/market-overview")
async def get_stock_market_overview() -> Dict[str, Any]:
    """Get stock market overview with top gainers, losers, and most active."""
    try:
        result = await stock_service.get_market_overview()
        return result
    except Exception as e:
        logger.error(f"Stock market overview API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Stock market service error: {str(e)}")


@router.get("/stocks/company-info")
async def get_company_info(
    symbol: str = Query(..., description="Stock symbol")
) -> Dict[str, Any]:
    """Get company information and fundamentals."""
    try:
        result = await stock_service.get_company_info(symbol.upper())
        return result
    except Exception as e:
        logger.error(f"Company info API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Company info service error: {str(e)}")


@router.get("/stocks/historical")
async def get_historical_stock_data(
    symbol: str = Query(..., description="Stock symbol"),
    period: str = Query("1M", description="Time period (1D, 1W, 1M, 3M, 1Y)")
) -> Dict[str, Any]:
    """Get historical stock data."""
    try:
        result = await stock_service.get_historical_data(symbol.upper(), period)
        return result
    except Exception as e:
        logger.error(f"Historical stock data API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Historical data service error: {str(e)}")


@router.get("/stocks/search")
async def search_stocks(
    query: str = Query(..., description="Search query for stocks")
) -> Dict[str, Any]:
    """Search for stocks by company name or symbol."""
    try:
        result = await stock_service.search_stocks(query)
        return result
    except Exception as e:
        logger.error(f"Stock search API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Stock search service error: {str(e)}")


@router.get("/sentiment/stock")
async def analyze_stock_sentiment(
    symbol: str = Query(..., description="Stock symbol"),
    timeframe: str = Query("24h", description="Time period (1h, 24h, 7d, 30d)")
) -> Dict[str, Any]:
    """Analyze sentiment for a specific stock."""
    try:
        result = await sentiment_service.analyze_stock_sentiment(symbol.upper(), timeframe)
        return result
    except Exception as e:
        logger.error(f"Stock sentiment API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sentiment analysis service error: {str(e)}")


@router.get("/sentiment/market")
async def analyze_market_sentiment(
    timeframe: str = Query("24h", description="Time period for analysis")
) -> Dict[str, Any]:
    """Analyze overall market sentiment."""
    try:
        result = await sentiment_service.analyze_market_sentiment(timeframe)
        return result
    except Exception as e:
        logger.error(f"Market sentiment API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Market sentiment service error: {str(e)}")


@router.get("/sentiment/topic")
async def analyze_topic_sentiment(
    topic: str = Query(..., description="Topic or keyword to analyze"),
    timeframe: str = Query("24h", description="Time period for analysis")
) -> Dict[str, Any]:
    """Analyze sentiment for a specific topic."""
    try:
        result = await sentiment_service.analyze_topic_sentiment(topic, timeframe)
        return result
    except Exception as e:
        logger.error(f"Topic sentiment API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Topic sentiment service error: {str(e)}")


@router.get("/sentiment/trending")
async def get_trending_sentiment(
    limit: int = Query(10, ge=1, le=20, description="Number of trending topics")
) -> Dict[str, Any]:
    """Get trending topics with sentiment analysis."""
    try:
        result = await sentiment_service.get_trending_sentiment(limit)
        return result
    except Exception as e:
        logger.error(f"Trending sentiment API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Trending sentiment service error: {str(e)}")


@router.get("/plugins/list")
async def list_plugins() -> Dict[str, Any]:
    """List all available plugins."""
    try:
        result = plugin_manager.get_plugin_info()
        return result
    except Exception as e:
        logger.error(f"Plugin list API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Plugin service error: {str(e)}")


@router.get("/plugins/{plugin_name}/info")
async def get_plugin_info(plugin_name: str) -> Dict[str, Any]:
    """Get information about a specific plugin."""
    try:
        result = plugin_manager.get_plugin_info(plugin_name)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Plugin info API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Plugin service error: {str(e)}")


@router.post("/plugins/{plugin_name}/execute")
async def execute_plugin(
    plugin_name: str,
    operation: str = Query(..., description="Operation to execute"),
    query: str = Query(..., description="Query or data for the operation")
) -> Dict[str, Any]:
    """Execute an operation on a specific plugin."""
    try:
        result = await plugin_manager.execute_plugin(plugin_name, operation, query)
        return result
    except Exception as e:
        logger.error(f"Plugin execution API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Plugin execution error: {str(e)}")


@router.post("/plugins/execute-all")
async def execute_all_plugins(
    operation: str = Query(..., description="Operation to execute"),
    query: str = Query(..., description="Query or data for the operation")
) -> Dict[str, Any]:
    """Execute an operation on all available plugins."""
    try:
        result = await plugin_manager.execute_all_plugins(operation, query)
        return result
    except Exception as e:
        logger.error(f"Plugin execution API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Plugin execution error: {str(e)}")


@router.get("/unified/context")
async def get_enhanced_context(
    query: str = Query(..., description="Query to analyze for context"),
    context_types: Optional[List[str]] = Query(None, description="Specific context types to fetch")
) -> Dict[str, Any]:
    """Get enhanced context by analyzing query and fetching relevant data from multiple sources."""
    try:
        result = await unified_service.get_enhanced_context(query, context_types)
        return result
    except Exception as e:
        logger.error(f"Enhanced context API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Enhanced context service error: {str(e)}")


@router.get("/unified/search")
async def search_all_sources(
    query: str = Query(..., description="Search query"),
    sources: Optional[List[str]] = Query(None, description="Specific sources to search"),
    limit_per_source: int = Query(5, ge=1, le=10, description="Results per source")
) -> Dict[str, Any]:
    """Search across all available data sources."""
    try:
        result = await unified_service.search_all_sources(query, sources, limit_per_source)
        return result
    except Exception as e:
        logger.error(f"Unified search API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unified search service error: {str(e)}")


@router.get("/unified/market-overview")
async def get_unified_market_overview() -> Dict[str, Any]:
    """Get comprehensive market overview from multiple sources."""
    try:
        result = await unified_service.get_market_overview()
        return result
    except Exception as e:
        logger.error(f"Unified market overview API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unified market service error: {str(e)}")


@router.get("/health")
async def get_all_services_health() -> Dict[str, Any]:
    """Get health status of all external API services."""
    try:
        result = await unified_service.get_service_health()
        return result
    except Exception as e:
        logger.error(f"Health check API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check service error: {str(e)}")


@router.get("/plugins/health")
async def get_plugins_health() -> Dict[str, Any]:
    """Get health status of all plugins."""
    try:
        result = await plugin_manager.health_check_all_plugins()
        return result
    except Exception as e:
        logger.error(f"Plugin health check API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Plugin health check error: {str(e)}")


# Convenience endpoints for common use cases

@router.get("/quick/weather")
async def quick_weather(
    location: str = Query(..., description="Location for weather")
) -> Dict[str, Any]:
    """Quick weather endpoint with current conditions and forecast."""
    try:
        current_task = weather_service.get_current_weather(location)
        forecast_task = weather_service.get_weather_forecast(location, 3)
        
        current, forecast = await asyncio.gather(current_task, forecast_task, return_exceptions=True)
        
        result = {"location": location}
        
        if not isinstance(current, Exception) and "error" not in current:
            result["current"] = current
        
        if not isinstance(forecast, Exception) and "error" not in forecast:
            result["forecast"] = forecast
        
        return result
    except Exception as e:
        logger.error(f"Quick weather API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Quick weather service error: {str(e)}")


@router.get("/quick/stock")
async def quick_stock(
    symbol: str = Query(..., description="Stock symbol")
) -> Dict[str, Any]:
    """Quick stock endpoint with quote and company info."""
    try:
        quote_task = stock_service.get_stock_quote(symbol.upper())
        info_task = stock_service.get_company_info(symbol.upper())
        
        quote, info = await asyncio.gather(quote_task, info_task, return_exceptions=True)
        
        result = {"symbol": symbol.upper()}
        
        if not isinstance(quote, Exception) and "error" not in quote:
            result["quote"] = quote
        
        if not isinstance(info, Exception) and "error" not in info:
            result["company_info"] = info
        
        return result
    except Exception as e:
        logger.error(f"Quick stock API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Quick stock service error: {str(e)}")


@router.get("/quick/sentiment")
async def quick_sentiment(
    query: str = Query(..., description="Topic or symbol for sentiment analysis")
) -> Dict[str, Any]:
    """Quick sentiment analysis for any topic or stock."""
    try:
        # Determine if it's a stock symbol or general topic
        if len(query) <= 5 and query.isupper():
            # Likely a stock symbol
            result = await sentiment_service.analyze_stock_sentiment(query)
        else:
            # General topic
            result = await sentiment_service.analyze_topic_sentiment(query)
        
        return result
    except Exception as e:
        logger.error(f"Quick sentiment API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Quick sentiment service error: {str(e)}")


import asyncio  # Import needed for gather operations

# =============================================================================
# Groq Compound Model Endpoints
# =============================================================================

@router.get("/groq-compound/status")
async def get_groq_compound_status() -> Dict[str, Any]:
    """Get status of Groq compound model service."""
    try:
        return {
            "available": groq_compound_service.is_available(),
            "model": groq_compound_service.compound_model,
            "timeout": groq_compound_service.timeout,
            "max_retries": groq_compound_service.max_retries
        }
    except Exception as e:
        logger.error(f"Groq compound status error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Groq compound service error: {str(e)}")


@router.post("/groq-compound/analyze-url")
async def analyze_url_with_compound(
    url: str = Query(..., description="URL to analyze"),
    question: Optional[str] = Query(None, description="Specific question about the URL")
) -> Dict[str, Any]:
    """Analyze a URL using Groq's compound model."""
    try:
        if not groq_compound_service.is_available():
            raise HTTPException(status_code=503, detail="Groq compound model service not available")
        
        # Create message with URL
        if question:
            message = f"{question} URL: {url}"
        else:
            message = f"Please analyze and summarize the content of this URL: {url}"
        
        # Generate response
        response_content = ""
        async for chunk in groq_compound_service.generate_response_with_urls(
            message=message,
            stream=False
        ):
            response_content += chunk
        
        return {
            "url": url,
            "question": question,
            "analysis": response_content,
            "model": groq_compound_service.compound_model
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Groq compound URL analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"URL analysis error: {str(e)}")


@router.post("/groq-compound/extract-website-data")
async def extract_website_data(
    message: str = Query(..., description="Message containing URLs to extract data from"),
    urls: Optional[List[str]] = Query(None, description="Specific URLs to analyze (optional)")
) -> Dict[str, Any]:
    """Extract website data using Groq compound model for use by other AI models."""
    try:
        if not groq_compound_service.is_available():
            raise HTTPException(status_code=503, detail="Groq compound model service not available")
        
        # Extract website data
        result = await groq_compound_service.extract_website_data(message, urls)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Website data extraction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Extraction error: {str(e)}")


@router.post("/groq-compound/chat-with-urls")
async def chat_with_urls(
    message: str = Query(..., description="Message that may contain URLs"),
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """Chat with Groq compound model, automatically detecting and processing URLs (Legacy endpoint)."""
    try:
        if not groq_compound_service.is_available():
            raise HTTPException(status_code=503, detail="Groq compound model service not available")
        
        # Check if message should use compound model
        should_use_compound = groq_compound_service.should_use_compound_model(message)
        detected_urls = groq_compound_service.detect_urls_in_message(message)
        
        if not should_use_compound:
            return {
                "message": message,
                "should_use_compound": False,
                "detected_urls": detected_urls,
                "response": "No URLs detected or compound model not needed for this query.",
                "note": "Consider using the hybrid approach via /api/chat/conversations endpoint"
            }
        
        # Generate response using compound model
        response_content = ""
        async for chunk in groq_compound_service.generate_response_with_urls(
            message=message,
            conversation_history=conversation_history or [],
            stream=False
        ):
            response_content += chunk
        
        return {
            "message": message,
            "should_use_compound": True,
            "detected_urls": detected_urls,
            "response": response_content,
            "model": groq_compound_service.compound_model,
            "note": "This is direct compound model usage. Consider using hybrid approach for better results."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Groq compound chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.post("/groq-compound/test")
async def test_groq_compound(
    test_url: str = Query("https://groq.com", description="URL to test with")
) -> Dict[str, Any]:
    """Test Groq compound model functionality."""
    try:
        result = await groq_compound_service.test_compound_model(test_url)
        return result
    except Exception as e:
        logger.error(f"Groq compound test error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")


@router.post("/groq-compound/hybrid-chat")
async def hybrid_chat(
    message: str = Query(..., description="User message"),
    primary_model: str = Query("openai/gpt-oss-120b", description="Primary AI model to use for response"),
    conversation_history: Optional[List[Dict[str, str]]] = None,
    user_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Hybrid approach: Use Groq compound for website data extraction + Primary AI model for response.
    This is the recommended way to handle URL-based queries.
    """
    try:
        from app.enhanced_chat_service import EnhancedChatService
        
        chat_service = EnhancedChatService()
        
        # Set default user context
        if not user_context:
            user_context = {
                "user_id": "api_user",
                "username": "api_user", 
                "is_authenticated": True
            }
        
        # Generate response using hybrid approach
        response_content = ""
        metadata = {
            "primary_model": primary_model,
            "used_compound_for_data": False,
            "urls_detected": [],
            "processing_steps": []
        }
        
        async for chunk in chat_service.generate_ai_response(
            message=message,
            model_id=primary_model,
            conversation_history=conversation_history,
            user_context=user_context
        ):
            response_content += chunk
            
            # Track processing steps
            if "🌐" in chunk:
                metadata["used_compound_for_data"] = True
                metadata["processing_steps"].append("website_analysis_started")
            elif "✅ Website analysis complete" in chunk:
                metadata["processing_steps"].append("website_analysis_completed")
        
        # Detect URLs for metadata
        urls = groq_compound_service.detect_urls_in_message(message)
        metadata["urls_detected"] = urls
        
        return {
            "message": message,
            "response": response_content,
            "metadata": metadata,
            "approach": "hybrid",
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Hybrid chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Hybrid chat error: {str(e)}")


@router.get("/groq-compound/detect-urls")
async def detect_urls_in_text(
    text: str = Query(..., description="Text to analyze for URLs")
) -> Dict[str, Any]:
    """Detect URLs in a given text."""
    try:
        urls = groq_compound_service.detect_urls_in_message(text)
        should_use_compound = groq_compound_service.should_use_compound_model(text)
        
        return {
            "text": text,
            "detected_urls": urls,
            "should_use_compound": should_use_compound,
            "url_count": len(urls),
            "recommendation": "Use /hybrid-chat endpoint for best results with URLs"
        }
        
    except Exception as e:
        logger.error(f"URL detection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"URL detection error: {str(e)}")