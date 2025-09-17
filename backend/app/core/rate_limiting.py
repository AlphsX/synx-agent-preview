"""
Rate limiting middleware for API abuse prevention.

This module provides rate limiting functionality using Redis for distributed
rate limiting and in-memory fallback for development environments.
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Optional, Tuple
import time
import asyncio
import logging
from collections import defaultdict, deque
import redis.asyncio as redis
from datetime import datetime, timedelta

from app.config import settings

logger = logging.getLogger(__name__)


class RateLimitExceeded(HTTPException):
    """Custom exception for rate limit violations."""
    
    def __init__(self, detail: str, retry_after: int = None):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"Retry-After": str(retry_after)} if retry_after else None
        )


class InMemoryRateLimiter:
    """In-memory rate limiter for development and fallback."""
    
    def __init__(self):
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.lock = asyncio.Lock()
    
    async def is_allowed(
        self, 
        key: str, 
        limit: int, 
        window: int
    ) -> Tuple[bool, int, int]:
        """
        Check if request is allowed under rate limit.
        
        Args:
            key: Unique identifier for rate limiting (IP, user ID, etc.)
            limit: Maximum requests allowed in window
            window: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, remaining_requests, reset_time)
        """
        async with self.lock:
            now = time.time()
            cutoff = now - window
            
            # Clean old requests
            while self.requests[key] and self.requests[key][0] < cutoff:
                self.requests[key].popleft()
            
            current_requests = len(self.requests[key])
            
            if current_requests >= limit:
                # Rate limit exceeded
                oldest_request = self.requests[key][0] if self.requests[key] else now
                reset_time = int(oldest_request + window)
                return False, 0, reset_time
            
            # Allow request
            self.requests[key].append(now)
            remaining = limit - (current_requests + 1)
            reset_time = int(now + window)
            
            return True, remaining, reset_time


class RedisRateLimiter:
    """Redis-based distributed rate limiter."""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
    
    async def initialize(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Redis rate limiter initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis rate limiter: {e}")
            self.redis_client = None
    
    async def is_allowed(
        self, 
        key: str, 
        limit: int, 
        window: int
    ) -> Tuple[bool, int, int]:
        """
        Check if request is allowed using Redis sliding window.
        
        Args:
            key: Unique identifier for rate limiting
            limit: Maximum requests allowed in window
            window: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, remaining_requests, reset_time)
        """
        if not self.redis_client:
            # Fallback to allowing all requests if Redis unavailable
            return True, limit - 1, int(time.time() + window)
        
        try:
            now = time.time()
            pipeline = self.redis_client.pipeline()
            
            # Use sliding window log approach
            rate_limit_key = f"rate_limit:{key}"
            
            # Remove expired entries
            pipeline.zremrangebyscore(rate_limit_key, 0, now - window)
            
            # Count current requests
            pipeline.zcard(rate_limit_key)
            
            # Add current request
            pipeline.zadd(rate_limit_key, {str(now): now})
            
            # Set expiration
            pipeline.expire(rate_limit_key, window + 1)
            
            results = await pipeline.execute()
            current_requests = results[1]  # Count after cleanup
            
            if current_requests >= limit:
                # Remove the request we just added since it's not allowed
                await self.redis_client.zrem(rate_limit_key, str(now))
                
                # Calculate reset time
                oldest_scores = await self.redis_client.zrange(
                    rate_limit_key, 0, 0, withscores=True
                )
                if oldest_scores:
                    oldest_time = oldest_scores[0][1]
                    reset_time = int(oldest_time + window)
                else:
                    reset_time = int(now + window)
                
                return False, 0, reset_time
            
            remaining = limit - (current_requests + 1)
            reset_time = int(now + window)
            
            return True, remaining, reset_time
            
        except Exception as e:
            logger.error(f"Redis rate limiting error: {e}")
            # Fallback to allowing request on Redis errors
            return True, limit - 1, int(time.time() + window)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""
    
    def __init__(self, app, requests_per_minute: int = 60, redis_url: str = None):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
        
        # Initialize rate limiters
        self.memory_limiter = InMemoryRateLimiter()
        self.redis_limiter = RedisRateLimiter(redis_url) if redis_url else None
        
        # Rate limiting rules for different endpoints
        self.endpoint_limits = {
            "/api/chat": {"limit": 30, "window": 60},  # 30 requests per minute for chat
            "/api/ai": {"limit": 20, "window": 60},    # 20 requests per minute for AI
            "/api/external": {"limit": 50, "window": 60},  # 50 requests per minute for external APIs
            "/api/auth/token": {"limit": 5, "window": 300},  # 5 login attempts per 5 minutes
        }
        
        # Exempt endpoints from rate limiting
        self.exempt_paths = {
            "/health", "/api/health", "/docs", "/redoc", "/openapi.json"
        }
    
    async def initialize(self):
        """Initialize Redis connection if available."""
        if self.redis_limiter:
            await self.redis_limiter.initialize()
    
    def get_client_identifier(self, request: Request) -> str:
        """
        Get unique identifier for rate limiting.
        
        Priority: User ID > API Key > IP Address
        """
        # Try to get user ID from authorization header
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                # In a real implementation, decode JWT to get user ID
                # For now, use a hash of the token
                import hashlib
                token_hash = hashlib.md5(auth_header.encode()).hexdigest()[:16]
                return f"user:{token_hash}"
            except Exception:
                pass
        
        # Try API key from headers
        api_key = request.headers.get("x-api-key")
        if api_key:
            import hashlib
            key_hash = hashlib.md5(api_key.encode()).hexdigest()[:16]
            return f"api_key:{key_hash}"
        
        # Fallback to IP address
        client_ip = request.client.host
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        return f"ip:{client_ip}"
    
    def get_rate_limit_for_path(self, path: str) -> Tuple[int, int]:
        """Get rate limit configuration for a specific path."""
        for endpoint_prefix, config in self.endpoint_limits.items():
            if path.startswith(endpoint_prefix):
                return config["limit"], config["window"]
        
        # Default rate limit
        return self.requests_per_minute, self.window_seconds
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        path = request.url.path
        
        # Skip rate limiting for exempt paths
        if path in self.exempt_paths:
            return await call_next(request)
        
        # Get client identifier and rate limits
        client_id = self.get_client_identifier(request)
        limit, window = self.get_rate_limit_for_path(path)
        
        # Check rate limit
        rate_limiter = self.redis_limiter or self.memory_limiter
        is_allowed, remaining, reset_time = await rate_limiter.is_allowed(
            client_id, limit, window
        )
        
        if not is_allowed:
            retry_after = reset_time - int(time.time())
            logger.warning(
                f"Rate limit exceeded for {client_id} on {path}. "
                f"Limit: {limit}/{window}s, Retry after: {retry_after}s"
            )
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {limit} per {window} seconds",
                    "retry_after": retry_after
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time)
                }
            )
        
        # Process request and add rate limit headers
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response


# Factory function to create rate limit middleware
def create_rate_limit_middleware(
    requests_per_minute: int = None,
    redis_url: str = None
) -> RateLimitMiddleware:
    """
    Create rate limit middleware with configuration.
    
    Args:
        requests_per_minute: Default requests per minute limit
        redis_url: Redis URL for distributed rate limiting
        
    Returns:
        Configured rate limit middleware
    """
    if requests_per_minute is None:
        requests_per_minute = settings.RATE_LIMIT_REQUESTS
    
    if redis_url is None:
        redis_url = settings.REDIS_URL
    
    return RateLimitMiddleware(
        app=None,  # Will be set by FastAPI
        requests_per_minute=requests_per_minute,
        redis_url=redis_url
    )