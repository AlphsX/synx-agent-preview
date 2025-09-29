"""
Comprehensive error handling and monitoring system.

This module provides:
- Graceful degradation for external API failures
- Structured error responses
- Retry logic with exponential backoff
- Error tracking and metrics
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Callable, TypeVar, Union
from functools import wraps
from datetime import datetime, timedelta
from enum import Enum
import traceback
import json

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
import aiohttp

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ErrorSeverity(Enum):
    """Error severity levels for monitoring and alerting."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ServiceType(Enum):
    """Types of services for error categorization."""
    AI_MODEL = "ai_model"
    SEARCH_API = "search_api"
    CRYPTO_API = "crypto_api"
    WEATHER_API = "weather_api"
    STOCK_API = "stock_api"
    SENTIMENT_API = "sentiment_api"
    DATABASE = "database"
    CACHE = "cache"
    VECTOR_DB = "vector_db"
    EXTERNAL_API = "external_api"


class ErrorCode(Enum):
    """Standardized error codes for different failure types."""
    # External API errors
    API_TIMEOUT = "API_TIMEOUT"
    API_RATE_LIMIT = "API_RATE_LIMIT"
    API_AUTH_FAILED = "API_AUTH_FAILED"
    API_UNAVAILABLE = "API_UNAVAILABLE"
    API_INVALID_RESPONSE = "API_INVALID_RESPONSE"
    
    # Service errors
    SERVICE_DEGRADED = "SERVICE_DEGRADED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    
    # Data errors
    INVALID_INPUT = "INVALID_INPUT"
    DATA_VALIDATION_FAILED = "DATA_VALIDATION_FAILED"
    
    # System errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"


class ErrorMetrics:
    """Track error metrics for monitoring and health checks."""
    
    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.error_history: List[Dict[str, Any]] = []
        self.service_health: Dict[str, Dict[str, Any]] = {}
        self.last_reset = datetime.now()
    
    def record_error(
        self, 
        service: ServiceType, 
        error_code: ErrorCode, 
        severity: ErrorSeverity,
        details: Optional[Dict[str, Any]] = None
    ):
        """Record an error occurrence."""
        key = f"{service.value}:{error_code.value}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1
        
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "service": service.value,
            "error_code": error_code.value,
            "severity": severity.value,
            "details": details or {}
        }
        
        self.error_history.append(error_record)
        
        # Keep only last 1000 errors
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]
        
        # Update service health
        self._update_service_health(service, error_code, severity)
        
        logger.error(f"Error recorded: {service.value} - {error_code.value} ({severity.value})")
    
    def record_success(self, service: ServiceType):
        """Record a successful operation."""
        service_key = service.value
        if service_key not in self.service_health:
            self.service_health[service_key] = {
                "status": "healthy",
                "consecutive_failures": 0,
                "last_success": datetime.now(),
                "last_failure": None,
                "failure_rate": 0.0
            }
        
        health = self.service_health[service_key]
        health["consecutive_failures"] = 0
        health["last_success"] = datetime.now()
        health["status"] = "healthy"
    
    def _update_service_health(self, service: ServiceType, error_code: ErrorCode, severity: ErrorSeverity):
        """Update service health based on error."""
        service_key = service.value
        
        if service_key not in self.service_health:
            self.service_health[service_key] = {
                "status": "healthy",
                "consecutive_failures": 0,
                "last_success": None,
                "last_failure": datetime.now(),
                "failure_rate": 0.0
            }
        
        health = self.service_health[service_key]
        health["consecutive_failures"] += 1
        health["last_failure"] = datetime.now()
        
        # Determine service status based on consecutive failures and severity
        if health["consecutive_failures"] >= 5 or severity == ErrorSeverity.CRITICAL:
            health["status"] = "unhealthy"
        elif health["consecutive_failures"] >= 3 or severity == ErrorSeverity.HIGH:
            health["status"] = "degraded"
        else:
            health["status"] = "healthy"
    
    def get_service_health(self, service: Optional[ServiceType] = None) -> Dict[str, Any]:
        """Get health status for a service or all services."""
        if service:
            return self.service_health.get(service.value, {"status": "unknown"})
        return self.service_health.copy()
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the specified time period."""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        recent_errors = [
            error for error in self.error_history
            if datetime.fromisoformat(error["timestamp"]) > cutoff
        ]
        
        # Count errors by service and severity
        service_counts = {}
        severity_counts = {}
        
        for error in recent_errors:
            service = error["service"]
            severity = error["severity"]
            
            service_counts[service] = service_counts.get(service, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "period_hours": hours,
            "total_errors": len(recent_errors),
            "errors_by_service": service_counts,
            "errors_by_severity": severity_counts,
            "recent_errors": recent_errors[-10:] if recent_errors else []
        }
    
    def reset_metrics(self):
        """Reset all metrics."""
        self.error_counts.clear()
        self.error_history.clear()
        self.service_health.clear()
        self.last_reset = datetime.now()
        logger.info("Error metrics reset")


# Global error metrics instance
error_metrics = ErrorMetrics()


class RetryConfig:
    """Configuration for retry logic with exponential backoff."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for the given attempt number."""
        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # Add 0-50% jitter
        
        return delay


