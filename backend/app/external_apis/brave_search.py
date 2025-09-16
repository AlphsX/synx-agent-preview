import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class BraveSearchService:
    """
    Brave Search service as fallback option for web search and news search.
    Enhanced with comprehensive error handling and rate limiting.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.BRAVE_SEARCH_API_KEY
        self.base_url = "https://api.search.brave.com/res/v1"
        self.timeout = settings.SEARCH_API_TIMEOUT
        self.max_retries = settings.MAX_RETRIES
        self.retry_delay = settings.RETRY_DELAY
        
        self.headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        } if self.api_key else None
        
        # Rate limiting tracking
        self._request_times = []
        self._max_requests_per_minute = 60  # Brave Search default limit
    
    async def search_web(self, query: str, count: int = 10, country: str = "US", 
                        search_lang: str = "en", ui_lang: str = "en-US") -> List[Dict[str, Any]]:
        """
        Perform web search using Brave Search API.
        
        Args:
            query: Search query string
            count: Number of results to return
            country: Country code for localized results
            search_lang: Language for search
            ui_lang: UI language
            
        Returns:
            List of search results with title, description, url, and metadata
        """
        if not self.api_key:
            logger.warning("Brave Search API key not configured, returning empty results")
            return []
        
        params = {
            "q": query,
            "count": min(count, 20),  # Brave Search max is 20
            "country": country,
            "search_lang": search_lang,
            "ui_lang": ui_lang,
            "safesearch": "moderate",
            "freshness": "pw"  # Past week for recent results
        }
        
        try:
            await self._check_rate_limit()
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                response_data = await self._make_request_with_retry(
                    session, f"{self.base_url}/web/search", params
                )
                
                if not response_data:
                    return []
                
                results = []
                
                # Extract web results
                for result in response_data.get("web", {}).get("results", []):
                    results.append({
                        "title": result.get("title", ""),
                        "description": result.get("description", ""),
                        "url": result.get("url", ""),
                        "published": result.get("published", ""),
                        "source": self._extract_domain(result.get("url", "")),
                        "type": "web"
                    })
                
                # Extract news results if available and requested
                if count > len(results):
                    remaining_count = count - len(results)
                    for result in response_data.get("news", {}).get("results", [])[:remaining_count]:
                        results.append({
                            "title": result.get("title", ""),
                            "description": result.get("description", ""),
                            "url": result.get("url", ""),
                            "published": result.get("age", ""),
                            "source": self._extract_domain(result.get("url", "")),
                            "type": "news"
                        })
                
                logger.info(f"Brave Search web search returned {len(results)} results for query: {query}")
                return results[:count]
                
        except Exception as e:
            logger.error(f"Brave Search web search error for query '{query}': {str(e)}")
            return []
    
    async def search(self, query: str, count: int = 10, country: str = "US", 
                    search_lang: str = "en", ui_lang: str = "en-US") -> List[Dict[str, Any]]:
        """Legacy method for backward compatibility."""
        return await self.search_web(query, count, country, search_lang, ui_lang)
    
    async def search_news(self, query: str, count: int = 5, freshness: str = "pd") -> List[Dict[str, Any]]:
        """
        Search for news using Brave Search API.
        
        Args:
            query: Search query string
            count: Number of results to return
            freshness: Freshness filter (pd=past day, pw=past week, pm=past month)
            
        Returns:
            List of news results with title, description, url, published date, and source
        """
        if not self.api_key:
            logger.warning("Brave Search API key not configured, returning empty results")
            return []
        
        params = {
            "q": query,
            "count": min(count, 20),  # Brave Search max is 20
            "freshness": freshness
        }
        
        try:
            await self._check_rate_limit()
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                response_data = await self._make_request_with_retry(
                    session, f"{self.base_url}/news/search", params
                )
                
                if not response_data:
                    return []
                
                results = []
                
                for result in response_data.get("results", []):
                    results.append({
                        "title": result.get("title", ""),
                        "description": result.get("description", ""),
                        "url": result.get("url", ""),
                        "published": result.get("age", ""),
                        "source": result.get("meta_url", {}).get("hostname", ""),
                        "type": "news"
                    })
                
                logger.info(f"Brave Search news search returned {len(results)} results for query: {query}")
                return results[:count]
                
        except Exception as e:
            logger.error(f"Brave Search news search error for query '{query}': {str(e)}")
            return []
    
    async def _make_request_with_retry(self, session: aiohttp.ClientSession, url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make HTTP request with retry logic and exponential backoff."""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                async with session.get(url, params=params, headers=self.headers) as response:
                    self._track_request_time()
                    
                    if response.status == 200:
                        return await response.json()
                    
                    elif response.status == 429:
                        # Rate limit exceeded
                        logger.warning(f"Brave Search rate limit exceeded, attempt {attempt + 1}")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay * (2 ** attempt))
                            continue
                    
                    elif response.status == 401:
                        logger.error("Brave Search authentication failed - check API key")
                        return None
                    
                    else:
                        logger.error(f"Brave Search request failed with status {response.status}")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay * (2 ** attempt))
                            continue
                    
            except asyncio.TimeoutError:
                last_exception = "Request timeout"
                logger.warning(f"Brave Search request timeout, attempt {attempt + 1}")
            except aiohttp.ClientError as e:
                last_exception = str(e)
                logger.warning(f"Brave Search client error: {e}, attempt {attempt + 1}")
            except Exception as e:
                last_exception = str(e)
                logger.error(f"Unexpected Brave Search error: {e}, attempt {attempt + 1}")
            
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay * (2 ** attempt))
        
        logger.error(f"Brave Search request failed after {self.max_retries} attempts. Last error: {last_exception}")
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
        """Check if Brave Search service is available (has API key)."""
        return bool(self.api_key)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the Brave Search service."""
        if not self.api_key:
            return {
                "status": "unavailable",
                "message": "API key not configured",
                "service": "Brave Search"
            }
        
        try:
            # Make a simple test request
            params = {
                "q": "test",
                "count": 1
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(
                    f"{self.base_url}/web/search", 
                    params=params, 
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        return {
                            "status": "healthy",
                            "message": "Service operational",
                            "service": "Brave Search"
                        }
                    else:
                        return {
                            "status": "error",
                            "message": f"HTTP {response.status}",
                            "service": "Brave Search"
                        }
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Health check failed: {str(e)}",
                "service": "Brave Search"
            }