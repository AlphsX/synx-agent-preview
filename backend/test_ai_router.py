#!/usr/bin/env python3
"""
Test script for AI Model Router functionality.

This script tests the AI model router with various scenarios:
- Model availability checking
- Response generation with fallback
- Provider status checking
- Mock responses when no API keys are configured
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.ai.service import AIService
from app.ai.models import ChatMessage


async def test_ai_service():
    """Test the AI service functionality"""
    print("🤖 Testing AI Model Router")
    print("=" * 50)
    
    # Initialize AI service
    ai_service = AIService()
    
    # Test 1: Get available models
    print("\n1. Testing available models:")
    models = ai_service.get_available_models()
    print(f"   Found {len(models)} models:")
    for model in models[:5]:  # Show first 5 models
        print(f"   - {model.id} ({model.provider}) - Available: {model.available}")
    
    # Test 2: Get provider status
    print("\n2. Testing provider status:")
    status = ai_service.get_provider_status()
    for provider, info in status.items():
        print(f"   - {provider}: Available={info['available']}, Models={info['models']}")
    
    # Test 3: Get recommended model
    print("\n3. Testing model recommendations:")
    for task_type in ["general", "fast", "cheap"]:
        recommended = ai_service.get_recommended_model(task_type)
        print(f"   - {task_type}: {recommended}")
    
    # Test 4: Test chat functionality
    print("\n4. Testing chat functionality:")
    test_message = "Hello! Can you tell me about artificial intelligence?"
    
    # Try to find an available model
    available_models = [m for m in models if m.available]
    if available_models:
        test_model = available_models[0].id
        print(f"   Using model: {test_model}")
        
        print("   Response:")
        response_parts = []
        async for chunk in ai_service.chat_with_context(
            message=test_message,
            model_id=test_model,
            stream=True
        ):
            response_parts.append(chunk)
            print(chunk, end="", flush=True)
        
        print(f"\n   Total response length: {len(''.join(response_parts))} characters")
    else:
        print("   No available models found, testing mock response:")
        print("   Response:")
        async for chunk in ai_service.generate_mock_response(
            message=test_message,
            model_id="demo-model",
            stream=True
        ):
            print(chunk, end="", flush=True)
        print()
    
    # Test 5: Test model availability checking
    print("\n5. Testing model availability:")
    test_models = ["gpt-4", "claude-3-5-sonnet-20241022", "llama-3.1-70b-versatile", "nonexistent-model"]
    for model_id in test_models:
        available = await ai_service.check_model_availability(model_id)
        print(f"   - {model_id}: {'✅ Available' if available else '❌ Not available'}")
    
    print("\n" + "=" * 50)
    print("✅ AI Model Router test completed!")


async def test_fallback_logic():
    """Test the fallback logic specifically"""
    print("\n🔄 Testing Fallback Logic")
    print("=" * 30)
    
    ai_service = AIService()
    
    # Test with a non-existent model to trigger fallback
    print("Testing fallback with non-existent model:")
    test_message = "This should trigger fallback logic."
    
    response_parts = []
    async for chunk in ai_service.chat_with_context(
        message=test_message,
        model_id="nonexistent-model-12345",
        stream=True
    ):
        response_parts.append(chunk)
        print(chunk, end="", flush=True)
    
    print(f"\nFallback response length: {len(''.join(response_parts))} characters")


if __name__ == "__main__":
    print("🚀 Starting AI Model Router Tests")
    
    try:
        # Run the main test
        asyncio.run(test_ai_service())
        
        # Run fallback test
        asyncio.run(test_fallback_logic())
        
        print("\n🎉 All tests completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()