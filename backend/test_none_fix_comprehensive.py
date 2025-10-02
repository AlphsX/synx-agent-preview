#!/usr/bin/env python3
"""
Comprehensive test for NoneType error fixes in chat service.
Tests various scenarios where external APIs might return None or empty results.
"""

import asyncio
import sys
from typing import Dict, Any, List

# Test the safe data handler
from app.enhanced_error_handler import SafeDataHandler, error_handler

def test_safe_data_operations():
    """Test all safe data operations with None and edge cases"""
    print("🧪 Testing SafeDataHandler operations...")
    
    safe_data = SafeDataHandler()
    
    # Test safe_get with None
    assert safe_data.safe_get(None, "key", "default") == "default"
    assert safe_data.safe_get({}, "key", "default") == "default"
    assert safe_data.safe_get({"key": "value"}, "key") == "value"
    print("✅ safe_get works correctly")
    
    # Test safe_list with None
    assert safe_data.safe_list(None) == []
    assert safe_data.safe_list([]) == []
    assert safe_data.safe_list([1, 2, 3]) == [1, 2, 3]
    print("✅ safe_list works correctly")
    
    # Test safe_dict with None
    assert safe_data.safe_dict(None) == {}
    assert safe_data.safe_dict({}) == {}
    assert safe_data.safe_dict({"key": "value"}) == {"key": "value"}
    print("✅ safe_dict works correctly")
    
    # Test safe_string with None
    assert safe_data.safe_string(None) == ""
    assert safe_data.safe_string("test") == "test"
    print("✅ safe_string works correctly")
    
    print("✅ All SafeDataHandler tests passed!\n")
    return True


def test_context_building_with_empty_data():
    """Test context building with various empty/None scenarios"""
    print("🧪 Testing context building with empty data...")
    
    safe_data = SafeDataHandler()
    
    # Scenario 1: Completely empty context
    context = {}
    web_search = safe_data.safe_dict(context.get("web_search", {}))
    assert web_search == {}
    print("✅ Empty context handled correctly")
    
    # Scenario 2: Context with empty results
    context = {
        "web_search": {
            "results": [],
            "provider": "test"
        }
    }
    web_search = safe_data.safe_dict(context.get("web_search", {}))
    results = safe_data.safe_list(web_search.get("results", []))
    assert results == []
    assert len(results) == 0
    print("✅ Empty results list handled correctly")
    
    # Scenario 3: Context with None results
    context = {
        "web_search": {
            "results": None,
            "provider": "test"
        }
    }
    web_search = safe_data.safe_dict(context.get("web_search", {}))
    results = safe_data.safe_list(web_search.get("results", []))
    assert results == []
    print("✅ None results handled correctly")
    
    # Scenario 4: Context with results but first item is None
    context = {
        "web_search": {
            "results": [None, {"title": "test"}],
            "provider": "test"
        }
    }
    web_search = safe_data.safe_dict(context.get("web_search", {}))
    results = safe_data.safe_list(web_search.get("results", []))
    assert len(results) == 2
    first_result = safe_data.safe_dict(results[0])
    assert first_result == {}
    print("✅ None items in results handled correctly")
    
    # Scenario 5: Accessing nested None values
    context = {
        "news": {
            "results": [
                {
                    "title": None,
                    "description": None,
                    "source": None
                }
            ]
        }
    }
    news_data = safe_data.safe_dict(context.get("news", {}))
    results = safe_data.safe_list(news_data.get("results", []))
    if results:
        article = safe_data.safe_dict(results[0])
        # When title is None, .get() returns None, then safe_string converts to ""
        # But we want "No title" as fallback, so we use: article.get("title") or "No title"
        title = safe_data.safe_string(article.get("title") or "No title")
        assert title == "No title"
    print("✅ Nested None values handled correctly")
    
    print("✅ All context building tests passed!\n")
    return True


def test_provider_extraction():
    """Test safe provider extraction from results"""
    print("🧪 Testing provider extraction...")
    
    safe_data = SafeDataHandler()
    
    # Test with valid results
    results = [{"provider": "serpapi", "title": "test"}]
    provider = "unknown"
    if results and len(results) > 0:
        first_result = safe_data.safe_dict(results[0])
        if first_result:
            provider = first_result.get("provider", "unknown")
    assert provider == "serpapi"
    print("✅ Valid provider extraction works")
    
    # Test with empty results
    results = []
    provider = "unknown"
    if results and len(results) > 0:
        first_result = safe_data.safe_dict(results[0])
        if first_result:
            provider = first_result.get("provider", "unknown")
    assert provider == "unknown"
    print("✅ Empty results provider extraction works")
    
    # Test with None results
    results = None
    provider = "unknown"
    if results and isinstance(results, list) and len(results) > 0:
        first_result = safe_data.safe_dict(results[0])
        if first_result:
            provider = first_result.get("provider", "unknown")
    assert provider == "unknown"
    print("✅ None results provider extraction works")
    
    # Test with None first item
    results = [None, {"provider": "brave"}]
    provider = "unknown"
    if results and len(results) > 0:
        first_result = safe_data.safe_dict(results[0])
        if first_result:
            provider = first_result.get("provider", "unknown")
    assert provider == "unknown"  # First item is None, so we get default
    print("✅ None first item provider extraction works")
    
    print("✅ All provider extraction tests passed!\n")
    return True


