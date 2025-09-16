from typing import List, AsyncGenerator, Dict, Any, Optional
from .router import AIModelRouter
from .models import ChatMessage, StreamChunk, AIModel
import logging

logger = logging.getLogger(__name__)


class AIService:
    """
    High-level AI service that provides a simplified interface to the AI model router.
    
    This service handles:
    - Message formatting and validation
    - Response streaming
    - Error handling
    - Logging and monitoring
    """
    
    def __init__(self):
        self.router = AIModelRouter()
        logger.info("AIService initialized")
    
    def get_available_models(self) -> List[AIModel]:
        """Get all available AI models"""
        return self.router.get_all_models()
    
    def get_models_by_provider(self, provider: str) -> List[AIModel]:
        """Get models for a specific provider"""
        return self.router.get_models_by_provider(provider)
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all AI providers"""
        return self.router.get_provider_status()
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model_id: str,
        stream: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Generate chat response.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model_id: The AI model to use
            stream: Whether to stream the response
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Yields:
            String chunks of the response
        """
        try:
            # Convert dict messages to ChatMessage objects
            chat_messages = []
            for msg in messages:
                if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                    chat_messages.append(ChatMessage(
                        role=msg['role'],
                        content=msg['content']
                    ))
                else:
                    logger.warning(f"Invalid message format: {msg}")
                    continue
            
            if not chat_messages:
                yield "Error: No valid messages provided"
                return
            
            # Generate response using the router
            async for chunk in self.router.generate_response(
                messages=chat_messages,
                model_id=model_id,
                stream=stream,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            ):
                if chunk.content:
                    yield chunk.content
                
                # Log errors
                if chunk.finish_reason == "error":
                    logger.error(f"AI generation error: {chunk.content}")
                
                # Break on completion
                if chunk.done:
                    break
                    
        except Exception as e:
            logger.error(f"Error in chat service: {e}")
            yield f"Error: {str(e)}"
    
    async def chat_with_context(
        self,
        message: str,
        model_id: str,
        conversation_history: List[Dict[str, str]] = None,
        system_message: str = None,
        stream: bool = True,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Generate chat response with conversation context.
        
        Args:
            message: The user message
            model_id: The AI model to use
            conversation_history: Previous messages in the conversation
            system_message: System prompt to set context
            stream: Whether to stream the response
            **kwargs: Additional parameters
            
        Yields:
            String chunks of the response
        """
        messages = []
        
        # Add system message if provided
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        # Add conversation history
        if conversation_history:
            messages.extend(conversation_history[-10:])  # Last 10 messages
        
        # Add current user message
        messages.append({"role": "user", "content": message})
        
        # Generate response
        async for chunk in self.chat(
            messages=messages,
            model_id=model_id,
            stream=stream,
            **kwargs
        ):
            yield chunk
    
    async def check_model_availability(self, model_id: str) -> bool:
        """Check if a specific model is available"""
        return await self.router.check_model_availability(model_id)
    
    def get_model_info(self, model_id: str) -> Optional[AIModel]:
        """Get information about a specific model"""
        all_models = self.get_available_models()
        for model in all_models:
            if model.id == model_id:
                return model
        return None
    
    def get_recommended_model(self, task_type: str = "general") -> Optional[str]:
        """
        Get a recommended model for a specific task type.
        
        Args:
            task_type: Type of task ("general", "coding", "creative", "fast", "cheap")
            
        Returns:
            Recommended model ID or None
        """
        available_models = self.get_available_models()
        if not available_models:
            return None
        
        # Define recommendations based on task type
        recommendations = {
            "general": ["gpt-4o", "claude-3-5-sonnet-20241022", "llama-3.1-70b-versatile"],
            "coding": ["gpt-4", "claude-3-5-sonnet-20241022", "llama-3.1-70b-versatile"],
            "creative": ["claude-3-5-sonnet-20241022", "gpt-4", "llama-3.1-70b-versatile"],
            "fast": ["gpt-4o-mini", "claude-3-5-haiku-20241022", "llama-3.1-8b-instant"],
            "cheap": ["gpt-3.5-turbo", "claude-3-haiku-20240307", "llama-3.1-8b-instant"]
        }
        
        preferred_models = recommendations.get(task_type, recommendations["general"])
        available_model_ids = [model.id for model in available_models if model.available]
        
        # Return first available model from preferences
        for model_id in preferred_models:
            if model_id in available_model_ids:
                return model_id
        
        # Fallback to any available model
        return available_model_ids[0] if available_model_ids else None
    
    async def generate_mock_response(
        self,
        message: str,
        model_id: str,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """Generate a mock response for demo purposes"""
        messages = [ChatMessage(role="user", content=message)]
        
        async for chunk in self.router.generate_mock_response(
            messages=messages,
            model_id=model_id,
            stream=stream
        ):
            if chunk.content:
                yield chunk.content
    
    def clear_cache(self):
        """Clear any cached data"""
        self.router.clear_availability_cache()
        logger.info("AI service cache cleared")