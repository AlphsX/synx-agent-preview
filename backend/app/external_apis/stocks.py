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


class StockService:
    """
    Stock market data service supporting multiple stock API providers.
    Provides real-time quotes, historical data, and market analysis.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or getattr(settings, 'ALPHA_VANTAGE_API_KEY', None)
        self.base_url = "https://www.alphavantage.co/query"
        
        # Fallback to free tier APIs if no key provided
        self.use_free_apis = not self.api_key
        
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
    
    async def get_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get real-time stock quote for a symbol.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL", "GOOGL")
            
        Returns:
            Current stock price and basic info
        """
        if not self.is_available():
            return await self._generate_mock_stock_data(symbol, "quote")
        
        # Start external API call tracking
        call_id = external_api_logger.start_call(
            service_name="alpha_vantage",
            method="GET",
            url=self.base_url,
            request_data={"symbol": symbol, "function": "GLOBAL_QUOTE"}
        )
        
        try:
            result = await retry_with_backoff(
                self._fetch_stock_quote,
                self.retry_config,
                ServiceType.STOCK_API,
                symbol
            )
            
            # Finish tracking successful call
            external_api_logger.finish_call(
                call_id=call_id,
                status_code=200,
                response_data={"symbol": symbol, "price": result.get("price")}
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Stock quote fetch failed for {symbol}: {str(e)}")
            
            # Record error metrics
            error_metrics.record_error(
                service=ServiceType.STOCK_API,
                error_code=ErrorCode.API_UNAVAILABLE,
                severity=ErrorSeverity.MEDIUM,
                details={
                    "symbol": symbol,
                    "error": str(e)
                }
            )
            
            # Finish tracking failed call
            external_api_logger.finish_call(call_id=call_id, error=e)
            
            return {"error": f"Error fetching quote for {symbol}: {str(e)}"}
    
    async def get_market_overview(self) -> Dict[str, Any]:
        """
        Get market overview with major indices and top movers.
        
        Returns:
            Market indices, top gainers, losers, and most active stocks
        """
        if not self.is_available():
            return await self._generate_mock_market_overview()
        
        # Start external API call tracking
        call_id = external_api_logger.start_call(
            service_name="alpha_vantage",
            method="GET",
            url=self.base_url,
            request_data={"function": "TOP_GAINERS_LOSERS"}
        )
        
        try:
            result = await retry_with_backoff(
                self._fetch_market_overview,
                self.retry_config,
                ServiceType.STOCK_API
            )
            
            # Finish tracking successful call
            external_api_logger.finish_call(
                call_id=call_id,
                status_code=200,
                response_data={"gainers_count": len(result.get("top_gainers", []))}
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Market overview fetch failed: {str(e)}")
            
            # Record error metrics
            error_metrics.record_error(
                service=ServiceType.STOCK_API,
                error_code=ErrorCode.API_UNAVAILABLE,
                severity=ErrorSeverity.MEDIUM,
                details={"error": str(e)}
            )
            
            # Finish tracking failed call
            external_api_logger.finish_call(call_id=call_id, error=e)
            
            return {"error": f"Error fetching market overview: {str(e)}"}
    
    async def get_company_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get company information and fundamentals.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Company overview, financials, and key metrics
        """
        if not self.is_available():
            return await self._generate_mock_company_info(symbol)
        
        # Start external API call tracking
        call_id = external_api_logger.start_call(
            service_name="alpha_vantage",
            method="GET",
            url=self.base_url,
            request_data={"symbol": symbol, "function": "OVERVIEW"}
        )
        
        try:
            result = await retry_with_backoff(
                self._fetch_company_info,
                self.retry_config,
                ServiceType.STOCK_API,
                symbol
            )
            
            # Finish tracking successful call
            external_api_logger.finish_call(
                call_id=call_id,
                status_code=200,
                response_data={"symbol": symbol, "company": result.get("name")}
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Company info fetch failed for {symbol}: {str(e)}")
            
            # Record error metrics
            error_metrics.record_error(
                service=ServiceType.STOCK_API,
                error_code=ErrorCode.API_UNAVAILABLE,
                severity=ErrorSeverity.MEDIUM,
                details={
                    "symbol": symbol,
                    "error": str(e)
                }
            )
            
            # Finish tracking failed call
            external_api_logger.finish_call(call_id=call_id, error=e)
            
            return {"error": f"Error fetching company info for {symbol}: {str(e)}"}
    
    async def get_historical_data(
        self, 
        symbol: str, 
        period: str = "1M"
    ) -> Dict[str, Any]:
        """
        Get historical stock data.
        
        Args:
            symbol: Stock symbol
            period: Time period ("1D", "1W", "1M", "3M", "1Y")
            
        Returns:
            Historical price data
        """
        if not self.is_available():
            return await self._generate_mock_historical_data(symbol, period)
        
        try:
            result = await retry_with_backoff(
                self._fetch_historical_data,
                self.retry_config,
                ServiceType.STOCK_API,
                symbol, period
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Historical data fetch failed for {symbol}: {str(e)}")
            return {"error": f"Error fetching historical data for {symbol}: {str(e)}"}
    
    async def search_stocks(self, query: str) -> Dict[str, Any]:
        """
        Search for stocks by company name or symbol.
        
        Args:
            query: Search query (company name or symbol)
            
        Returns:
            List of matching stocks
        """
        if not self.is_available():
            return await self._generate_mock_search_results(query)
        
        try:
            result = await retry_with_backoff(
                self._fetch_stock_search,
                self.retry_config,
                ServiceType.STOCK_API,
                query
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Stock search failed for {query}: {str(e)}")
            return {"error": f"Error searching stocks for {query}: {str(e)}"}
    
    async def _fetch_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """Internal method to fetch stock quote."""
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": self.api_key
            }
            
            async with session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if "Global Quote" in data:
                        quote = data["Global Quote"]
                        return {
                            "symbol": quote.get("01. symbol", symbol),
                            "price": float(quote.get("05. price", 0)),
                            "change": float(quote.get("09. change", 0)),
                            "change_percent": quote.get("10. change percent", "0%").replace("%", ""),
                            "volume": int(quote.get("06. volume", 0)),
                            "open": float(quote.get("02. open", 0)),
                            "high": float(quote.get("03. high", 0)),
                            "low": float(quote.get("04. low", 0)),
                            "previous_close": float(quote.get("08. previous close", 0)),
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        return {"error": "Invalid response format or symbol not found"}
                
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
    
    async def _fetch_market_overview(self) -> Dict[str, Any]:
        """Internal method to fetch market overview."""
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            params = {
                "function": "TOP_GAINERS_LOSERS",
                "apikey": self.api_key
            }
            
            async with session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return {
                        "top_gainers": [
                            {
                                "symbol": item.get("ticker", ""),
                                "price": float(item.get("price", 0)),
                                "change": float(item.get("change_amount", 0)),
                                "change_percent": item.get("change_percentage", "0%").replace("%", ""),
                                "volume": int(item.get("volume", 0))
                            }
                            for item in data.get("top_gainers", [])[:10]
                        ],
                        "top_losers": [
                            {
                                "symbol": item.get("ticker", ""),
                                "price": float(item.get("price", 0)),
                                "change": float(item.get("change_amount", 0)),
                                "change_percent": item.get("change_percentage", "0%").replace("%", ""),
                                "volume": int(item.get("volume", 0))
                            }
                            for item in data.get("top_losers", [])[:10]
                        ],
                        "most_active": [
                            {
                                "symbol": item.get("ticker", ""),
                                "price": float(item.get("price", 0)),
                                "change": float(item.get("change_amount", 0)),
                                "change_percent": item.get("change_percentage", "0%").replace("%", ""),
                                "volume": int(item.get("volume", 0))
                            }
                            for item in data.get("most_actively_traded", [])[:10]
                        ],
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    error_text = await response.text()
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=f"API error: {error_text}"
                    )
    
    async def _fetch_company_info(self, symbol: str) -> Dict[str, Any]:
        """Internal method to fetch company information."""
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            params = {
                "function": "OVERVIEW",
                "symbol": symbol,
                "apikey": self.api_key
            }
            
            async with session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if "Symbol" in data:
                        return {
                            "symbol": data.get("Symbol", symbol),
                            "name": data.get("Name", ""),
                            "description": data.get("Description", ""),
                            "sector": data.get("Sector", ""),
                            "industry": data.get("Industry", ""),
                            "market_cap": data.get("MarketCapitalization", ""),
                            "pe_ratio": data.get("PERatio", ""),
                            "dividend_yield": data.get("DividendYield", ""),
                            "eps": data.get("EPS", ""),
                            "beta": data.get("Beta", ""),
                            "52_week_high": data.get("52WeekHigh", ""),
                            "52_week_low": data.get("52WeekLow", ""),
                            "analyst_target_price": data.get("AnalystTargetPrice", ""),
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        return {"error": "Company information not found"}
                else:
                    error_text = await response.text()
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=f"API error: {error_text}"
                    )
    
    async def _fetch_historical_data(self, symbol: str, period: str) -> Dict[str, Any]:
        """Internal method to fetch historical data."""
        # Map period to Alpha Vantage function
        function_map = {
            "1D": "TIME_SERIES_INTRADAY",
            "1W": "TIME_SERIES_DAILY",
            "1M": "TIME_SERIES_DAILY",
            "3M": "TIME_SERIES_DAILY",
            "1Y": "TIME_SERIES_DAILY"
        }
        
        function = function_map.get(period, "TIME_SERIES_DAILY")
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            params = {
                "function": function,
                "symbol": symbol,
                "apikey": self.api_key
            }
            
            if function == "TIME_SERIES_INTRADAY":
                params["interval"] = "60min"
            
            async with session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract time series data
                    time_series_key = None
                    for key in data.keys():
                        if "Time Series" in key:
                            time_series_key = key
                            break
                    
                    if time_series_key and time_series_key in data:
                        time_series = data[time_series_key]
                        
                        # Convert to list format
                        historical_data = []
                        for date_str, values in list(time_series.items())[:100]:  # Limit to 100 points
                            historical_data.append({
                                "date": date_str,
                                "open": float(values.get("1. open", 0)),
                                "high": float(values.get("2. high", 0)),
                                "low": float(values.get("3. low", 0)),
                                "close": float(values.get("4. close", 0)),
                                "volume": int(values.get("5. volume", 0))
                            })
                        
                        return {
                            "symbol": symbol,
                            "period": period,
                            "data": historical_data,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        return {"error": "Historical data not found"}
                else:
                    error_text = await response.text()
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=f"API error: {error_text}"
                    )
    
    async def _fetch_stock_search(self, query: str) -> Dict[str, Any]:
        """Internal method to search stocks."""
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            params = {
                "function": "SYMBOL_SEARCH",
                "keywords": query,
                "apikey": self.api_key
            }
            
            async with session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if "bestMatches" in data:
                        matches = []
                        for match in data["bestMatches"][:10]:  # Limit to 10 results
                            matches.append({
                                "symbol": match.get("1. symbol", ""),
                                "name": match.get("2. name", ""),
                                "type": match.get("3. type", ""),
                                "region": match.get("4. region", ""),
                                "currency": match.get("8. currency", ""),
                                "match_score": float(match.get("9. matchScore", 0))
                            })
                        
                        return {
                            "query": query,
                            "matches": matches,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        return {"query": query, "matches": [], "timestamp": datetime.now().isoformat()}
                else:
                    error_text = await response.text()
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=f"API error: {error_text}"
                    )
    
    async def _generate_mock_stock_data(self, symbol: str, data_type: str) -> Dict[str, Any]:
        """Generate mock stock data when API is unavailable."""
        logger.info(f"Generating mock stock data for {symbol}")
        
        if data_type == "quote":
            return {
                "symbol": symbol,
                "price": 150.25,
                "change": 2.50,
                "change_percent": "1.69",
                "volume": 1000000,
                "open": 148.00,
                "high": 152.00,
                "low": 147.50,
                "previous_close": 147.75,
                "timestamp": datetime.now().isoformat(),
                "mock": True
            }
        
        return {"error": "Unknown data type"}
    
    async def _generate_mock_market_overview(self) -> Dict[str, Any]:
        """Generate mock market overview data."""
        logger.info("Generating mock market overview data")
        
        mock_stocks = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
        
        return {
            "top_gainers": [
                {
                    "symbol": stock,
                    "price": 150.0 + i * 10,
                    "change": 2.5 + i * 0.5,
                    "change_percent": f"{1.5 + i * 0.3:.2f}",
                    "volume": 1000000 + i * 100000
                }
                for i, stock in enumerate(mock_stocks)
            ],
            "top_losers": [
                {
                    "symbol": stock,
                    "price": 100.0 - i * 5,
                    "change": -1.5 - i * 0.3,
                    "change_percent": f"-{1.2 + i * 0.2:.2f}",
                    "volume": 800000 + i * 50000
                }
                for i, stock in enumerate(mock_stocks)
            ],
            "most_active": [
                {
                    "symbol": stock,
                    "price": 120.0 + i * 8,
                    "change": 1.0 + i * 0.2,
                    "change_percent": f"{0.8 + i * 0.1:.2f}",
                    "volume": 2000000 + i * 200000
                }
                for i, stock in enumerate(mock_stocks)
            ],
            "timestamp": datetime.now().isoformat(),
            "mock": True
        }
    
    async def _generate_mock_company_info(self, symbol: str) -> Dict[str, Any]:
        """Generate mock company information."""
        logger.info(f"Generating mock company info for {symbol}")
        
        return {
            "symbol": symbol,
            "name": f"Mock Company {symbol}",
            "description": f"This is mock company information for {symbol}.",
            "sector": "Technology",
            "industry": "Software",
            "market_cap": "1000000000",
            "pe_ratio": "25.5",
            "dividend_yield": "1.2",
            "eps": "5.85",
            "beta": "1.15",
            "52_week_high": "180.00",
            "52_week_low": "120.00",
            "analyst_target_price": "165.00",
            "timestamp": datetime.now().isoformat(),
            "mock": True
        }
    
    async def _generate_mock_historical_data(self, symbol: str, period: str) -> Dict[str, Any]:
        """Generate mock historical data."""
        logger.info(f"Generating mock historical data for {symbol}")
        
        # Generate 30 days of mock data
        historical_data = []
        base_price = 150.0
        
        for i in range(30):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            price_variation = (i % 10 - 5) * 2  # Simple price variation
            
            historical_data.append({
                "date": date,
                "open": base_price + price_variation,
                "high": base_price + price_variation + 3,
                "low": base_price + price_variation - 2,
                "close": base_price + price_variation + 1,
                "volume": 1000000 + i * 10000
            })
        
        return {
            "symbol": symbol,
            "period": period,
            "data": historical_data,
            "timestamp": datetime.now().isoformat(),
            "mock": True
        }
    
    async def _generate_mock_search_results(self, query: str) -> Dict[str, Any]:
        """Generate mock search results."""
        logger.info(f"Generating mock search results for {query}")
        
        mock_results = [
            {
                "symbol": f"MOCK{i}",
                "name": f"Mock Company {i} ({query})",
                "type": "Equity",
                "region": "United States",
                "currency": "USD",
                "match_score": 0.9 - i * 0.1
            }
            for i in range(1, 4)
        ]
        
        return {
            "query": query,
            "matches": mock_results,
            "timestamp": datetime.now().isoformat(),
            "mock": True
        }
    
    def is_available(self) -> bool:
        """Check if stock service is available."""
        return bool(self.api_key) or self.use_free_apis
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the stock service."""
        if not self.api_key:
            return {
                "status": "mock",
                "message": "API key not configured, using mock data",
                "service": "Alpha Vantage"
            }
        
        try:
            # Test with a simple quote request for AAPL
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                params = {
                    "function": "GLOBAL_QUOTE",
                    "symbol": "AAPL",
                    "apikey": self.api_key
                }
                
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        return {
                            "status": "healthy",
                            "message": "Service operational",
                            "service": "Alpha Vantage"
                        }
                    else:
                        return {
                            "status": "error",
                            "message": f"HTTP {response.status}",
                            "service": "Alpha Vantage"
                        }
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Health check failed: {str(e)}",
                "service": "Alpha Vantage"
            }