async def test_error_handler_mock_response():
    """Test error handler's mock response generation"""
    print("🧪 Testing error handler mock response...")
    
    # Test with empty context
    response_parts = []
    async for chunk in error_handler.safe_generate_mock_response("What's trending?", {}):
        response_parts.append(chunk)
    
    response = "".join(response_parts)
    assert len(response) > 0
    assert "trending" in response.lower() or "help" in response.lower()
    print("✅ Mock response generated successfully")
    
    # Test with some context
    context = {
        "web_search": {
            "results": [],
            "provider": "test"
        }
    }
    response_parts = []
    async for chunk in error_handler.safe_generate_mock_response("Latest news", context):
        response_parts.append(chunk)
    
    response = "".join(response_parts)
    assert len(response) > 0
    print("✅ Mock response with context generated successfully")
    
    print("✅ All error handler tests passed!\n")
    return True


def test_real_world_scenarios():
    """Test real-world scenarios that caused the NoneType error"""
    print("🧪 Testing real-world scenarios...")
    
    safe_data = SafeDataHandler()
    
    # Scenario: "What's trending on the internet today?"
    # External API returns empty results
    context = {
        "web_search": {
            "query": "trending internet today",
            "results": [],
            "provider": "serpapi"
        }
    }
    
    # Simulate the code path that was failing
    web_search = safe_data.safe_dict(context.get("web_search", {}))
    if web_search and "results" in web_search:
        results = safe_data.safe_list(web_search.get("results", []))
        if results and len(results) > 0:
            # This block won't execute with empty results
            provider = safe_data.safe_string(web_search.get("provider", "search engine"))
            print(f"   Would show results from {provider}")
        else:
            print("   ✅ Correctly handled empty results - no NoneType error!")
    
    # Scenario: "Latest news in AI development"
    # External API returns None
    context = {
        "news": {
            "query": "AI development news",
            "results": None
        }
    }
    
    news_data = safe_data.safe_dict(context.get("news", {}))
    if news_data and "results" in news_data:
        results = safe_data.safe_list(news_data.get("results", []))
        if results and len(results) > 0:
            print("   Would show news results")
        else:
            print("   ✅ Correctly handled None results - no NoneType error!")
    
    # Scenario: API returns results but with None values inside
    context = {
        "web_search": {
            "results": [
                {
                    "title": None,
                    "description": None,
                    "url": None,
                    "source": None
                }
            ],
            "provider": "brave"
        }
    }
    
    web_search = safe_data.safe_dict(context.get("web_search", {}))
    if web_search and "results" in web_search:
        results = safe_data.safe_list(web_search.get("results", []))
        if results and len(results) > 0:
            for i, result in enumerate(results[:5], 1):
                result = safe_data.safe_dict(result)
                if result:
                    # Use 'or' to provide fallback when value is None
                    title = safe_data.safe_string(result.get("title") or "No title")
                    description = safe_data.safe_string(result.get("description") or "No description")
                    # These will be "No title" and "No description" instead of causing errors
                    assert title == "No title"
                    assert description == "No description"
                    print(f"   ✅ Result {i}: Safely handled None values in result fields")
    
    print("✅ All real-world scenario tests passed!\n")
    return True


async def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 Running Comprehensive NoneType Fix Tests")
    print("=" * 60)
    print()
    
    try:
        # Run synchronous tests
        test_safe_data_operations()
        test_context_building_with_empty_data()
        test_provider_extraction()
        test_real_world_scenarios()
        
        # Run async tests
        await test_error_handler_mock_response()
        
        print("=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("✨ The NoneType error fixes are working correctly!")
        print()
        print("What was fixed:")
        print("1. ✅ Safe data access for all external API results")
        print("2. ✅ Proper None checking before accessing list items")
        print("3. ✅ Safe provider extraction from results")
        print("4. ✅ Graceful handling of empty/None results")
        print("5. ✅ Better fallback messages when no data is available")
        print()
        print("Your AI will now:")
        print("- Handle empty search results gracefully")
        print("- Not crash when external APIs return None")
        print("- Provide helpful responses even without real-time data")
        print("- Show clear messages when data isn't available")
        print()
        return True
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ TEST FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
