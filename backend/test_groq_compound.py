#!/usr/bin/env python3
"""
Test script for Groq Compound Model functionality

This script tests the Groq compound model integration for URL-based queries.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.external_apis.groq_compound_service import groq_compound_service
from app.enhanced_chat_service import EnhancedChatService


async def test_url_detection():
    """Test URL detection functionality"""
    print("🔍 Testing URL Detection...")
    
    test_messages = [
        "Check out this article: https://groq.com/blog/inside-the-lpu-deconstructing-groq-speed",
        "What do you think about www.example.com?",
        "Visit google.com for more info",
        "This is just a regular message without URLs",
        "Multiple URLs: https://groq.com and https://openai.com",
        "Mixed content with https://github.com/groq and some text"
    ]
    
    for message in test_messages:
        urls = groq_compound_service.detect_urls_in_message(message)
        should_use = groq_compound_service.should_use_compound_model(message)
        
        print(f"\nMessage: {message}")
        print(f"URLs detected: {urls}")
        print(f"Should use compound: {should_use}")


async def test_compound_model():
    """Test the compound model with a real URL"""
    print("\n🤖 Testing Groq Compound Model...")
    
    if not groq_compound_service.is_available():
        print("❌ Groq compound service not available (API key not configured)")
        return
    
    test_url = "https://groq.com"
    test_message = f"Please summarize the key points of this page: {test_url}"
    
    print(f"Test message: {test_message}")
    print("Generating response...")
    
    try:
        response_content = ""
        async for chunk in groq_compound_service.generate_response_with_urls(
            message=test_message,
            stream=True
        ):
            response_content += chunk
            print(chunk, end="", flush=True)
        
        print(f"\n\n✅ Response generated successfully!")
        print(f"Response length: {len(response_content)} characters")
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def test_enhanced_chat_integration():
    """Test integration with enhanced chat service"""
    print("\n💬 Testing Enhanced Chat Integration...")
    
    chat_service = EnhancedChatService()
    
    test_message = "Analyze this page for me: https://groq.com/blog/inside-the-lpu-deconstructing-groq-speed"
    
    print(f"Test message: {test_message}")
    print("Generating response through enhanced chat service...")
    
    try:
        response_content = ""
        async for chunk in chat_service.generate_ai_response(
            message=test_message,
            model_id="groq/compound",  # This should trigger compound model usage
            conversation_id=None,
            user_context={"user_id": "test", "username": "test_user", "is_authenticated": True}
        ):
            response_content += chunk
            print(chunk, end="", flush=True)
        
        print(f"\n\n✅ Enhanced chat response generated successfully!")
        print(f"Response length: {len(response_content)} characters")
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    """Run all tests"""
    print("🚀 Starting Groq Compound Model Tests\n")
    
    # Test URL detection
    await test_url_detection()
    
    # Test compound model directly
    await test_compound_model()
    
    # Test enhanced chat integration
    await test_enhanced_chat_integration()
    
    print("\n🏁 All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())