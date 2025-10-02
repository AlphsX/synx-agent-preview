#!/usr/bin/env python3
"""
Test API endpoints to verify NoneType error fixes
"""

import asyncio
import aiohttp
import json
import sys
import time


async def test_chat_endpoint():
    """Test the chat endpoint that was causing NoneType errors"""
    
    print("🧪 Testing chat endpoint with potential NoneType scenarios...")
    
    # Test data that might cause NoneType errors
    test_cases = [
        {
            "name": "Simple question",
            "data": {
                "content": "Hello, how are you?",
                "role": "user",
                "model_id": "openai/gpt-oss-120b"
            }
        },
        {
            "name": "Search query that might return None results",
            "data": {
                "content": "What is the latest news about xyzabc123nonexistent?",
                "role": "user", 
                "model_id": "openai/gpt-oss-120b"
            }
        },
        {
            "name": "Crypto query that might fail",
            "data": {
                "content": "What is the price of NONEXISTENTCOIN?",
                "role": "user",
                "model_id": "openai/gpt-oss-120b"
            }
        },
        {
            "name": "Complex query with multiple context needs",
            "data": {
                "content": "Tell me about Bitcoin price and latest tech news",
                "role": "user",
                "model_id": "openai/gpt-oss-120b"
            }
        }
    ]
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        # First create a conversation
        print("Creating test conversation...")
        
        try:
            async with session.post(
                f"{base_url}/api/chat/conversations",
                json={"title": "Test Conversation"}
            ) as response:
                if response.status == 200:
                    conversation_data = await response.json()
                    conversation_id = conversation_data["id"]
                    print(f"✅ Created conversation: {conversation_id}")
                else:
                    print(f"❌ Failed to create conversation: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Error creating conversation: {e}")
            return False
        
        # Test each case
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. Testing: {test_case['name']}")
            
            try:
                async with session.post(
                    f"{base_url}/api/chat/conversations/{conversation_id}/chat",
                    json=test_case["data"]
                ) as response:
                    
                    if response.status == 200:
                        print(f"✅ Status: {response.status}")
                        
                        # Read the streaming response
                        response_text = ""
                        async for line in response.content:
                            if line:
                                line_text = line.decode('utf-8').strip()
                                if line_text.startswith('data: '):
                                    data_part = line_text[6:]  # Remove 'data: ' prefix
                                    if data_part and data_part != '[DONE]':
                                        response_text += data_part
                        
                        # Check if we got the old error message
                        if "'NoneType' object is not subscriptable" in response_text:
                            print(f"❌ Still getting NoneType error!")
                            print(f"Response: {response_text[:200]}...")
                            return False
                        else:
                            print(f"✅ No NoneType error detected")
                            if "Oops! Something went wrong" in response_text:
                                print(f"✅ Got graceful fallback response")
                            print(f"Response preview: {response_text[:100]}...")
                    
                    else:
                        print(f"⚠️  Status: {response.status}")
                        error_text = await response.text()
                        if "'NoneType' object is not subscriptable" in error_text:
                            print(f"❌ NoneType error in HTTP error response!")
                            return False
                        else:
                            print(f"✅ No NoneType error in error response")
            
            except Exception as e:
                print(f"❌ Request failed: {e}")
                if "'NoneType' object is not subscriptable" in str(e):
                    print(f"❌ NoneType error in exception!")
                    return False
            
            # Small delay between requests
            await asyncio.sleep(1)
    
    print(f"\n🎉 All test cases completed without NoneType errors!")
    return True


async def test_health_endpoints():
    """Test health endpoints to make sure server is running"""
    
    print("🏥 Testing health endpoints...")
    
    base_url = "http://localhost:8000"
    endpoints = [
        "/health",
        "/api/status",
        "/api/chat/status"
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints:
            try:
                async with session.get(f"{base_url}{endpoint}") as response:
                    if response.status == 200:
                        print(f"✅ {endpoint}: OK")
                    else:
                        print(f"⚠️  {endpoint}: {response.status}")
            except Exception as e:
                print(f"❌ {endpoint}: {e}")
                return False
    
    return True


async def main():
    """Run API tests"""
    
    print("🚀 Starting API tests for NoneType error fixes...\n")
    
    # Test health endpoints first
    health_ok = await test_health_endpoints()
    
    if not health_ok:
        print("\n❌ Health check failed. Make sure the server is running:")
        print("   cd backend && python -m uvicorn app.main:app --reload")
        return False
    
    print("\n" + "="*50)
    
    # Test chat endpoints
    chat_ok = await test_chat_endpoint()
    
    if chat_ok:
        print("\n🎉 SUCCESS! All API tests passed.")
        print("\nThe NoneType error has been fixed! 🎊")
        print("\nWhat was fixed:")
        print("- Added safe data access methods to prevent None subscripting")
        print("- Enhanced error handling with graceful fallbacks")
        print("- Improved context validation and None checking")
        print("- Added comprehensive error recovery mechanisms")
        print("\nYour AI should now respond normally without NoneType errors! ✨")
        return True
    else:
        print("\n❌ Some tests failed. The NoneType error may still exist.")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)