async def retry_with_backoff(
    func: Callable[..., T],
    retry_config: RetryConfig,
    service: ServiceType,
    *args,
    **kwargs
) -> T:
    """
    Execute a function with retry logic and exponential backoff.
    
    Args:
        func: The function to execute
        retry_config: Retry configuration
        service: Service type for error tracking
        *args: Function arguments
        **kwargs: Function keyword arguments
    
    Returns:
        Function result
    
    Raises:
        Exception: If all retries are exhausted
    """
    last_exception = None
    
    for attempt in range(retry_config.max_retries + 1):
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            
            # Record success if not the first attempt
            if attempt > 0:
                error_metrics.record_success(service)
                logger.info(f"Retry successful for {service.value} after {attempt} attempts")
            
            return result
            
        except Exception as e:
            last_exception = e
            
            # Determine error code and severity
            error_code = _classify_exception(e)
            severity = _determine_severity(e, attempt, retry_config.max_retries)
            
            # Record error
            error_metrics.record_error(
                service=service,
                error_code=error_code,
                severity=severity,
                details={
                    "attempt": attempt + 1,
                    "max_retries": retry_config.max_retries,
                    "exception_type": type(e).__name__,
                    "exception_message": str(e)
                }
            )
            
            # Don't retry on the last attempt
            if attempt == retry_config.max_retries:
                break
            
            # Calculate delay and wait
            delay = retry_config.get_delay(attempt)
            logger.warning(
                f"Attempt {attempt + 1} failed for {service.value}: {str(e)}. "
                f"Retrying in {delay:.2f} seconds..."
            )
            await asyncio.sleep(delay)
    
    # All retries exhausted
    logger.error(f"All retries exhausted for {service.value}. Last error: {last_exception}")
    raise last_exception


def _classify_exception(exception: Exception) -> ErrorCode:
    """Classify an exception into an error code."""
    if isinstance(exception, asyncio.TimeoutError):
        return ErrorCode.API_TIMEOUT
    elif isinstance(exception, aiohttp.ClientResponseError):
        if exception.status == 429:
            return ErrorCode.API_RATE_LIMIT
        elif exception.status in (401, 403):
            return ErrorCode.API_AUTH_FAILED
        elif exception.status >= 500:
            return ErrorCode.API_UNAVAILABLE
        else:
            return ErrorCode.API_INVALID_RESPONSE
    elif isinstance(exception, aiohttp.ClientError):
        return ErrorCode.API_UNAVAILABLE
    elif isinstance(exception, ValueError):
        return ErrorCode.DATA_VALIDATION_FAILED
    else:
        return ErrorCode.INTERNAL_ERROR


def _determine_severity(exception: Exception, attempt: int, max_retries: int) -> ErrorSeverity:
    """Determine error severity based on exception type and retry attempt."""
    if isinstance(exception, (asyncio.TimeoutError, aiohttp.ClientError)):
        if attempt >= max_retries:
            return ErrorSeverity.HIGH
        else:
            return ErrorSeverity.MEDIUM
    elif isinstance(exception, ValueError):
        return ErrorSeverity.LOW
    else:
        return ErrorSeverity.HIGH if attempt >= max_retries else ErrorSeverity.MEDIUM


