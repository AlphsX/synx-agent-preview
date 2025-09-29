#!/usr/bin/env python3
"""
External API Validation Script
Task 17: Optimize and finalize system integration

This script validates all external API integrations with real API keys:
1. Groq AI API
2. SerpAPI (web search)
3. Brave Search API (fallback)
4. Binance API (cryptocurrency data)
"""

import asyncio
import aiohttp
import json
import os
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExternalAPIValidator:
    def __init__(self):
        self.results = {}
        self.session = None
        
        # API keys from environment
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        self.serp_api_key = os.getenv('SERP_API_KEY')
        self.brave_api_key = os.getenv('BRAVE_SEARCH_API_KEY')
        self.binance_api_key = os.getenv('BINANCE_API_KEY')
        self.binance_secret = os.getenv('BINANCE_SECRET_KEY')

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def log_result(self, api_name: str, success: bool, details: str = "", data: Any = None):
        """Log API validation result"""
        status = "✅ WORKING" if success else "❌ FAILED"
        logger.info(f"{status} - {api_name}: {details}")
        
        self.results[api_name] = {
            "success": success,
            "details": details,
            "data": data,
            "configured": True
        }

    async def validate_groq_api(self) -> bool:
        """Validate Groq AI API"""
        if not self.groq_api_key:
            self.log_result("Groq AI API", False, "API key not configured")
            return False

        try:
            # Test Groq API directly
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messages": [
                    {"role": "user", "content": "Hello, this is a test. Please respond with 'API test successful'."}
                ],
                "model": "llama-3.1-8b-instant",
                "max_tokens": 50,
                "temperature": 0.1
            }
            
            async with self.session.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    choices = data.get("choices", [])
                    if choices and len(choices) > 0:
                        content = choices[0].get("message", {}).get("content", "")
                        self.log_result("Groq AI API", True, f"Response received: {content[:50]}...", {"model": "llama-3.1-8b-instant"})
                        return True
                    else:
                        self.log_result("Groq AI API", False, "No choices in API response")
                        return False
                else:
                    error_text = await response.text()
                    self.log_result("Groq AI API", False, f"HTTP {response.status}: {error_text[:100]}")
                    return False
                    
        except Exception as e:
            self.log_result("Groq AI API", False, f"Connection error: {e}")
            return False

    async def validate_serpapi(self) -> bool:
        """Validate SerpAPI"""
        if not self.serp_api_key:
            self.log_result("SerpAPI", False, "API key not configured")
            return False

        try:
            params = {
                "engine": "google",
                "q": "artificial intelligence news",
                "api_key": self.serp_api_key,
                "num": 3
            }
            
            async with self.session.get(
                "https://serpapi.com/search",
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    organic_results = data.get("organic_results", [])
                    if organic_results:
                        self.log_result("SerpAPI", True, f"Retrieved {len(organic_results)} search results", {"results_count": len(organic_results)})
                        return True
                    else:
                        self.log_result("SerpAPI", False, "No search results returned")
                        return False
                else:
                    error_text = await response.text()
                    self.log_result("SerpAPI", False, f"HTTP {response.status}: {error_text[:100]}")
                    return False
                    
        except Exception as e:
            self.log_result("SerpAPI", False, f"Connection error: {e}")
            return False

    async def validate_brave_search(self) -> bool:
        """Validate Brave Search API"""
        if not self.brave_api_key:
            self.log_result("Brave Search API", False, "API key not configured")
            return False

        try:
            headers = {
                "X-Subscription-Token": self.brave_api_key,
                "Accept": "application/json"
            }
            
            params = {
                "q": "machine learning",
                "count": 3
            }
            
            async with self.session.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers=headers,
                params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    web_results = data.get("web", {}).get("results", [])
                    if web_results:
                        self.log_result("Brave Search API", True, f"Retrieved {len(web_results)} search results", {"results_count": len(web_results)})
                        return True
                    else:
                        self.log_result("Brave Search API", False, "No search results returned")
                        return False
                else:
                    error_text = await response.text()
                    self.log_result("Brave Search API", False, f"HTTP {response.status}: {error_text[:100]}")
                    return False
                    
        except Exception as e:
            self.log_result("Brave Search API", False, f"Connection error: {e}")
            return False

    async def validate_binance_api(self) -> bool:
        """Validate Binance API"""
        if not self.binance_api_key:
            self.log_result("Binance API", False, "API key not configured")
            return False

        try:
            # Test public endpoint (no signature required)
            async with self.session.get(
                "https://api.binance.com/api/v3/ticker/price",
                params={"symbol": "BTCUSDT"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    price = data.get("price")
                    if price:
                        self.log_result("Binance API", True, f"BTC price: ${float(price):,.2f}", {"btc_price": price})
                        return True
                    else:
                        self.log_result("Binance API", False, "No price data returned")
                        return False
                else:
                    error_text = await response.text()
                    self.log_result("Binance API", False, f"HTTP {response.status}: {error_text[:100]}")
                    return False
                    
        except Exception as e:
            self.log_result("Binance API", False, f"Connection error: {e}")
            return False

    async def validate_backend_integration(self) -> bool:
        """Validate that backend can use the external APIs"""
        try:
            # Test backend's AI chat with real API
            chat_payload = {
                "content": "Hello, please respond briefly to confirm the API is working.",
                "role": "user",
                "model_id": "llama-3.1-8b-instant"
            }
            
            async with self.session.post(
                "http://localhost:8000/api/chat/conversations/api-validation/chat",
                json=chat_payload
            ) as response:
                if response.status == 200:
                    # Read streaming response
                    content_received = False
                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]
                            if data_str and data_str != '{"type": "done"}':
                                content_received = True
                                break
                    
                    self.log_result("Backend AI Integration", content_received, 
                                  "Backend successfully using AI API" if content_received else "No AI response received")
                    return content_received
                else:
                    self.log_result("Backend AI Integration", False, f"HTTP {response.status}")
                    return False
                    
        except Exception as e:
            self.log_result("Backend AI Integration", False, f"Connection error: {e}")
            return False

    async def run_validation(self) -> Dict[str, Any]:
        """Run all external API validations"""
        logger.info("🔍 Starting external API validation...")
        
        # Check API key configuration
        api_keys_configured = {
            "GROQ_API_KEY": bool(self.groq_api_key),
            "SERP_API_KEY": bool(self.serp_api_key),
            "BRAVE_SEARCH_API_KEY": bool(self.brave_api_key),
            "BINANCE_API_KEY": bool(self.binance_api_key),
            "BINANCE_SECRET_KEY": bool(self.binance_secret)
        }
        
        logger.info(f"API Keys configured: {sum(api_keys_configured.values())}/5")
        
        # Run validations
        await self.validate_groq_api()
        await self.validate_serpapi()
        await self.validate_brave_search()
        await self.validate_binance_api()
        await self.validate_backend_integration()
        
        return self.generate_report(api_keys_configured)

    def generate_report(self, api_keys_configured: Dict[str, bool]) -> Dict[str, Any]:
        """Generate validation report"""
        working_apis = sum(1 for result in self.results.values() if result["success"])
        total_apis = len(self.results)
        
        return {
            "summary": {
                "total_apis_tested": total_apis,
                "working_apis": working_apis,
                "failed_apis": total_apis - working_apis,
                "success_rate": f"{(working_apis / total_apis * 100):.1f}%" if total_apis > 0 else "0%",
                "api_keys_configured": sum(api_keys_configured.values()),
                "total_api_keys": len(api_keys_configured)
            },
            "api_key_status": api_keys_configured,
            "validation_results": self.results,
            "recommendations": self.generate_recommendations()
        }

    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        # Check each API
        if not self.results.get("Groq AI API", {}).get("success"):
            if self.groq_api_key:
                recommendations.append("❗ Groq API key configured but not working - check key validity")
            else:
                recommendations.append("⚠️ Groq API key not configured - AI chat will use demo responses")
        
        if not self.results.get("SerpAPI", {}).get("success"):
            if self.serp_api_key:
                recommendations.append("❗ SerpAPI key configured but not working - check key validity and quota")
            else:
                recommendations.append("⚠️ SerpAPI key not configured - web search will use fallback or demo responses")
        
        if not self.results.get("Brave Search API", {}).get("success"):
            if self.brave_api_key:
                recommendations.append("❗ Brave Search API key configured but not working - check key validity")
            else:
                recommendations.append("⚠️ Brave Search API key not configured - search fallback unavailable")
        
        if not self.results.get("Binance API", {}).get("success"):
            if self.binance_api_key:
                recommendations.append("❗ Binance API key configured but not working - check key validity")
            else:
                recommendations.append("⚠️ Binance API key not configured - crypto data will use demo responses")
        
        # Positive feedback
        working_apis = sum(1 for result in self.results.values() if result["success"])
        if working_apis >= 3:
            recommendations.append("✅ Most external APIs are working correctly")
        
        if self.results.get("Backend AI Integration", {}).get("success"):
            recommendations.append("✅ Backend integration with external APIs is functional")
        
        return recommendations

    def print_report(self, report: Dict[str, Any]):
        """Print formatted validation report"""
        print("\n" + "="*80)
        print("🔍 EXTERNAL API VALIDATION REPORT")
        print("="*80)
        
        summary = report["summary"]
        print(f"📊 SUMMARY:")
        print(f"   APIs Tested: {summary['total_apis_tested']}")
        print(f"   Working: {summary['working_apis']}")
        print(f"   Failed: {summary['failed_apis']}")
        print(f"   Success Rate: {summary['success_rate']}")
        print(f"   API Keys Configured: {summary['api_keys_configured']}/{summary['total_api_keys']}")
        
        print(f"\n🔑 API KEY STATUS:")
        for key, configured in report["api_key_status"].items():
            status = "✅ Configured" if configured else "❌ Missing"
            print(f"   {key}: {status}")
        
        print(f"\n🧪 VALIDATION RESULTS:")
        for api_name, result in report["validation_results"].items():
            status = "✅ WORKING" if result["success"] else "❌ FAILED"
            print(f"   {status} {api_name}: {result['details']}")
        
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in report["recommendations"]:
            print(f"   {rec}")
        
        print("\n" + "="*80)


async def main():
    """Main validation execution"""
    try:
        async with ExternalAPIValidator() as validator:
            report = await validator.run_validation()
            validator.print_report(report)
            
            # Save report to file
            with open("external_api_validation_report.json", "w") as f:
                json.dump(report, f, indent=2)
            
            logger.info("External API validation report saved to external_api_validation_report.json")
            
    except KeyboardInterrupt:
        logger.info("Validation interrupted by user")
    except Exception as e:
        logger.error(f"Validation failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())