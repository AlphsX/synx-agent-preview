"""
Structured logging middleware for API requests and responses.

This module provides comprehensive logging for:
- All API requests and responses
- External API calls
- Error tracking
- Performance monitoring
- Security events
"""

import json
import logging
import time
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

from fastapi import Request, Response
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import aiohttp

logger = logging.getLogger(__name__)


class StructuredLogger:
    """Structured logger for consistent log formatting."""
    
    def __init__(self, logger_name: str = __name__):
        self.logger = logging.getLogger(logger_name)
    
    def log_request(
        self,
        request: Request,
        request_id: str,
        start_time: float,
        user_id: Optional[str] = None
    ):
        """Log incoming API request."""
        log_data = {
            "event_type": "api_request",
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": self._sanitize_headers(dict(request.headers)),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", ""),
            "user_id": user_id,
            "start_time": start_time
        }
        
        self.logger.info(f"API Request: {request.method} {request.url.path}", extra={"structured_data": log_data})
    
    def log_response(
        self,
        request: Request,
        response: Response,
        request_id: str,
        start_time: float,
        end_time: float,
        user_id: Optional[str] = None,
        error: Optional[Exception] = None
    ):
        """Log API response."""
        duration = end_time - start_time
        
        log_data = {
            "event_type": "api_response",
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "response_size": len(response.body) if hasattr(response, 'body') and response.body else 0,
            "user_id": user_id,
            "error": str(error) if error else None
        }
        
        # Determine log level based on status code
        if response.status_code >= 500:
            log_level = logging.ERROR
            message = f"API Error: {request.method} {request.url.path} - {response.status_code}"
        elif response.status_code >= 400:
            log_level = logging.WARNING
            message = f"API Client Error: {request.method} {request.url.path} - {response.status_code}"
        else:
            log_level = logging.INFO
            message = f"API Response: {request.method} {request.url.path} - {response.status_code} ({duration*1000:.2f}ms)"
        
        self.logger.log(log_level, message, extra={"structured_data": log_data})
    
    def log_external_api_call(
        self,
        service_name: str,
        method: str,
        url: str,
        request_data: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
        duration: Optional[float] = None,
        error: Optional[Exception] = None,
        request_id: Optional[str] = None
    ):
        """Log external API call."""
        log_data = {
            "event_type": "external_api_call",
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "service_name": service_name,
            "method": method,
            "url": url,
            "request_data": self._sanitize_request_data(request_data),
            "response_data": self._truncate_response_data(response_data),
            "status_code": status_code,
            "duration_ms": round(duration * 1000, 2) if duration else None,
            "success": error is None and (status_code is None or 200 <= status_code < 300),
            "error": str(error) if error else None
        }
        
        if error or (status_code and status_code >= 400):
            self.logger.error(f"External API Error: {service_name} {method} {url}", extra={"structured_data": log_data})
        else:
            self.logger.info(f"External API Call: {service_name} {method} {url}", extra={"structured_data": log_data})
    
    def log_security_event(
        self,
        event_type: str,
        request: Request,
        details: Dict[str, Any],
        severity: str = "medium",
        user_id: Optional[str] = None
    ):
        """Log security-related events."""
        log_data = {
            "event_type": "security_event",
            "security_event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "severity": severity,
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", ""),
            "url": str(request.url),
            "method": request.method,
            "user_id": user_id,
            "details": details
        }
        
        if severity in ("high", "critical"):
            self.logger.error(f"Security Event: {event_type}", extra={"structured_data": log_data})
        else:
            self.logger.warning(f"Security Event: {event_type}", extra={"structured_data": log_data})
    
    def log_performance_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "ms",
        tags: Optional[Dict[str, str]] = None,
        request_id: Optional[str] = None
    ):
        """Log performance metrics."""
        log_data = {
            "event_type": "performance_metric",
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "metric_name": metric_name,
            "value": value,
            "unit": unit,
            "tags": tags or {}
        }
        
        self.logger.info(f"Performance Metric: {metric_name} = {value}{unit}", extra={"structured_data": log_data})
    
    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Remove sensitive headers from logging."""
        sensitive_headers = {
            "authorization", "x-api-key", "cookie", "x-subscription-token",
            "x-auth-token", "bearer", "api-key", "secret"
        }
        
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _sanitize_request_data(self, data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Remove sensitive data from request logging."""
        if not data:
            return data
        
        sensitive_keys = {
            "password", "api_key", "secret", "token", "authorization",
            "credit_card", "ssn", "social_security"
        }
        
        sanitized = {}
        for key, value in data.items():
            if key.lower() in sensitive_keys:
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_request_data(value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _truncate_response_data(self, data: Optional[Dict[str, Any]], max_size: int = 1000) -> Optional[Dict[str, Any]]:
        """Truncate large response data for logging."""
        if not data:
            return data
        
        try:
            json_str = json.dumps(data)
            if len(json_str) > max_size:
                return {"truncated": True, "size": len(json_str), "preview": json_str[:max_size]}
            return data
        except (TypeError, ValueError):
            return {"error": "Unable to serialize response data"}
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging all API requests and responses."""
    
    def __init__(self, app, logger_name: str = "api"):
        super().__init__(app)
        self.structured_logger = StructuredLogger(logger_name)
    
    async def dispatch(self, request: Request, call_next) -> StarletteResponse:
        """Process request and log details."""
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Record start time
        start_time = time.time()
        
        # Extract user ID if available (from JWT token, session, etc.)
        user_id = self._extract_user_id(request)
        
        # Log incoming request
        self.structured_logger.log_request(request, request_id, start_time, user_id)
        
        # Process request
        response = None
        error = None
        
        try:
            response = await call_next(request)
        except Exception as e:
            error = e
            # Create error response
            response = Response(
                content=json.dumps({"error": "Internal server error", "request_id": request_id}),
                status_code=500,
                media_type="application/json"
            )
        
        # Record end time
        end_time = time.time()
        
        # Log response
        self.structured_logger.log_response(
            request, response, request_id, start_time, end_time, user_id, error
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
    
    def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request (implement based on your auth system)."""
        # This is a placeholder - implement based on your authentication system
        # For example, extract from JWT token, session, etc.
        
        # Check for user in request state (set by auth middleware)
        if hasattr(request.state, "user"):
            return getattr(request.state.user, "id", None)
        
        # Check for user ID in headers (for API keys, etc.)
        user_id_header = request.headers.get("x-user-id")
        if user_id_header:
            return user_id_header
        
        return None


class ExternalAPILogger:
    """Logger specifically for external API calls with retry tracking."""
    
    def __init__(self):
        self.structured_logger = StructuredLogger("external_api")
        self.active_calls: Dict[str, Dict[str, Any]] = {}
    
    def start_call(
        self,
        service_name: str,
        method: str,
        url: str,
        request_data: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> str:
        """Start tracking an external API call."""
        call_id = str(uuid.uuid4())
        
        self.active_calls[call_id] = {
            "service_name": service_name,
            "method": method,
            "url": url,
            "request_data": request_data,
            "request_id": request_id,
            "start_time": time.time(),
            "attempts": 0
        }
        
        return call_id
    
    def log_attempt(self, call_id: str, attempt: int, error: Optional[Exception] = None):
        """Log a retry attempt."""
        if call_id not in self.active_calls:
            return
        
        call_data = self.active_calls[call_id]
        call_data["attempts"] = attempt
        
        if error:
            self.structured_logger.log_external_api_call(
                service_name=call_data["service_name"],
                method=call_data["method"],
                url=call_data["url"],
                request_data=call_data["request_data"],
                error=error,
                request_id=call_data["request_id"]
            )
    
    def finish_call(
        self,
        call_id: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None
    ):
        """Finish tracking an external API call."""
        if call_id not in self.active_calls:
            return
        
        call_data = self.active_calls[call_id]
        duration = time.time() - call_data["start_time"]
        
        # Log final result
        self.structured_logger.log_external_api_call(
            service_name=call_data["service_name"],
            method=call_data["method"],
            url=call_data["url"],
            request_data=call_data["request_data"],
            response_data=response_data,
            status_code=status_code,
            duration=duration,
            error=error,
            request_id=call_data["request_id"]
        )
        
        # Log performance metric
        self.structured_logger.log_performance_metric(
            metric_name=f"external_api_duration_{call_data['service_name']}",
            value=duration * 1000,  # Convert to milliseconds
            unit="ms",
            tags={
                "service": call_data["service_name"],
                "method": call_data["method"],
                "success": str(error is None and (status_code is None or 200 <= status_code < 300)),
                "attempts": str(call_data["attempts"])
            },
            request_id=call_data["request_id"]
        )
        
        # Clean up
        del self.active_calls[call_id]


class PerformanceLogger:
    """Logger for performance metrics and monitoring."""
    
    def __init__(self):
        self.structured_logger = StructuredLogger("performance")
        self.metrics_buffer: List[Dict[str, Any]] = []
        self.buffer_size = 100
    
    def log_database_query(
        self,
        query: str,
        duration: float,
        rows_affected: Optional[int] = None,
        request_id: Optional[str] = None
    ):
        """Log database query performance."""
        self.structured_logger.log_performance_metric(
            metric_name="database_query_duration",
            value=duration * 1000,
            unit="ms",
            tags={
                "query_type": self._classify_query(query),
                "rows_affected": str(rows_affected) if rows_affected is not None else "unknown"
            },
            request_id=request_id
        )
    
    def log_ai_generation(
        self,
        model_id: str,
        prompt_tokens: Optional[int],
        completion_tokens: Optional[int],
        duration: float,
        request_id: Optional[str] = None
    ):
        """Log AI generation performance."""
        self.structured_logger.log_performance_metric(
            metric_name="ai_generation_duration",
            value=duration * 1000,
            unit="ms",
            tags={
                "model_id": model_id,
                "prompt_tokens": str(prompt_tokens) if prompt_tokens else "unknown",
                "completion_tokens": str(completion_tokens) if completion_tokens else "unknown",
                "total_tokens": str((prompt_tokens or 0) + (completion_tokens or 0))
            },
            request_id=request_id
        )
    
    def log_vector_search(
        self,
        query_length: int,
        results_count: int,
        duration: float,
        request_id: Optional[str] = None
    ):
        """Log vector search performance."""
        self.structured_logger.log_performance_metric(
            metric_name="vector_search_duration",
            value=duration * 1000,
            unit="ms",
            tags={
                "query_length": str(query_length),
                "results_count": str(results_count)
            },
            request_id=request_id
        )
    
    def _classify_query(self, query: str) -> str:
        """Classify database query type."""
        query_lower = query.lower().strip()
        
        if query_lower.startswith("select"):
            return "select"
        elif query_lower.startswith("insert"):
            return "insert"
        elif query_lower.startswith("update"):
            return "update"
        elif query_lower.startswith("delete"):
            return "delete"
        elif query_lower.startswith("create"):
            return "create"
        elif query_lower.startswith("drop"):
            return "drop"
        else:
            return "other"


# Global logger instances
structured_logger = StructuredLogger()
external_api_logger = ExternalAPILogger()
performance_logger = PerformanceLogger()