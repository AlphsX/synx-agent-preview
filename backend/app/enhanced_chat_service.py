from typing import List, AsyncGenerator, Dict, Any, Optional
import asyncio
import json
import aiohttp
import re
import redis.asyncio as redis
from datetime import datetime, timedelta
import hashlib
import logging
import time
from app.config import settings
from app.external_apis.search_service import search_service
from app.external_apis.binance import BinanceService
from app.ai.service import AIService
from app.vector.service import vector_service
from app.conversation_service import conversation_service
from app.auth.schemas import UserResponse

logger = logging.getLogger(__name__)

class EnhancedChatService:
    def __init__(self):
        self.ai_service = AIService()
        self.search_service = search_service
        self.binance_service = BinanceService()
        self.vector_service = vector_service
        
        # Redis for conversation history caching
        self.redis_client = None
        # Initialize Redis asynchronously when first needed
        
        # Context detection patterns
        self.search_patterns = [
            r'\b(search|find|look up|what is|tell me about|latest|news|current|recent)\b',
            r'\b(happening|trending|update|information about)\b',
            r'\?(.*?)$'  # Questions
        ]
        
        self.crypto_patterns = [
            r'\b(bitcoin|btc|ethereum|eth|crypto|cryptocurrency|binance|trading|price|market|coin|token)\b',
            r'\b(dogecoin|doge|litecoin|ltc|ripple|xrp|cardano|ada|solana|sol)\b',
            r'\$[A-Z]{2,10}\b'  # Crypto symbols like $BTC
        ]
        
        self.news_patterns = [
            r'\b(news|breaking|headline|recent news|latest news|today|yesterday)\b',
            r'\b(announcement|press release|update|report)\b'
        ]
        
        logger.info("EnhancedChatService initialized with AI router, search service, and Redis caching")
    
    async def _initialize_redis(self):
        """Initialize Redis connection for conversation caching"""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis connection established for conversation caching")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Conversation caching disabled.")
            self.redis_client = None
        
    async def generate_ai_response(self, 
                                 message: str,
                                 model_id: str,
                                 conversation_id: Optional[str] = None,
                                 conversation_history: List[Dict] = None,
                                 user_context: Optional[Dict[str, Any]] = None) -> AsyncGenerator[str, None]:
        """Generate AI response with enhanced context from external APIs and conversation history"""
        
        start_time = time.time()
        context_fetch_start = time.time()
        had_errors = False
        error_details = {}
        
        try:
            # Set default user context if not provided
            if user_context is None:
                user_context = {
                    "user_id": None,
                    "username": "anonymous",
                    "is_authenticated": False
                }
            
            # Get conversation history from database if available
            if conversation_id and not conversation_history:
                conversation_history = await self._get_conversation_history_from_db(conversation_id, user_context)
            
            if conversation_history is None:
                conversation_history = []
            
            # Analyze message for external data needs with intelligent context detection
            enhanced_context = await self._get_enhanced_context(message, user_context)
            context_fetch_time = (time.time() - context_fetch_start) * 1000  # Convert to milliseconds
            
            # Build system message with enhanced context and user information
            system_message = self._build_enhanced_system_message(enhanced_context, user_context)
            
            # Prepare messages for AI service
            messages = [{"role": "system", "content": system_message}]
            messages.extend(conversation_history[-10:])  # Last 10 messages for context
            messages.append({"role": "user", "content": message})
            
            # Store user message in database with user context
            user_message_id = None
            if conversation_id:
                user_message_id = await self._store_user_message(conversation_id, message, user_context)
            
            # Generate response using AI service with router
            ai_start_time = time.time()
            response_content = ""
            token_count = 0
            
            try:
                async for chunk in self.ai_service.chat(
                    messages=messages,
                    model_id=model_id,
                    stream=True,
                    temperature=0.7,
                    max_tokens=2000
                ):
                    response_content += chunk
                    token_count += len(chunk.split())  # Rough token estimation
                    yield chunk
            except Exception as ai_error:
                had_errors = True
                error_details = {"ai_service_error": str(ai_error), "used_fallback": True}
                logger.error(f"AI service error: {ai_error}")
                # Fallback to mock response
                async for chunk in self._generate_enhanced_mock_response(message, enhanced_context):
                    response_content += chunk
                    yield chunk
            
            ai_response_time = (time.time() - ai_start_time) * 1000
            total_processing_time = (time.time() - start_time) * 1000
            
            # Store AI response and cache the conversation if we have an ID
            assistant_message_id = None
            if conversation_id:
                assistant_message_id = await self._store_ai_response(
                    conversation_id, response_content, model_id, enhanced_context, user_context
                )
                await self._cache_conversation_message(
                    conversation_id, message, response_content, model_id, enhanced_context, user_context
                )
            
            # Track analytics for both messages (non-blocking)
            if conversation_id:
                try:
                    await self._track_message_analytics(
                        user_message_id, assistant_message_id, conversation_id,
                        user_context.get("user_id"), total_processing_time,
                        context_fetch_time, ai_response_time, enhanced_context,
                        token_count, had_errors, error_details
                    )
                except Exception as analytics_error:
                    # Don't let analytics errors break the main chat flow
                    logger.warning(f"Analytics tracking failed: {analytics_error}")
                
        except Exception as e:
            had_errors = True
            error_details = {"general_error": str(e)}
            logger.error(f"Error in generate_ai_response: {e}")
            # Fallback to enhanced mock response
            async for chunk in self._generate_enhanced_mock_response(message, {}):
                yield chunk
    
    async def _get_enhanced_context(self, message: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Intelligent context detection and data retrieval from multiple sources"""
        context = {}
        message_lower = message.lower()
        
        # Determine context needs using pattern matching
        needs_web_search = self._needs_web_search(message_lower)
        needs_crypto_data = self._needs_crypto_data(message_lower)
        needs_news = self._needs_news_search(message_lower)
        needs_vector_search = self._needs_vector_search(message_lower)
        
        # Concurrent data fetching for better performance
        tasks = []
        
        if needs_web_search:
            tasks.append(self._fetch_web_search_context(message))
        
        if needs_crypto_data:
            tasks.append(self._fetch_crypto_context(message))
        
        if needs_news:
            tasks.append(self._fetch_news_context(message))
        
        if needs_vector_search:
            tasks.append(self._fetch_vector_context(message))
        
        # Execute all context fetching tasks concurrently
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Merge results into context
            for result in results:
                if isinstance(result, dict) and not isinstance(result, Exception):
                    context.update(result)
                elif isinstance(result, Exception):
                    logger.warning(f"Context fetching error: {result}")
        
        logger.info(f"Enhanced context gathered: {list(context.keys())}")
        return context
    
    def _needs_web_search(self, message: str) -> bool:
        """Determine if message needs web search"""
        return any(re.search(pattern, message, re.IGNORECASE) for pattern in self.search_patterns)
    
    def _needs_crypto_data(self, message: str) -> bool:
        """Determine if message needs cryptocurrency data"""
        return any(re.search(pattern, message, re.IGNORECASE) for pattern in self.crypto_patterns)
    
    def _needs_news_search(self, message: str) -> bool:
        """Determine if message needs news search"""
        return any(re.search(pattern, message, re.IGNORECASE) for pattern in self.news_patterns)
    
    def _needs_vector_search(self, message: str) -> bool:
        """Determine if message needs vector database search"""
        # Look for specific domain knowledge queries
        domain_patterns = [
            r'\b(documentation|docs|guide|tutorial|how to|explain|definition)\b',
            r'\b(company|project|product|service|feature)\b'
        ]
        return any(re.search(pattern, message, re.IGNORECASE) for pattern in domain_patterns)
    
    async def _fetch_web_search_context(self, message: str) -> Dict[str, Any]:
        """Fetch web search context using SerpAPI as primary provider"""
        try:
            # Use unified search service with SerpAPI priority
            search_results = await self.search_service.search_web(message, count=5)
            
            if search_results:
                return {
                    "web_search": {
                        "query": message,
                        "results": search_results,
                        "provider": search_results[0].get("provider", "unknown") if search_results else "none"
                    }
                }
        except Exception as e:
            logger.error(f"Web search context error: {e}")
            return {"web_search": {"error": str(e), "query": message}}
        
        return {}
    
    async def _fetch_crypto_context(self, message: str) -> Dict[str, Any]:
        """Fetch cryptocurrency market context"""
        try:
            # Get market data and trending information
            market_task = self.binance_service.get_market_data()
            trending_task = self.binance_service.get_top_gainers_losers(limit=5)
            
            market_data, trending_data = await asyncio.gather(
                market_task, trending_task, return_exceptions=True
            )
            
            context_data = {}
            
            if not isinstance(market_data, Exception):
                context_data["market"] = market_data
            
            if not isinstance(trending_data, Exception):
                context_data["trending"] = trending_data
            
            if context_data:
                return {"crypto_data": context_data}
                
        except Exception as e:
            logger.error(f"Crypto context error: {e}")
            return {"crypto_data": {"error": str(e)}}
        
        return {}
    
    async def _fetch_news_context(self, message: str) -> Dict[str, Any]:
        """Fetch news context using search service"""
        try:
            # Use unified search service for news
            news_results = await self.search_service.search_news(message, count=5)
            
            if news_results:
                return {
                    "news": {
                        "query": message,
                        "results": news_results,
                        "provider": news_results[0].get("provider", "unknown") if news_results else "none"
                    }
                }
        except Exception as e:
            logger.error(f"News context error: {e}")
            return {"news": {"error": str(e), "query": message}}
        
        return {}
    
    async def _fetch_vector_context(self, message: str) -> Dict[str, Any]:
        """Fetch vector database context for domain knowledge"""
        try:
            # Search vector database for relevant documents
            vector_results = await self.vector_service.search(message, top_k=3)
            
            if vector_results:
                return {
                    "vector_search": {
                        "query": message,
                        "results": vector_results
                    }
                }
        except Exception as e:
            logger.error(f"Vector search context error: {e}")
            return {"vector_search": {"error": str(e), "query": message}}
        
        return {}
    
    def _build_enhanced_system_message(self, context: Dict[str, Any], user_context: Dict[str, Any] = None) -> str:
        """Build comprehensive system message with all available context"""
        # Build user-aware base message
        if user_context and user_context.get("is_authenticated"):
            username = user_context.get("username", "User")
            base_message = f"""You are Checkmate Spec Preview, an AI assistant inspired by Sync. You're witty, 
            informative, and have access to real-time information through multiple data sources. You can search 
            the web, get cryptocurrency data, access news, and retrieve domain-specific knowledge. 

            You are currently assisting {username}, who is authenticated. You can provide personalized responses 
            and maintain conversation context. Use the provided context to give accurate, current, and helpful responses."""
        else:
            base_message = """You are Checkmate Spec Preview, an AI assistant inspired by Sync. You're witty, 
            informative, and have access to real-time information through multiple data sources. You can search 
            the web, get cryptocurrency data, access news, and retrieve domain-specific knowledge. 

            You are currently in anonymous mode. Use the provided context to give accurate, current, and helpful responses."""
        
        context_sections = []
        
        # Web search context
        if context.get("web_search") and "results" in context["web_search"]:
            search_data = context["web_search"]
            provider = search_data.get("provider", "search engine")
            context_sections.append(f"\n=== WEB SEARCH RESULTS (via {provider}) ===")
            
            for i, result in enumerate(search_data["results"][:5], 1):
                title = result.get("title", "No title")
                description = result.get("description", "No description")
                url = result.get("url", "")
                source = result.get("source", "")
                
                context_sections.append(f"{i}. {title}")
                if description:
                    context_sections.append(f"   {description}")
                if source:
                    context_sections.append(f"   Source: {source}")
                context_sections.append("")
        
        # Cryptocurrency context
        if context.get("crypto_data"):
            crypto_data = context["crypto_data"]
            if "market" in crypto_data and not crypto_data.get("error"):
                context_sections.append("\n=== CRYPTOCURRENCY MARKET DATA ===")
                
                for symbol, data in crypto_data["market"].items():
                    if isinstance(data, dict):
                        price = data.get("price", "N/A")
                        change = data.get("change", "N/A")
                        volume = data.get("volume", "N/A")
                        context_sections.append(f"{symbol}: ${price} (24h: {change}%) Volume: {volume}")
                
                if "trending" in crypto_data and "gainers" in crypto_data["trending"]:
                    context_sections.append("\nTop Gainers:")
                    for gainer in crypto_data["trending"]["gainers"][:5]:
                        symbol = gainer.get("symbol", "")
                        change = gainer.get("change", 0)
                        context_sections.append(f"  {symbol}: +{change:.2f}%")
                
                if "trending" in crypto_data and "losers" in crypto_data["trending"]:
                    context_sections.append("\nTop Losers:")
                    for loser in crypto_data["trending"]["losers"][:3]:
                        symbol = loser.get("symbol", "")
                        change = loser.get("change", 0)
                        context_sections.append(f"  {symbol}: {change:.2f}%")
        
        # News context
        if context.get("news") and "results" in context["news"]:
            news_data = context["news"]
            provider = news_data.get("provider", "news service")
            context_sections.append(f"\n=== LATEST NEWS (via {provider}) ===")
            
            for i, article in enumerate(news_data["results"][:5], 1):
                title = article.get("title", "No title")
                description = article.get("description", "")
                published = article.get("published", "")
                source = article.get("source", "")
                
                context_sections.append(f"{i}. {title}")
                if description:
                    context_sections.append(f"   {description}")
                if published:
                    context_sections.append(f"   Published: {published}")
                if source:
                    context_sections.append(f"   Source: {source}")
                context_sections.append("")
        
        # Vector search context
        if context.get("vector_search") and "results" in context["vector_search"]:
            vector_data = context["vector_search"]
            context_sections.append("\n=== DOMAIN KNOWLEDGE ===")
            
            for i, result in enumerate(vector_data["results"][:3], 1):
                content = result.get("content", "")
                similarity = result.get("similarity_score", 0)
                metadata = result.get("metadata", {})
                
                context_sections.append(f"{i}. Relevance: {similarity:.2f}")
                context_sections.append(f"   {content[:200]}...")
                if metadata:
                    context_sections.append(f"   Metadata: {metadata}")
                context_sections.append("")
        
        # Combine all sections
        if context_sections:
            base_message += "\n" + "\n".join(context_sections)
            base_message += "\n=== END CONTEXT ===\n"
            base_message += "\nUse this context information to provide accurate and helpful responses. "
            base_message += "Cite sources when appropriate and indicate when information is current."
        
        return base_message
    
    async def _get_conversation_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """Retrieve conversation history from Redis cache"""
        if not self.redis_client:
            await self._initialize_redis()
        
        if not self.redis_client:
            return []
        
        try:
            cache_key = f"conversation:{conversation_id}"
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                history = json.loads(cached_data)
                logger.info(f"Retrieved conversation history for {conversation_id}: {len(history)} messages")
                return history
                
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
        
        return []
    
    async def _get_conversation_history_from_db(self, conversation_id: str, user_context: Dict[str, Any] = None) -> List[Dict[str, str]]:
        """Retrieve conversation history from database with Redis fallback"""
        try:
            # First try to get from database
            history = await conversation_service.get_conversation_history(
                conversation_id=conversation_id,
                limit=20
            )
            
            if history:
                logger.info(f"Retrieved conversation history from database for {conversation_id}: {len(history)} messages")
                return history
            
            # Fallback to Redis cache
            return await self._get_conversation_history(conversation_id)
            
        except Exception as e:
            logger.error(f"Error retrieving conversation history from database: {e}")
            # Fallback to Redis cache
            return await self._get_conversation_history(conversation_id)
    
    async def _store_user_message(self, conversation_id: str, message: str, user_context: Dict[str, Any] = None):
        """Store user message in database"""
        try:
            # Add user context to message metadata
            metadata = {}
            if user_context:
                metadata = {
                    "user_id": user_context.get("user_id"),
                    "username": user_context.get("username"),
                    "is_authenticated": user_context.get("is_authenticated", False)
                }
            
            message_obj = await conversation_service.add_message(
                conversation_id=conversation_id,
                content=message,
                role="user",
                metadata=metadata
            )
            logger.info(f"Stored user message in conversation {conversation_id} for user {user_context.get('username', 'anonymous')}")
            return str(message_obj.id) if message_obj else None
        except Exception as e:
            logger.error(f"Error storing user message: {e}")
            return None
    
    async def _store_ai_response(self, conversation_id: str, response: str, model_id: str, context: Dict[str, Any], user_context: Dict[str, Any] = None):
        """Store AI response in database with context data"""
        try:
            context_summary = {
                "context_types": list(context.keys()),
                "providers_used": self._extract_providers_from_context(context),
                "timestamp": datetime.now().isoformat(),
                "user_context": {
                    "user_id": user_context.get("user_id") if user_context else None,
                    "username": user_context.get("username") if user_context else "anonymous",
                    "is_authenticated": user_context.get("is_authenticated", False) if user_context else False
                }
            }
            
            message_obj = await conversation_service.add_message(
                conversation_id=conversation_id,
                content=response,
                role="assistant",
                model_id=model_id,
                context_data=context_summary
            )
            logger.info(f"Stored AI response in conversation {conversation_id} for user {user_context.get('username', 'anonymous') if user_context else 'anonymous'}")
            return str(message_obj.id) if message_obj else None
        except Exception as e:
            logger.error(f"Error storing AI response: {e}")
            return None
    
    def _extract_providers_from_context(self, context: Dict[str, Any]) -> List[str]:
        """Extract provider information from context data"""
        providers = []
        
        # Safely extract web search provider
        web_search = context.get("web_search") or {}
        if web_search.get("provider"):
            providers.append(web_search["provider"])
        
        # Safely extract news provider
        news = context.get("news") or {}
        if news.get("provider"):
            providers.append(news["provider"])
        
        # Check for crypto data
        if context.get("crypto_data"):
            providers.append("Binance")
        
        # Check for vector search
        if context.get("vector_search"):
            providers.append("Vector Database")
        
        return providers
    
    async def _cache_conversation_message(self, conversation_id: str, user_message: str, 
                                        ai_response: str, model_id: str, context: Dict[str, Any], user_context: Dict[str, Any] = None):
        """Cache conversation message in Redis"""
        if not self.redis_client:
            await self._initialize_redis()
        
        if not self.redis_client:
            return
        
        try:
            cache_key = f"conversation:{conversation_id}"
            
            # Get existing history
            existing_history = await self._get_conversation_history(conversation_id)
            
            # Add new messages
            timestamp = datetime.now().isoformat()
            new_messages = [
                {
                    "role": "user",
                    "content": user_message,
                    "timestamp": timestamp
                },
                {
                    "role": "assistant", 
                    "content": ai_response,
                    "model_id": model_id,
                    "context_used": list(context.keys()),
                    "timestamp": timestamp
                }
            ]
            
            # Combine and limit to last 50 messages
            updated_history = (existing_history + new_messages)[-50:]
            
            # Cache with 24 hour expiration
            await self.redis_client.setex(
                cache_key,
                timedelta(hours=24),
                json.dumps(updated_history)
            )
            
            logger.info(f"Cached conversation message for {conversation_id}")
            
        except Exception as e:
            logger.error(f"Error caching conversation message: {e}")
    
    async def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation summary and metadata from database"""
        try:
            # Get summary from database
            db_summary = await conversation_service.get_conversation_summary(conversation_id)
            
            if db_summary and not db_summary.get("error"):
                return db_summary
            
            # Fallback to Redis cache summary
            history = await self._get_conversation_history(conversation_id)
            
            if not history:
                return {"message_count": 0, "last_activity": None}
            
            # Calculate summary statistics from cache
            user_messages = [msg for msg in history if msg.get("role") == "user"]
            ai_messages = [msg for msg in history if msg.get("role") == "assistant"]
            
            # Get unique models used
            models_used = list(set(msg.get("model_id") for msg in ai_messages if msg.get("model_id")))
            
            # Get context types used
            context_types = set()
            for msg in ai_messages:
                if msg.get("context_used"):
                    context_types.update(msg["context_used"])
            
            return {
                "message_count": len(history),
                "user_messages": len(user_messages),
                "ai_messages": len(ai_messages),
                "models_used": models_used,
                "context_types_used": list(context_types),
                "last_activity": history[-1].get("timestamp") if history else None,
                "source": "cache"
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation summary: {e}")
            return {"error": str(e)}
    
    async def clear_conversation_history(self, conversation_id: str) -> bool:
        """Clear conversation history from cache and database"""
        try:
            # Clear from database (delete all messages)
            messages = await conversation_service.get_conversation_messages(conversation_id)
            if messages:
                # Note: In a real implementation, you might want to soft-delete or archive
                # For now, we'll just clear the cache and keep database intact
                logger.info(f"Found {len(messages)} messages in conversation {conversation_id}")
            
            # Clear from Redis cache
            if not self.redis_client:
                await self._initialize_redis()
            
            if self.redis_client:
                cache_key = f"conversation:{conversation_id}"
                result = await self.redis_client.delete(cache_key)
                logger.info(f"Cleared conversation cache for {conversation_id}")
                return bool(result)
            
            return True
            
        except Exception as e:
            logger.error(f"Error clearing conversation history: {e}")
            return False
    
    async def create_conversation(self, title: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new conversation"""
        try:
            conversation = await conversation_service.create_conversation(
                title=title,
                user_id=user_id,
                metadata={
                    "enhanced_features": [
                        "real_time_search",
                        "crypto_data", 
                        "news_updates",
                        "vector_search",
                        "conversation_history"
                    ],
                    "created_by": "enhanced_chat_service"
                }
            )
            
            logger.info(f"Created conversation {conversation.id}")
            return {
                "id": conversation.id,
                "title": conversation.title,
                "user_id": conversation.user_id,
                "created_at": conversation.created_at.isoformat(),
                "enhanced_features": True
            }
            
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            raise
    
    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation details"""
        try:
            conversation = await conversation_service.get_conversation(conversation_id)
            
            if not conversation:
                return None
            
            return {
                "id": conversation.id,
                "title": conversation.title,
                "user_id": conversation.user_id,
                "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
                "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
                "metadata": conversation.metadata
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation: {e}")
            return None
    
    async def get_user_conversations(self, user_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversations for a user"""
        try:
            conversations = await conversation_service.get_user_conversations(
                user_id=user_id,
                limit=limit
            )
            
            result = []
            for conv in conversations:
                # Get message count for each conversation
                summary = await conversation_service.get_conversation_summary(conv.id)
                
                result.append({
                    "id": conv.id,
                    "title": conv.title,
                    "user_id": conv.user_id,
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat(),
                    "message_count": summary.get("total_messages", 0),
                    "last_message_at": summary.get("last_message_at"),
                    "models_used": summary.get("models_used", []),
                    "metadata": conv.metadata
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting user conversations: {e}")
            return []
    
    async def _track_message_analytics(
        self,
        user_message_id: Optional[str],
        assistant_message_id: Optional[str],
        conversation_id: str,
        user_id: Optional[int],
        total_processing_time: float,
        context_fetch_time: float,
        ai_response_time: float,
        context_data: Dict[str, Any],
        token_count: int,
        had_errors: bool,
        error_details: Dict[str, Any]
    ):
        """Track analytics for messages (async background task)"""
        try:
            # Use safe analytics service to avoid breaking chat flow
            from app.analytics.service_safe import safe_analytics_service
            
            # Track analytics for assistant message (the one with processing metrics)
            if assistant_message_id:
                await safe_analytics_service.track_message_analytics(
                    message_id=assistant_message_id,
                    conversation_id=conversation_id,
                    user_id=user_id,
                    processing_time=total_processing_time,
                    context_data=context_data,
                    tokens_used=token_count,
                    had_errors=had_errors,
                    error_details=error_details
                )
            
            # Track basic analytics for user message if needed
            if user_message_id:
                await safe_analytics_service.track_message_analytics(
                    message_id=user_message_id,
                    conversation_id=conversation_id,
                    user_id=user_id,
                    processing_time=0.0,  # User messages don't have processing time
                    context_data={},
                    tokens_used=0,
                    had_errors=False,
                    error_details={}
                )
                
        except Exception as e:
            # Don't let analytics errors break the main flow
            logger.warning(f"Analytics tracking failed gracefully: {e}")
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get available AI models with enhanced capabilities"""
        try:
            models = await self.ai_service.get_available_models()
            
            # Add enhanced capabilities info to each model
            enhanced_models = []
            for model in models:
                enhanced_model = {
                    **model,
                    "enhanced_features": [
                        "real_time_web_search",
                        "cryptocurrency_data",
                        "news_updates",
                        "vector_knowledge_search",
                        "conversation_history",
                        "intelligent_context_detection",
                        "analytics_tracking"
                    ]
                }
                enhanced_models.append(enhanced_model)
            
            return enhanced_models
            
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return []
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all enhanced chat services"""
        try:
            status = {
                "ai_service": {
                    "available": True,
                    "models_count": len(await self.get_available_models()),
                    "status": "operational"
                },
                "search_service": {
                    "available": True,
                    "providers": await self.search_service.get_provider_status(),
                    "status": "operational"
                },
                "crypto_service": {
                    "available": self.binance_service.is_available(),
                    "status": "operational" if self.binance_service.is_available() else "unavailable"
                },
                "vector_service": {
                    "available": True,  # Assume available for now
                    "status": "operational"
                },
                "redis_cache": {
                    "available": self.redis_client is not None,
                    "status": "operational" if self.redis_client else "unavailable"
                },
                "analytics": {
                    "available": True,
                    "tracking_enabled": True,
                    "status": "operational"
                }
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return {"error": str(e)}
    
    async def get_conversation_with_messages(
        self, 
        conversation_id: str, 
        limit: int = 50
    ) -> Optional[Dict[str, Any]]:
        """Get conversation with messages and analytics"""
        try:
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                return None
            
            # Get messages
            messages = await conversation_service.get_conversation_messages(
                conversation_id=conversation_id,
                limit=limit,
                include_context=True
            )
            
            # Get analytics summary
            summary = await self.get_conversation_summary(conversation_id)
            
            return {
                **conversation,
                "messages": messages,
                "summary": summary,
                "analytics_available": True
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation with messages: {e}")
            return None
    
    async def get_conversation_with_messages(self, conversation_id: str, limit: int = 50) -> Optional[Dict[str, Any]]:
        """Get conversation with its messages"""
        try:
            result = await conversation_service.get_conversation_with_messages(
                conversation_id=conversation_id,
                message_limit=limit
            )
            
            if not result:
                return None
            
            return {
                "conversation": {
                    "id": result["conversation"].id,
                    "title": result["conversation"].title,
                    "user_id": result["conversation"].user_id,
                    "created_at": result["conversation"].created_at.isoformat(),
                    "updated_at": result["conversation"].updated_at.isoformat(),
                    "metadata": result["conversation"].metadata
                },
                "messages": [
                    {
                        "id": msg.id,
                        "content": msg.content,
                        "role": msg.role,
                        "model_id": msg.model_id,
                        "context_data": msg.context_data,
                        "created_at": msg.created_at.isoformat()
                    }
                    for msg in result["messages"]
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation with messages: {e}")
            return None
    
    async def _generate_enhanced_mock_response(self, message: str, context: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """Generate enhanced mock response with context when AI services are unavailable"""
        
        # Analyze what type of response to give based on context
        if context.get("web_search") and context["web_search"].get("results"):
            yield "Based on my web search using "
            provider = context["web_search"].get("provider", "search engine")
            yield f"{provider}, "
            await asyncio.sleep(0.1)
            
            result = context["web_search"]["results"][0]
            yield f"I found that {result.get('title', 'information')}. "
            await asyncio.sleep(0.1)
            
            if result.get("description"):
                yield f"{result['description'][:200]}... "
                await asyncio.sleep(0.1)
        
        elif context.get("crypto_data") and context["crypto_data"].get("market"):
            yield "Looking at the current cryptocurrency market data, "
            await asyncio.sleep(0.1)
            
            market = context["crypto_data"]["market"]
            if "BTCUSDT" in market:
                btc_data = market["BTCUSDT"]
                price = btc_data.get("price", "N/A")
                change = btc_data.get("change", "N/A")
                yield f"Bitcoin is trading at ${price} with a 24h change of {change}%. "
                await asyncio.sleep(0.1)
            
            if context["crypto_data"].get("trending", {}).get("gainers"):
                top_gainer = context["crypto_data"]["trending"]["gainers"][0]
                yield f"The top gainer today is {top_gainer.get('symbol', 'N/A')} "
                yield f"with a {top_gainer.get('change', 0):.2f}% increase. "
                await asyncio.sleep(0.1)
        
        elif context.get("news") and context["news"].get("results"):
            yield "Based on the latest news, "
            await asyncio.sleep(0.1)
            
            news_item = context["news"]["results"][0]
            yield f"{news_item.get('title', 'there are recent updates')}. "
            await asyncio.sleep(0.1)
            
            if news_item.get("description"):
                yield f"{news_item['description'][:150]}... "
                await asyncio.sleep(0.1)
        
        elif context.get("vector_search") and context["vector_search"].get("results"):
            yield "From my knowledge base, "
            await asyncio.sleep(0.1)
            
            vector_result = context["vector_search"]["results"][0]
            content = vector_result.get("content", "")
            yield f"{content[:200]}... "
            await asyncio.sleep(0.1)
        
        else:
            yield f"I understand you're asking about: '{message}'. "
            await asyncio.sleep(0.1)
            yield "I'm currently running in demo mode, but I have access to "
            await asyncio.sleep(0.1)
            yield "real-time web search, cryptocurrency data, news updates, "
            await asyncio.sleep(0.1)
            yield "and domain knowledge through vector search. "
            await asyncio.sleep(0.1)
            yield "Configure your AI API keys to enable full intelligent responses!"
            await asyncio.sleep(0.1)
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get available AI models with enhanced capabilities"""
        models = self.ai_service.get_available_models()
        
        # Add enhanced capabilities metadata
        enhanced_models = []
        for model in models:
            enhanced_model = {
                "id": model.id,
                "name": model.name,
                "provider": model.provider,
                "description": model.description,
                "available": model.available,
                "enhanced_features": [
                    "real_time_web_search",
                    "cryptocurrency_data", 
                    "news_updates",
                    "vector_knowledge_search",
                    "conversation_history"
                ]
            }
            enhanced_models.append(enhanced_model)
        
        return enhanced_models
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get status of all enhanced chat services"""
        status = {
            "ai_service": self.ai_service.get_provider_status(),
            "search_service": await self.search_service.get_provider_status(),
            "crypto_service": self.binance_service.is_available(),
            "vector_service": await self.vector_service.health_check() if hasattr(self.vector_service, 'health_check') else True,
            "redis_cache": self.redis_client is not None
        }
        
        return status