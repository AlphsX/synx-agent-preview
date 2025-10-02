#!/usr/bin/env python3
"""
Test script to verify NoneType error fixes
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.enhanced_error_handler import SafeDataHandler, error_handler


def test_safe_data_handler():
    """Test SafeDataHandler with various None scenarios"""
    print("Testing SafeDataHandler...")
    
    safe_data = SafeDataHandler()
    
    # Test safe_get with None
    result = safe_data.safe_get(None, "key", "default")
    assert result == "default", f"Expected 'default', got {result}"
    print("✅ safe_get with None: PASS")
    
    # Test safe_index with None
    result = safe_data.safe_index(None, 0, "default")
    assert result == "default", f"Expected 'default', got {result}"
    print("✅ safe_index with None: PASS")
    
    # Test safe_list with None
    result = safe_data.safe_list(None)
    assert result == [], f"Expected [], got {result}"
    print("✅ safe_list with None: PASS")
    
    # Test safe_dict with None
    result = safe_data.safe_dict(None)
    assert result == {}, f"Expected {{}}, got {result}"
    print("✅ safe_dict with None: PASS")
    
    # Test with empty list
    result = safe_data.safe_index([], 0, "default")
    assert result == "default", f"Expected 'default', got {result}"
    print("✅ safe_index with empty list: PASS")
    
    # Test with valid data
    data = {"key": "value"}
    result = safe_data.safe_get(data, "key", "default")
    assert result == "value", f"Expected 'value', got {result}"
    print("✅ safe_get with valid data: PASS")
    
    # Test with valid list
    data = ["item1", "item2"]
    result = safe_data.safe_index(data, 0, "default")
    assert result == "item1", f"Expected 'item1', got {result}"
    print("✅ safe_index with valid list: PASS")
    
    print("All SafeDataHandler tests passed! ✅")


async def test_error_handler():
    """Test error handler mock response generation"""
    print("\nTesting error handler...")
    
    # Test with None context
    response_chunks = []
    async for chunk in error_handler.safe_generate_mock_response("test message", None):
        response_chunks.append(chunk)
    
    response = "".join(response_chunks)
    assert len(response) > 0, "Expected non-empty response"
    print("✅ Mock response with None context: PASS")
    
    # Test with empty context
    response_chunks = []
    async for chunk in error_handler.safe_generate_mock_response("test message", {}):
        response_chunks.append(chunk)
    
    response = "".join(response_chunks)
    assert len(response) > 0, "Expected non-empty response"
    print("✅ Mock response with empty context: PASS")
    
    # Test with web search context (but None results)
    context = {
        "web_search": {
            "results": None
        }
    }
    response_chunks = []
    async for chunk in error_handler.safe_generate_mock_response("test message", context):
        response_chunks.append(chunk)
    
    response = "".join(response_chunks)
    assert len(response) > 0, "Expected non-empty response"
    print("✅ Mock response with None web search results: PASS")
    
    # Test with valid web search context
    context = {
        "web_search": {
            "results": [
                {"title": "Test Title", "description": "Test Description"},
                {"title": None, "description": None}  # Test None values
            ]
        }
    }
    response_chunks = []
    async for chunk in error_handler.safe_generate_mock_response("test message", context):
        response_chunks.append(chunk)
    
    response = "".join(response_chunks)
    assert "Test Title" in response, "Expected title in response"
    print("✅ Mock response with valid web search context: PASS")
    
    print("All error handler tests passed! ✅")


def test_none_subscriptable_scenarios():
    """Test scenarios that would cause 'NoneType' object is not subscriptable"""
    print("\nTesting NoneType subscriptable scenarios...")
    
    safe_data = SafeDataHandler()
    
    # Scenario 1: None[0] - would cause error
    try:
        result = safe_data.safe_index(None, 0, "safe")
        assert result == "safe", f"Expected 'safe', got {result}"
        print("✅ Prevented None[0] error: PASS")
    except Exception as e:
        print(f"❌ Failed to prevent None[0] error: {e}")
        return False
    
    # Scenario 2: None["key"] - would cause error
    try:
        result = safe_data.safe_get(None, "key", "safe")
        assert result == "safe", f"Expected 'safe', got {result}"
        print("✅ Prevented None['key'] error: PASS")
    except Exception as e:
        print(f"❌ Failed to prevent None['key'] error: {e}")
        return False
    
    # Scenario 3: results[0] where results is None
    try:
        results = None
        result = safe_data.safe_index(results, 0, {"provider": "fallback"})
        provider = safe_data.safe_get(result, "provider", "unknown")
        assert provider == "fallback", f"Expected 'fallback', got {provider}"
        print("✅ Prevented results[0] where results is None: PASS")
    except Exception as e:
        print(f"❌ Failed to prevent results[0] error: {e}")
        return False
    
    # Scenario 4: Complex nested access
    try:
        context = None
        web_search = safe_data.safe_get(context, "web_search", {})
        results = safe_data.safe_get(web_search, "results", [])
        first_result = safe_data.safe_index(results, 0, {})
        provider = safe_data.safe_get(first_result, "provider", "unknown")
        assert provider == "unknown", f"Expected 'unknown', got {provider}"
        print("✅ Prevented complex nested None access: PASS")
    except Exception as e:
        print(f"❌ Failed to prevent complex nested access: {e}")
        return False
    
    print("All NoneType subscriptable tests passed! ✅")
    return True


async def main():
    """Run all tests"""
    print("🧪 Testing NoneType error fixes...\n")
    
    try:
        # Test SafeDataHandler
        test_safe_data_handler()
        
        # Test error handler
        await test_error_handler()
        
        # Test NoneType subscriptable scenarios
        success = test_none_subscriptable_scenarios()
        
        if success:
            print("\n🎉 All tests passed! The NoneType error fixes are working correctly.")
            print("\nThe enhanced error handler will now:")
            print("- Safely handle None values in all data access")
            print("- Provide helpful fallback responses when AI services fail")
            print("- Prevent 'NoneType object is not subscriptable' errors")
            print("- Generate contextual responses based on available data")
            return True
        else:
            print("\n❌ Some tests failed. Please check the implementation.")
            return False
            
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)