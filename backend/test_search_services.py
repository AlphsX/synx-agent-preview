#!/usr/bin/env python3
"""
Test script for search services implementation.
This script tests the SerpAPI, Brave Search, and unified SearchService.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.external_apis.serpapi import SerpAPIService
from app.external_apis.brave_search import BraveSearchService
from app.external_apis.search_service import SearchService, SearchProvider


async def test_serpapi():
    """Test SerpAPI service."""
    print("\n=== Testing SerpAPI Service ===")
    
    service = SerpAPIService()
    
    # Check availability
    print(f"SerpAPI available: {service.is_available()}")
    
    if service.is_available():
        # Test web search
        print("Testing web search...")
        results = await service.search_web("Python programming", count=3)
        print(f"Web search results: {len(results)}")
        for i, result in enumerate(results[:2], 1):
            print(f"  {i}. {result.get('title', 'No title')}")
        
        # Test news search
        print("Testing news search...")
        news_results = await service.search_news("artificial intelligence", count=2)
        print(f"News search results: {len(news_results)}")
        for i, result in enumerate(news_results[:2], 1):
            print(f"  {i}. {result.get('title', 'No title')}")
    else:
        print("SerpAPI not available (no API key configured)")


async def test_brave_search():
    """Test Brave Search service."""
    print("\n=== Testing Brave Search Service ===")
    
    service = BraveSearchService()
    
    # Check availability
    print(f"Brave Search available: {service.is_available()}")
    
    if service.is_available():
        # Test web search
        print("Testing web search...")
        results = await service.search_web("Python programming", count=3)
        print(f"Web search results: {len(results)}")
        for i, result in enumerate(results[:2], 1):
            print(f"  {i}. {result.get('title', 'No title')}")
        
        # Test news search
        print("Testing news search...")
        news_results = await service.search_news("artificial intelligence", count=2)
        print(f"News search results: {len(news_results)}")
        for i, result in enumerate(news_results[:2], 1):
            print(f"  {i}. {result.get('title', 'No title')}")
    else:
        print("Brave Search not available (no API key configured)")


async def test_unified_search():
    """Test unified SearchService."""
    print("\n=== Testing Unified Search Service ===")
    
    service = SearchService()
    
    # Get provider status
    status = await service.get_provider_status()
    print("Provider status:")
    for provider, info in status["providers"].items():
        print(f"  {provider}: available={info['available']}, healthy={info['healthy']}")
    print(f"Recommended provider: {status['recommended']}")
    
    # Test web search with auto provider selection
    print("\nTesting unified web search...")
    results = await service.search_web("machine learning", count=3)
    print(f"Unified web search results: {len(results)}")
    for i, result in enumerate(results[:2], 1):
        provider = result.get('provider', 'unknown')
        print(f"  {i}. [{provider}] {result.get('title', 'No title')}")
    
    # Test news search
    print("\nTesting unified news search...")
    news_results = await service.search_news("technology news", count=2)
    print(f"Unified news search results: {len(news_results)}")
    for i, result in enumerate(news_results[:2], 1):
        provider = result.get('provider', 'unknown')
        print(f"  {i}. [{provider}] {result.get('title', 'No title')}")
    
    # Test combined search
    print("\nTesting combined search...")
    combined = await service.search_combined("artificial intelligence", web_count=2, news_count=2)
    print(f"Combined search - Web: {len(combined['web'])}, News: {len(combined['news'])}")


async def test_health_checks():
    """Test health check functionality."""
    print("\n=== Testing Health Checks ===")
    
    # Test individual services
    serpapi = SerpAPIService()
    brave = BraveSearchService()
    
    if serpapi.is_available():
        health = await serpapi.health_check()
        print(f"SerpAPI health: {health['status']} - {health['message']}")
    
    if brave.is_available():
        health = await brave.health_check()
        print(f"Brave Search health: {health['status']} - {health['message']}")


async def main():
    """Run all tests."""
    print("Starting search services tests...")
    print("Note: Tests will show limited results if API keys are not configured")
    
    try:
        await test_serpapi()
        await test_brave_search()
        await test_unified_search()
        await test_health_checks()
        
        print("\n=== All tests completed ===")
        
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())