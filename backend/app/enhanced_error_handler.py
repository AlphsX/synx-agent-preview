"""
Enhanced Error Handler for AI Chat Service

This module provides comprehensive error handling and fallback mechanisms
to prevent NoneType errors and ensure graceful degradation.
"""

import logging
import traceback
from typing import Any, Dict, List, Optional, AsyncGenerator
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)


class SafeDataHandler:
    """Safe data handling utilities to prevent NoneType errors"""
    
    @staticmethod
    def safe_get(data: Any, key: str, default: Any = None) -> Any:
        """Safely get value from dictionary-like object"""
        try:
            if data is None:
                return default
            if isinstance(data, dict):
                return data.get(key, default)
            if hasattr(data, key):
                return getattr(data, key, default)
            return default
        except Exception:
            return default
    
    @staticmethod
    def safe_index(data: Any, index: int, default: Any = None) -> Any:
        """Safely get item from list-like object"""
        try:
            if data is None:
                return default
            if isinstance(data, (list, tuple)) and len(data) > index >= 0:
                return data[index]
            return default
        except Exception:
            return default
    
    @staticmethod
    def safe_list(data: Any) -> List[Any]:
        """Safely convert to list"""
        try:
            if data is None:
                return []
            if isinstance(data, list):
                return data
            if isinstance(data, (tuple, set)):
                return list(data)
            return [data]
        except Exception:
            return []
    
    @staticmethod
    def safe_dict(data: Any) -> Dict[str, Any]:
        """Safely convert to dictionary"""
        try:
            if data is None:
                return {}
            if isinstance(data, dict):
                return data
            return {}
        except Exception:
            return {}
    
    @staticmethod
    def safe_string(data: Any, default: str = "") -> str:
        """Safely convert to string"""
        try:
            if data is None:
                return default
            return str(data)
        except Exception:
            return default
    
    @staticmethod
    def safe_int(data: Any, default: int = 0) -> int:
        """Safely convert to integer"""
        try:
            if data is None:
                return default
            return int(data)
        except Exception:
            return default
    
    @staticmethod
    def safe_float(data: Any, default: float = 0.0) -> float:
        """Safely convert to float"""
        try:
            if data is None:
                return default
            return float(data)
        except Exception:
            return default


def safe_async_generator(fallback_message: str = "Oops! Something went wrong on my end: 'NoneType' object is not subscriptable 😅 Let me try to help you anyway! 💫"):
    """Decorator to safely handle async generators and provide fallback responses"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                async for item in func(*args, **kwargs):
                    yield item
            except TypeError as e:
                if "'NoneType' object is not subscriptable" in str(e):
                    logger.error(f"NoneType subscriptable error in {func.__name__}: {e}")
                    yield fallback_message
                else:
                    logger.error(f"TypeError in {func.__name__}: {e}")
                    yield f"Error: {str(e)}"
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                logger.error(traceback.format_exc())
                yield f"Error: {str(e)}"
        return wrapper
    return decorator


def safe_async_function(fallback_result: Any = None):
    """Decorator to safely handle async functions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except TypeError as e:
                if "'NoneType' object is not subscriptable" in str(e):
                    logger.error(f"NoneType subscriptable error in {func.__name__}: {e}")
                    return fallback_result
                else:
                    logger.error(f"TypeError in {func.__name__}: {e}")
                    return fallback_result
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                logger.error(traceback.format_exc())
                return fallback_result
        return wrapper
    return decorator


