"""
Groq Compound Model Service for URL-based queries

This service handles queries that contain URLs by using Groq's compound model
which can visit websites and analyze their content.
"""

import re
import json
import aiohttp
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class GroqCompoundService:
    """Service for handling URL-based queries using Groq's compound model"""
    
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.base_url = "https://api.groq.com/openai/v1"
        self.compound_model = "groq/compound"
        self.timeout = 120  # Longer timeout for web browsing
        self.max_retries = 3
        
        # URL detection patterns
        self.url_patterns = [
            r'https?://[^\s<>"{}|\\^`\[\]]+',  # Standard HTTP/HTTPS URLs
            r'www\.[^\s<>"{}|\\^`\[\]]+',      # www. URLs without protocol
            r'[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?'  # Domain.tld URLs
        ]
        
        logger.info("GroqCompoundService initialized")
    
    def is_available(self) -> bool:
        """Check if the service is available (has API key)"""
        return bool(self.api_key)
    
    def detect_urls_in_message(self, message: str) -> List[str]:
        """
        Detect URLs in a message using regex patterns.
        
        Args:
            message: The user message to analyze
            
        Returns:
            List of detected URLs
        """
        try:
            if not message or not isinstance(message, str):
                return []
                
            urls = []
            
            for pattern in self.url_patterns:
                try:
                    matches = re.findall(pattern, message, re.IGNORECASE)
                    for match in matches:
                        if not match or not isinstance(match, str):
                            continue
                            
                        # Normalize URL
                        url = match.strip()
                        if not url:
                            continue
                            
                        if not url.startswith(('http://', 'https://')):
                            if url.startswith('www.'):
                                url = f"https://{url}"
                            elif '.' in url:
                                url = f"https://{url}"
                        
                        if url and url not in urls:
                            urls.append(url)
                            
                except Exception as pattern_error:
                    logger.warning(f"Error with pattern {pattern}: {pattern_error}")
                    continue
            
            return urls
            
        except Exception as e:
            logger.error(f"Error in detect_urls_in_message: {e}")
            return []
    
    def should_use_compound_model(self, message: str) -> bool:
        """
        Determine if a message should use the compound model.
        
        Args:
            message: The user message to analyze
            
        Returns:
            True if compound model should be used, False otherwise
        """
        try:
            if not self.is_available():
                return False
            
            if not message or not isinstance(message, str):
                return False
            
            # Check for URLs in the message
            urls = self.detect_urls_in_message(message)
            if urls and len(urls) > 0:
                logger.info(f"URLs detected in message: {urls}")
                return True
            
            # Check for web-related keywords that might benefit from browsing
            web_keywords = [
                'visit', 'browse', 'check website', 'look at site', 'analyze page',
                'what does this site say', 'summarize this page', 'read this article',
                'check this link', 'what\'s on this page'
            ]
            
            message_lower = message.lower()
            for keyword in web_keywords:
                if keyword in message_lower:
                    # Still need a URL to be present
                    if urls and len(urls) > 0:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error in should_use_compound_model: {e}")
            return False
    
    async def generate_response_with_urls(
        self,
        message: str,
        conversation_history: List[Dict[str, str]] = None,
        system_message: str = None,
        stream: bool = True,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Generate response using Groq compound model for URL-based queries.
        
        Args:
            message: The user message containing URLs
            conversation_history: Previous conversation messages
            system_message: System prompt
            stream: Whether to stream the response
            **kwargs: Additional parameters
            
        Yields:
            String chunks of the response
        """
        if not self.is_available():
            yield "Error: Groq API key not configured for compound model."
            return
        
        # Detect URLs in the message
        urls = self.detect_urls_in_message(message)
        if not urls:
            yield "Error: No URLs detected in message for compound model processing."
            return
        
        # Prepare messages for the compound model
        messages = []
        
        # Add system message if provided, or use default for data extraction
        if system_message:
            messages.append({"role": "system", "content": system_message})
        else:
            default_system = """You are a specialized web content extraction assistant. Your job is to visit websites and extract key information for analysis by other AI systems.

IMPORTANT INSTRUCTIONS:
1. Visit the provided URLs and extract the main content
2. Focus on factual information, key points, and important details
3. Organize the information clearly with headings and bullet points
4. Include relevant data, statistics, quotes, and examples
5. Maintain objectivity - don't add opinions or interpretations
6. Structure the output for easy consumption by other AI systems

FORMAT YOUR RESPONSE AS:
**Website Title/Topic**
• Key Point 1
• Key Point 2
• Key Point 3

**Main Content Summary**
[Detailed summary of the main content]

**Important Details**
• Specific data, dates, numbers
• Key quotes or statements
• Technical specifications (if applicable)

**Additional Information**
• Related topics mentioned
• Links to other resources (if relevant)"""
            messages.append({"role": "system", "content": default_system})
        
        # Add conversation history
        if conversation_history:
            messages.extend(conversation_history[-10:])  # Last 10 messages for context
        
        # Add the current user message
        messages.append({"role": "user", "content": message})
        
        # Prepare headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Groq-Model-Version": "latest"  # Use latest version for compound model
        }
        
        # Prepare payload
        payload = {
            "model": self.compound_model,
            "messages": messages,
            "stream": stream,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4000)
        }
        
        # Make request with retry logic
        for attempt in range(self.max_retries + 1):
            try:
                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as session:
                    async with session.post(
                        f"{self.base_url}/chat/completions",
                        json=payload,
                        headers=headers
                    ) as response:
                        
                        if response.status == 200:
                            if stream:
                                async for chunk in self._process_streaming_response(response):
                                    yield chunk
                            else:
                                content = await self._process_non_streaming_response(response)
                                yield content
                            return
                        
                        elif response.status in [429, 500, 502, 503, 504] and attempt < self.max_retries:
                            # Retry on rate limits and server errors
                            delay = min(2 ** attempt, 30)  # Exponential backoff, max 30s
                            logger.warning(f"Groq compound request failed (attempt {attempt + 1}), retrying in {delay}s: HTTP {response.status}")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            # Final error
                            error_text = await response.text()
                            error_msg = self._format_error_message(response.status, error_text)
                            yield f"Error: {error_msg}"
                            return
                            
            except Exception as e:
                if attempt < self.max_retries and isinstance(e, (asyncio.TimeoutError, aiohttp.ClientError)):
                    delay = min(2 ** attempt, 30)
                    logger.warning(f"Groq compound request failed (attempt {attempt + 1}), retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"Groq compound request failed after {attempt + 1} attempts: {e}")
                    yield f"Error: {self._format_exception_message(e)}"
                    return
    
    async def _process_streaming_response(self, response: aiohttp.ClientResponse) -> AsyncGenerator[str, None]:
        """Process streaming response from Groq compound model"""
        try:
            async for line in response.content:
                if line:
                    line_text = line.decode('utf-8').strip()
                    if line_text.startswith('data: '):
                        data_text = line_text[6:]
                        if data_text == '[DONE]':
                            break
                        
                        try:
                            data = json.loads(data_text)
                            if not data or not isinstance(data, dict):
                                continue
                                
                            choices = data.get('choices', [])
                            if not choices or not isinstance(choices, list) or len(choices) == 0:
                                continue
                                
                            choice = choices[0]
                            if not choice or not isinstance(choice, dict):
                                continue
                                
                            delta = choice.get('delta', {})
                            if not isinstance(delta, dict):
                                continue
                                
                            content = delta.get('content', '')
                            if content and isinstance(content, str):
                                yield content
                            
                            # Check for finish reason
                            finish_reason = choice.get('finish_reason')
                            if finish_reason:
                                break
                                
                        except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as e:
                            logger.warning(f"Error parsing streaming response: {e}")
                            continue
                            
        except Exception as e:
            logger.error(f"Error in streaming response processing: {e}")
            yield f"Error processing response: {str(e)}"
    
    async def _process_non_streaming_response(self, response: aiohttp.ClientResponse) -> str:
        """Process non-streaming response from Groq compound model"""
        try:
            data = await response.json()
            if not data or not isinstance(data, dict):
                return "Error: Invalid response format from Groq compound model"
                
            choices = data.get('choices', [])
            if not choices or not isinstance(choices, list) or len(choices) == 0:
                return "Error: No choices in response from Groq compound model"
                
            choice = choices[0]
            if not choice or not isinstance(choice, dict):
                return "Error: Invalid choice format from Groq compound model"
                
            message = choice.get('message', {})
            if not isinstance(message, dict):
                return "Error: Invalid message format from Groq compound model"
                
            content = message.get('content', '')
            if not content or not isinstance(content, str):
                return "Error: No content in response from Groq compound model"
                
            return content
            
        except Exception as e:
            logger.error(f"Error processing non-streaming response: {e}")
            return f"Error processing response: {str(e)}"
    
    def _format_error_message(self, status_code: int, error_text: str) -> str:
        """Format error message for user-friendly display"""
        if status_code == 401:
            return "Invalid API key for Groq compound model. Please check your Groq API key."
        elif status_code == 403:
            return "Access denied to Groq compound model. Please check your API permissions."
        elif status_code == 404:
            return "Groq compound model not found. Please check if you have access to this model."
        elif status_code == 429:
            return "Rate limit exceeded for Groq compound model. Please try again later."
        elif status_code >= 500:
            return "Groq server error. Please try again later."
        else:
            return f"Groq compound model error (HTTP {status_code}): {error_text}"
    
    def _format_exception_message(self, exception: Exception) -> str:
        """Format exception message for user-friendly display"""
        if isinstance(exception, asyncio.TimeoutError):
            return "Request timed out while processing URLs. Please try again."
        elif isinstance(exception, aiohttp.ClientError):
            return "Connection error while accessing Groq compound model. Please check your internet connection."
        else:
            return f"Unexpected error with Groq compound model: {str(exception)}"
    
    async def extract_website_data(
        self,
        message: str,
        urls: List[str] = None
    ) -> Dict[str, Any]:
        """
        Extract data from websites for use by other AI models.
        
        Args:
            message: Original user message
            urls: List of URLs to analyze (optional, will detect if not provided)
            
        Returns:
            Dictionary with extracted website data
        """
        try:
            if not self.is_available():
                return {"error": "Groq compound service not available", "success": False}
            
            # Detect URLs if not provided
            if not urls:
                urls = self.detect_urls_in_message(message)
            
            if not urls:
                return {"error": "No URLs found to analyze", "success": False}
            
            # Create extraction prompt
            extraction_prompt = f"""Please visit and extract key information from the following URLs for analysis:

URLs to analyze: {', '.join(urls)}

Original user request: {message}

Extract the most relevant information that would help answer the user's question. Focus on facts, data, and key points."""
            
            # Extract website content
            extracted_content = ""
            async for chunk in self.generate_response_with_urls(
                message=extraction_prompt,
                stream=True,
                temperature=0.2,  # Low temperature for factual extraction
                max_tokens=3000
            ):
                extracted_content += chunk
            
            if extracted_content and len(extracted_content.strip()) > 50:
                return {
                    "success": True,
                    "urls_analyzed": urls,
                    "extracted_content": extracted_content,
                    "content_length": len(extracted_content),
                    "extraction_method": "groq_compound"
                }
            else:
                return {
                    "error": "Failed to extract meaningful content from websites",
                    "success": False,
                    "urls_attempted": urls
                }
                
        except Exception as e:
            logger.error(f"Error in extract_website_data: {e}")
            return {
                "error": str(e),
                "success": False,
                "urls_attempted": urls or []
            }

    async def test_compound_model(self, test_url: str = "https://groq.com") -> Dict[str, Any]:
        """
        Test the compound model with a simple URL.
        
        Args:
            test_url: URL to test with
            
        Returns:
            Dictionary with test results
        """
        if not self.is_available():
            return {"success": False, "error": "Groq API key not configured"}
        
        test_message = f"Please summarize the key points of this page: {test_url}"
        
        try:
            response_content = ""
            async for chunk in self.generate_response_with_urls(
                message=test_message,
                stream=True
            ):
                response_content += chunk
            
            return {
                "success": True,
                "test_url": test_url,
                "response_length": len(response_content),
                "response_preview": response_content[:200] + "..." if len(response_content) > 200 else response_content
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "test_url": test_url
            }


# Global instance
groq_compound_service = GroqCompoundService()