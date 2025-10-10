import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from app.config import settings
from .search_service import SearchService, SearchProvider
from .binance import BinanceService
from .weather import WeatherService
from .stocks import StockService
from .sentiment import SentimentAnalysisService
from .plugin_system import PluginManager, plugin_manager
from ..core.error_handling import (
    retry_with_backoff, RetryConfig, ServiceType, ErrorCode, ErrorSeverity, error_metrics
)
from ..core.logging_middleware import external_api_logger

logger = logging.getLogger(__name__)


class UnifiedExternalAPIService:
    """
    Unified service that orchestrates all external API integrations.
    Provides a single interface for accessing weather, stocks, sentiment, search, crypto, and plugin data.
    """
    
    def __init__(self):
        # Initialize all services
        self.search_service = SearchService()
        self.crypto_service = BinanceService()
        self.weather_service = WeatherService()
        self.stock_service = StockService()
        self.sentiment_service = SentimentAnalysisService()
        self.plugin_manager = plugin_manager
        
        # Service registry for dynamic access
        self.services = {
            "search": self.search_service,
            "crypto": self.crypto_service,
            "weather": self.weather_service,
            "stocks": self.stock_service,
            "sentiment": self.sentiment_service,
            "plugins": self.plugin_manager
        }
        
        logger.info("Unified External API Service initialized")
    
    async def get_enhanced_context(self, query: str, context_types: List[str] = None) -> Dict[str, Any]:
        """
        Get enhanced context by analyzing the query and fetching relevant data from multiple sources.
        
        Args:
            query: The user query to analyze
            context_types: Specific context types to fetch, or None for auto-detection
            
        Returns:
            Dictionary containing context data from various sources
        """
        if context_types is None:
            context_types = self._detect_context_types(query)
        
        context = {
            "query": query,
            "detected_types": context_types,
            "timestamp": datetime.now().isoformat()
        }
        
        # Fetch data from relevant sources concurrently
        tasks = []
        
        if "web_search" in context_types:
            tasks.append(self._fetch_web_search_context(query))
        
        if "crypto" in context_types:
            tasks.append(self._fetch_crypto_context(query))
        
        if "weather" in context_types:
            tasks.append(self._fetch_weather_context(query))
        
        if "stocks" in context_types:
            tasks.append(self._fetch_stock_context(query))
        
        if "sentiment" in context_types:
            tasks.append(self._fetch_sentiment_context(query))
        
        if "plugins" in context_types:
            tasks.append(self._fetch_plugin_context(query))
        
        # Execute all tasks concurrently
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Context fetch failed: {str(result)}")
                    continue
                
                if result:
                    context.update(result)
        
        return context
    
    async def search_all_sources(
        self, 
        query: str, 
        sources: List[str] = None,
        limit_per_source: int = 5
    ) -> Dict[str, Any]:
        """
        Search across all available data sources.
        
        Args:
            query: Search query
            sources: Specific sources to search, or None for all
            limit_per_source: Maximum results per source
            
        Returns:
            Combined search results from all sources
        """
        if sources is None:
            sources = ["web", "news", "stocks", "crypto", "weather", "sentiment", "plugins"]
        
        results = {
            "query": query,
            "sources_searched": sources,
            "timestamp": datetime.now().isoformat()
        }
        
        # Search tasks
        tasks = []
        
        if "web" in sources:
            tasks.append(self._search_web(query, limit_per_source))
        
        if "news" in sources:
            tasks.append(self._search_news(query, limit_per_source))
        
        if "stocks" in sources:
            tasks.append(self._search_stocks(query, limit_per_source))
        
        if "crypto" in sources:
            tasks.append(self._search_crypto(query))
        
        if "weather" in sources:
            tasks.append(self._search_weather(query))
        
        if "sentiment" in sources:
            tasks.append(self._search_sentiment(query))
        
        if "plugins" in sources:
            tasks.append(self._search_plugins(query, limit_per_source))
        
        # Execute searches concurrently
        if tasks:
            search_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process and combine results
            for i, result in enumerate(search_results):
                if isinstance(result, Exception):
                    logger.error(f"Search failed for source {sources[i]}: {str(result)}")
                    continue
                
                if result:
                    results.update(result)
        
        return results
    
    async def get_market_overview(self) -> Dict[str, Any]:
        """
        Get comprehensive market overview including stocks, crypto, and sentiment.
        
        Returns:
            Combined market data from multiple sources
        """
        overview = {
            "timestamp": datetime.now().isoformat(),
            "market_status": "open"  # This could be determined dynamically
        }
        
        # Fetch market data concurrently
        tasks = [
            self.stock_service.get_market_overview(),
            self.crypto_service.get_market_data(),
            self.sentiment_service.analyze_market_sentiment()
        ]
        
        try:
            stock_data, crypto_data, sentiment_data = await asyncio.gather(
                *tasks, return_exceptions=True
            )
            
            # Process stock data
            if not isinstance(stock_data, Exception) and "error" not in stock_data:
                overview["stocks"] = stock_data
            
            # Process crypto data
            if not isinstance(crypto_data, Exception) and "error" not in crypto_data:
                overview["crypto"] = crypto_data
            
            # Process sentiment data
            if not isinstance(sentiment_data, Exception) and "error" not in sentiment_data:
                overview["sentiment"] = sentiment_data
            
            return overview
        
        except Exception as e:
            logger.error(f"Market overview fetch failed: {str(e)}")
            return {"error": f"Failed to fetch market overview: {str(e)}"}
    
    async def get_service_health(self) -> Dict[str, Any]:
        """
        Get health status of all external API services.
        
        Returns:
            Health status for all services
        """
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "services": {}
        }
        
        # Health check tasks
        health_tasks = [
            ("search", self.search_service.get_service_health()),
            ("crypto", self.crypto_service.health_check()),
            ("weather", self.weather_service.health_check()),
            ("stocks", self.stock_service.health_check()),
            ("sentiment", self.sentiment_service.health_check()),
            ("plugins", self.plugin_manager.health_check_all_plugins())
        ]
        
        # Execute health checks concurrently
        for service_name, task in health_tasks:
            try:
                health_result = await task
                health_status["services"][service_name] = health_result
            except Exception as e:
                health_status["services"][service_name] = {
                    "status": "error",
                    "message": f"Health check failed: {str(e)}",
                    "service": service_name
                }
        
        # Calculate overall health
        healthy_services = sum(
            1 for service in health_status["services"].values()
            if isinstance(service, dict) and service.get("status") == "healthy"
        )
        total_services = len(health_status["services"])
        
        if healthy_services == total_services:
            overall_status = "healthy"
        elif healthy_services > total_services // 2:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        health_status["overall_status"] = overall_status
        health_status["healthy_services"] = healthy_services
        health_status["total_services"] = total_services
        
        return health_status
    
    def _detect_context_types(self, query: str) -> List[str]:
        """
        Analyze query to detect what types of context data would be relevant.
        
        Args:
            query: User query to analyze
            
        Returns:
            List of relevant context types
        """
        query_lower = query.lower()
        context_types = []
        
        # Weather keywords
        weather_keywords = [
            "weather", "temperature", "rain", "snow", "sunny", "cloudy",
            "forecast", "climate", "humidity", "wind", "storm"
        ]
        if any(keyword in query_lower for keyword in weather_keywords):
            context_types.append("weather")
        
        # Stock keywords
        stock_keywords = [
            "stock", "share", "nasdaq", "s&p", "dow", "market", "trading",
            "earnings", "dividend", "ipo", "ticker", "equity"
        ]
        if any(keyword in query_lower for keyword in stock_keywords):
            context_types.append("stocks")
        
        # Crypto keywords
        crypto_keywords = [
            "bitcoin", "ethereum", "crypto", "cryptocurrency", "btc", "eth",
            "blockchain", "defi", "nft", "altcoin", "binance"
        ]
        if any(keyword in query_lower for keyword in crypto_keywords):
            context_types.append("crypto")
        
        # Sentiment keywords
        sentiment_keywords = [
            "sentiment", "opinion", "feeling", "mood", "bullish", "bearish",
            "positive", "negative", "trending", "social"
        ]
        if any(keyword in query_lower for keyword in sentiment_keywords):
            context_types.append("sentiment")
        
        # Current events / news keywords
        news_keywords = [
            "news", "latest", "recent", "today", "current", "breaking",
            "update", "happening", "trend"
        ]
        if any(keyword in query_lower for keyword in news_keywords):
            context_types.append("web_search")
        
        # If no specific context detected, use web search as default
        if not context_types:
            context_types.append("web_search")
        
        # Always include plugins for additional data sources
        context_types.append("plugins")
        
        return context_types
    
    async def _fetch_web_search_context(self, query: str) -> Dict[str, Any]:
        """Fetch web search context."""
        try:
            logger.info(f"Fetching web search context for: {query}")
            web_results = await self.search_service.search_web(query, count=5)
            news_results = await self.search_service.search_news(query, count=3)
            
            # Ensure results are lists
            if web_results is None:
                web_results = []
            if news_results is None:
                news_results = []
            
            logger.info(f"Web search results: {len(web_results)} web, {len(news_results)} news")
            
            return {
                "web_search": {
                    "web_results": web_results,
                    "news_results": news_results,
                    "total_results": len(web_results) + len(news_results)
                }
            }
        except Exception as e:
            logger.error(f"Web search context fetch failed: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {}
    
    async def _fetch_crypto_context(self, query: str) -> Dict[str, Any]:
        """Fetch cryptocurrency context."""
        try:
            # Extract potential crypto symbols from query
            crypto_symbols = self._extract_crypto_symbols(query)
            
            if crypto_symbols:
                market_data = await self.crypto_service.get_market_data(crypto_symbols)
            else:
                market_data = await self.crypto_service.get_market_data()
            
            return {"crypto": market_data}
        except Exception as e:
            logger.error(f"Crypto context fetch failed: {str(e)}")
            return {}
    
    async def _fetch_weather_context(self, query: str) -> Dict[str, Any]:
        """Fetch weather context."""
        try:
            # Extract location from query
            location = self._extract_location(query)
            
            if location:
                weather_data = await self.weather_service.get_current_weather(location)
                return {"weather": weather_data}
            else:
                return {"weather": {"error": "No location detected in query"}}
        except Exception as e:
            logger.error(f"Weather context fetch failed: {str(e)}")
            return {}
    
    async def _fetch_stock_context(self, query: str) -> Dict[str, Any]:
        """Fetch stock market context."""
        try:
            # Extract potential stock symbols from query
            stock_symbols = self._extract_stock_symbols(query)
            
            if stock_symbols:
                stock_data = {}
                for symbol in stock_symbols[:3]:  # Limit to 3 symbols
                    quote = await self.stock_service.get_stock_quote(symbol)
                    if "error" not in quote:
                        stock_data[symbol] = quote
                
                return {"stocks": stock_data}
            else:
                market_overview = await self.stock_service.get_market_overview()
                return {"stocks": market_overview}
        except Exception as e:
            logger.error(f"Stock context fetch failed: {str(e)}")
            return {}
    
    async def _fetch_sentiment_context(self, query: str) -> Dict[str, Any]:
        """Fetch sentiment analysis context."""
        try:
            sentiment_data = await self.sentiment_service.analyze_topic_sentiment(query)
            return {"sentiment": sentiment_data}
        except Exception as e:
            logger.error(f"Sentiment context fetch failed: {str(e)}")
            return {}
    
    async def _fetch_plugin_context(self, query: str) -> Dict[str, Any]:
        """Fetch context from plugins."""
        try:
            plugin_results = await self.plugin_manager.execute_all_plugins("fetch_data", query, limit=3)
            return {"plugins": plugin_results}
        except Exception as e:
            logger.error(f"Plugin context fetch failed: {str(e)}")
            return {}
    
    async def _search_web(self, query: str, limit: int) -> Dict[str, Any]:
        """Search web sources."""
        try:
            results = await self.search_service.search_web(query, count=limit)
            return {"web": results}
        except Exception as e:
            return {"web": {"error": str(e)}}
    
    async def _search_news(self, query: str, limit: int) -> Dict[str, Any]:
        """Search news sources."""
        try:
            results = await self.search_service.search_news(query, count=limit)
            return {"news": results}
        except Exception as e:
            return {"news": {"error": str(e)}}
    
    async def _search_stocks(self, query: str, limit: int) -> Dict[str, Any]:
        """Search stock data."""
        try:
            results = await self.stock_service.search_stocks(query)
            return {"stocks": results}
        except Exception as e:
            return {"stocks": {"error": str(e)}}
    
    async def _search_crypto(self, query: str) -> Dict[str, Any]:
        """Search crypto data."""
        try:
            symbols = self._extract_crypto_symbols(query)
            if symbols:
                results = await self.crypto_service.get_market_data(symbols)
            else:
                results = await self.crypto_service.get_market_data()
            return {"crypto": results}
        except Exception as e:
            return {"crypto": {"error": str(e)}}
    
    async def _search_weather(self, query: str) -> Dict[str, Any]:
        """Search weather data."""
        try:
            location = self._extract_location(query)
            if location:
                results = await self.weather_service.get_current_weather(location)
            else:
                results = {"error": "No location detected"}
            return {"weather": results}
        except Exception as e:
            return {"weather": {"error": str(e)}}
    
    async def _search_sentiment(self, query: str) -> Dict[str, Any]:
        """Search sentiment data."""
        try:
            results = await self.sentiment_service.analyze_topic_sentiment(query)
            return {"sentiment": results}
        except Exception as e:
            return {"sentiment": {"error": str(e)}}
    
    async def _search_plugins(self, query: str, limit: int) -> Dict[str, Any]:
        """Search plugin data."""
        try:
            results = await self.plugin_manager.execute_all_plugins("fetch_data", query, limit=limit)
            return {"plugins": results}
        except Exception as e:
            return {"plugins": {"error": str(e)}}
    
    def _extract_crypto_symbols(self, query: str) -> List[str]:
        """Extract cryptocurrency symbols from query."""
        query_upper = query.upper()
        common_symbols = ["BTC", "ETH", "BNB", "ADA", "SOL", "DOT", "LINK", "UNI", "AVAX", "MATIC"]
        
        found_symbols = []
        for symbol in common_symbols:
            if symbol in query_upper or f"{symbol}USDT" in query_upper:
                found_symbols.append(f"{symbol}USDT")
        
        return found_symbols
    
    def _extract_stock_symbols(self, query: str) -> List[str]:
        """Extract stock symbols from query."""
        query_upper = query.upper()
        common_symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "NFLX", "AMD", "INTC"]
        
        found_symbols = []
        for symbol in common_symbols:
            if symbol in query_upper:
                found_symbols.append(symbol)
        
        return found_symbols
    
    def _extract_location(self, query: str) -> Optional[str]:
        """Extract location from query."""
        # Simple location extraction - in a real implementation, you might use NLP
        location_keywords = ["in", "at", "for", "weather in", "temperature in"]
        
        query_lower = query.lower()
        for keyword in location_keywords:
            if keyword in query_lower:
                # Extract text after the keyword
                parts = query_lower.split(keyword, 1)
                if len(parts) > 1:
                    location = parts[1].strip().split()[0:3]  # Take up to 3 words
                    return " ".join(location).title()
        
        # If no keyword found, check for common city names
        common_cities = [
            "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
            "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose",
            "London", "Paris", "Tokyo", "Sydney", "Toronto", "Berlin"
        ]
        
        for city in common_cities:
            if city.lower() in query_lower:
                return city
        
        return None


# Global unified service instance
unified_service = UnifiedExternalAPIService()