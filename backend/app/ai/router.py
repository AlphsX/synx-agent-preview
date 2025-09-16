import asyncio
from typing import List, AsyncGenerator, Dict, Any, Optional
from datetime import datetime, timedelta
from ..config import settings
from .models import ChatMessage, StreamChunk, AIModel, ModelAvailability
from .providers.groq_provider import GroqProvider
from .providers.openai_provider import OpenAIProvider
from .providers.anthropic_provider import AnthropicProvider
from .providers.base import BaseAIProvider
import logging

logger = logging.getLogger(__name__)


class AIModelRouter:
    """
    Central router for AI model providers with fallback logic and availability checking.
    
    This class manages multiple AI providers (Groq, OpenAI, Anthropic) and provides:
    - Unified interface for all providers
    - Model availability checking and caching
    - Automatic fallback when models are unavailable
    - Streaming response handling
    - Error handling and recovery
    """
    
    def __init__(self):
        # Initialize providers
        self.providers: Dict[str, BaseAIProvider] = {
            "groq": GroqProvider(settings.GROQ_API_KEY),
            "openai": OpenAIProvider(settings.OPENAI_API_KEY),
            "anthropic": AnthropicProvider(settings.ANTHROPIC_API_KEY)
        }
        
        # Model availability cache
        self.availability_cache: Dict[str, ModelAvailability] = {}
        self.cache_duration = timedelta(minutes=5)  # Cache for 5 minutes
        
        # Fallback order for each provider
        self.fallback_models = {
            "groq": ["llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
            "openai": ["gpt-4o-mini", "gpt-3.5-turbo", "gpt-4"],
            "anthropic": ["claude-3-5-haiku-20241022", "claude-3-sonnet-20240229", "claude-3-5-sonnet-20241022"]
        }
        
        logger.info("AIModelRouter initialized with providers: %s", list(self.providers.keys()))
    
    def get_all_models(self) -> List[AIModel]:
        """Get all available models from all providers"""
        all_models = []
        for provider in self.providers.values():
            if provider.is_available():
                all_models.extend(provider.get_supported_models())
        return all_models
    
    def get_models_by_provider(self, provider_name: str) -> List[AIModel]:
        """Get models for a specific provider"""
        provider = self.providers.get(provider_name)
        if provider and provider.is_available():
            return provider.get_supported_models()
        return []
    
    def get_provider_for_model(self, model_id: str) -> Optional[str]:
        """Determine which provider handles a specific model"""
        for provider_name, provider in self.providers.items():
            if provider.is_available():
                for model in provider.get_supported_models():
                    if model.id == model_id:
                        return provider_name
        return None
    
    async def check_model_availability(self, model_id: str, force_check: bool = False) -> bool:
        """
        Check if a model is available, with caching.
        
        Args:
            model_id: The model ID to check
            force_check: Force a fresh check, ignoring cache
            
        Returns:
            True if model is available, False otherwise
        """
        # Check cache first
        if not force_check and model_id in self.availability_cache:
            cached = self.availability_cache[model_id]
            if datetime.now() - cached.last_checked < self.cache_duration:
                return cached.available
        
        # Find provider for this model
        provider_name = self.get_provider_for_model(model_id)
        if not provider_name:
            logger.warning(f"No provider found for model: {model_id}")
            return False
        
        provider = self.providers[provider_name]
        if not provider.is_available():
            logger.warning(f"Provider {provider_name} not available for model: {model_id}")
            return False
        
        # Check availability
        try:
            available = await provider.check_availability(model_id)
            
            # Update cache
            self.availability_cache[model_id] = ModelAvailability(
                model_id=model_id,
                available=available,
                last_checked=datetime.now()
            )
            
            return available
        except Exception as e:
            logger.error(f"Error checking availability for {model_id}: {e}")
            
            # Update cache with error
            self.availability_cache[model_id] = ModelAvailability(
                model_id=model_id,
                available=False,
                error=str(e),
                last_checked=datetime.now()
            )
            
            return False
    
    def get_fallback_model(self, original_model_id: str) -> Optional[str]:
        """
        Get a fallback model when the original is unavailable.
        
        Args:
            original_model_id: The model that failed
            
        Returns:
            A fallback model ID or None if no fallback available
        """
        provider_name = self.get_provider_for_model(original_model_id)
        if not provider_name:
            # Try to find any available model from any provider
            for provider_name, fallback_list in self.fallback_models.items():
                provider = self.providers.get(provider_name)
                if provider and provider.is_available():
                    return fallback_list[0]  # Return first fallback
            return None
        
        # Get fallback models for the same provider
        fallback_list = self.fallback_models.get(provider_name, [])
        for fallback_model in fallback_list:
            if fallback_model != original_model_id:
                return fallback_model
        
        return None
    
    async def generate_response(
        self, 
        messages: List[ChatMessage], 
        model_id: str,
        stream: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        enable_fallback: bool = True,
        **kwargs
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Generate AI response with automatic fallback handling.
        
        Args:
            messages: List of chat messages
            model_id: The model to use
            stream: Whether to stream the response
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            enable_fallback: Whether to use fallback models on failure
            **kwargs: Additional parameters for the AI provider
            
        Yields:
            StreamChunk objects containing the response
        """
        original_model_id = model_id
        attempted_models = []
        
        while model_id and model_id not in attempted_models:
            attempted_models.append(model_id)
            
            # Find provider for this model
            provider_name = self.get_provider_for_model(model_id)
            if not provider_name:
                logger.error(f"No provider found for model: {model_id}")
                if enable_fallback:
                    model_id = self.get_fallback_model(model_id)
                    if model_id:
                        logger.info(f"Falling back to model: {model_id}")
                        continue
                
                yield StreamChunk(
                    content=f"Error: No provider available for model {original_model_id}",
                    model_id=original_model_id,
                    provider="unknown",
                    finish_reason="error",
                    done=True
                )
                return
            
            provider = self.providers[provider_name]
            if not provider.is_available():
                logger.warning(f"Provider {provider_name} not available")
                if enable_fallback:
                    model_id = self.get_fallback_model(model_id)
                    if model_id:
                        logger.info(f"Falling back to model: {model_id}")
                        continue
                
                yield StreamChunk(
                    content=f"Error: Provider {provider_name} not available",
                    model_id=original_model_id,
                    provider=provider_name,
                    finish_reason="error",
                    done=True
                )
                return
            
            # Check model availability
            if not await self.check_model_availability(model_id):
                logger.warning(f"Model {model_id} not available")
                if enable_fallback:
                    fallback_model = self.get_fallback_model(model_id)
                    if fallback_model and fallback_model not in attempted_models:
                        model_id = fallback_model
                        logger.info(f"Falling back to model: {model_id}")
                        continue
                
                yield StreamChunk(
                    content=f"Error: Model {model_id} not available",
                    model_id=original_model_id,
                    provider=provider_name,
                    finish_reason="error",
                    done=True
                )
                return
            
            # Generate response
            try:
                logger.info(f"Generating response with {provider_name}:{model_id}")
                
                error_occurred = False
                async for chunk in provider.generate_response(
                    messages=messages,
                    model_id=model_id,
                    stream=stream,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                ):
                    # Check if this is an error chunk
                    if chunk.finish_reason == "error":
                        error_occurred = True
                        if enable_fallback:
                            logger.warning(f"Error with {model_id}: {chunk.content}")
                            break  # Try fallback
                        else:
                            yield chunk  # Return error if no fallback
                            return
                    else:
                        yield chunk
                        if chunk.done:
                            return  # Successfully completed
                
                # If we get here and error_occurred is True, try fallback
                if error_occurred and enable_fallback:
                    fallback_model = self.get_fallback_model(model_id)
                    if fallback_model and fallback_model not in attempted_models:
                        model_id = fallback_model
                        logger.info(f"Falling back to model: {model_id}")
                        continue
                
                # If no fallback or fallback failed, return error
                if error_occurred:
                    yield StreamChunk(
                        content=f"Error: All models failed for request",
                        model_id=original_model_id,
                        provider=provider_name,
                        finish_reason="error",
                        done=True
                    )
                    return
                
            except Exception as e:
                logger.error(f"Unexpected error with {provider_name}:{model_id}: {e}")
                
                if enable_fallback:
                    fallback_model = self.get_fallback_model(model_id)
                    if fallback_model and fallback_model not in attempted_models:
                        model_id = fallback_model
                        logger.info(f"Falling back to model: {model_id}")
                        continue
                
                yield StreamChunk(
                    content=f"Error: {str(e)}",
                    model_id=original_model_id,
                    provider=provider_name,
                    finish_reason="error",
                    done=True
                )
                return
        
        # If we've exhausted all models
        yield StreamChunk(
            content="Error: All available models have been tried and failed",
            model_id=original_model_id,
            provider="unknown",
            finish_reason="error",
            done=True
        )
    
    async def generate_mock_response(
        self, 
        messages: List[ChatMessage], 
        model_id: str,
        stream: bool = True
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Generate a mock response when no real providers are available.
        This is useful for demo mode or when API keys are not configured.
        """
        mock_responses = [
            "I'm currently running in demo mode. ",
            "In the full implementation, I would connect to real AI APIs like ",
            f"{model_id} to provide intelligent responses. ",
            "Please configure your API keys to enable full functionality!"
        ]
        
        for i, response_part in enumerate(mock_responses):
            await asyncio.sleep(0.1)  # Simulate streaming delay
            yield StreamChunk(
                content=response_part,
                model_id=model_id,
                provider="demo",
                finish_reason="stop" if i == len(mock_responses) - 1 else None,
                done=i == len(mock_responses) - 1
            )
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all providers"""
        status = {}
        for name, provider in self.providers.items():
            status[name] = {
                "available": provider.is_available(),
                "models": len(provider.get_supported_models()) if provider.is_available() else 0,
                "provider_name": provider.get_provider_name()
            }
        return status
    
    def clear_availability_cache(self):
        """Clear the model availability cache"""
        self.availability_cache.clear()
        logger.info("Model availability cache cleared")