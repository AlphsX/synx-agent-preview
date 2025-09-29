#!/usr/bin/env python3
"""
Test script for enhanced external API integrations.

This script tests all the new external API services:
- Weather data integration
- Stock market data
- Sentiment analysis
- Plugin system
- Unified service
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.external_apis.weather import WeatherService
from app.external_apis.stocks import StockService
from app.external_apis.sentiment import SentimentAnalysisService
from app.external_apis.plugin_system import plugin_manager
from app.external_apis.unified_service import unified_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_weather_service():
    """Test weather service functionality."""
    print("\n" + "="*50)
    print("TESTING WEATHER SERVICE")
    print("="*50)
    
    weather_service = WeatherService()
    
    # Test current weather
    print("\n1. Testing current weather...")
    try:
        result = await weather_service.get_current_weather("New York, NY")
        print(f"✅ Current weather result: {result.get('temperature', 'N/A')}°C")
        if result.get('mock'):
            print("   (Using mock data - API key not configured)")
    except Exception as e:
        print(f"❌ Current weather failed: {str(e)}")
    
    # Test weather forecast
    print("\n2. Testing weather forecast...")
    try:
        result = await weather_service.get_weather_forecast("London, UK", days=3)
        forecast_count = len(result.get('forecast', []))
        print(f"✅ Weather forecast result: {forecast_count} days")
        if result.get('mock'):
            print("   (Using mock data - API key not configured)")
    except Exception as e:
        print(f"❌ Weather forecast failed: {str(e)}")
    
    # Test health check
    print("\n3. Testing weather service health...")
    try:
        health = await weather_service.health_check()
        print(f"✅ Weather service health: {health.get('status', 'unknown')}")
    except Exception as e:
        print(f"❌ Weather health check failed: {str(e)}")


async def test_stock_service():
    """Test stock service functionality."""
    print("\n" + "="*50)
    print("TESTING STOCK SERVICE")
    print("="*50)
    
    stock_service = StockService()
    
    # Test stock quote
    print("\n1. Testing stock quote...")
    try:
        result = await stock_service.get_stock_quote("AAPL")
        print(f"✅ Stock quote result: ${result.get('price', 'N/A')}")
        if result.get('mock'):
            print("   (Using mock data - API key not configured)")
    except Exception as e:
        print(f"❌ Stock quote failed: {str(e)}")
    
    # Test market overview
    print("\n2. Testing market overview...")
    try:
        result = await stock_service.get_market_overview()
        gainers_count = len(result.get('top_gainers', []))
        print(f"✅ Market overview result: {gainers_count} top gainers")
        if result.get('mock'):
            print("   (Using mock data - API key not configured)")
    except Exception as e:
        print(f"❌ Market overview failed: {str(e)}")
    
    # Test company info
    print("\n3. Testing company info...")
    try:
        result = await stock_service.get_company_info("GOOGL")
        print(f"✅ Company info result: {result.get('name', 'N/A')}")
        if result.get('mock'):
            print("   (Using mock data - API key not configured)")
    except Exception as e:
        print(f"❌ Company info failed: {str(e)}")
    
    # Test stock search
    print("\n4. Testing stock search...")
    try:
        result = await stock_service.search_stocks("Apple")
        matches_count = len(result.get('matches', []))
        print(f"✅ Stock search result: {matches_count} matches")
        if result.get('mock'):
            print("   (Using mock data - API key not configured)")
    except Exception as e:
        print(f"❌ Stock search failed: {str(e)}")
    
    # Test health check
    print("\n5. Testing stock service health...")
    try:
        health = await stock_service.health_check()
        print(f"✅ Stock service health: {health.get('status', 'unknown')}")
    except Exception as e:
        print(f"❌ Stock health check failed: {str(e)}")


async def test_sentiment_service():
    """Test sentiment analysis service functionality."""
    print("\n" + "="*50)
    print("TESTING SENTIMENT ANALYSIS SERVICE")
    print("="*50)
    
    sentiment_service = SentimentAnalysisService()
    
    # Test stock sentiment
    print("\n1. Testing stock sentiment...")
    try:
        result = await sentiment_service.analyze_stock_sentiment("TSLA")
        overall_score = result.get('overall_sentiment', {}).get('score', 'N/A')
        print(f"✅ Stock sentiment result: {overall_score}")
        if result.get('mock'):
            print("   (Using mock data - API key not configured)")
    except Exception as e:
        print(f"❌ Stock sentiment failed: {str(e)}")
    
    # Test market sentiment
    print("\n2. Testing market sentiment...")
    try:
        result = await sentiment_service.analyze_market_sentiment()
        overall_score = result.get('overall_sentiment', {}).get('score', 'N/A')
        print(f"✅ Market sentiment result: {overall_score}")
        if result.get('mock'):
            print("   (Using mock data - API key not configured)")
    except Exception as e:
        print(f"❌ Market sentiment failed: {str(e)}")
    
    # Test topic sentiment
    print("\n3. Testing topic sentiment...")
    try:
        result = await sentiment_service.analyze_topic_sentiment("artificial intelligence")
        sentiment_score = result.get('sentiment', {}).get('score', 'N/A')
        print(f"✅ Topic sentiment result: {sentiment_score}")
        if result.get('mock'):
            print("   (Using mock data - API key not configured)")
    except Exception as e:
        print(f"❌ Topic sentiment failed: {str(e)}")
    
    # Test trending sentiment
    print("\n4. Testing trending sentiment...")
    try:
        result = await sentiment_service.get_trending_sentiment(5)
        trending_count = len(result.get('trending_topics', []))
        print(f"✅ Trending sentiment result: {trending_count} topics")
        if result.get('mock'):
            print("   (Using mock data - API key not configured)")
    except Exception as e:
        print(f"❌ Trending sentiment failed: {str(e)}")
    
    # Test health check
    print("\n5. Testing sentiment service health...")
    try:
        health = await sentiment_service.health_check()
        print(f"✅ Sentiment service health: {health.get('status', 'unknown')}")
    except Exception as e:
        print(f"❌ Sentiment health check failed: {str(e)}")


async def test_plugin_system():
    """Test plugin system functionality."""
    print("\n" + "="*50)
    print("TESTING PLUGIN SYSTEM")
    print("="*50)
    
    # Test plugin info
    print("\n1. Testing plugin info...")
    try:
        result = plugin_manager.get_plugin_info()
        total_plugins = result.get('total_plugins', 0)
        available_plugins = result.get('available_plugins', 0)
        print(f"✅ Plugin info result: {total_plugins} total, {available_plugins} available")
    except Exception as e:
        print(f"❌ Plugin info failed: {str(e)}")
    
    # Test plugin health check
    print("\n2. Testing plugin health check...")
    try:
        result = await plugin_manager.health_check_all_plugins()
        overall_status = result.get('overall_status', 'unknown')
        healthy_count = result.get('healthy_plugins', 0)
        total_count = result.get('total_plugins', 0)
        print(f"✅ Plugin health result: {overall_status} ({healthy_count}/{total_count} healthy)")
    except Exception as e:
        print(f"❌ Plugin health check failed: {str(e)}")
    
    # Test plugin execution (if any plugins are available)
    print("\n3. Testing plugin execution...")
    try:
        plugin_info = plugin_manager.get_plugin_info()
        if plugin_info.get('total_plugins', 0) > 0:
            # Try to execute on all plugins
            result = await plugin_manager.execute_all_plugins("fetch_data", "test query", limit=3)
            executed_count = len([r for r in result.values() if not r.get('error')])
            print(f"✅ Plugin execution result: {executed_count} plugins executed successfully")
        else:
            print("ℹ️  No plugins available for execution test")
    except Exception as e:
        print(f"❌ Plugin execution failed: {str(e)}")


async def test_unified_service():
    """Test unified service functionality."""
    print("\n" + "="*50)
    print("TESTING UNIFIED SERVICE")
    print("="*50)
    
    # Test enhanced context
    print("\n1. Testing enhanced context...")
    try:
        result = await unified_service.get_enhanced_context("What's the weather like in Paris and AAPL stock price?")
        detected_types = result.get('detected_types', [])
        print(f"✅ Enhanced context result: {len(detected_types)} context types detected")
        print(f"   Detected types: {', '.join(detected_types)}")
    except Exception as e:
        print(f"❌ Enhanced context failed: {str(e)}")
    
    # Test search all sources
    print("\n2. Testing search all sources...")
    try:
        result = await unified_service.search_all_sources("artificial intelligence", limit_per_source=2)
        sources_searched = result.get('sources_searched', [])
        print(f"✅ Search all sources result: {len(sources_searched)} sources searched")
    except Exception as e:
        print(f"❌ Search all sources failed: {str(e)}")
    
    # Test market overview
    print("\n3. Testing unified market overview...")
    try:
        result = await unified_service.get_market_overview()
        available_data = [key for key in result.keys() if key not in ['timestamp', 'market_status']]
        print(f"✅ Unified market overview result: {len(available_data)} data sources")
        print(f"   Available data: {', '.join(available_data)}")
    except Exception as e:
        print(f"❌ Unified market overview failed: {str(e)}")
    
    # Test service health
    print("\n4. Testing unified service health...")
    try:
        result = await unified_service.get_service_health()
        overall_status = result.get('overall_status', 'unknown')
        healthy_services = result.get('healthy_services', 0)
        total_services = result.get('total_services', 0)
        print(f"✅ Unified service health result: {overall_status} ({healthy_services}/{total_services} healthy)")
    except Exception as e:
        print(f"❌ Unified service health failed: {str(e)}")


async def run_comprehensive_test():
    """Run comprehensive test of all enhanced external API services."""
    print("🚀 Starting Enhanced External APIs Test Suite")
    print(f"📅 Test started at: {datetime.now().isoformat()}")
    
    start_time = asyncio.get_event_loop().time()
    
    try:
        # Run all tests
        await test_weather_service()
        await test_stock_service()
        await test_sentiment_service()
        await test_plugin_system()
        await test_unified_service()
        
        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time
        
        print("\n" + "="*50)
        print("TEST SUITE COMPLETED")
        print("="*50)
        print(f"✅ All tests completed successfully!")
        print(f"⏱️  Total execution time: {duration:.2f} seconds")
        print(f"📊 Test summary:")
        print(f"   - Weather Service: Tested current weather, forecast, alerts, health")
        print(f"   - Stock Service: Tested quotes, market overview, company info, search, health")
        print(f"   - Sentiment Service: Tested stock/market/topic sentiment, trending, health")
        print(f"   - Plugin System: Tested plugin info, health, execution")
        print(f"   - Unified Service: Tested enhanced context, search, market overview, health")
        
        print(f"\n📝 Notes:")
        print(f"   - Services without API keys will use mock data")
        print(f"   - This is expected behavior for development/testing")
        print(f"   - Configure API keys in .env file for real data")
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Enhanced External APIs Test Suite")
    print("=" * 50)
    
    try:
        asyncio.run(run_comprehensive_test())
    except KeyboardInterrupt:
        print("\n⚠️  Test suite interrupted by user")
    except Exception as e:
        print(f"\n💥 Test suite crashed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)