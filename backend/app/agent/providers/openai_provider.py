import json
import asyncio
from typing import List, AsyncGenerator, Optional, Dict, Any
from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError
from ..models import ChatMessage, StreamChunk, AIModel
from .base import BaseAIProvider
import logging
import time
import random

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseAIProvider):
    """OpenAI provider for GPT models with enhanced error handling and retry logic"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.client = AsyncOpenAI(api_key=api_key, timeout=60.0) if api_key else None
        self.timeout = 60
        self.max_retries = 3
        self.base_delay = 1.0
        self.max_delay = 60.0
        
        # OpenAI model configurations with optimized parameters
        self.models = [
            AIModel(
                id="gpt-4",
                name="GPT-4",
                provider="openai",
                description="OpenAI's most capable model, great for complex tasks",
                max_tokens=8192,
                supports_streaming=True,
                available=self.available,
                cost_per_token=0.00003
            ),
            AIModel(
                id="gpt-4-turbo",
                name="GPT-4 Turbo",
                provider="openai",
                description="OpenAI's GPT-4 Turbo with improved speed and efficiency",
                max_tokens=128000,
                supports_streaming=True,
                available=self.available,
                cost_per_token=0.00001
            ),
            AIModel(
                id="gpt-3.5-turbo",
                name="GPT-3.5 Turbo",
                provider="openai",
                description="Fast and efficient model for most conversational tasks",
                max_tokens=16385,
                supports_streaming=True,
                available=self.available,
                cost_per_token=0.0000015
            ),
            AIModel(
                id="gpt-4o",
                name="GPT-4o",
                provider="openai",
                description="OpenAI's latest multimodal model with vision capabilities",
                max_tokens=128000,
                supports_streaming=True,
                available=self.available,
                cost_per_token=0.000005
            ),
            AIModel(
                id="gpt-4o-mini",
                name="GPT-4o Mini",
                provider="openai",
                description="Smaller, faster version of GPT-4o",
                max_tokens=128000,
                supports_streaming=True,
                available=self.available,
                cost_per_token=0.00000015
            )
        ]
        
        # Model-specific parameter optimizations
        self.model_configs = {
            "gpt-4": {
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "stop": None
            },
            "gpt-4-turbo": {
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "stop": None
            },
            "gpt-3.5-turbo": {
                "temperature": 0.7,
                "max_tokens": 2048,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "stop": None
            },
            "gpt-4o": {
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "stop": None
            },
            "gpt-4o-mini": {
                "temperature": 0.7,
                "max_tokens": 2048,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "stop": None
            }
        }
    
    def get_provider_name(self) -> str:
        return "openai"
    
    def get_supported_models(self) -> List[AIModel]:
        return self.models
    
    async def _exponential_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter"""
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        jitter = random.uniform(0.1, 0.3) * delay
        return delay + jitter
    
    async def _should_retry(self, exception: Exception, attempt: int) -> bool:
        """Determine if we should retry based on the exception type and attempt count"""
        if attempt >= self.max_retries:
            return False
        
        # Retry on rate limits, timeouts, and temporary server errors
        if isinstance(exception, (RateLimitError, APITimeoutError)):
            return True
        
        if isinstance(exception, APIError):
            # Retry on 5xx server errors and 429 rate limits
            if hasattr(exception, 'status_code'):
                return exception.status_code in [429, 500, 502, 503, 504]
        
        # Retry on connection errors
        if isinstance(exception, (asyncio.TimeoutError, ConnectionError)):
            return True
        
        return False
    
    async def check_availability(self, model_id: str) -> bool:
        """Check if OpenAI model is available with retry logic"""
        if not self.client:
            return False
        
        for attempt in range(self.max_retries + 1):
            try:
                models = await self.client.models.list()
                available_models = [model.id for model in models.data]
                return model_id in available_models
            except Exception as e:
                if await self._should_retry(e, attempt):
                    delay = await self._exponential_backoff_delay(attempt)
                    logger.warning(f"OpenAI availability check failed (attempt {attempt + 1}), retrying in {delay:.2f}s: {e}")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"Error checking OpenAI model availability after {attempt + 1} attempts: {e}")
                    return False
        
        return False
    
    def _get_model_parameters(self, model_id: str, **kwargs) -> Dict[str, Any]:
        """Get optimized parameters for a specific model"""
        # Start with model-specific defaults
        params = self.model_configs.get(model_id, self.model_configs["gpt-3.5-turbo"]).copy()
        
        # Override with user-provided parameters
        for key, value in kwargs.items():
            if key in params and value is not None:
                params[key] = value
        
        return params
    
    async def generate_response(
        self, 
        messages: List[ChatMessage], 
        model_id: str,
        stream: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncGenerator[StreamChunk, None]:
        """Generate response using OpenAI API with enhanced error handling and retry logic"""
        
        if not self.client:
            yield StreamChunk(
                content="Error: OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.",
                model_id=model_id,
                provider="openai",
                finish_reason="error",
                done=True
            )
            return
        
        # Get optimized parameters for this model
        model_params = self._get_model_parameters(model_id, temperature=temperature, max_tokens=max_tokens, **kwargs)
        
        # Convert messages to OpenAI format
        openai_messages = []
        for msg in messages:
            openai_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Retry logic for the entire request
        for attempt in range(self.max_retries + 1):
            try:
                if stream:
                    # Streaming response with retry logic
                    async for chunk in self._generate_streaming_response(
                        model_id, openai_messages, model_params, attempt
                    ):
                        yield chunk
                        if chunk.done:
                            return
                else:
                    # Non-streaming response with retry logic
                    async for chunk in self._generate_non_streaming_response(
                        model_id, openai_messages, model_params, attempt
                    ):
                        yield chunk
                        if chunk.done:
                            return
                
                # If we get here, the request succeeded
                return
                
            except Exception as e:
                if await self._should_retry(e, attempt):
                    delay = await self._exponential_backoff_delay(attempt)
                    logger.warning(f"OpenAI request failed (attempt {attempt + 1}), retrying in {delay:.2f}s: {e}")
                    await asyncio.sleep(delay)
                    continue
                else:
                    # Final error after all retries
                    error_msg = self._format_error_message(e)
                    logger.error(f"OpenAI request failed after {attempt + 1} attempts: {error_msg}")
                    yield StreamChunk(
                        content=f"Error: {error_msg}",
                        model_id=model_id,
                        provider="openai",
                        finish_reason="error",
                        done=True
                    )
                    return
    
    async def _generate_streaming_response(
        self, 
        model_id: str, 
        messages: List[Dict[str, str]], 
        params: Dict[str, Any],
        attempt: int
    ) -> AsyncGenerator[StreamChunk, None]:
        """Generate streaming response with proper error handling"""
        try:
            stream_response = await self.client.chat.completions.create(
                model=model_id,
                messages=messages,
                stream=True,
                **params
            )
            
            async for chunk in stream_response:
                if chunk.choices and len(chunk.choices) > 0:
                    choice = chunk.choices[0]
                    if choice and choice.delta and choice.delta.content:
                        yield StreamChunk(
                            content=choice.delta.content,
                            model_id=model_id,
                            provider="openai",
                            finish_reason=choice.finish_reason,
                            done=choice.finish_reason is not None
                        )
                    elif choice.finish_reason:
                        yield StreamChunk(
                            content="",
                            model_id=model_id,
                            provider="openai",
                            finish_reason=choice.finish_reason,
                            done=True
                        )
                        
        except Exception as e:
            # Re-raise to be handled by the retry logic
            raise e
    
    async def _generate_non_streaming_response(
        self, 
        model_id: str, 
        messages: List[Dict[str, str]], 
        params: Dict[str, Any],
        attempt: int
    ) -> AsyncGenerator[StreamChunk, None]:
        """Generate non-streaming response with proper error handling"""
        try:
            response = await self.client.chat.completions.create(
                model=model_id,
                messages=messages,
                stream=False,
                **params
            )
            
            if response.choices and len(response.choices) > 0:
                choice = response.choices[0]
                content = choice.message.content or "" if choice and choice.message else ""
                
                yield StreamChunk(
                    content=content,
                    model_id=model_id,
                    provider="openai",
                    finish_reason=choice.finish_reason,
                    done=True
                )
            else:
                yield StreamChunk(
                    content="Error: No response from OpenAI API",
                    model_id=model_id,
                    provider="openai",
                    finish_reason="error",
                    done=True
                )
                
        except Exception as e:
            # Re-raise to be handled by the retry logic
            raise e
    
    def _format_error_message(self, exception: Exception) -> str:
        """Format error message for user-friendly display"""
        if isinstance(exception, RateLimitError):
            return "Rate limit exceeded. Please try again later."
        elif isinstance(exception, APITimeoutError):
            return "Request timed out. Please try again."
        elif isinstance(exception, APIError):
            if hasattr(exception, 'status_code'):
                if exception.status_code == 401:
                    return "Invalid API key. Please check your OpenAI API key."
                elif exception.status_code == 403:
                    return "Access denied. Please check your OpenAI API permissions."
                elif exception.status_code == 404:
                    return "Model not found. Please check the model ID."
                elif exception.status_code >= 500:
                    return "OpenAI server error. Please try again later."
            return f"OpenAI API error: {str(exception)}"
        elif isinstance(exception, asyncio.TimeoutError):
            return "Request timed out. Please try again."
        elif isinstance(exception, ConnectionError):
            return "Connection error. Please check your internet connection."
        else:
            return f"Unexpected error: {str(exception)}"