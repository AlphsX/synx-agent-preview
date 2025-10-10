import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class SerpAPIService:
    """
    SerpAPI service for web search and news search capabilities.
    Provides comprehensive search functionality with rate limiting and error handling.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.SERP_API_KEY
        self.base_url = "https://serpapi.com/search"
        self.timeout = settings.SEARCH_API_TIMEOUT
        self.max_retries = settings.MAX_RETRIES
        self.retry_delay = settings.RETRY_DELAY
        
        # Rate limiting tracking
        self._request_times = []
        self._max_requests_per_minute = 100  # SerpAPI default limit
        
    async def search_web(self, query: str, count: int = 10, location: str = "United States") -> List[Dict[str, Any]]:
        """
        Perform web search using SerpAPI Google Search.
        
        Args:
            query: Search query string
            count: Number of results to return (max 100)
            location: Geographic location for search
            
        Returns:
            List of search results with title, description, url, and metadata
        """
        if not self.api_key:
            logger.warning("SerpAPI key not configured, returning empty results")
            return []
        
        params = {
            "engine": "google",
            "q": query,
            "api_key": self.api_key,
            "num": min(count, 100),  # SerpAPI max is 100
            "location": location,
            "hl": "en",
            "gl": "us",
            "safe": "active"
        }
        
        try:
            await self._check_rate_limit()
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout), connector=aiohttp.TCPConnector(ssl=False)) as session:
                response_data = await self._make_request_with_retry(session, params)
                
                if not response_data:
                    return []
                
                results = []
                
                # Extract organic search results
                for result in response_data.get("organic_results", []):
                    results.append({
                        "title": result.get("title", ""),
                        "description": result.get("snippet", ""),
                        "url": result.get("link", ""),
                        "published": result.get("date", ""),
                        "source": self._extract_domain(result.get("link", "")),
                        "type": "web",
                        "position": result.get("position", 0)
                    })
                
                # Add featured snippet if available
                if "answer_box" in response_data:
                    answer_box = response_data["answer_box"]
                    results.insert(0, {
                        "title": f"Featured: {answer_box.get('title', query)}",
                        "description": answer_box.get("answer", answer_box.get("snippet", "")),
                        "url": answer_box.get("link", ""),
                        "published": "",
                        "source": self._extract_domain(answer_box.get("link", "")),
                        "type": "featured",
                        "position": 0
                    })
                
                logger.info(f"SerpAPI web search returned {len(results)} results for query: {query}")
                return results[:count]
                
        except Exception as e:
            logger.error(f"SerpAPI web search error for query '{query}': {str(e)}")
            return []
    
    async def search_news(self, query: str, count: int = 5, time_period: str = "1d") -> List[Dict[str, Any]]:
        """
        Search for news using SerpAPI Google News.
        
        Args:
            query: Search query string
            count: Number of results to return
            time_period: Time period for news (1h, 1d, 1w, 1m, 1y)
            
        Returns:
            List of news results with title, description, url, published date, and source
        """
        if not self.api_key:
            logger.warning("SerpAPI key not configured, returning empty results")
            return []
        
        params = {
            "engine": "google_news",
            "q": query,
            "api_key": self.api_key,
            "num": min(count, 100),
            "hl": "en",
            "gl": "us",
            "tbm": "nws"
        }
        
        # Add time period filter
        if time_period:
            time_filters = {
                "1h": "qdr:h",
                "1d": "qdr:d", 
                "1w": "qdr:w",
                "1m": "qdr:m",
                "1y": "qdr:y"
            }
            if time_period in time_filters:
                params["tbs"] = time_filters[time_period]
        
        try:
            await self._check_rate_limit()
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout), connector=aiohttp.TCPConnector(ssl=False)) as session:
                response_data = await self._make_request_with_retry(session, params)
                
                if not response_data:
                    return []
                
                results = []
                
                # Extract news results
                for result in response_data.get("news_results", []):
                    results.append({
                        "title": result.get("title", ""),
                        "description": result.get("snippet", ""),
                        "url": result.get("link", ""),
                        "published": result.get("date", ""),
                        "source": result.get("source", ""),
                        "type": "news",
                        "thumbnail": result.get("thumbnail", "")
                    })
                
                logger.info(f"SerpAPI news search returned {len(results)} results for query: {query}")
                return results[:count]
                
        except Exception as e:
            logger.error(f"SerpAPI news search error for query '{query}': {str(e)}")
            return []
    
    async def _make_request_with_retry(self, session: aiohttp.ClientSession, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make HTTP request with retry logic and exponential backoff."""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                async with session.get(self.base_url, params=params) as response:
                    self._track_request_time()
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Check for API errors
                        if "error" in data:
                            logger.error(f"SerpAPI error: {data['error']}")
                            return None
                        
                        return data
                    
                    elif response.status == 429:
                        # Rate limit exceeded
                        logger.warning(f"SerpAPI rate limit exceeded, attempt {attempt + 1}")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay * (2 ** attempt))
                            continue
                    
                    elif response.status == 401:
                        logger.error("SerpAPI authentication failed - check API key")
                        return None
                    
                    else:
                        logger.error(f"SerpAPI request failed with status {response.status}")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay * (2 ** attempt))
                            continue
                    
            except asyncio.TimeoutError:
                last_exception = "Request timeout"
                logger.warning(f"SerpAPI request timeout, attempt {attempt + 1}")
            except aiohttp.ClientError as e:
                last_exception = str(e)
                logger.warning(f"SerpAPI client error: {e}, attempt {attempt + 1}")
            except Exception as e:
                last_exception = str(e)
                logger.error(f"Unexpected SerpAPI error: {e}, attempt {attempt + 1}")
            
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay * (2 ** attempt))
        
        logger.error(f"SerpAPI request failed after {self.max_retries} attempts. Last error: {last_exception}")
        return None
    
    async def _check_rate_limit(self):
        """Check and enforce rate limiting."""
        now = datetime.now()
        
        # Remove requests older than 1 minute
        self._request_times = [
            req_time for req_time in self._request_times 
            if now - req_time < timedelta(minutes=1)
        ]
        
        # Check if we're at the rate limit
        if len(self._request_times) >= self._max_requests_per_minute:
            # Calculate how long to wait
            oldest_request = min(self._request_times)
            wait_time = 60 - (now - oldest_request).total_seconds()
            
            if wait_time > 0:
                logger.warning(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
    
    def _track_request_time(self):
        """Track the time of the current request for rate limiting."""
        self._request_times.append(datetime.now())
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain name from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.replace('www.', '')
        except Exception:
            return ""
    
    def is_available(self) -> bool:
        """Check if SerpAPI service is available (has API key)."""
        return bool(self.api_key)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the SerpAPI service."""
        if not self.api_key:
            return {
                "status": "unavailable",
                "message": "API key not configured",
                "service": "SerpAPI"
            }
        
        try:
            # Make a simple test request
            params = {
                "engine": "google",
                "q": "test",
                "api_key": self.api_key,
                "num": 1
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5), connector=aiohttp.TCPConnector(ssl=False)) as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "error" not in data:
                            return {
                                "status": "healthy",
                                "message": "Service operational",
                                "service": "SerpAPI"
                            }
                        else:
                            return {
                                "status": "error",
                                "message": f"API error: {data['error']}",
                                "service": "SerpAPI"
                            }
                    else:
                        return {
                            "status": "error",
                            "message": f"HTTP {response.status}",
                            "service": "SerpAPI"
                        }
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Health check failed: {str(e)}",
                "service": "SerpAPI"
            }