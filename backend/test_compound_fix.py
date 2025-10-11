#!/usr/bin/env python3
"""
Test script to verify the compound model fix
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.external_apis.groq_compound_service import groq_compound_service
from app.enhanced_chat_service import EnhancedChatService


async def test_url_detection_fix():
    """Test URL detection with various inputs including edge cases"""
    print("🔍 Testing URL Detection Fix...")
    
    test_cases = [
        "Summarize the key points of this page: https://groq.com/blog/inside-the-lpu-deconstructing-groq-speed",
        "",  # Empty string
        None,  # None value
        123,  # Non-string
        "Just a regular message",
        "Check out https://groq.com and www.example.com",
    ]
    
    for i, message in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {repr(message)}")
        
        try:
            urls = groq_compound_service.detect_urls_in_message(message)
            should_use = groq_compound_service.should_use_compound_model(message)
            
            print(f"   URLs detected: {urls}")
            print(f"   Should use compound: {should_use}")
            print("   ✅ No errors")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")


async def test_enhanced_chat_fix():
    """Test enhanced chat service with URL message"""
    print("\n\n💬 Testing Enhanced Chat Fix...")
    
    chat_service = EnhancedChatService()
    
    test_message = "Summarize the key points of this page: https://groq.com/blog/inside-the-lpu-deconstructing-groq-speed"
    
    print(f"Test message: {test_message}")
    print("Generating response...")
    
    try:
        response_content = ""
        chunk_count = 0
        
        async for chunk in chat_service.generate_ai_response(
            message=test_message,
            model_id="groq/compound",
            conversation_id=None,
            user_context={
                "user_id": "test_user",
                "username": "test_user", 
                "is_authenticated": True
            }
        ):
            if chunk:
                response_content += chunk
                chunk_count += 1
                print(chunk, end="", flush=True)
        
        print(f"\n\n✅ Response completed!")
        print(f"Total chunks: {chunk_count}")
        print(f"Response length: {len(response_content)} characters")
        
        if "Oops! Something went wrong" in response_content:
            print("❌ Still getting error message")
        else:
            print("✅ No error message detected")
            
    except Exception as e:
        print(f"❌ Exception: {e}")


async def test_compound_service_directly():
    """Test compound service directly"""
    print("\n\n🤖 Testing Compound Service Directly...")
    
    if not groq_compound_service.is_available():
        print("❌ Groq compound service not available (API key not configured)")
        print("This is expected if GROQ_API_KEY is not set")
        return
    
    test_message = "Please analyze this page: https://groq.com"
    
    print(f"Test message: {test_message}")
    print("Generating response...")
    
    try:
        response_content = ""
        chunk_count = 0
        
        async for chunk in groq_compound_service.generate_response_with_urls(
            message=test_message,
            stream=True
        ):
            if chunk:
                response_content += chunk
                chunk_count += 1
                print(chunk, end="", flush=True)
        
        print(f"\n\n✅ Direct compound service test completed!")
        print(f"Total chunks: {chunk_count}")
        print(f"Response length: {len(response_content)} characters")
        
    except Exception as e:
        print(f"❌ Exception: {e}")


async def main():
    """Run all tests"""
    print("🚀 Testing Compound Model Fix\n")
    
    # Test URL detection with edge cases
    await test_url_detection_fix()
    
    # Test enhanced chat service
    await test_enhanced_chat_fix()
    
    # Test compound service directly
    await test_compound_service_directly()
    
    print("\n🏁 All tests completed!")
    print("\nIf you see '✅ No error message detected', the fix is working!")


if __name__ == "__main__":
    asyncio.run(main())