class EnhancedErrorHandler:
    """Enhanced error handler with specific handling for common AI service errors"""
    
    def __init__(self):
        self.safe_data = SafeDataHandler()
    
    async def safe_generate_mock_response(self, message: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        """Generate a safe mock response when AI services fail"""
        try:
            context = self.safe_data.safe_dict(context)
            
            # Check if we have any context to work with
            has_web_search = bool(context.get("web_search", {}).get("results"))
            has_crypto_data = bool(context.get("crypto_data", {}).get("market"))
            has_news = bool(context.get("news", {}).get("results"))
            has_vector_search = bool(context.get("vector_search", {}).get("results"))
            
            # Generate contextual response
            if has_web_search or has_news:
                yield "I found some relevant information for you! "
                
                # Web search results
                web_results = self.safe_data.safe_list(
                    self.safe_data.safe_get(
                        self.safe_data.safe_get(context, "web_search", {}), 
                        "results", []
                    )
                )
                
                if web_results:
                    yield "Based on recent web search results:\n\n"
                    for i, result in enumerate(web_results[:3], 1):
                        result = self.safe_data.safe_dict(result)
                        title = self.safe_data.safe_string(result.get("title", ""), "Untitled")
                        description = self.safe_data.safe_string(result.get("description", ""), "No description available")
                        yield f"{i}. **{title}**\n   {description}\n\n"
                
                # News results
                news_results = self.safe_data.safe_list(
                    self.safe_data.safe_get(
                        self.safe_data.safe_get(context, "news", {}), 
                        "results", []
                    )
                )
                
                if news_results:
                    yield "Latest news updates:\n\n"
                    for i, article in enumerate(news_results[:2], 1):
                        article = self.safe_data.safe_dict(article)
                        title = self.safe_data.safe_string(article.get("title", ""), "Untitled")
                        description = self.safe_data.safe_string(article.get("description", ""), "No description available")
                        yield f"{i}. **{title}**\n   {description}\n\n"
            
            elif has_crypto_data:
                yield "Here's the latest cryptocurrency market information:\n\n"
                
                crypto_data = self.safe_data.safe_dict(context.get("crypto_data", {}))
                market_data = self.safe_data.safe_dict(crypto_data.get("market", {}))
                
                for symbol, data in market_data.items():
                    data = self.safe_data.safe_dict(data)
                    price = self.safe_data.safe_string(data.get("price", "N/A"))
                    change = self.safe_data.safe_string(data.get("change", "N/A"))
                    yield f"**{symbol}**: ${price} (24h change: {change}%)\n"
                
                yield "\n"
            
            elif has_vector_search:
                yield "Based on the knowledge base, here's what I found:\n\n"
                
                vector_results = self.safe_data.safe_list(
                    self.safe_data.safe_get(
                        self.safe_data.safe_get(context, "vector_search", {}), 
                        "results", []
                    )
                )
                
                for i, result in enumerate(vector_results[:2], 1):
                    result = self.safe_data.safe_dict(result)
                    content = self.safe_data.safe_string(result.get("content", ""), "No content available")
                    similarity = self.safe_data.safe_float(result.get("similarity_score", 0))
                    yield f"{i}. (Relevance: {similarity:.2f})\n   {content[:200]}...\n\n"
            
            else:
                # Generic helpful response
                yield f"I understand you're asking about: '{message}'\n\n"
                yield "While I'm experiencing some technical difficulties with my AI processing, "
                yield "I'm still here to help! Could you please:\n\n"
                yield "1. Try rephrasing your question\n"
                yield "2. Be more specific about what you're looking for\n"
                yield "3. Let me know if you need information about a particular topic\n\n"
                yield "I have access to web search, cryptocurrency data, news, and knowledge base - "
                yield "so I can still provide you with current and relevant information! 🚀"
            
        except Exception as e:
            logger.error(f"Error in safe_generate_mock_response: {e}")
            yield "I apologize, but I'm experiencing technical difficulties. Please try again in a moment. 🔧"
    
    def safe_extract_providers(self, context: Dict[str, Any]) -> List[str]:
        """Safely extract provider information from context"""
        try:
            context = self.safe_data.safe_dict(context)
            providers = []
            
            # Web search provider
            web_search = self.safe_data.safe_dict(context.get("web_search", {}))
            web_provider = self.safe_data.safe_string(web_search.get("provider", ""))
            if web_provider:
                providers.append(web_provider)
            
            # News provider
            news = self.safe_data.safe_dict(context.get("news", {}))
            news_provider = self.safe_data.safe_string(news.get("provider", ""))
            if news_provider:
                providers.append(news_provider)
            
            # Crypto data
            if context.get("crypto_data"):
                providers.append("Binance")
            
            # Vector search
            if context.get("vector_search"):
                providers.append("Vector Database")
            
            return providers
            
        except Exception as e:
            logger.error(f"Error extracting providers: {e}")
            return []
    
    def safe_build_context_summary(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Safely build context summary"""
        try:
            context = self.safe_data.safe_dict(context)
            
            return {
                "context_types": list(context.keys()) if context else [],
                "providers_used": self.safe_extract_providers(context),
                "has_web_search": bool(context.get("web_search", {}).get("results")),
                "has_crypto_data": bool(context.get("crypto_data", {}).get("market")),
                "has_news": bool(context.get("news", {}).get("results")),
                "has_vector_search": bool(context.get("vector_search", {}).get("results")),
                "timestamp": self.safe_data.safe_string(context.get("timestamp", ""))
            }
            
        except Exception as e:
            logger.error(f"Error building context summary: {e}")
            return {
                "context_types": [],
                "providers_used": [],
                "has_web_search": False,
                "has_crypto_data": False,
                "has_news": False,
                "has_vector_search": False,
                "timestamp": ""
            }


# Global error handler instance
error_handler = EnhancedErrorHandler()