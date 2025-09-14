import aiohttp
from typing import List, Dict, Any, Optional
from app.config import settings

class BraveSearchService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.BRAVE_SEARCH_API_KEY
        self.base_url = "https://api.search.brave.com/res/v1"
        self.headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        } if self.api_key else None
    
    async def search(self, query: str, count: int = 10, country: str = "US", 
                    search_lang: str = "en", ui_lang: str = "en-US") -> List[Dict[str, Any]]:
        """Perform web search using Brave Search API"""
        
        if not self.api_key:
            return [{"title": "API Key Required", "description": "Brave Search API key not configured", "url": "#"}]
        
        params = {
            "q": query,
            "count": count,
            "country": country,
            "search_lang": search_lang,
            "ui_lang": ui_lang,
            "safesearch": "moderate",
            "freshness": "pw"  # Past week for recent results
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/web/search",
                    params=params,
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        
                        # Extract web results
                        for result in data.get("web", {}).get("results", [])[:count]:
                            results.append({
                                "title": result.get("title", ""),
                                "description": result.get("description", ""),
                                "url": result.get("url", ""),
                                "published": result.get("published", ""),
                                "type": "web"
                            })
                        
                        # Extract news results if available
                        for result in data.get("news", {}).get("results", [])[:3]:
                            results.append({
                                "title": result.get("title", ""),
                                "description": result.get("description", ""),
                                "url": result.get("url", ""),
                                "published": result.get("age", ""),
                                "type": "news"
                            })
                        
                        return results
                    else:
                        return [{"title": "Search Error", "description": f"API returned status {response.status}", "url": "#"}]
        
        except Exception as e:
            return [{"title": "Search Error", "description": f"Error: {str(e)}", "url": "#"}]
    
    async def search_news(self, query: str, count: int = 5) -> List[Dict[str, Any]]:
        """Search for news specifically"""
        
        if not self.api_key:
            return [{"title": "API Key Required", "description": "Brave Search API key not configured"}]
        
        params = {
            "q": query,
            "count": count,
            "freshness": "pd"  # Past day for news
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/news/search",
                    params=params,
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        
                        for result in data.get("results", []):
                            results.append({
                                "title": result.get("title", ""),
                                "description": result.get("description", ""),
                                "url": result.get("url", ""),
                                "published": result.get("age", ""),
                                "source": result.get("meta_url", {}).get("hostname", "")
                            })
                        
                        return results
                    else:
                        return [{"title": "News Search Error", "description": f"API returned status {response.status}"}]
        
        except Exception as e:
            return [{"title": "News Search Error", "description": f"Error: {str(e)}"}]