"""
Enhanced error handler with safe data handling and async generators.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, AsyncGenerator
from functools import wraps

logger = logging.getLogger(__name__)


class SafeDataHandler:
    """Safe data handling to prevent NoneType errors."""
    
    def safe_dict(self, data: Any) -> Dict[str, Any]:
        """Safely convert data to dict, return empty dict if None or invalid."""
        if data is None:
            return {}
        if isinstance(data, dict):
            return data
        return {}
    
    def safe_list(self, data: Any) -> List[Any]:
        """Safely convert data to list, return empty list if None or invalid."""
        if data is None:
            return []
        if isinstance(data, list):
            return data
        return []
    
    def safe_string(self, data: Any, default: str = "") -> str:
        """Safely convert data to string, return default if None."""
        if data is None:
            return default
        return str(data)
    
    def safe_get(self, data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """Safely get value from dict, handle None dict."""
        if data is None or not isinstance(data, dict):
            return default
        return data.get(key, default)


class ErrorHandler:
    """Enhanced error handler with fallback responses."""
    
    def __init__(self):
        self.safe_data = SafeDataHandler()
    
    async def safe_generate_mock_response(self, message: str, context: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """Generate a safe mock response when AI service fails."""
        try:
            # Create a friendly fallback response
            fallback_message = f"""I'm having some technical difficulties right now, but I'm still here to help! 😅

You asked: "{message}"

While I can't access real-time data at the moment, I can still provide general information and assistance. Let me know if you'd like me to help with something else! 💫"""
            
            # Stream the response in chunks
            words = fallback_message.split()
            for i in range(0, len(words), 3):  # Send 3 words at a time
                chunk = " ".join(words[i:i+3]) + " "
                yield chunk
                await asyncio.sleep(0.1)  # Small delay for streaming effect
                
        except Exception as e:
            logger.error(f"Error in safe_generate_mock_response: {e}")
            yield "I'm experiencing technical difficulties. Please try again later. 🔧"
    
    def safe_extract_providers(self, context: Dict[str, Any]) -> List[str]:
        """Safely extract provider information from context."""
        providers = []
        
        try:
            context = self.safe_data.safe_dict(context)
            
            # Check web search providers
            web_search = self.safe_data.safe_dict(context.get("web_search", {}))
            if web_search:
                provider = self.safe_data.safe_string(web_search.get("provider", ""))
                if provider:
                    providers.append(provider)
            
            # Check news providers
            news = self.safe_data.safe_dict(context.get("news", {}))
            if news:
                provider = self.safe_data.safe_string(news.get("provider", ""))
                if provider:
                    providers.append(provider)
            
            # Check crypto providers
            crypto_data = self.safe_data.safe_dict(context.get("crypto_data", {}))
            if crypto_data and not crypto_data.get("error"):
                providers.append("Binance")
            
            # Check vector search
            vector_search = self.safe_data.safe_dict(context.get("vector_search", {}))
            if vector_search and not vector_search.get("error"):
                providers.append("Vector Database")
                
        except Exception as e:
            logger.error(f"Error extracting providers: {e}")
        
        return providers


def safe_async_generator(fallback_message: str):
    """Decorator to safely handle async generator functions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                async for chunk in func(*args, **kwargs):
                    yield chunk
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                # Yield the fallback message
                yield fallback_message
        return wrapper
    return decorator


# Global instances
error_handler = ErrorHandler()
safe_data_handler = SafeDataHandler()