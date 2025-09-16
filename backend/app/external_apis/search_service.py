import asyncio
from typing import List, Dict, Any, Optional, Literal
from enum import Enum
import logging
from app.config import settings
from .serpapi import SerpAPIService
from .brave_search import BraveSearchService

logger = logging.getLogger(__name__)


class SearchProvider(Enum):
    """Available search providers."""
    SERPAPI = "serpapi"
    BRAVE = "brave"
    AUTO = "auto"


class SearchService:
    """
    Unified search service that routes between SerpAPI and Brave Search.
    Provides intelligent fallback and load balancing between providers.
    """
    
    def __init__(self):
        self.serpapi = SerpAPIService()
        self.brave = BraveSearchService()
        
        # Provider priority: SerpAPI first, then Brave Search
        self._provider_priority = [
            (SearchProvider.SERPAPI, self.serpapi),
            (SearchProvider.BRAVE, self.brave)
        ]
        
        # Track provider health and performance
        self._provider_health = {}
        self._provider_response_times = {}
        
    async def search_web(
        self, 
        query: str, 
        count: int = 10, 
        provider: SearchProvider = SearchProvider.AUTO,
        location: str = "United States"
    ) -> List[Dict[str, Any]]:
        """
        Perform web search with automatic provider selection and fallback.
        
        Args:
            query: Search query string
            count: Number of results to return
            provider: Specific provider to use, or AUTO for intelligent routing
            location: Geographic location for search
            
        Returns:
            List of search results with unified format
        """
        if not query.strip():
            logger.warning("Empty search query provided")
            return []
        
        # Determine which provider(s) to use
        providers_to_try = self._get_providers_to_try(provider, "web")
        
        for provider_enum, service in providers_to_try:
            try:
                logger.info(f"Attempting web search with {provider_enum.value} for query: {query}")
                
                # Measure response time
                import time
                start_time = time.time()
                
                if provider_enum == SearchProvider.SERPAPI:
                    results = await service.search_web(query, count, location)
                else:  # Brave Search
                    results = await service.search_web(query, count)
                
                response_time = time.time() - start_time
                self._update_provider_metrics(provider_enum, response_time, success=True)
                
                if results:
                    # Add provider metadata to results
                    for result in results:
                        result["provider"] = provider_enum.value
                        result["response_time"] = response_time
                    
                    logger.info(f"Web search successful with {provider_enum.value}: {len(results)} results")
                    return results
                else:
                    logger.warning(f"No results from {provider_enum.value} for query: {query}")
                    
            except Exception as e:
                logger.error(f"Web search failed with {provider_enum.value}: {str(e)}")
                self._update_provider_metrics(provider_enum, 0, success=False)
                continue
        
        logger.error(f"All web search providers failed for query: {query}")
        return []
    
    async def search_news(
        self, 
        query: str, 
        count: int = 5, 
        provider: SearchProvider = SearchProvider.AUTO,
        time_period: str = "1d"
    ) -> List[Dict[str, Any]]:
        """
        Perform news search with automatic provider selection and fallback.
        
        Args:
            query: Search query string
            count: Number of results to return
            provider: Specific provider to use, or AUTO for intelligent routing
            time_period: Time period for news (1h, 1d, 1w, 1m, 1y)
            
        Returns:
            List of news results with unified format
        """
        if not query.strip():
            logger.warning("Empty news search query provided")
            return []
        
        # Determine which provider(s) to use
        providers_to_try = self._get_providers_to_try(provider, "news")
        
        for provider_enum, service in providers_to_try:
            try:
                logger.info(f"Attempting news search with {provider_enum.value} for query: {query}")
                
                # Measure response time
                import time
                start_time = time.time()
                
                if provider_enum == SearchProvider.SERPAPI:
                    results = await service.search_news(query, count, time_period)
                else:  # Brave Search
                    # Map time periods for Brave Search
                    brave_time_map = {
                        "1h": "pd",  # Brave doesn't have hourly, use daily
                        "1d": "pd",
                        "1w": "pw", 
                        "1m": "pm",
                        "1y": "py"
                    }
                    brave_time = brave_time_map.get(time_period, "pd")
                    results = await service.search_news(query, count, brave_time)
                
                response_time = time.time() - start_time
                self._update_provider_metrics(provider_enum, response_time, success=True)
                
                if results:
                    # Add provider metadata to results
                    for result in results:
                        result["provider"] = provider_enum.value
                        result["response_time"] = response_time
                    
                    logger.info(f"News search successful with {provider_enum.value}: {len(results)} results")
                    return results
                else:
                    logger.warning(f"No news results from {provider_enum.value} for query: {query}")
                    
            except Exception as e:
                logger.error(f"News search failed with {provider_enum.value}: {str(e)}")
                self._update_provider_metrics(provider_enum, 0, success=False)
                continue
        
        logger.error(f"All news search providers failed for query: {query}")
        return []
    
    async def search_combined(
        self, 
        query: str, 
        web_count: int = 8, 
        news_count: int = 3,
        provider: SearchProvider = SearchProvider.AUTO
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Perform combined web and news search.
        
        Args:
            query: Search query string
            web_count: Number of web results to return
            news_count: Number of news results to return
            provider: Specific provider to use, or AUTO for intelligent routing
            
        Returns:
            Dictionary with 'web' and 'news' keys containing respective results
        """
        # Run web and news searches concurrently
        web_task = asyncio.create_task(
            self.search_web(query, web_count, provider)
        )
        news_task = asyncio.create_task(
            self.search_news(query, news_count, provider)
        )
        
        web_results, news_results = await asyncio.gather(
            web_task, news_task, return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(web_results, Exception):
            logger.error(f"Web search failed: {web_results}")
            web_results = []
        
        if isinstance(news_results, Exception):
            logger.error(f"News search failed: {news_results}")
            news_results = []
        
        return {
            "web": web_results,
            "news": news_results,
            "total_results": len(web_results) + len(news_results)
        }
    
    def _get_providers_to_try(self, requested_provider: SearchProvider, search_type: str) -> List[tuple]:
        """
        Determine which providers to try based on availability and health.
        
        Args:
            requested_provider: The requested provider
            search_type: Type of search ("web" or "news")
            
        Returns:
            List of (provider_enum, service) tuples in order of preference
        """
        if requested_provider != SearchProvider.AUTO:
            # Use specific provider if requested
            for provider_enum, service in self._provider_priority:
                if provider_enum == requested_provider and service.is_available():
                    return [(provider_enum, service)]
            
            logger.warning(f"Requested provider {requested_provider.value} not available")
            return []
        
        # Auto selection: use all available providers in priority order
        available_providers = []
        
        for provider_enum, service in self._provider_priority:
            if service.is_available():
                # Check provider health
                health = self._provider_health.get(provider_enum, {"healthy": True, "failures": 0})
                
                # Skip providers with too many recent failures
                if health["failures"] < 3:
                    available_providers.append((provider_enum, service))
                else:
                    logger.warning(f"Skipping {provider_enum.value} due to recent failures")
        
        if not available_providers:
            logger.error("No search providers available")
        
        return available_providers
    
    def _update_provider_metrics(self, provider: SearchProvider, response_time: float, success: bool):
        """Update provider health and performance metrics."""
        # Update health tracking
        if provider not in self._provider_health:
            self._provider_health[provider] = {"healthy": True, "failures": 0, "last_success": None}
        
        health = self._provider_health[provider]
        
        if success:
            health["failures"] = max(0, health["failures"] - 1)  # Reduce failure count on success
            health["last_success"] = asyncio.get_event_loop().time()
            health["healthy"] = True
        else:
            health["failures"] += 1
            if health["failures"] >= 3:
                health["healthy"] = False
        
        # Update response time tracking
        if provider not in self._provider_response_times:
            self._provider_response_times[provider] = []
        
        if success and response_time > 0:
            times = self._provider_response_times[provider]
            times.append(response_time)
            
            # Keep only last 10 response times
            if len(times) > 10:
                times.pop(0)
    
    async def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all search providers."""
        status = {
            "providers": {},
            "recommended": None
        }
        
        # Check each provider
        for provider_enum, service in self._provider_priority:
            provider_name = provider_enum.value
            
            # Get basic availability
            is_available = service.is_available()
            
            # Get health metrics
            health = self._provider_health.get(provider_enum, {"healthy": True, "failures": 0})
            response_times = self._provider_response_times.get(provider_enum, [])
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Perform health check if available
            health_check = None
            if is_available:
                try:
                    health_check = await service.health_check()
                except Exception as e:
                    health_check = {
                        "status": "error",
                        "message": f"Health check failed: {str(e)}",
                        "service": provider_name
                    }
            
            status["providers"][provider_name] = {
                "available": is_available,
                "healthy": health["healthy"],
                "failures": health["failures"],
                "avg_response_time": round(avg_response_time, 3),
                "health_check": health_check
            }
        
        # Determine recommended provider
        for provider_enum, service in self._provider_priority:
            if (service.is_available() and 
                self._provider_health.get(provider_enum, {"healthy": True})["healthy"]):
                status["recommended"] = provider_enum.value
                break
        
        return status
    
    async def reset_provider_health(self, provider: Optional[SearchProvider] = None):
        """Reset health metrics for a specific provider or all providers."""
        if provider:
            if provider in self._provider_health:
                self._provider_health[provider] = {"healthy": True, "failures": 0}
                logger.info(f"Reset health metrics for {provider.value}")
        else:
            self._provider_health.clear()
            self._provider_response_times.clear()
            logger.info("Reset health metrics for all providers")


# Global search service instance
search_service = SearchService()