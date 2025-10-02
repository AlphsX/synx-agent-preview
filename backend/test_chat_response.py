#!/usr/bin/env python3
"""
Test script to verify chat responses are working correctly
"""

import asyncio
import sys
from app.enhanced_chat_service import EnhancedChatService

async def test_trending_query():
    """Test a trending query to see the actual response"""
    print("=" * 70)
    print("Testing: What's trending on the internet today?")
    print("=" * 70)
    
    service = EnhancedChatService()
    
    # Test query
    message = "What's trending on the internet today?"
    model_id = "llama-3.1-70b-versatile"  # Groq model
    
    print(f"\nModel: {model_id}")
    print(f"Query: {message}\n")
    print("Response:")
    print("-" * 70)
    
    response_parts = []
    try:
        async for chunk in service.generate_ai_response(
            message=message,
            model_id=model_id,
            conversation_history=[],
            user_context={
                "user_id": None,
                "username": "test_user",
                "is_authenticated": False
            }
        ):
            response_parts.append(chunk)
            print(chunk, end="", flush=True)
        
        print("\n" + "-" * 70)
        print(f"\nTotal response length: {len(''.join(response_parts))} characters")
        
        # Check for issues
        full_response = ''.join(response_parts)
        if "Search?" in full_response or "search(" in full_response.lower():
            print("\n⚠️  WARNING: Response contains search function calls!")
            print("This means the AI is trying to call tools instead of using provided context.")
        elif "NoneType" in full_response:
            print("\n❌ ERROR: NoneType error still present!")
        elif len(full_response) < 50:
            print("\n⚠️  WARNING: Response is very short or empty!")
        else:
            print("\n✅ Response looks good!")
        
        return full_response
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_news_query():
    """Test a news query"""
    print("\n" + "=" * 70)
    print("Testing: Latest news in AI development")
    print("=" * 70)
    
    service = EnhancedChatService()
    
    message = "Latest news in AI development"
    model_id = "llama-3.1-70b-versatile"
    
    print(f"\nModel: {model_id}")
    print(f"Query: {message}\n")
    print("Response:")
    print("-" * 70)
    
    response_parts = []
    try:
        async for chunk in service.generate_ai_response(
            message=message,
            model_id=model_id,
            conversation_history=[],
            user_context={
                "user_id": None,
                "username": "test_user",
                "is_authenticated": False
            }
        ):
            response_parts.append(chunk)
            print(chunk, end="", flush=True)
        
        print("\n" + "-" * 70)
        
        full_response = ''.join(response_parts)
        if "Search?" in full_response or "search(" in full_response.lower():
            print("\n⚠️  WARNING: Response contains search function calls!")
        elif "NoneType" in full_response:
            print("\n❌ ERROR: NoneType error still present!")
        elif len(full_response) < 50:
            print("\n⚠️  WARNING: Response is very short or empty!")
        else:
            print("\n✅ Response looks good!")
        
        return full_response
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_general_query():
    """Test a general knowledge query (should work without external data)"""
    print("\n" + "=" * 70)
    print("Testing: What is artificial intelligence?")
    print("=" * 70)
    
    service = EnhancedChatService()
    
    message = "What is artificial intelligence?"
    model_id = "llama-3.1-70b-versatile"
    
    print(f"\nModel: {model_id}")
    print(f"Query: {message}\n")
    print("Response:")
    print("-" * 70)
    
    response_parts = []
    try:
        async for chunk in service.generate_ai_response(
            message=message,
            model_id=model_id,
            conversation_history=[],
            user_context={
                "user_id": None,
                "username": "test_user",
                "is_authenticated": False
            }
        ):
            response_parts.append(chunk)
            print(chunk, end="", flush=True)
        
        print("\n" + "-" * 70)
        
        full_response = ''.join(response_parts)
        if "Search?" in full_response or "search(" in full_response.lower():
            print("\n⚠️  WARNING: Response contains search function calls!")
        elif len(full_response) < 50:
            print("\n⚠️  WARNING: Response is very short or empty!")
        else:
            print("\n✅ Response looks good!")
        
        return full_response
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Run all tests"""
    print("\n🧪 Testing Chat Response System")
    print("=" * 70)
    
    results = {
        "trending": None,
        "news": None,
        "general": None
    }
    
    # Test 1: Trending query (needs external data)
    results["trending"] = await test_trending_query()
    await asyncio.sleep(2)
    
    # Test 2: News query (needs external data)
    results["news"] = await test_news_query()
    await asyncio.sleep(2)
    
    # Test 3: General query (no external data needed)
    results["general"] = await test_general_query()
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    issues = []
    
    for test_name, response in results.items():
        if response is None:
            print(f"❌ {test_name}: Failed to get response")
            issues.append(f"{test_name}: No response")
        elif "Search?" in response or "search(" in response.lower():
            print(f"⚠️  {test_name}: Contains function calls")
            issues.append(f"{test_name}: Function calls detected")
        elif "NoneType" in response:
            print(f"❌ {test_name}: NoneType error")
            issues.append(f"{test_name}: NoneType error")
        elif len(response) < 50:
            print(f"⚠️  {test_name}: Response too short ({len(response)} chars)")
            issues.append(f"{test_name}: Short response")
        else:
            print(f"✅ {test_name}: OK ({len(response)} chars)")
    
    print("\n" + "=" * 70)
    
    if issues:
        print(f"\n⚠️  Found {len(issues)} issue(s):")
        for issue in issues:
            print(f"  - {issue}")
        print("\nRecommendations:")
        if any("function calls" in i.lower() for i in issues):
            print("  1. Check system message - AI is trying to call functions")
            print("  2. Make sure no tools/functions are being sent to the API")
            print("  3. Try a different model that doesn't use function calling")
        if any("nonetype" in i.lower() for i in issues):
            print("  1. Check enhanced_chat_service.py for None handling")
            print("  2. Verify SafeDataHandler is being used correctly")
        if any("short response" in i.lower() for i in issues):
            print("  1. Check if external APIs are returning data")
            print("  2. Verify system message is being built correctly")
        return False
    else:
        print("\n🎉 All tests passed!")
        return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
