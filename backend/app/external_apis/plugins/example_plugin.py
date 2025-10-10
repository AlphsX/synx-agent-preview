"""
Example custom data source plugin demonstrating the plugin architecture.
This plugin fetches data from a hypothetical external API.
"""

import aiohttp
import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
from app.external_apis.plugin_system import DataSourcePlugin

logger = logging.getLogger(__name__)


class ExampleDataPlugin(DataSourcePlugin):
    """
    Example data source plugin that demonstrates the plugin architecture.
    This can be used as a template for creating custom data source plugins.
    """
    
    VERSION = "1.0.0"
    DESCRIPTION = "Example data source plugin for demonstration"
    AUTHOR = "AI Agent Team"
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.api_key = self.config.get('api_key')
        self.base_url = self.config.get('base_url', 'https://api.example.com')
        self.timeout = self.config.get('timeout', 30)
    
    async def fetch_data(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Fetch data from the example API.
        
        Args:
            query: Search query or identifier
            **kwargs: Additional parameters like limit, category, etc.
            
        Returns:
            Dictionary containing the fetched data
        """
        if not self.is_available():
            return await self._generate_mock_data(query, **kwargs)
        
        try:
            # Prepare request parameters
            params = {
                "q": query,
                "limit": kwargs.get("limit", 10),
                "category": kwargs.get("category", "general")
            }
            
            if self.api_key:
                params["api_key"] = self.api_key
            
            # Make API request
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(f"{self.base_url}/search", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Process and format the response
                        results = []
                        for item in data.get("results", []):
                            results.append({
                                "id": item.get("id", ""),
                                "title": item.get("title", ""),
                                "description": item.get("description", ""),
                                "url": item.get("url", ""),
                                "category": item.get("category", ""),
                                "score": item.get("relevance_score", 0.0),
                                "published_at": item.get("published_at", "")
                            })
                        
                        return {
                            "query": query,
                            "results": results,
                            "total_count": data.get("total_count", len(results)),
                            "timestamp": datetime.now().isoformat(),
                            "source": "example_api"
                        }
                    
                    elif response.status == 429:
                        return {"error": "Rate limit exceeded"}
                    
                    else:
                        error_text = await response.text()
                        return {"error": f"API error: {response.status} - {error_text}"}
        
        except asyncio.TimeoutError:
            return {"error": "Request timeout"}
        
        except Exception as e:
            logger.error(f"Example plugin fetch_data failed: {str(e)}")
            return {"error": f"Failed to fetch data: {str(e)}"}
    
    async def get_categories(self) -> Dict[str, Any]:
        """
        Get available categories from the API.
        This is a custom operation specific to this plugin.
        
        Returns:
            List of available categories
        """
        if not self.is_available():
            return {
                "categories": ["general", "technology", "business", "science"],
                "mock": True
            }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                params = {}
                if self.api_key:
                    params["api_key"] = self.api_key
                
                async with session.get(f"{self.base_url}/categories", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "categories": data.get("categories", []),
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        return {"error": f"Failed to fetch categories: {response.status}"}
        
        except Exception as e:
            logger.error(f"Example plugin get_categories failed: {str(e)}")
            return {"error": f"Failed to fetch categories: {str(e)}"}
    
    async def get_trending(self, limit: int = 10) -> Dict[str, Any]:
        """
        Get trending items from the API.
        Another custom operation for this plugin.
        
        Args:
            limit: Number of trending items to return
            
        Returns:
            List of trending items
        """
        if not self.is_available():
            return await self._generate_mock_trending(limit)
        
        try:
            params = {"limit": limit}
            if self.api_key:
                params["api_key"] = self.api_key
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(f"{self.base_url}/trending", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        trending_items = []
                        for item in data.get("trending", []):
                            trending_items.append({
                                "title": item.get("title", ""),
                                "score": item.get("trending_score", 0.0),
                                "category": item.get("category", ""),
                                "url": item.get("url", ""),
                                "rank": item.get("rank", 0)
                            })
                        
                        return {
                            "trending_items": trending_items,
                            "timestamp": datetime.now().isoformat(),
                            "source": "example_api"
                        }
                    else:
                        return {"error": f"Failed to fetch trending: {response.status}"}
        
        except Exception as e:
            logger.error(f"Example plugin get_trending failed: {str(e)}")
            return {"error": f"Failed to fetch trending: {str(e)}"}
    
    def is_available(self) -> bool:
        """
        Check if the example API is available.
        For this example, we'll always return True to demonstrate mock functionality.
        
        Returns:
            True if available, False otherwise
        """
        # In a real plugin, you might check for API key, network connectivity, etc.
        return True  # Always available for demo purposes
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the example API.
        
        Returns:
            Health status information
        """
        if not self.api_key:
            return {
                "status": "mock",
                "message": "API key not configured, using mock data",
                "service": "Example API"
            }
        
        try:
            # Test with a simple request
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                params = {}
                if self.api_key:
                    params["api_key"] = self.api_key
                
                async with session.get(f"{self.base_url}/health", params=params) as response:
                    if response.status == 200:
                        return {
                            "status": "healthy",
                            "message": "Service operational",
                            "service": "Example API"
                        }
                    else:
                        return {
                            "status": "error",
                            "message": f"HTTP {response.status}",
                            "service": "Example API"
                        }
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Health check failed: {str(e)}",
                "service": "Example API"
            }
    
    def get_supported_operations(self) -> List[str]:
        """
        Get list of supported operations for this plugin.
        
        Returns:
            List of operation names
        """
        return ["fetch_data", "get_categories", "get_trending", "health_check"]
    
    def get_required_config(self) -> List[str]:
        """
        Get list of required configuration keys.
        
        Returns:
            List of required configuration keys
        """
        return []  # No required config for this example
    
    def get_optional_config(self) -> List[str]:
        """
        Get list of optional configuration keys.
        
        Returns:
            List of optional configuration keys
        """
        return ["api_key", "base_url", "timeout"]
    
    async def _generate_mock_data(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Generate mock data when the API is not available.
        
        Args:
            query: Search query
            **kwargs: Additional parameters
            
        Returns:
            Mock data response
        """
        logger.info(f"Generating mock data for query: {query}")
        
        limit = kwargs.get("limit", 10)
        category = kwargs.get("category", "general")
        
        # Generate mock results
        results = []
        for i in range(min(limit, 5)):  # Limit mock results
            results.append({
                "id": f"mock_{i+1}",
                "title": f"Mock Result {i+1} for '{query}'",
                "description": f"This is a mock result for the query '{query}' in category '{category}'.",
                "url": f"https://example.com/mock-result-{i+1}",
                "category": category,
                "score": 0.9 - (i * 0.1),
                "published_at": datetime.now().isoformat()
            })
        
        return {
            "query": query,
            "results": results,
            "total_count": len(results),
            "timestamp": datetime.now().isoformat(),
            "source": "example_api",
            "mock": True
        }
    
    async def _generate_mock_trending(self, limit: int) -> Dict[str, Any]:
        """
        Generate mock trending data.
        
        Args:
            limit: Number of trending items
            
        Returns:
            Mock trending data
        """
        logger.info(f"Generating mock trending data with limit: {limit}")
        
        trending_topics = [
            "Artificial Intelligence", "Climate Change", "Space Exploration",
            "Renewable Energy", "Quantum Computing", "Biotechnology",
            "Cryptocurrency", "Virtual Reality", "Machine Learning", "Robotics"
        ]
        
        trending_items = []
        for i, topic in enumerate(trending_topics[:limit]):
            trending_items.append({
                "title": topic,
                "score": 100.0 - (i * 5),
                "category": "technology",
                "url": f"https://example.com/trending/{topic.lower().replace(' ', '-')}",
                "rank": i + 1
            })
        
        return {
            "trending_items": trending_items,
            "timestamp": datetime.now().isoformat(),
            "source": "example_api",
            "mock": True
        }


class WeatherDataPlugin(DataSourcePlugin):
    """
    Example weather data plugin that integrates with weather APIs.
    This demonstrates how to create specialized plugins for specific data types.
    """
    
    VERSION = "1.0.0"
    DESCRIPTION = "Weather data plugin for location-based weather information"
    AUTHOR = "AI Agent Team"
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.api_key = self.config.get('api_key')
        self.base_url = "https://api.openweathermap.org/data/2.5"
    
    async def fetch_data(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Fetch weather data for a location.
        
        Args:
            query: Location name (e.g., "New York, NY")
            **kwargs: Additional parameters like units, forecast_days
            
        Returns:
            Weather data for the location
        """
        if not self.is_available():
            return await self._generate_mock_weather(query, **kwargs)
        
        try:
            units = kwargs.get("units", "metric")
            forecast_days = kwargs.get("forecast_days", 1)
            
            if forecast_days == 1:
                # Current weather
                params = {
                    "q": query,
                    "appid": self.api_key,
                    "units": units
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.base_url}/weather", params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            return {
                                "location": query,
                                "current_weather": {
                                    "temperature": data["main"]["temp"],
                                    "feels_like": data["main"]["feels_like"],
                                    "humidity": data["main"]["humidity"],
                                    "description": data["weather"][0]["description"],
                                    "wind_speed": data.get("wind", {}).get("speed", 0)
                                },
                                "timestamp": datetime.now().isoformat(),
                                "units": units
                            }
                        else:
                            return {"error": f"Weather API error: {response.status}"}
            else:
                # Forecast
                params = {
                    "q": query,
                    "appid": self.api_key,
                    "units": units,
                    "cnt": forecast_days * 8  # 8 forecasts per day (3-hour intervals)
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.base_url}/forecast", params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # Process forecast data
                            forecast = []
                            for item in data["list"][:forecast_days * 8]:
                                forecast.append({
                                    "datetime": item["dt_txt"],
                                    "temperature": item["main"]["temp"],
                                    "description": item["weather"][0]["description"],
                                    "humidity": item["main"]["humidity"]
                                })
                            
                            return {
                                "location": query,
                                "forecast": forecast,
                                "timestamp": datetime.now().isoformat(),
                                "units": units
                            }
                        else:
                            return {"error": f"Weather API error: {response.status}"}
        
        except Exception as e:
            logger.error(f"Weather plugin fetch_data failed: {str(e)}")
            return {"error": f"Failed to fetch weather data: {str(e)}"}
    
    def is_available(self) -> bool:
        """Check if weather API is available."""
        return bool(self.api_key)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on weather API."""
        if not self.is_available():
            return {
                "status": "unavailable",
                "message": "API key not configured",
                "service": "OpenWeather API"
            }
        
        try:
            params = {
                "q": "London,UK",
                "appid": self.api_key
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{self.base_url}/weather", params=params) as response:
                    if response.status == 200:
                        return {
                            "status": "healthy",
                            "message": "Service operational",
                            "service": "OpenWeather API"
                        }
                    else:
                        return {
                            "status": "error",
                            "message": f"HTTP {response.status}",
                            "service": "OpenWeather API"
                        }
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Health check failed: {str(e)}",
                "service": "OpenWeather API"
            }
    
    def get_required_config(self) -> List[str]:
        """Get required configuration keys."""
        return ["api_key"]
    
    async def _generate_mock_weather(self, location: str, **kwargs) -> Dict[str, Any]:
        """Generate mock weather data."""
        logger.info(f"Generating mock weather data for {location}")
        
        forecast_days = kwargs.get("forecast_days", 1)
        units = kwargs.get("units", "metric")
        
        if forecast_days == 1:
            return {
                "location": location,
                "current_weather": {
                    "temperature": 22.5,
                    "feels_like": 24.0,
                    "humidity": 65,
                    "description": "partly cloudy",
                    "wind_speed": 3.2
                },
                "timestamp": datetime.now().isoformat(),
                "units": units,
                "mock": True
            }
        else:
            # Generate forecast
            forecast = []
            for i in range(forecast_days * 2):  # 2 forecasts per day for simplicity
                forecast.append({
                    "datetime": (datetime.now() + datetime.timedelta(hours=i*12)).isoformat(),
                    "temperature": 20.0 + (i % 10),
                    "description": "partly cloudy",
                    "humidity": 60 + (i % 20)
                })
            
            return {
                "location": location,
                "forecast": forecast,
                "timestamp": datetime.now().isoformat(),
                "units": units,
                "mock": True
            }