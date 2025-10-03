import json
import asyncio
from typing import List, AsyncGenerator, Optional, Dict, Any
from anthropic import AsyncAnthropic, APIError, RateLimitError, APITimeoutError
from ..models import ChatMessage, StreamChunk, AIModel
from .base import BaseAIProvider
import logging
import time
import random

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseAIProvider):
    """Anthropic provider for Claude models with enhanced error handling and retry logic"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.client = AsyncAnthropic(api_key=api_key, timeout=60.0) if api_key else None
        self.timeout = 60
        self.max_retries = 3
        self.base_delay = 1.0
        self.max_delay = 60.0
        
        # Anthropic model configurations with optimized parameters
        self.models = [
            AIModel(
                id="claude-3-5-sonnet-20241022",
                name="Claude 3.5 Sonnet",
                provider="anthropic",
                description="Anthropic's most intelligent model with excellent reasoning",
                max_tokens=8192,
                supports_streaming=True,
                available=self.available,
                cost_per_token=0.000003
            ),
            AIModel(
                id="claude-3-5-haiku-20241022",
                name="Claude 3.5 Haiku",
                provider="anthropic",
                description="Fast and efficient Claude model for everyday tasks",
                max_tokens=8192,
                supports_streaming=True,
                available=self.available,
                cost_per_token=0.00000025
            ),
            AIModel(
                id="claude-3-opus-20240229",
                name="Claude 3 Opus",
                provider="anthropic",
                description="Anthropic's most powerful model for complex tasks",
                max_tokens=4096,
                supports_streaming=True,
                available=self.available,
                cost_per_token=0.000015
            ),
            AIModel(
                id="claude-3-sonnet-20240229",
                name="Claude 3 Sonnet",
                provider="anthropic",
                description="Balanced Claude model for most use cases",
                max_tokens=4096,
                supports_streaming=True,
                available=self.available,
                cost_per_token=0.000003
            ),
            AIModel(
                id="claude-3-haiku-20240307",
                name="Claude 3 Haiku",
                provider="anthropic",
                description="Fast and cost-effective Claude model",
                max_tokens=4096,
                supports_streaming=True,
                available=self.available,
                cost_per_token=0.00000025
            )
        ]
        
        # Model-specific parameter optimizations
        self.model_configs = {
            "claude-3-5-sonnet-20241022": {
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 1.0,
                "top_k": 40,
                "stop_sequences": None
            },
            "claude-3-5-haiku-20241022": {
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 1.0,
                "top_k": 40,
                "stop_sequences": None
            },
            "claude-3-opus-20240229": {
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 1.0,
                "top_k": 40,
                "stop_sequences": None
            },
            "claude-3-sonnet-20240229": {
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 1.0,
                "top_k": 40,
                "stop_sequences": None
            },
            "claude-3-haiku-20240307": {
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 1.0,
                "top_k": 40,
                "stop_sequences": None
            }
        }
    
    def get_provider_name(self) -> str:
        return "anthropic"
    
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
        """Check if Anthropic model is available with retry logic"""
        if not self.client:
            return False
        
        for attempt in range(self.max_retries + 1):
            try:
                # Anthropic doesn't have a models endpoint, so we'll try a minimal request
                response = await self.client.messages.create(
                    model=model_id,
                    max_tokens=1,
                    messages=[{"role": "user", "content": "test"}]
                )
                return True
            except Exception as e:
                if await self._should_retry(e, attempt):
                    delay = await self._exponential_backoff_delay(attempt)
                    logger.warning(f"Anthropic availability check failed (attempt {attempt + 1}), retrying in {delay:.2f}s: {e}")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"Error checking Anthropic model availability after {attempt + 1} attempts: {e}")
                    return False
        
        return False
    
    def _get_model_parameters(self, model_id: str, **kwargs) -> Dict[str, Any]:
        """Get optimized parameters for a specific model"""
        # Start with model-specific defaults
        params = self.model_configs.get(model_id, self.model_configs["claude-3-haiku-20240307"]).copy()
        
        # Override with user-provided parameters
        for key, value in kwargs.items():
            if key in params and value is not None:
                params[key] = value
        
        return params
    
    def _convert_messages_to_anthropic_format(self, messages: List[ChatMessage]) -> tuple:
        """Convert messages to Anthropic format (system message separate)"""
        system_message = ""
        anthropic_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                anthropic_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        return system_message, anthropic_messages
    
    async def generate_response(
        self, 
        messages: List[ChatMessage], 
        model_id: str,
        stream: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncGenerator[StreamChunk, None]:
        """Generate response using Anthropic API with enhanced error handling and retry logic"""
        
        if not self.client:
            yield StreamChunk(
                content="Error: Anthropic API key not configured. Please set ANTHROPIC_API_KEY environment variable.",
                model_id=model_id,
                provider="anthropic",
                finish_reason="error",
                done=True
            )
            return
        
        # Get optimized parameters for this model
        model_params = self._get_model_parameters(model_id, temperature=temperature, max_tokens=max_tokens, **kwargs)
        
        # Convert messages to Anthropic format
        system_message, anthropic_messages = self._convert_messages_to_anthropic_format(messages)
        
        # Ensure we have at least one user message
        if not anthropic_messages:
            anthropic_messages = [{"role": "user", "content": "Hello"}]
        
        # Retry logic for the entire request
        for attempt in range(self.max_retries + 1):
            try:
                if stream:
                    # Streaming response with retry logic
                    async for chunk in self._generate_streaming_response(
                        model_id, anthropic_messages, system_message, model_params, attempt
                    ):
                        yield chunk
                        if chunk.done:
                            return
                else:
                    # Non-streaming response with retry logic
                    async for chunk in self._generate_non_streaming_response(
                        model_id, anthropic_messages, system_message, model_params, attempt
                    ):
                        yield chunk
                        if chunk.done:
                            return
                
                # If we get here, the request succeeded
                return
                
            except Exception as e:
                if await self._should_retry(e, attempt):
                    delay = await self._exponential_backoff_delay(attempt)
                    logger.warning(f"Anthropic request failed (attempt {attempt + 1}), retrying in {delay:.2f}s: {e}")
                    await asyncio.sleep(delay)
                    continue
                else:
                    # Final error after all retries
                    error_msg = self._format_error_message(e)
                    logger.error(f"Anthropic request failed after {attempt + 1} attempts: {error_msg}")
                    yield StreamChunk(
                        content=f"Error: {error_msg}",
                        model_id=model_id,
                        provider="anthropic",
                        finish_reason="error",
                        done=True
                    )
                    return
    
    async def _generate_streaming_response(
        self, 
        model_id: str, 
        messages: List[Dict[str, str]], 
        system_message: str,
        params: Dict[str, Any],
        attempt: int
    ) -> AsyncGenerator[StreamChunk, None]:
        """Generate streaming response with proper error handling"""
        try:
            # Prepare request parameters
            request_params = {
                "model": model_id,
                "messages": messages,
                **params
            }
            
            if system_message:
                request_params["system"] = system_message
            
            async with self.client.messages.stream(**request_params) as stream_response:
                async for event in stream_response:
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, 'text'):
                            yield StreamChunk(
                                content=event.delta.text,
                                model_id=model_id,
                                provider="anthropic",
                                finish_reason=None,
                                done=False
                            )
                    elif event.type == "message_stop":
                        yield StreamChunk(
                            content="",
                            model_id=model_id,
                            provider="anthropic",
                            finish_reason="stop",
                            done=True
                        )
                        
        except Exception as e:
            # Re-raise to be handled by the retry logic
            raise e
    
    async def _generate_non_streaming_response(
        self, 
        model_id: str, 
        messages: List[Dict[str, str]], 
        system_message: str,
        params: Dict[str, Any],
        attempt: int
    ) -> AsyncGenerator[StreamChunk, None]:
        """Generate non-streaming response with proper error handling"""
        try:
            # Prepare request parameters
            request_params = {
                "model": model_id,
                "messages": messages,
                **params
            }
            
            if system_message:
                request_params["system"] = system_message
            
            response = await self.client.messages.create(**request_params)
            
            if response.content:
                content = ""
                for block in response.content:
                    if hasattr(block, 'text'):
                        content += block.text
                
                yield StreamChunk(
                    content=content,
                    model_id=model_id,
                    provider="anthropic",
                    finish_reason=response.stop_reason,
                    done=True
                )
            else:
                yield StreamChunk(
                    content="Error: No response from Anthropic API",
                    model_id=model_id,
                    provider="anthropic",
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
                    return "Invalid API key. Please check your Anthropic API key."
                elif exception.status_code == 403:
                    return "Access denied. Please check your Anthropic API permissions."
                elif exception.status_code == 404:
                    return "Model not found. Please check the model ID."
                elif exception.status_code >= 500:
                    return "Anthropic server error. Please try again later."
            return f"Anthropic API error: {str(exception)}"
        elif isinstance(exception, asyncio.TimeoutError):
            return "Request timed out. Please try again."
        elif isinstance(exception, ConnectionError):
            return "Connection error. Please check your internet connection."
        else:
            return f"Unexpected error: {str(exception)}"