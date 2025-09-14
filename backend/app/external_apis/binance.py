import aiohttp
import hmac
import hashlib
import time
from typing import Dict, Any, List, Optional
from urllib.parse import urlencode
from app.config import settings

class BinanceService:
    def __init__(self, api_key: str = None, secret_key: str = None):
        self.api_key = api_key or settings.BINANCE_API_KEY
        self.secret_key = secret_key or settings.BINANCE_SECRET_KEY
        self.base_url = "https://api.binance.com/api/v3"
        self.headers = {
            "X-MBX-APIKEY": self.api_key
        } if self.api_key else None
    
    def _generate_signature(self, params: str) -> str:
        """Generate HMAC SHA256 signature for authenticated requests"""
        if not self.secret_key:
            return ""
        return hmac.new(
            self.secret_key.encode('utf-8'),
            params.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    async def get_market_data(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Get cryptocurrency market data"""
        
        if symbols is None:
            symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT"]
        
        try:
            async with aiohttp.ClientSession() as session:
                # Get 24hr ticker statistics
                async with session.get(f"{self.base_url}/ticker/24hr") as response:
                    if response.status == 200:
                        data = await response.json()
                        market_data = {}
                        
                        for ticker in data:
                            symbol = ticker.get("symbol", "")
                            if symbol in symbols:
                                market_data[symbol] = {
                                    "symbol": symbol,
                                    "price": float(ticker.get("lastPrice", 0)),
                                    "change": float(ticker.get("priceChangePercent", 0)),
                                    "volume": float(ticker.get("volume", 0)),
                                    "high": float(ticker.get("highPrice", 0)),
                                    "low": float(ticker.get("lowPrice", 0)),
                                    "openPrice": float(ticker.get("openPrice", 0))
                                }
                        
                        return market_data
                    else:
                        return {"error": f"API returned status {response.status}"}
        
        except Exception as e:
            return {"error": f"Error fetching market data: {str(e)}"}
    
    async def get_ticker_price(self, symbol: str) -> Dict[str, Any]:
        """Get current price for a specific symbol"""
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {"symbol": symbol.upper()}
                async with session.get(
                    f"{self.base_url}/ticker/price",
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "symbol": data.get("symbol", ""),
                            "price": float(data.get("price", 0))
                        }
                    else:
                        return {"error": f"API returned status {response.status}"}
        
        except Exception as e:
            return {"error": f"Error fetching price: {str(e)}"}
    
    async def get_top_gainers_losers(self, limit: int = 10) -> Dict[str, List[Dict]]:
        """Get top gainers and losers"""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/ticker/24hr") as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Filter USDT pairs and sort by price change
                        usdt_pairs = [
                            {
                                "symbol": ticker.get("symbol", ""),
                                "price": float(ticker.get("lastPrice", 0)),
                                "change": float(ticker.get("priceChangePercent", 0)),
                                "volume": float(ticker.get("quoteVolume", 0))
                            }
                            for ticker in data
                            if ticker.get("symbol", "").endswith("USDT") and 
                               float(ticker.get("quoteVolume", 0)) > 10000000  # Filter by volume
                        ]
                        
                        # Sort by percentage change
                        gainers = sorted(usdt_pairs, key=lambda x: x["change"], reverse=True)[:limit]
                        losers = sorted(usdt_pairs, key=lambda x: x["change"])[:limit]
                        
                        return {
                            "gainers": gainers,
                            "losers": losers
                        }
                    else:
                        return {"error": f"API returned status {response.status}"}
        
        except Exception as e:
            return {"error": f"Error fetching gainers/losers: {str(e)}"}
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information (requires API key and secret)"""
        
        if not self.api_key or not self.secret_key:
            return {"error": "API key and secret required for account info"}
        
        try:
            timestamp = int(time.time() * 1000)
            params = f"timestamp={timestamp}"
            signature = self._generate_signature(params)
            
            url = f"{self.base_url}/account?{params}&signature={signature}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract relevant account info
                        balances = [
                            {
                                "asset": balance["asset"],
                                "free": float(balance["free"]),
                                "locked": float(balance["locked"])
                            }
                            for balance in data.get("balances", [])
                            if float(balance["free"]) > 0 or float(balance["locked"]) > 0
                        ]
                        
                        return {
                            "accountType": data.get("accountType", ""),
                            "canTrade": data.get("canTrade", False),
                            "canWithdraw": data.get("canWithdraw", False),
                            "canDeposit": data.get("canDeposit", False),
                            "balances": balances
                        }
                    else:
                        error_text = await response.text()
                        return {"error": f"API error: {response.status} - {error_text}"}
        
        except Exception as e:
            return {"error": f"Error fetching account info: {str(e)}"}