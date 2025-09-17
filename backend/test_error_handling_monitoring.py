#!/usr/bin/env python3
"""
Test script for comprehensive error handling and monitoring system.

This script tests:
- Error handling and retry logic
- Health check endpoints
- Structured logging
- Graceful degradation
- Performance monitoring
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any
import logging

# Configure logging to see structured logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"


async def test_health_endpoints():
    """Test all health check endpoints."""
    print("\n" + "="*50)
    print("TESTING HEALTH CHECK ENDPOINTS")
    print("="*50)
    
    health_endpoints = [
        "/api/health",
        "/api/health/services/ai_groq",
        "/api/health/ai",
        "/api/health/search",
        "/api/health/database",
        "/api/health/errors",
        "/api/health/status",
        "/api/health/readiness",
        "/api/health/liveness"
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint in health_endpoints:
            try:
                print(f"\nTesting: {endpoint}")
                async with session.get(f"{BASE_URL}{endpoint}") as response:
                    status = response.status
                    data = await response.json()
                    
                    print(f"  Status: {status}")
                    if status == 200:
                        print(f"  Response: {json.dumps(data, indent=2)[:200]}...")
                    else:
                        print(f"  Error: {data}")
                        
            except Exception as e:
                print(f"  Failed: {str(e)}")


async def test_search_with_error_handling():
    """Test search services with error handling."""
    print("\n" + "="*50)
    print("TESTING SEARCH WITH ERROR HANDLING")
    print("="*50)
    
    search_queries = [
        "artificial intelligence",
        "cryptocurrency news",
        "python programming"
    ]
    
    async with aiohttp.ClientSession() as session:
        for query in search_queries:
            try:
                print(f"\nTesting search: {query}")
                
                # Test web search
                payload = {
                    "query": query,
                    "search_type": "web",
                    "count": 5
                }
                
                async with session.post(
                    f"{BASE_URL}/api/external/search",
                    json=payload
                ) as response:
                    status = response.status
                    data = await response.json()
                    
                    print(f"  Web Search Status: {status}")
                    if status == 200:
                        results = data.get("results", [])
                        print(f"  Results: {len(results)} found")
                        if results:
                            print(f"  Provider: {results[0].get('provider', 'unknown')}")
                    else:
                        print(f"  Error: {data}")
                
                # Test news search
                payload["search_type"] = "news"
                
                async with session.post(
                    f"{BASE_URL}/api/external/search",
                    json=payload
                ) as response:
                    status = response.status
                    data = await response.json()
                    
                    print(f"  News Search Status: {status}")
                    if status == 200:
                        results = data.get("results", [])
                        print(f"  Results: {len(results)} found")
                        if results:
                            print(f"  Provider: {results[0].get('provider', 'unknown')}")
                    else:
                        print(f"  Error: {data}")
                        
            except Exception as e:
                print(f"  Failed: {str(e)}")


async def test_ai_services_with_retry():
    """Test AI services with retry logic."""
    print("\n" + "="*50)
    print("TESTING AI SERVICES WITH RETRY LOGIC")
    print("="*50)
    
    # First, get available models
    async with aiohttp.ClientSession() as session:
        try:
            print("Getting available AI models...")
            async with session.get(f"{BASE_URL}/api/ai/models") as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get("models", [])
                    print(f"Available models: {len(models)}")
                    
                    if models:
                        # Test with first available model
                        model_id = models[0]["id"]
                        print(f"Testing with model: {model_id}")
                        
                        # Test chat completion
                        chat_payload = {
                            "messages": [
                                {"role": "user", "content": "Hello, this is a test message"}
                            ],
                            "model_id": model_id,
                            "stream": False
                        }
                        
                        async with session.post(
                            f"{BASE_URL}/api/chat/completions",
                            json=chat_payload
                        ) as chat_response:
                            status = chat_response.status
                            print(f"Chat completion status: {status}")
                            
                            if status == 200:
                                chat_data = await chat_response.json()
                                print("Chat completion successful")
                            else:
                                error_data = await chat_response.json()
                                print(f"Chat error: {error_data}")
                    else:
                        print("No models available for testing")
                else:
                    print(f"Failed to get models: {response.status}")
                    
        except Exception as e:
            print(f"AI service test failed: {str(e)}")


async def test_crypto_service():
    """Test cryptocurrency service with error handling."""
    print("\n" + "="*50)
    print("TESTING CRYPTO SERVICE")
    print("="*50)
    
    async with aiohttp.ClientSession() as session:
        try:
            print("Testing crypto market data...")
            async with session.get(f"{BASE_URL}/api/external/crypto/market") as response:
                status = response.status
                data = await response.json()
                
                print(f"Crypto market status: {status}")
                if status == 200:
                    market_data = data.get("data", {})
                    print(f"Market data symbols: {list(market_data.keys())}")
                else:
                    print(f"Crypto error: {data}")
                    
        except Exception as e:
            print(f"Crypto service test failed: {str(e)}")


async def test_error_metrics():
    """Test error metrics collection."""
    print("\n" + "="*50)
    print("TESTING ERROR METRICS")
    print("="*50)
    
    async with aiohttp.ClientSession() as session:
        try:
            # Get current error metrics
            print("Getting error metrics...")
            async with session.get(f"{BASE_URL}/api/health/errors") as response:
                if response.status == 200:
                    data = await response.json()
                    error_summary = data.get("data", {}).get("error_summary", {})
                    
                    print(f"Total errors (24h): {error_summary.get('total_errors', 0)}")
                    print(f"Errors by service: {error_summary.get('errors_by_service', {})}")
                    print(f"Errors by severity: {error_summary.get('errors_by_severity', {})}")
                else:
                    print(f"Failed to get error metrics: {response.status}")
                    
            # Test error metrics reset
            print("\nTesting error metrics reset...")
            async with session.post(f"{BASE_URL}/api/health/errors/reset") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"Reset successful: {data.get('message', 'Unknown')}")
                else:
                    print(f"Reset failed: {response.status}")
                    
        except Exception as e:
            print(f"Error metrics test failed: {str(e)}")


async def test_performance_monitoring():
    """Test performance monitoring."""
    print("\n" + "="*50)
    print("TESTING PERFORMANCE MONITORING")
    print("="*50)
    
    # Simulate multiple concurrent requests to test performance
    async def make_request(session, endpoint, payload=None):
        start_time = time.time()
        try:
            if payload:
                async with session.post(endpoint, json=payload) as response:
                    await response.json()
            else:
                async with session.get(endpoint) as response:
                    await response.json()
            
            duration = time.time() - start_time
            return duration, True
        except Exception as e:
            duration = time.time() - start_time
            return duration, False
    
    async with aiohttp.ClientSession() as session:
        print("Running concurrent requests to test performance...")
        
        # Create multiple concurrent requests
        tasks = []
        for i in range(10):
            tasks.append(make_request(session, f"{BASE_URL}/api/health/status"))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful_requests = sum(1 for duration, success in results if success)
        total_time = sum(duration for duration, success in results)
        avg_time = total_time / len(results)
        
        print(f"Concurrent requests: {len(tasks)}")
        print(f"Successful requests: {successful_requests}")
        print(f"Average response time: {avg_time:.3f}s")


async def main():
    """Run all tests."""
    print("COMPREHENSIVE ERROR HANDLING AND MONITORING TEST")
    print("=" * 60)
    
    try:
        # Test health endpoints
        await test_health_endpoints()
        
        # Test search services
        await test_search_with_error_handling()
        
        # Test AI services
        await test_ai_services_with_retry()
        
        # Test crypto service
        await test_crypto_service()
        
        # Test error metrics
        await test_error_metrics()
        
        # Test performance monitoring
        await test_performance_monitoring()
        
        print("\n" + "="*60)
        print("ALL TESTS COMPLETED")
        print("="*60)
        
    except Exception as e:
        print(f"Test suite failed: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())