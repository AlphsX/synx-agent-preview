"""
Comprehensive health check system for all services.

This module provides health checks for:
- AI model providers (Groq, OpenAI, Anthropic)
- Search services (SerpAPI, Brave Search)
- Cryptocurrency services (Binance)
- Database services (PostgreSQL, Redis)
- Vector database services
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import aiohttp
import time

from ..config import settings
from .error_handling import error_metrics, ServiceType, ErrorCode, ErrorSeverity

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheck:
    """Individual health check result."""
    
    def __init__(
        self,
        service_name: str,
        status: HealthStatus,
        message: str = "",
        response_time: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
        last_checked: Optional[datetime] = None
    ):
        self.service_name = service_name
        self.status = status
        self.message = message
        self.response_time = response_time
        self.details = details or {}
        self.last_checked = last_checked or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        return {
            "service": self.service_name,
            "status": self.status.value,
            "message": self.message,
            "response_time_ms": round(self.response_time * 1000, 2) if self.response_time else None,
            "last_checked": self.last_checked.isoformat(),
            "details": self.details
        }


class HealthCheckService:
    """Centralized health check service."""
    
    def __init__(self):
        self.health_cache: Dict[str, HealthCheck] = {}
        self.cache_ttl = timedelta(minutes=5)  # Cache health checks for 5 minutes
    
    async def check_all_services(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Check health of all services."""
        checks = {}
        
        # AI Services
        ai_checks = await self._check_ai_services(force_refresh)
        checks.update(ai_checks)
        
        # Search Services
        search_checks = await self._check_search_services(force_refresh)
        checks.update(search_checks)
        
        # Crypto Services
        crypto_checks = await self._check_crypto_services(force_refresh)
        checks.update(crypto_checks)
        
        # Database Services
        db_checks = await self._check_database_services(force_refresh)
        checks.update(db_checks)
        
        # Vector Database
        vector_checks = await self._check_vector_services(force_refresh)
        checks.update(vector_checks)
        
        # Calculate overall health
        overall_status = self._calculate_overall_health(checks)
        
        return {
            "overall_status": overall_status.value,
            "timestamp": datetime.now().isoformat(),
            "services": {name: check.to_dict() for name, check in checks.items()},
            "summary": self._generate_health_summary(checks)
        }
    
    async def check_service(self, service_name: str, force_refresh: bool = False) -> HealthCheck:
        """Check health of a specific service."""
        # Check cache first
        if not force_refresh and service_name in self.health_cache:
            cached_check = self.health_cache[service_name]
            if datetime.now() - cached_check.last_checked < self.cache_ttl:
                return cached_check
        
        # Perform health check based on service type
        if service_name.startswith("ai_"):
            check = await self._check_ai_service(service_name)
        elif service_name.startswith("search_"):
            check = await self._check_search_service(service_name)
        elif service_name.startswith("crypto_"):
            check = await self._check_crypto_service(service_name)
        elif service_name.startswith("database_"):
            check = await self._check_database_service(service_name)
        elif service_name.startswith("vector_"):
            check = await self._check_vector_service(service_name)
        else:
            check = HealthCheck(
                service_name=service_name,
                status=HealthStatus.UNKNOWN,
                message="Unknown service type"
            )
        
        # Cache the result
        self.health_cache[service_name] = check
        return check
    
    async def _check_ai_services(self, force_refresh: bool = False) -> Dict[str, HealthCheck]:
        """Check health of AI services."""
        checks = {}
        
        # Check Groq
        if settings.GROQ_API_KEY:
            checks["ai_groq"] = await self._check_groq_health()
        else:
            checks["ai_groq"] = HealthCheck(
                service_name="ai_groq",
                status=HealthStatus.UNHEALTHY,
                message="API key not configured"
            )
        
        # Check OpenAI
        if settings.OPENAI_API_KEY:
            checks["ai_openai"] = await self._check_openai_health()
        else:
            checks["ai_openai"] = HealthCheck(
                service_name="ai_openai",
                status=HealthStatus.UNHEALTHY,
                message="API key not configured"
            )
        
        # Check Anthropic
        if settings.ANTHROPIC_API_KEY:
            checks["ai_anthropic"] = await self._check_anthropic_health()
        else:
            checks["ai_anthropic"] = HealthCheck(
                service_name="ai_anthropic",
                status=HealthStatus.UNHEALTHY,
                message="API key not configured"
            )
        
        return checks
    
    async def _check_search_services(self, force_refresh: bool = False) -> Dict[str, HealthCheck]:
        """Check health of search services."""
        checks = {}
        
        # Check SerpAPI
        if settings.SERP_API_KEY:
            checks["search_serpapi"] = await self._check_serpapi_health()
        else:
            checks["search_serpapi"] = HealthCheck(
                service_name="search_serpapi",
                status=HealthStatus.UNHEALTHY,
                message="API key not configured"
            )
        
        # Check Brave Search
        if settings.BRAVE_SEARCH_API_KEY:
            checks["search_brave"] = await self._check_brave_search_health()
        else:
            checks["search_brave"] = HealthCheck(
                service_name="search_brave",
                status=HealthStatus.UNHEALTHY,
                message="API key not configured"
            )
        
        return checks
    
    async def _check_crypto_services(self, force_refresh: bool = False) -> Dict[str, HealthCheck]:
        """Check health of crypto services."""
        checks = {}
        
        # Binance public API doesn't require API key for basic health check
        checks["crypto_binance"] = await self._check_binance_health()
        
        return checks
    
    async def _check_database_services(self, force_refresh: bool = False) -> Dict[str, HealthCheck]:
        """Check health of database services."""
        checks = {}
        
        # Check PostgreSQL
        checks["database_postgresql"] = await self._check_postgresql_health()
        
        # Check Redis
        checks["database_redis"] = await self._check_redis_health()
        
        return checks
    
    async def _check_vector_services(self, force_refresh: bool = False) -> Dict[str, HealthCheck]:
        """Check health of vector database services."""
        checks = {}
        
        # Check vector database (PostgreSQL with pgvector)
        checks["vector_database"] = await self._check_vector_database_health()
        
        return checks
    
    async def _check_groq_health(self) -> HealthCheck:
        """Check Groq API health."""
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                
                # Make a simple API call to check availability
                async with session.get(
                    "https://api.groq.com/openai/v1/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        model_count = len(data.get("data", []))
                        
                        return HealthCheck(
                            service_name="ai_groq",
                            status=HealthStatus.HEALTHY,
                            message=f"Service operational with {model_count} models available",
                            response_time=response_time,
                            details={"model_count": model_count}
                        )
                    else:
                        return HealthCheck(
                            service_name="ai_groq",
                            status=HealthStatus.UNHEALTHY,
                            message=f"API returned status {response.status}",
                            response_time=response_time
                        )
        
        except asyncio.TimeoutError:
            return HealthCheck(
                service_name="ai_groq",
                status=HealthStatus.UNHEALTHY,
                message="Request timeout"
            )
        except Exception as e:
            return HealthCheck(
                service_name="ai_groq",
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}"
            )
    
    async def _check_openai_health(self) -> HealthCheck:
        """Check OpenAI API health."""
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                }
                
                async with session.get(
                    "https://api.openai.com/v1/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        model_count = len(data.get("data", []))
                        
                        return HealthCheck(
                            service_name="ai_openai",
                            status=HealthStatus.HEALTHY,
                            message=f"Service operational with {model_count} models available",
                            response_time=response_time,
                            details={"model_count": model_count}
                        )
                    else:
                        return HealthCheck(
                            service_name="ai_openai",
                            status=HealthStatus.UNHEALTHY,
                            message=f"API returned status {response.status}",
                            response_time=response_time
                        )
        
        except Exception as e:
            return HealthCheck(
                service_name="ai_openai",
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}"
            )
    
    async def _check_anthropic_health(self) -> HealthCheck:
        """Check Anthropic API health."""
        try:
            start_time = time.time()
            
            # Anthropic doesn't have a models endpoint, so we'll make a minimal completion request
            async with aiohttp.ClientSession() as session:
                headers = {
                    "x-api-key": settings.ANTHROPIC_API_KEY,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                }
                
                payload = {
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "Hi"}]
                }
                
                async with session.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        return HealthCheck(
                            service_name="ai_anthropic",
                            status=HealthStatus.HEALTHY,
                            message="Service operational",
                            response_time=response_time
                        )
                    else:
                        return HealthCheck(
                            service_name="ai_anthropic",
                            status=HealthStatus.UNHEALTHY,
                            message=f"API returned status {response.status}",
                            response_time=response_time
                        )
        
        except Exception as e:
            return HealthCheck(
                service_name="ai_anthropic",
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}"
            )
    
    async def _check_serpapi_health(self) -> HealthCheck:
        """Check SerpAPI health."""
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                params = {
                    "engine": "google",
                    "q": "test",
                    "api_key": settings.SERP_API_KEY,
                    "num": 1
                }
                
                async with session.get(
                    "https://serpapi.com/search",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        if "error" not in data:
                            return HealthCheck(
                                service_name="search_serpapi",
                                status=HealthStatus.HEALTHY,
                                message="Service operational",
                                response_time=response_time
                            )
                        else:
                            return HealthCheck(
                                service_name="search_serpapi",
                                status=HealthStatus.UNHEALTHY,
                                message=f"API error: {data['error']}",
                                response_time=response_time
                            )
                    else:
                        return HealthCheck(
                            service_name="search_serpapi",
                            status=HealthStatus.UNHEALTHY,
                            message=f"HTTP {response.status}",
                            response_time=response_time
                        )
        
        except Exception as e:
            return HealthCheck(
                service_name="search_serpapi",
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}"
            )
    
    async def _check_brave_search_health(self) -> HealthCheck:
        """Check Brave Search health."""
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip",
                    "X-Subscription-Token": settings.BRAVE_SEARCH_API_KEY
                }
                
                params = {
                    "q": "test",
                    "count": 1
                }
                
                async with session.get(
                    "https://api.search.brave.com/res/v1/web/search",
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        return HealthCheck(
                            service_name="search_brave",
                            status=HealthStatus.HEALTHY,
                            message="Service operational",
                            response_time=response_time
                        )
                    else:
                        return HealthCheck(
                            service_name="search_brave",
                            status=HealthStatus.UNHEALTHY,
                            message=f"HTTP {response.status}",
                            response_time=response_time
                        )
        
        except Exception as e:
            return HealthCheck(
                service_name="search_brave",
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}"
            )
    
    async def _check_binance_health(self) -> HealthCheck:
        """Check Binance API health."""
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.binance.com/api/v3/ping",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        return HealthCheck(
                            service_name="crypto_binance",
                            status=HealthStatus.HEALTHY,
                            message="Service operational",
                            response_time=response_time
                        )
                    else:
                        return HealthCheck(
                            service_name="crypto_binance",
                            status=HealthStatus.UNHEALTHY,
                            message=f"HTTP {response.status}",
                            response_time=response_time
                        )
        
        except Exception as e:
            return HealthCheck(
                service_name="crypto_binance",
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}"
            )
    
    async def _check_postgresql_health(self) -> HealthCheck:
        """Check PostgreSQL database health."""
        try:
            from ..database.connection import get_database
            
            start_time = time.time()
            
            # Try to get database connection and execute a simple query
            db = await get_database()
            if db:
                # Execute a simple query
                result = await db.fetch_one("SELECT 1 as test")
                response_time = time.time() - start_time
                
                if result and result["test"] == 1:
                    return HealthCheck(
                        service_name="database_postgresql",
                        status=HealthStatus.HEALTHY,
                        message="Database connection successful",
                        response_time=response_time
                    )
                else:
                    return HealthCheck(
                        service_name="database_postgresql",
                        status=HealthStatus.UNHEALTHY,
                        message="Query execution failed"
                    )
            else:
                return HealthCheck(
                    service_name="database_postgresql",
                    status=HealthStatus.UNHEALTHY,
                    message="Database connection failed"
                )
        
        except Exception as e:
            return HealthCheck(
                service_name="database_postgresql",
                status=HealthStatus.UNHEALTHY,
                message=f"Database health check failed: {str(e)}"
            )
    
    async def _check_redis_health(self) -> HealthCheck:
        """Check Redis cache health."""
        try:
            import redis.asyncio as redis
            
            start_time = time.time()
            
            # Try to connect to Redis
            redis_client = redis.from_url(settings.REDIS_URL)
            
            # Execute a simple ping
            result = await redis_client.ping()
            response_time = time.time() - start_time
            
            await redis_client.close()
            
            if result:
                return HealthCheck(
                    service_name="database_redis",
                    status=HealthStatus.HEALTHY,
                    message="Redis connection successful",
                    response_time=response_time
                )
            else:
                return HealthCheck(
                    service_name="database_redis",
                    status=HealthStatus.UNHEALTHY,
                    message="Redis ping failed"
                )
        
        except Exception as e:
            return HealthCheck(
                service_name="database_redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Redis health check failed: {str(e)}"
            )
    
    async def _check_vector_database_health(self) -> HealthCheck:
        """Check vector database health."""
        try:
            from ..vector.service import vector_service
            
            start_time = time.time()
            
            # Check if vector service is initialized and working
            if hasattr(vector_service, 'is_initialized') and vector_service.is_initialized():
                # Try a simple vector operation
                test_result = await vector_service.search("test query", top_k=1)
                response_time = time.time() - start_time
                
                return HealthCheck(
                    service_name="vector_database",
                    status=HealthStatus.HEALTHY,
                    message="Vector database operational",
                    response_time=response_time,
                    details={"search_results": len(test_result) if test_result else 0}
                )
            else:
                return HealthCheck(
                    service_name="vector_database",
                    status=HealthStatus.UNHEALTHY,
                    message="Vector service not initialized"
                )
        
        except Exception as e:
            return HealthCheck(
                service_name="vector_database",
                status=HealthStatus.UNHEALTHY,
                message=f"Vector database health check failed: {str(e)}"
            )
    
    def _calculate_overall_health(self, checks: Dict[str, HealthCheck]) -> HealthStatus:
        """Calculate overall system health based on individual service checks."""
        if not checks:
            return HealthStatus.UNKNOWN
        
        healthy_count = sum(1 for check in checks.values() if check.status == HealthStatus.HEALTHY)
        degraded_count = sum(1 for check in checks.values() if check.status == HealthStatus.DEGRADED)
        unhealthy_count = sum(1 for check in checks.values() if check.status == HealthStatus.UNHEALTHY)
        
        total_count = len(checks)
        healthy_percentage = (healthy_count / total_count) * 100
        
        # Determine overall status
        if healthy_percentage >= 80:
            return HealthStatus.HEALTHY
        elif healthy_percentage >= 50 or (healthy_count + degraded_count) >= unhealthy_count:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.UNHEALTHY
    
    def _generate_health_summary(self, checks: Dict[str, HealthCheck]) -> Dict[str, Any]:
        """Generate a summary of health check results."""
        status_counts = {
            HealthStatus.HEALTHY.value: 0,
            HealthStatus.DEGRADED.value: 0,
            HealthStatus.UNHEALTHY.value: 0,
            HealthStatus.UNKNOWN.value: 0
        }
        
        total_response_time = 0
        response_time_count = 0
        
        for check in checks.values():
            status_counts[check.status.value] += 1
            
            if check.response_time:
                total_response_time += check.response_time
                response_time_count += 1
        
        avg_response_time = (total_response_time / response_time_count) if response_time_count > 0 else None
        
        return {
            "total_services": len(checks),
            "status_breakdown": status_counts,
            "average_response_time_ms": round(avg_response_time * 1000, 2) if avg_response_time else None,
            "critical_services_down": [
                check.service_name for check in checks.values()
                if check.status == HealthStatus.UNHEALTHY and check.service_name.startswith(("ai_", "database_"))
            ]
        }
    
    def clear_cache(self):
        """Clear health check cache."""
        self.health_cache.clear()
        logger.info("Health check cache cleared")


# Global health check service instance
health_check_service = HealthCheckService()