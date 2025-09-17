"""
Security utilities and middleware for the AI Agent API.

This module provides security utilities including API key validation,
secure headers, and security monitoring.
"""

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, List, Optional, Set
import logging
import hashlib
import secrets
import time
from datetime import datetime, timedelta

from app.config import settings
from app.auth.middleware import api_key_validator

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""
    
    def __init__(self, app):
        super().__init__(app)
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains" if settings.is_production else None
        }
    
    async def dispatch(self, request: Request, call_next):
        """Add security headers to response."""
        response = await call_next(request)
        
        # Add security headers
        for header, value in self.security_headers.items():
            if value is not None:
                response.headers[header] = value
        
        # Add server identification
        response.headers["Server"] = "AI-Agent-API/1.0"
        
        return response


class APIKeySecurityManager:
    """Manager for API key security and validation."""
    
    def __init__(self):
        self.failed_attempts: Dict[str, List[datetime]] = {}
        self.blocked_keys: Set[str] = set()
        self.max_attempts = 5
        self.block_duration = timedelta(minutes=15)
        self.attempt_window = timedelta(minutes=5)
    
    def validate_api_key_format(self, api_key: str) -> bool:
        """
        Validate API key format (basic security check).
        
        Args:
            api_key: API key to validate
            
        Returns:
            True if format is valid
        """
        if not api_key or len(api_key) < 16:
            return False
        
        # Check for common patterns that indicate test/demo keys
        dangerous_patterns = [
            "test", "demo", "example", "sample", "fake", "mock",
            "12345", "abcde", "aaaaa", "00000"
        ]
        
        api_key_lower = api_key.lower()
        return not any(pattern in api_key_lower for pattern in dangerous_patterns)
    
    def record_failed_attempt(self, identifier: str):
        """
        Record a failed API key attempt.
        
        Args:
            identifier: IP address or user identifier
        """
        now = datetime.now()
        
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = []
        
        # Clean old attempts
        cutoff = now - self.attempt_window
        self.failed_attempts[identifier] = [
            attempt for attempt in self.failed_attempts[identifier]
            if attempt > cutoff
        ]
        
        # Add new attempt
        self.failed_attempts[identifier].append(now)
        
        # Check if should block
        if len(self.failed_attempts[identifier]) >= self.max_attempts:
            self.blocked_keys.add(identifier)
            logger.warning(f"Blocked identifier {identifier} due to repeated failed attempts")
    
    def is_blocked(self, identifier: str) -> bool:
        """
        Check if an identifier is currently blocked.
        
        Args:
            identifier: IP address or user identifier
            
        Returns:
            True if blocked
        """
        if identifier not in self.blocked_keys:
            return False
        
        # Check if block has expired
        if identifier in self.failed_attempts:
            latest_attempt = max(self.failed_attempts[identifier])
            if datetime.now() - latest_attempt > self.block_duration:
                self.blocked_keys.discard(identifier)
                self.failed_attempts.pop(identifier, None)
                return False
        
        return True
    
    def get_security_status(self) -> Dict[str, any]:
        """
        Get current security status.
        
        Returns:
            Security status information
        """
        return {
            "blocked_identifiers": len(self.blocked_keys),
            "failed_attempts_tracked": len(self.failed_attempts),
            "api_services_available": api_key_validator.get_available_services(),
            "security_level": "high" if settings.is_production else "development"
        }


class SecureAPIKeyValidator:
    """Enhanced API key validator with security features."""
    
    def __init__(self):
        self.security_manager = APIKeySecurityManager()
    
    def get_client_identifier(self, request: Request) -> str:
        """Get client identifier for security tracking."""
        # Try to get real IP
        client_ip = request.client.host
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        return client_ip
    
    async def validate_request_security(self, request: Request) -> Dict[str, any]:
        """
        Validate request security and return security context.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Security context dictionary
            
        Raises:
            HTTPException: If security validation fails
        """
        client_id = self.get_client_identifier(request)
        
        # Check if client is blocked
        if self.security_manager.is_blocked(client_id):
            logger.warning(f"Blocked request from {client_id}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed attempts. Please try again later."
            )
        
        # Validate API keys in headers
        api_key_header = request.headers.get("x-api-key")
        if api_key_header:
            if not self.security_manager.validate_api_key_format(api_key_header):
                self.security_manager.record_failed_attempt(client_id)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key format"
                )
        
        # Check for suspicious patterns in request
        user_agent = request.headers.get("user-agent", "").lower()
        suspicious_agents = ["bot", "crawler", "spider", "scraper"]
        
        is_suspicious = any(agent in user_agent for agent in suspicious_agents)
        
        return {
            "client_id": client_id,
            "is_suspicious": is_suspicious,
            "user_agent": user_agent,
            "has_api_key": bool(api_key_header),
            "timestamp": datetime.now().isoformat()
        }


class SecurityMonitor:
    """Security monitoring and alerting system."""
    
    def __init__(self):
        self.security_events: List[Dict[str, any]] = []
        self.max_events = 1000
    
    def log_security_event(self, event_type: str, details: Dict[str, any], severity: str = "info"):
        """
        Log a security event.
        
        Args:
            event_type: Type of security event
            details: Event details
            severity: Event severity (info, warning, critical)
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "severity": severity,
            "details": details
        }
        
        self.security_events.append(event)
        
        # Keep only recent events
        if len(self.security_events) > self.max_events:
            self.security_events = self.security_events[-self.max_events:]
        
        # Log based on severity
        if severity == "critical":
            logger.critical(f"Security event: {event_type} - {details}")
        elif severity == "warning":
            logger.warning(f"Security event: {event_type} - {details}")
        else:
            logger.info(f"Security event: {event_type} - {details}")
    
    def get_security_summary(self, hours: int = 24) -> Dict[str, any]:
        """
        Get security summary for the last N hours.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Security summary
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        
        recent_events = [
            event for event in self.security_events
            if datetime.fromisoformat(event["timestamp"]) > cutoff
        ]
        
        # Count by type and severity
        event_counts = {}
        severity_counts = {"info": 0, "warning": 0, "critical": 0}
        
        for event in recent_events:
            event_type = event["type"]
            severity = event["severity"]
            
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
            severity_counts[severity] += 1
        
        return {
            "period_hours": hours,
            "total_events": len(recent_events),
            "event_types": event_counts,
            "severity_breakdown": severity_counts,
            "latest_events": recent_events[-10:] if recent_events else []
        }


# Global security instances
security_manager = APIKeySecurityManager()
secure_validator = SecureAPIKeyValidator()
security_monitor = SecurityMonitor()


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.
    
    Args:
        length: Token length in bytes
        
    Returns:
        Hex-encoded secure token
    """
    return secrets.token_hex(length)


def hash_sensitive_data(data: str, salt: str = None) -> str:
    """
    Hash sensitive data with optional salt.
    
    Args:
        data: Data to hash
        salt: Optional salt (generated if not provided)
        
    Returns:
        Hashed data
    """
    if salt is None:
        salt = secrets.token_hex(16)
    
    combined = f"{salt}{data}{settings.SECRET_KEY}"
    return hashlib.sha256(combined.encode()).hexdigest()


def verify_hashed_data(data: str, hashed: str, salt: str) -> bool:
    """
    Verify hashed data against original.
    
    Args:
        data: Original data
        hashed: Hashed data to verify against
        salt: Salt used in hashing
        
    Returns:
        True if data matches hash
    """
    expected_hash = hash_sensitive_data(data, salt)
    return secrets.compare_digest(expected_hash, hashed)