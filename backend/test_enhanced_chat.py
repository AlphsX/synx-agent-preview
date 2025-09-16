#!/usr/bin/env python3
"""
Test script for Enhanced Chat Service functionality
"""

import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.enhanced_chat_service import EnhancedChatService

async def test_enhanced_chat():
    """Test the enhanced chat service"""
    print("🧪 Testing Enhanced Chat Service...")
    
    # Initialize service
    service = EnhancedChatService()
    print("✅ Service initialized")
    
    # Test context detection
    test_messages = [
        "What's the latest news about AI?",
        "What's the current Bitcoin price?", 
        "Search for information about FastAPI",
        "Hello, how are you?"
    ]
    
    for message in test_messages:
        print(f"\n📝 Testing message: '{message}'")
        
        try:
            # Test context detection
            context = await service._get_enhanced_context(message)
            print(f"🔍 Context detected: {list(context.keys())}")
            
            # Test response generation (first few chunks)
            print("🤖 Generating response...")
            chunk_count = 0
            async for chunk in service.generate_ai_response(
                message=message,
                model_id="openai/gpt-oss-120b",
                conversation_id="test_conv"
            ):
                if chunk_count < 3:  # Only show first 3 chunks
                    print(f"   Chunk {chunk_count + 1}: {chunk[:50]}...")
                chunk_count += 1
                if chunk_count >= 5:  # Limit for testing
                    break
            
            print(f"✅ Generated {chunk_count} chunks")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test service status
    print("\n📊 Testing service status...")
    try:
        status = await service.get_service_status()
        print(f"✅ Service status: {status}")
    except Exception as e:
        print(f"❌ Status error: {e}")
    
    print("\n🎉 Enhanced Chat Service test completed!")

if __name__ == "__main__":
    asyncio.run(test_enhanced_chat())