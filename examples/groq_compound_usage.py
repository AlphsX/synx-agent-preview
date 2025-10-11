#!/usr/bin/env python3
"""
Groq Compound Model Usage Examples

This file demonstrates how to use the Groq compound model for URL-based queries.
"""

import asyncio
import json
from typing import List, Dict, Any

# Example usage of the Groq compound service
async def example_url_detection():
    """Example: Detect URLs in messages"""
    from backend.app.external_apis.groq_compound_service import groq_compound_service
    
    print("🔍 URL Detection Examples")
    print("=" * 50)
    
    test_messages = [
        "Check out this article: https://groq.com/blog/inside-the-lpu-deconstructing-groq-speed",
        "What do you think about www.example.com and https://openai.com?",
        "Visit google.com for more information",
        "This is just a regular message without URLs",
        "Multiple URLs: https://groq.com, www.github.com, and example.org"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. Message: {message}")
        
        urls = groq_compound_service.detect_urls_in_message(message)
        should_use = groq_compound_service.should_use_compound_model(message)
        
        print(f"   URLs detected: {urls}")
        print(f"   Should use compound: {should_use}")


async def example_compound_chat():
    """Example: Chat with URL analysis"""
    from backend.app.external_apis.groq_compound_service import groq_compound_service
    
    print("\n\n🤖 Compound Model Chat Example")
    print("=" * 50)
    
    if not groq_compound_service.is_available():
        print("❌ Groq compound service not available (API key not configured)")
        return
    
    # Example message with URL
    message = "Please analyze and summarize this page: https://groq.com"
    
    print(f"User message: {message}")
    print("\nAI Response:")
    print("-" * 30)
    
    try:
        response_content = ""
        async for chunk in groq_compound_service.generate_response_with_urls(
            message=message,
            stream=True
        ):
            print(chunk, end="", flush=True)
            response_content += chunk
        
        print(f"\n\n✅ Response completed ({len(response_content)} characters)")
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def example_enhanced_chat_integration():
    """Example: Using compound model through enhanced chat service"""
    from backend.app.enhanced_chat_service import EnhancedChatService
    
    print("\n\n💬 Enhanced Chat Integration Example")
    print("=" * 50)
    
    chat_service = EnhancedChatService()
    
    # Message with URL that should trigger compound model
    message = "Analyze this Groq blog post for me: https://groq.com/blog/inside-the-lpu-deconstructing-groq-speed"
    
    print(f"User message: {message}")
    print("\nAI Response (via Enhanced Chat):")
    print("-" * 40)
    
    try:
        response_content = ""
        async for chunk in chat_service.generate_ai_response(
            message=message,
            model_id="groq/compound",
            conversation_id=None,
            user_context={
                "user_id": "example_user",
                "username": "demo_user",
                "is_authenticated": True
            }
        ):
            print(chunk, end="", flush=True)
            response_content += chunk
        
        print(f"\n\n✅ Enhanced chat response completed ({len(response_content)} characters)")
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def example_api_usage():
    """Example: Using the REST API endpoints"""
    import aiohttp
    
    print("\n\n🌐 REST API Usage Examples")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Example 1: Check service status
    print("1. Checking service status...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/api/v1/external/groq-compound/status") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   Status: {'Available' if data['available'] else 'Unavailable'}")
                    print(f"   Model: {data['model']}")
                    print(f"   Timeout: {data['timeout']}s")
                else:
                    print(f"   Error: HTTP {response.status}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 2: URL detection
    print("\n2. Testing URL detection...")
    test_text = "Check out https://groq.com and www.example.com"
    try:
        async with aiohttp.ClientSession() as session:
            params = {"text": test_text}
            async with session.get(f"{base_url}/api/v1/external/groq-compound/detect-urls", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   Text: {data['text']}")
                    print(f"   URLs: {data['detected_urls']}")
                    print(f"   Should use compound: {data['should_use_compound']}")
                else:
                    print(f"   Error: HTTP {response.status}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 3: Chat with URLs (if service is available)
    print("\n3. Testing chat with URLs...")
    message = "Summarize this page: https://groq.com"
    try:
        async with aiohttp.ClientSession() as session:
            params = {"message": message}
            async with session.post(f"{base_url}/api/v1/external/groq-compound/chat-with-urls", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   Message: {data['message']}")
                    print(f"   URLs detected: {data['detected_urls']}")
                    print(f"   Used compound: {data['should_use_compound']}")
                    print(f"   Response preview: {data['response'][:100]}...")
                elif response.status == 503:
                    print("   Service unavailable (API key not configured)")
                else:
                    error_text = await response.text()
                    print(f"   Error: HTTP {response.status} - {error_text}")
    except Exception as e:
        print(f"   Error: {e}")


def example_frontend_integration():
    """Example: Frontend JavaScript integration"""
    print("\n\n🎨 Frontend Integration Example")
    print("=" * 50)
    
    js_code = '''
// Example: Chat with URL detection
async function chatWithUrls(message) {
  try {
    const response = await fetch('/api/v1/external/groq-compound/chat-with-urls', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    console.log('URLs detected:', data.detected_urls);
    console.log('Used compound model:', data.should_use_compound);
    console.log('AI response:', data.response);
    
    return data;
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
}

// Example: Direct URL analysis
async function analyzeUrl(url, question = null) {
  try {
    const params = new URLSearchParams({ url });
    if (question) params.append('question', question);
    
    const response = await fetch(`/api/v1/external/groq-compound/analyze-url?${params}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    console.log('URL:', data.url);
    console.log('Analysis:', data.analysis);
    
    return data;
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
}

// Usage examples
chatWithUrls("Analyze this page: https://groq.com/blog/inside-the-lpu-deconstructing-groq-speed");
analyzeUrl("https://groq.com", "What are the key features of Groq?");
'''
    
    print("JavaScript code for frontend integration:")
    print(js_code)


async def main():
    """Run all examples"""
    print("🚀 Groq Compound Model Usage Examples")
    print("=" * 60)
    
    # Run examples
    await example_url_detection()
    await example_compound_chat()
    await example_enhanced_chat_integration()
    await example_api_usage()
    example_frontend_integration()
    
    print("\n\n🏁 All examples completed!")
    print("\nNext steps:")
    print("1. Configure GROQ_API_KEY in your .env file")
    print("2. Start the backend server: python backend/working_server.py")
    print("3. Visit http://localhost:3000/test-compound-model to test the frontend")
    print("4. Use the API endpoints in your own applications")


if __name__ == "__main__":
    asyncio.run(main())