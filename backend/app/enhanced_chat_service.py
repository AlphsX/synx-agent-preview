from typing import List, AsyncGenerator, Dict, Any
import asyncio
import json
import aiohttp
import re
from app.config import settings
from app.external_apis.brave_search import BraveSearchService
from app.external_apis.binance import BinanceService

class EnhancedChatService:
    def __init__(self):
        self.groq_api_key = settings.GROQ_API_KEY
        self.openai_api_key = settings.OPENAI_API_KEY
        self.anthropic_api_key = settings.ANTHROPIC_API_KEY
        self.brave_search = BraveSearchService()
        self.binance_service = BinanceService()
        
    async def generate_ai_response(self, 
                                 message: str,
                                 model_id: str,
                                 conversation_history: List[Dict] = None) -> AsyncGenerator[str, None]:
        """Generate AI response with enhanced context from external APIs"""
        
        if conversation_history is None:
            conversation_history = []
        
        # Analyze message for external data needs
        enhanced_context = await self._get_enhanced_context(message)
        
        # Build system message with enhanced context
        system_message = self._build_enhanced_system_message(enhanced_context)
        
        # Add system message and conversation history
        messages = [{"role": "system", "content": system_message}]
        messages.extend(conversation_history[-10:])  # Last 10 messages
        messages.append({"role": "user", "content": message})
        
        # Route to appropriate AI service based on model
        if model_id.startswith("gpt"):
            async for chunk in self._generate_openai_response(messages, model_id):
                yield chunk
        elif model_id.startswith("claude"):
            async for chunk in self._generate_anthropic_response(messages, model_id):
                yield chunk
        elif model_id.startswith("groq") or "llama" in model_id.lower():
            async for chunk in self._generate_groq_response(messages, model_id):
                yield chunk
        else:
            # Enhanced mock response with context
            async for chunk in self._generate_enhanced_mock_response(message, enhanced_context):
                yield chunk
    
    async def _get_enhanced_context(self, message: str) -> Dict[str, Any]:
        """Get enhanced context from external APIs based on message content"""
        context = {}
        
        # Check for search-related keywords
        search_keywords = ["search", "find", "what is", "tell me about", "latest", "news", "current", "recent"]
        if any(keyword in message.lower() for keyword in search_keywords):
            try:
                search_results = await self.brave_search.search(message, count=3)
                context["web_search"] = {
                    "query": message,
                    "results": search_results[:3]  # Top 3 results
                }
            except Exception as e:
                context["web_search"] = {"error": str(e)}
        
        # Check for crypto-related keywords  
        crypto_keywords = ["bitcoin", "btc", "ethereum", "eth", "crypto", "cryptocurrency", 
                          "binance", "trading", "price", "market", "coin", "token"]
        if any(keyword in message.lower() for keyword in crypto_keywords):
            try:
                # Get crypto market data
                market_data = await self.binance_service.get_market_data()
                trending_data = await self.binance_service.get_top_gainers_losers(limit=5)
                
                context["crypto_data"] = {
                    "market": market_data,
                    "trending": trending_data
                }
            except Exception as e:
                context["crypto_data"] = {"error": str(e)}
        
        # Check for news-related keywords
        news_keywords = ["news", "breaking", "headline", "recent news", "latest news"]
        if any(keyword in message.lower() for keyword in news_keywords):
            try:
                news_results = await self.brave_search.search_news(message, count=3)
                context["news"] = {
                    "query": message,
                    "results": news_results
                }
            except Exception as e:
                context["news"] = {"error": str(e)}
        
        return context
    
    def _build_enhanced_system_message(self, context: Dict[str, Any]) -> str:
        """Build system message with enhanced context"""
        base_message = """You are Checkmate Spec Preview, an AI assistant inspired by Sync. You're witty, 
        informative, and have access to real-time information. You can search the web, get cryptocurrency 
        data, and provide intelligent responses with current information."""
        
        if context.get("web_search"):
            search_data = context["web_search"]
            if "results" in search_data:
                base_message += "\n\nCurrent web search results:\n"
                for result in search_data["results"]:
                    base_message += f"- {result.get('title', '')}: {result.get('description', '')}\n"
        
        if context.get("crypto_data"):
            crypto_data = context["crypto_data"]
            if "market" in crypto_data and not crypto_data.get("error"):
                base_message += "\n\nCurrent cryptocurrency market data:\n"
                for symbol, data in crypto_data["market"].items():
                    if isinstance(data, dict):
                        base_message += f"- {symbol}: ${data.get('price', 'N/A')} (24h: {data.get('change', 'N/A')}%)\n"
                
                if "trending" in crypto_data:
                    trending = crypto_data["trending"]
                    if "gainers" in trending:
                        base_message += "\nTop gainers:\n"
                        for gainer in trending["gainers"][:3]:
                            base_message += f"- {gainer.get('symbol', '')}: +{gainer.get('change', 0):.2f}%\n"
        
        if context.get("news"):
            news_data = context["news"]
            if "results" in news_data:
                base_message += "\n\nLatest news:\n"
                for article in news_data["results"]:
                    base_message += f"- {article.get('title', '')}\n"
        
        return base_message
    
    async def _generate_enhanced_mock_response(self, message: str, context: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """Generate enhanced mock response with context"""
        
        # Analyze what type of response to give
        if context.get("web_search"):
            yield "Based on my web search, "
            await asyncio.sleep(0.1)
            yield f"I found information about '{message}'. "
            await asyncio.sleep(0.1)
            
            if context["web_search"].get("results"):
                result = context["web_search"]["results"][0]
                yield f"According to recent sources: {result.get('description', 'Information found.')}"
                await asyncio.sleep(0.1)
        
        elif context.get("crypto_data"):
            yield "Looking at the current cryptocurrency market, "
            await asyncio.sleep(0.1)
            
            if context["crypto_data"].get("market"):
                btc_data = context["crypto_data"]["market"].get("BTCUSDT", {})
                if btc_data:
                    yield f"Bitcoin is currently trading at ${btc_data.get('price', 'N/A')}. "
                    await asyncio.sleep(0.1)
            
            yield "The crypto market is showing interesting movements. "
            await asyncio.sleep(0.1)
        
        else:
            yield f"I understand you're asking about: '{message}'. "
            await asyncio.sleep(0.1)
            yield "While I'm currently running in demo mode, in the full implementation "
            await asyncio.sleep(0.1)
            yield "I would connect to real AI APIs like OpenAI, Anthropic, and Groq "
            await asyncio.sleep(0.1)
            yield "to provide intelligent responses with real-time data access!"
            await asyncio.sleep(0.1)
    
    async def _generate_groq_response(self, messages: List[dict], model_id: str) -> AsyncGenerator[str, None]:
        """Generate response using Groq API for ultra-fast inference"""
        if not self.groq_api_key:
            async for chunk in self._generate_enhanced_mock_response("Groq API key not configured", {}):
                yield chunk
            return
        
        try:
            # Map model names to Groq model IDs
            groq_model_map = {
                "groq-llama-3.1-70b": "llama-3.1-70b-versatile",
                "groq-llama-3.1-8b": "llama-3.1-8b-instant",
                "groq-mixtral": "mixtral-8x7b-32768"
            }
            
            actual_model = groq_model_map.get(model_id, "llama-3.1-70b-versatile")
            
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": actual_model,
                "messages": messages,
                "stream": True,
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        async for line in response.content:
                            if line:
                                line_text = line.decode('utf-8').strip()
                                if line_text.startswith('data: '):
                                    data_text = line_text[6:]
                                    if data_text != '[DONE]':
                                        try:
                                            data = json.loads(data_text)
                                            content = data.get('choices', [{}])[0].get('delta', {}).get('content', '')
                                            if content:
                                                yield content
                                        except json.JSONDecodeError:
                                            continue
                    else:
                        yield f"Error: Groq API returned status {response.status}"
                        
        except Exception as e:
            yield f"Error with Groq API: {str(e)}"
    
    async def _generate_openai_response(self, messages: List[dict], model_id: str) -> AsyncGenerator[str, None]:
        """Generate response using OpenAI API"""
        if not self.openai_api_key:
            async for chunk in self._generate_enhanced_mock_response("OpenAI API key not configured", {}):
                yield chunk
            return
        
        # Implementation similar to Groq but for OpenAI
        async for chunk in self._generate_enhanced_mock_response("OpenAI response would go here", {}):
            yield chunk
    
    async def _generate_anthropic_response(self, messages: List[dict], model_id: str) -> AsyncGenerator[str, None]:
        """Generate response using Anthropic API"""
        if not self.anthropic_api_key:
            async for chunk in self._generate_enhanced_mock_response("Anthropic API key not configured", {}):
                yield chunk
            return
        
        # Implementation for Anthropic
        async for chunk in self._generate_enhanced_mock_response("Claude response would go here", {}):
            yield chunk