class GracefulDegradation:
    """Handles graceful degradation when services fail."""
    
    def __init__(self):
        self.fallback_responses = {}
        self.service_priorities = {}
    
    def register_fallback(
        self, 
        service: ServiceType, 
        fallback_func: Callable[..., Any],
        priority: int = 1
    ):
        """Register a fallback function for a service."""
        if service not in self.fallback_responses:
            self.fallback_responses[service] = []
        
        self.fallback_responses[service].append({
            "func": fallback_func,
            "priority": priority
        })
        
        # Sort by priority (higher priority first)
        self.fallback_responses[service].sort(key=lambda x: x["priority"], reverse=True)
    
    async def execute_with_fallback(
        self,
        primary_func: Callable[..., T],
        service: ServiceType,
        *args,
        **kwargs
    ) -> T:
        """Execute function with fallback options."""
        try:
            return await primary_func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Primary service {service.value} failed: {e}")
            
            # Try fallback options
            fallbacks = self.fallback_responses.get(service, [])
            for fallback in fallbacks:
                try:
                    logger.info(f"Trying fallback for {service.value}")
                    result = await fallback["func"](*args, **kwargs)
                    logger.info(f"Fallback successful for {service.value}")
                    return result
                except Exception as fallback_error:
                    logger.warning(f"Fallback failed for {service.value}: {fallback_error}")
                    continue
            
            # No fallbacks worked
            logger.error(f"All fallbacks exhausted for {service.value}")
            raise e


# Global graceful degradation instance
graceful_degradation = GracefulDegradation()


class StructuredError:
    """Structured error response format."""
    
    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        service: ServiceType,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        fallback_available: bool = False
    ):
        self.error_code = error_code
        self.message = message
        self.service = service
        self.severity = severity
        self.details = details or {}
        self.fallback_available = fallback_available
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        return {
            "error": {
                "code": self.error_code.value,
                "message": self.message,
                "service": self.service.value,
                "severity": self.severity.value,
                "timestamp": self.timestamp,
                "details": self.details,
                "fallback_available": self.fallback_available
            }
        }
    
    def to_http_exception(self, status_code: int = 500) -> HTTPException:
        """Convert to FastAPI HTTPException."""
        return HTTPException(
            status_code=status_code,
            detail=self.to_dict()["error"]
        )


async def handle_api_error(
    request: Request,
    call_next: Callable,
    response: Response
) -> Response:
    """Middleware for handling API errors with structured responses."""
    try:
        return await call_next(request)
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Convert unexpected errors to structured format
        error_code = _classify_exception(e)
        severity = ErrorSeverity.HIGH
        
        structured_error = StructuredError(
            error_code=error_code,
            message=f"Unexpected error: {str(e)}",
            service=ServiceType.EXTERNAL_API,  # Default service
            severity=severity,
            details={
                "exception_type": type(e).__name__,
                "traceback": traceback.format_exc()
            }
        )
        
        # Record error
        error_metrics.record_error(
            service=ServiceType.EXTERNAL_API,
            error_code=error_code,
            severity=severity,
            details=structured_error.details
        )
        
        return JSONResponse(
            status_code=500,
            content=structured_error.to_dict()
        )


def error_handler(service: ServiceType):
    """Decorator for handling errors in service functions."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                error_metrics.record_success(service)
                return result
            except Exception as e:
                error_code = _classify_exception(e)
                severity = _determine_severity(e, 0, 1)
                
                error_metrics.record_error(
                    service=service,
                    error_code=error_code,
                    severity=severity,
                    details={
                        "function": func.__name__,
                        "exception_type": type(e).__name__,
                        "exception_message": str(e)
                    }
                )
                
                raise StructuredError(
                    error_code=error_code,
                    message=str(e),
                    service=service,
                    severity=severity
                ).to_http_exception()
        
        return wrapper
    return decorator