import aiohttp
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.config import settings
from ..core.error_handling import (
    retry_with_backoff, RetryConfig, ServiceType, ErrorCode, ErrorSeverity, error_metrics
)
from ..core.logging_middleware import external_api_logger

logger = logging.getLogger(__name__)


class WeatherService:
    """
    Weather data service supporting multiple weather API providers.
    Provides current weather, forecasts, and location-based weather queries.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or getattr(settings, 'OPENWEATHER_API_KEY', None)
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.geo_url = "https://api.openweathermap.org/geo/1.0"
        
        # Configure retry settings
        self.retry_config = RetryConfig(
            max_retries=3,
            base_delay=1.0,
            max_delay=30.0,
            exponential_base=2.0,
            jitter=True
        )
        
        # Request timeout
        self.timeout = getattr(settings, 'EXTERNAL_API_TIMEOUT', 30)
    
    async def get_current_weather(
        self, 
        location: str, 
        units: str = "metric"
    ) -> Dict[str, Any]:
        """
        Get current weather for a location.
        
        Args:
            location: City name, state/country (e.g., "New York, NY, US")
            units: Temperature units ("metric", "imperial", "kelvin")
            
        Returns:
            Current weather data with temperature, conditions, etc.
        """
        if not self.is_available():
            return await self._generate_mock_weather(location, "current")
        
        # Start external API call tracking
        call_id = external_api_logger.start_call(
            service_name="openweather",
            method="GET",
            url=f"{self.base_url}/weather",
            request_data={"location": location, "units": units}
        )
        
        try:
            # Get coordinates for the location first
            coords = await self._get_coordinates(location)
            if not coords:
                return {"error": f"Location '{location}' not found"}
            
            result = await retry_with_backoff(
                self._fetch_current_weather,
                self.retry_config,
                ServiceType.WEATHER_API,
                coords["lat"], coords["lon"], units
            )
            
            # Add location info to result
            result["location"] = {
                "name": coords.get("name", location),
                "country": coords.get("country", ""),
                "state": coords.get("state", ""),
                "lat": coords["lat"],
                "lon": coords["lon"]
            }
            
            # Finish tracking successful call
            external_api_logger.finish_call(
                call_id=call_id,
                status_code=200,
                response_data={"location": location, "temperature": result.get("temperature")}
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Current weather fetch failed for {location}: {str(e)}")
            
            # Record error metrics
            error_metrics.record_error(
                service=ServiceType.WEATHER_API,
                error_code=ErrorCode.API_UNAVAILABLE,
                severity=ErrorSeverity.MEDIUM,
                details={
                    "location": location,
                    "error": str(e)
                }
            )
            
            # Finish tracking failed call
            external_api_logger.finish_call(call_id=call_id, error=e)
            
            return {"error": f"Error fetching weather for {location}: {str(e)}"}
    
    async def get_weather_forecast(
        self, 
        location: str, 
        days: int = 5, 
        units: str = "metric"
    ) -> Dict[str, Any]:
        """
        Get weather forecast for a location.
        
        Args:
            location: City name, state/country
            days: Number of days to forecast (1-5)
            units: Temperature units
            
        Returns:
            Weather forecast data
        """
        if not self.is_available():
            return await self._generate_mock_weather(location, "forecast", days)
        
        # Start external API call tracking
        call_id = external_api_logger.start_call(
            service_name="openweather",
            method="GET",
            url=f"{self.base_url}/forecast",
            request_data={"location": location, "days": days, "units": units}
        )
        
        try:
            # Get coordinates for the location first
            coords = await self._get_coordinates(location)
            if not coords:
                return {"error": f"Location '{location}' not found"}
            
            result = await retry_with_backoff(
                self._fetch_weather_forecast,
                self.retry_config,
                ServiceType.WEATHER_API,
                coords["lat"], coords["lon"], days, units
            )
            
            # Add location info to result
            result["location"] = {
                "name": coords.get("name", location),
                "country": coords.get("country", ""),
                "state": coords.get("state", ""),
                "lat": coords["lat"],
                "lon": coords["lon"]
            }
            
            # Finish tracking successful call
            external_api_logger.finish_call(
                call_id=call_id,
                status_code=200,
                response_data={"location": location, "forecast_days": len(result.get("forecast", []))}
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Weather forecast fetch failed for {location}: {str(e)}")
            
            # Record error metrics
            error_metrics.record_error(
                service=ServiceType.WEATHER_API,
                error_code=ErrorCode.API_UNAVAILABLE,
                severity=ErrorSeverity.MEDIUM,
                details={
                    "location": location,
                    "days": days,
                    "error": str(e)
                }
            )
            
            # Finish tracking failed call
            external_api_logger.finish_call(call_id=call_id, error=e)
            
            return {"error": f"Error fetching forecast for {location}: {str(e)}"}
    
    async def get_weather_alerts(self, location: str) -> Dict[str, Any]:
        """
        Get weather alerts for a location.
        
        Args:
            location: City name, state/country
            
        Returns:
            Weather alerts and warnings
        """
        if not self.is_available():
            return {"alerts": [], "location": location}
        
        try:
            # Get coordinates for the location first
            coords = await self._get_coordinates(location)
            if not coords:
                return {"error": f"Location '{location}' not found"}
            
            result = await retry_with_backoff(
                self._fetch_weather_alerts,
                self.retry_config,
                ServiceType.WEATHER_API,
                coords["lat"], coords["lon"]
            )
            
            # Add location info to result
            result["location"] = {
                "name": coords.get("name", location),
                "country": coords.get("country", ""),
                "state": coords.get("state", "")
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Weather alerts fetch failed for {location}: {str(e)}")
            return {"error": f"Error fetching alerts for {location}: {str(e)}"}
    
    async def _get_coordinates(self, location: str) -> Optional[Dict[str, Any]]:
        """Get latitude and longitude for a location using geocoding."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                params = {
                    "q": location,
                    "limit": 1,
                    "appid": self.api_key
                }
                
                async with session.get(f"{self.geo_url}/direct", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data:
                            return {
                                "lat": data[0]["lat"],
                                "lon": data[0]["lon"],
                                "name": data[0].get("name", ""),
                                "country": data[0].get("country", ""),
                                "state": data[0].get("state", "")
                            }
                    return None
        
        except Exception as e:
            logger.error(f"Geocoding failed for {location}: {str(e)}")
            return None
    
    async def _fetch_current_weather(
        self, 
        lat: float, 
        lon: float, 
        units: str
    ) -> Dict[str, Any]:
        """Internal method to fetch current weather data."""
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            params = {
                "lat": lat,
                "lon": lon,
                "units": units,
                "appid": self.api_key
            }
            
            async with session.get(f"{self.base_url}/weather", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return {
                        "temperature": data["main"]["temp"],
                        "feels_like": data["main"]["feels_like"],
                        "humidity": data["main"]["humidity"],
                        "pressure": data["main"]["pressure"],
                        "description": data["weather"][0]["description"],
                        "main": data["weather"][0]["main"],
                        "icon": data["weather"][0]["icon"],
                        "wind_speed": data.get("wind", {}).get("speed", 0),
                        "wind_direction": data.get("wind", {}).get("deg", 0),
                        "visibility": data.get("visibility", 0) / 1000,  # Convert to km
                        "uv_index": data.get("uvi", 0),
                        "timestamp": datetime.now().isoformat(),
                        "units": units
                    }
                elif response.status == 429:
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=429,
                        message="Rate limit exceeded"
                    )
                else:
                    error_text = await response.text()
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=f"API error: {error_text}"
                    )
    
    async def _fetch_weather_forecast(
        self, 
        lat: float, 
        lon: float, 
        days: int, 
        units: str
    ) -> Dict[str, Any]:
        """Internal method to fetch weather forecast data."""
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            params = {
                "lat": lat,
                "lon": lon,
                "units": units,
                "appid": self.api_key
            }
            
            async with session.get(f"{self.base_url}/forecast", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Process forecast data (OpenWeather returns 5-day forecast with 3-hour intervals)
                    forecast_list = []
                    current_date = None
                    daily_data = {}
                    
                    for item in data["list"][:days * 8]:  # 8 intervals per day (3-hour intervals)
                        dt = datetime.fromtimestamp(item["dt"])
                        date_str = dt.strftime("%Y-%m-%d")
                        
                        if date_str != current_date:
                            if current_date and daily_data:
                                forecast_list.append(daily_data)
                            
                            current_date = date_str
                            daily_data = {
                                "date": date_str,
                                "temperature_min": item["main"]["temp"],
                                "temperature_max": item["main"]["temp"],
                                "description": item["weather"][0]["description"],
                                "main": item["weather"][0]["main"],
                                "icon": item["weather"][0]["icon"],
                                "humidity": item["main"]["humidity"],
                                "wind_speed": item.get("wind", {}).get("speed", 0),
                                "precipitation": item.get("rain", {}).get("3h", 0) + item.get("snow", {}).get("3h", 0)
                            }
                        else:
                            # Update min/max temperatures for the day
                            daily_data["temperature_min"] = min(daily_data["temperature_min"], item["main"]["temp"])
                            daily_data["temperature_max"] = max(daily_data["temperature_max"], item["main"]["temp"])
                    
                    # Add the last day if it exists
                    if daily_data:
                        forecast_list.append(daily_data)
                    
                    return {
                        "forecast": forecast_list[:days],
                        "units": units,
                        "timestamp": datetime.now().isoformat()
                    }
                elif response.status == 429:
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=429,
                        message="Rate limit exceeded"
                    )
                else:
                    error_text = await response.text()
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=f"API error: {error_text}"
                    )
    
    async def _fetch_weather_alerts(self, lat: float, lon: float) -> Dict[str, Any]:
        """Internal method to fetch weather alerts."""
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key
            }
            
            async with session.get(f"{self.base_url}/onecall", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    alerts = data.get("alerts", [])
                    
                    processed_alerts = []
                    for alert in alerts:
                        processed_alerts.append({
                            "event": alert.get("event", ""),
                            "description": alert.get("description", ""),
                            "start": datetime.fromtimestamp(alert.get("start", 0)).isoformat(),
                            "end": datetime.fromtimestamp(alert.get("end", 0)).isoformat(),
                            "sender_name": alert.get("sender_name", ""),
                            "tags": alert.get("tags", [])
                        })
                    
                    return {
                        "alerts": processed_alerts,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    # If alerts endpoint fails, return empty alerts
                    return {
                        "alerts": [],
                        "timestamp": datetime.now().isoformat()
                    }
    
    async def _generate_mock_weather(
        self, 
        location: str, 
        weather_type: str = "current", 
        days: int = 1
    ) -> Dict[str, Any]:
        """Generate mock weather data when API is unavailable."""
        logger.info(f"Generating mock weather data for {location}")
        
        if weather_type == "current":
            return {
                "temperature": 22.5,
                "feels_like": 24.0,
                "humidity": 65,
                "pressure": 1013,
                "description": "partly cloudy",
                "main": "Clouds",
                "icon": "02d",
                "wind_speed": 3.2,
                "wind_direction": 180,
                "visibility": 10.0,
                "uv_index": 5,
                "timestamp": datetime.now().isoformat(),
                "units": "metric",
                "location": {
                    "name": location,
                    "country": "Mock",
                    "state": "Demo",
                    "lat": 0.0,
                    "lon": 0.0
                },
                "mock": True
            }
        
        elif weather_type == "forecast":
            forecast_list = []
            for i in range(days):
                date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
                forecast_list.append({
                    "date": date,
                    "temperature_min": 18.0 + i,
                    "temperature_max": 25.0 + i,
                    "description": "partly cloudy",
                    "main": "Clouds",
                    "icon": "02d",
                    "humidity": 60 + i * 2,
                    "wind_speed": 2.5 + i * 0.5,
                    "precipitation": 0.0
                })
            
            return {
                "forecast": forecast_list,
                "units": "metric",
                "timestamp": datetime.now().isoformat(),
                "location": {
                    "name": location,
                    "country": "Mock",
                    "state": "Demo"
                },
                "mock": True
            }
        
        return {"error": "Unknown weather type"}
    
    def is_available(self) -> bool:
        """Check if weather service is available."""
        return bool(self.api_key)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the weather service."""
        if not self.is_available():
            return {
                "status": "unavailable",
                "message": "API key not configured",
                "service": "OpenWeather"
            }
        
        try:
            # Test with a simple weather request for London
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                params = {
                    "q": "London,UK",
                    "appid": self.api_key
                }
                
                async with session.get(f"{self.base_url}/weather", params=params) as response:
                    if response.status == 200:
                        return {
                            "status": "healthy",
                            "message": "Service operational",
                            "service": "OpenWeather"
                        }
                    else:
                        return {
                            "status": "error",
                            "message": f"HTTP {response.status}",
                            "service": "OpenWeather"
                        }
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Health check failed: {str(e)}",
                "service": "OpenWeather"
            }