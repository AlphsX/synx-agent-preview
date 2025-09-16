from abc import ABC, abstractmethod
from typing import List, AsyncGenerator, Dict, Any, Optional
from ..models import ChatMessage, ChatResponse, StreamChunk, AIModel


class BaseAIProvider(ABC):
    """Base class for AI providers with enhanced error handling and retry capabilities"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.available = api_key is not None
        # Default retry configuration - can be overridden by subclasses
        self.max_retries = 3
        self.base_delay = 1.0
        self.max_delay = 60.0
    
    @abstractmethod
    async def generate_response(
        self, 
        messages: List[ChatMessage], 
        model_id: str,
        stream: bool = True,
        **kwargs
    ) -> AsyncGenerator[StreamChunk, None]:
        """Generate AI response with retry logic and error handling"""
        pass
    
    @abstractmethod
    async def check_availability(self, model_id: str) -> bool:
        """Check if model is available with retry logic"""
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[AIModel]:
        """Get list of supported models"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get provider name"""
        pass
    
    def is_available(self) -> bool:
        """Check if provider is available"""
        return self.available
    
    def get_model_parameters(self, model_id: str, **kwargs) -> Dict[str, Any]:
        """Get optimized parameters for a specific model (can be overridden by subclasses)"""
        return kwargs
    
    def get_retry_config(self) -> Dict[str, Any]:
        """Get retry configuration for this provider"""
        return {
            "max_retries": self.max_retries,
            "base_delay": self.base_delay,
            "max_delay": self.max_delay
        }