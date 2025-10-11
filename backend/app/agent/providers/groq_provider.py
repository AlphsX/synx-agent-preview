import json
import aiohttp
import asyncio
from typing import List, AsyncGenerator, Dict, Any, Optional
from ..models import ChatMessage, StreamChunk, AIModel
from .base import BaseAIProvider
import logging
import time
import random

logger = logging.getLogger(__name__)


class GroqProvider(BaseAIProvider):
    """Groq AI provider for ultra-fast inference with enhanced error handling and retry logic"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.base_url = "https://api.groq.com/openai/v1"
        self.timeout = 60
        self.max_retries = 3
        self.base_delay = 1.0
        self.max_delay = 60.0
        
        # Groq model configurations with optimized parameters
        self.models = [
            AIModel(
                id="groq/compound",
                name="Groq Compound Model",
                provider="groq",
                description="Groq's compound model with web browsing capabilities for URL analysis",
                max_tokens=8192,
                supports_streaming=True,
                available=self.available
            ),
            AIModel(
                id="openai/gpt-oss-120b",
                name="GPT OSS 120B",
                provider="groq",
                description="OpenAI's GPT OSS 120B model for advanced reasoning",
                max_tokens=8192,
                supports_streaming=True,
                available=self.available
            ),
            AIModel(
                id="meta-llama/llama-4-maverick-17b-128e-instruct",
                name="Llama 4 Maverick 17B",
                provider="groq",
                description="Meta's Llama 4 Maverick 17B instruction-tuned model",
                max_tokens=8192,
                supports_streaming=True,
                available=self.available
            ),
            AIModel(
                id="deepseek-r1-distill-llama-70b",
                name="DeepSeek R1 Distill Llama 70B",
                provider="groq",
                description="DeepSeek's R1 distilled Llama 70B model",
                max_tokens=8192,
                supports_streaming=True,
                available=self.available
            ),
            AIModel(
                id="qwen/qwen3-32b",
                name="Qwen 3 32B",
                provider="groq",
                description="Alibaba's Qwen 3 32B model for multilingual tasks",
                max_tokens=8192,
                supports_streaming=True,
                available=self.available
            ),
            AIModel(
                id="moonshotai/kimi-k2-instruct-0905",
                name="Kimi K2 Instruct",
                provider="groq",
                description="MoonshotAI's Kimi K2 instruction-tuned model",
                max_tokens=8192,
                supports_streaming=True,
                available=self.available
            ),
            # Keep some existing models for backward compatibility
            AIModel(
                id="llama-3.1-70b-versatile",
                name="Llama 3.1 70B Versatile",
                provider="groq",
                description="Meta's Llama 3.1 70B model optimized for versatile tasks",
                max_tokens=8192,
                supports_streaming=True,
                available=self.available
            ),
            AIModel(
                id="llama-3.1-8b-instant",
                name="Llama 3.1 8B Instant",
                provider="groq",
                description="Meta's Llama 3.1 8B model optimized for speed",
                max_tokens=8192,
                supports_streaming=True,
                available=self.available
            )
        ]
        
        # Model-specific parameter optimizations
        self.model_configs = {
            "groq/compound": {
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "stop": None
            },
            "openai/gpt-oss-120b": {
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "stop": None
            },
            "meta-llama/llama-4-maverick-17b-128e-instruct": {
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "stop": None
            },
            "deepseek-r1-distill-llama-70b": {
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "stop": None
            },
            "qwen/qwen3-32b": {
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "stop": None
            },
            "moonshotai/kimi-k2-instruct-0905": {
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "stop": None
            },
            "llama-3.1-70b-versatile": {
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "stop": None
            },
            "llama-3.1-8b-instant": {
                "temperature": 0.7,
                "max_tokens": 4096,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "stop": None
            }
        }
    
    def get_provider_name(self) -> str:
        return "groq"
    
    def get_supported_models(self) -> List[AIModel]:
        return self.models
    
    async def _exponential_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter"""
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        jitter = random.uniform(0.1, 0.3) * delay
        return delay + jitter
    
    async def _should_retry(self, status_code: int, attempt: int) -> bool:
        """Determine if we should retry based on the status code and attempt count"""
        if attempt >= self.max_retries:
            return False
        
        # Retry on rate limits, timeouts, and temporary server errors
        return status_code in [429, 500, 502, 503, 504]
    
    def _get_model_parameters(self, model_id: str, **kwargs) -> Dict[str, Any]:
        """Get optimized parameters for a specific model"""
        # Start with model-specific defaults
        params = self.model_configs.get(model_id, self.model_configs["openai/gpt-oss-120b"]).copy()
        
        # Override with user-provided parameters
        for key, value in kwargs.items():
            if key in params and value is not None:
                params[key] = value
        
        return params
    
    async def check_availability(self, model_id: str) -> bool:
        """Check if Groq model is available with retry logic"""
        if not self.api_key:
            return False
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        for attempt in range(self.max_retries + 1):
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                    async with session.get(f"{self.base_url}/models", headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            available_models = [model["id"] for model in data.get("data", [])]
                            return model_id in available_models
                        elif await self._should_retry(response.status, attempt):
                            delay = await self._exponential_backoff_delay(attempt)
                            logger.warning(f"Groq availability check failed (attempt {attempt + 1}), retrying in {delay:.2f}s: HTTP {response.status}")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            return False
            except Exception as e:
                if attempt < self.max_retries:
                    delay = await self._exponential_backoff_delay(attempt)
                    logger.warning(f"Groq availability check failed (attempt {attempt + 1}), retrying in {delay:.2f}s: {e}")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"Error checking Groq model availability after {attempt + 1} attempts: {e}")
                    return False
        
        return False
    
    async def generate_response(
        self, 
        messages: List[ChatMessage], 
        model_id: str,
        stream: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncGenerator[StreamChunk, None]:
        """Generate response using Groq API with enhanced error handling and retry logic"""
        
        if not self.api_key:
            yield StreamChunk(
                content="Error: Groq API key not configured. Please set GROQ_API_KEY environment variable.",
                model_id=model_id,
                provider="groq",
                finish_reason="error",
                done=True
            )
            return
        
        # Get optimized parameters for this model
        model_params = self._get_model_parameters(model_id, temperature=temperature, max_tokens=max_tokens, **kwargs)
        
        # Convert messages to Groq format
        groq_messages = []
        for msg in messages:
            groq_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Add special header for compound model
        if model_id == "groq/compound":
            headers["Groq-Model-Version"] = "latest"
        
        payload = {
            "model": model_id,
            "messages": groq_messages,
            "stream": stream,
            **model_params
        }
        
        # Retry logic for the entire request
        for attempt in range(self.max_retries + 1):
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                    async with session.post(
                        f"{self.base_url}/chat/completions",
                        json=payload,
                        headers=headers
                    ) as response:
                        
                        if response.status == 200:
                            if stream:
                                # Streaming response
                                async for chunk in self._process_streaming_response(response, model_id):
                                    yield chunk
                                    if chunk.done:
                                        return
                            else:
                                # Non-streaming response
                                async for chunk in self._process_non_streaming_response(response, model_id):
                                    yield chunk
                                    if chunk.done:
                                        return
                            return
                        
                        elif await self._should_retry(response.status, attempt):
                            delay = await self._exponential_backoff_delay(attempt)
                            error_text = await response.text()
                            logger.warning(f"Groq request failed (attempt {attempt + 1}), retrying in {delay:.2f}s: HTTP {response.status} - {error_text}")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            # Final error without retry
                            error_text = await response.text()
                            error_msg = self._format_error_message(response.status, error_text)
                            yield StreamChunk(
                                content=f"Error: {error_msg}",
                                model_id=model_id,
                                provider="groq",
                                finish_reason="error",
                                done=True
                            )
                            return
                        
            except Exception as e:
                if attempt < self.max_retries and isinstance(e, (asyncio.TimeoutError, aiohttp.ClientError)):
                    delay = await self._exponential_backoff_delay(attempt)
                    logger.warning(f"Groq request failed (attempt {attempt + 1}), retrying in {delay:.2f}s: {e}")
                    await asyncio.sleep(delay)
                    continue
                else:
                    # Final error after all retries
                    error_msg = self._format_exception_message(e)
                    logger.error(f"Groq request failed after {attempt + 1} attempts: {error_msg}")
                    yield StreamChunk(
                        content=f"Error: {error_msg}",
                        model_id=model_id,
                        provider="groq",
                        finish_reason="error",
                        done=True
                    )
                    return
    
    async def _process_streaming_response(
        self, 
        response: aiohttp.ClientResponse, 
        model_id: str
    ) -> AsyncGenerator[StreamChunk, None]:
        """Process streaming response from Groq API"""
        async for line in response.content:
            if line:
                line_text = line.decode('utf-8').strip()
                if line_text.startswith('data: '):
                    data_text = line_text[6:]
                    if data_text == '[DONE]':
                        yield StreamChunk(
                            content="",
                            model_id=model_id,
                            provider="groq",
                            finish_reason="stop",
                            done=True
                        )
                        break
                    
                    try:
                        data = json.loads(data_text)
                        choices = data.get('choices', [])
                        if choices and len(choices) > 0:
                            choice = choices[0]
                            if choice:
                                delta = choice.get('delta', {})
                                content = delta.get('content', '')
                                finish_reason = choice.get('finish_reason')
                                
                                if content:
                                    yield StreamChunk(
                                        content=content,
                                        model_id=model_id,
                                        provider="groq",
                                        finish_reason=finish_reason,
                                        done=finish_reason is not None
                                    )
                            
                            if content:
                                yield StreamChunk(
                                    content=content,
                                    model_id=model_id,
                                    provider="groq",
                                    finish_reason=finish_reason,
                                    done=finish_reason is not None
                                )
                    except json.JSONDecodeError:
                        continue
    
    async def _process_non_streaming_response(
        self, 
        response: aiohttp.ClientResponse, 
        model_id: str
    ) -> AsyncGenerator[StreamChunk, None]:
        """Process non-streaming response from Groq API"""
        data = await response.json()
        choices = data.get('choices', [])
        if choices and len(choices) > 0:
            choice = choices[0]
            content = choice.get('message', {}).get('content', '') if choice else ''
            finish_reason = choice.get('finish_reason') if choice else None
            
            yield StreamChunk(
                content=content,
                model_id=model_id,
                provider="groq",
                finish_reason=finish_reason,
                done=True
            )
        else:
            yield StreamChunk(
                content="Error: No response from Groq API",
                model_id=model_id,
                provider="groq",
                finish_reason="error",
                done=True
            )
    
    def _format_error_message(self, status_code: int, error_text: str) -> str:
        """Format error message for user-friendly display"""
        if status_code == 401:
            return "Invalid API key. Please check your Groq API key."
        elif status_code == 403:
            return "Access denied. Please check your Groq API permissions."
        elif status_code == 404:
            return "Model not found. Please check the model ID."
        elif status_code == 429:
            return "Rate limit exceeded. Please try again later."
        elif status_code >= 500:
            return "Groq server error. Please try again later."
        else:
            return f"Groq API error (HTTP {status_code}): {error_text}"
    
    def _format_exception_message(self, exception: Exception) -> str:
        """Format exception message for user-friendly display"""
        if isinstance(exception, asyncio.TimeoutError):
            return "Request timed out. Please try again."
        elif isinstance(exception, aiohttp.ClientError):
            return "Connection error. Please check your internet connection."
        else:
            return f"Unexpected error: {str(exception)}"