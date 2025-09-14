from typing import List, AsyncGenerator, Dict, Any
import asyncio
import json
import aiohttp
from app.config import settings

class ChatService:
    def __init__(self):
        self.groq_api_key = settings.GROQ_API_KEY
        self.openai_api_key = settings.OPENAI_API_KEY
        self.anthropic_api_key = settings.ANTHROPIC_API_KEY
        
    async def generate_ai_response(self, 
                                 message: str,
                                 model_id: str,
                                 conversation_history: List[Dict] = None) -> AsyncGenerator[str, None]:
        """Generate AI response with streaming"""
        
        if conversation_history is None:
            conversation_history = []
        
        # Add system message and user message
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant inspired by Sync. You're witty, informative, and can access real-time information."}
        ]
        
        # Add conversation history
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
            # Default mock response
            async for chunk in self._generate_mock_response(message):
                yield chunk
    
    async def _generate_mock_response(self, message: str) -> AsyncGenerator[str, None]:
        """Generate a mock response for testing"""
        response_parts = [
            f"Thanks for your message: '{message}'. ",
            "I'm a mock AI assistant. ",
            "In the full implementation, I would connect to real AI APIs ",
            "like OpenAI, Anthropic, and Groq for intelligent responses. ",
            "I can also search the web and get crypto data!"
        ]
        
        for part in response_parts:
            yield part
            await asyncio.sleep(0.1)
    
    async def _generate_groq_response(self, messages: List[dict], model_id: str) -> AsyncGenerator[str, None]:
        """Generate response using Groq API for ultra-fast inference"""
        if not self.groq_api_key:
            async for chunk in self._generate_mock_response("Groq API key not configured"):
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
            async for chunk in self._generate_mock_response("OpenAI API key not configured"):
                yield chunk
            return
        
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model_id,
                "messages": messages,
                "stream": True,
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
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
                        yield f"Error: OpenAI API returned status {response.status}"
                        
        except Exception as e:
            yield f"Error with OpenAI API: {str(e)}"
    
    async def _generate_anthropic_response(self, messages: List[dict], model_id: str) -> AsyncGenerator[str, None]:
        """Generate response using Anthropic API"""
        if not self.anthropic_api_key:
            async for chunk in self._generate_mock_response("Anthropic API key not configured"):
                yield chunk
            return
        
        # For now, return mock response as Anthropic streaming implementation is more complex
        async for chunk in self._generate_mock_response("Claude response would go here"):
            yield chunk