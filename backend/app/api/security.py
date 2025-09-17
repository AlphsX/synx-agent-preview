"""
Security monitoring and management endpoints.

This module provides endpoints for monitoring security status,
managing API keys, and viewing security events.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Dict, List, Optional
import logging
from datetime import datetime

from app.auth.middleware import get_current_active_user, get_optional_user
from app.auth.schemas import UserResponse
from app.core.security import security_manager, secure_validator, security_monitor, api_key_validator
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/security/status")
async def get_security_status(
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """
    Get current security status and API service availability.
    
    Returns security information including:
    - API service availability
    - Security configuration status
    - Rate limiting status
    """
    try:
        # Get API service availability
        api_services = api_key_validator.get_available_services()
        
        # Get security manager status
        security_status = security_manager.get_security_status()
        
        # Basic security info (safe to expose)
        status_info = {
            "api_services": api_services,
            "security_level": "production" if settings.is_production else "development",
            "authentication_enabled": True,
            "rate_limiting_enabled": True,
            "security_headers_enabled": True,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add detailed info for authenticated users
        if current_user:
            status_info.update({
                "user_authenticated": True,
                "user_id": current_user.id,
                "username": current_user.username,
                "blocked_identifiers": security_status.get("blocked_identifiers", 0)
            })
        else:
            status_info["user_authenticated"] = False
        
        return status_info
        
    except Exception as e:
        logger.error(f"Error getting security status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security status"
        )


@router.get("/security/api-keys/validation")
async def validate_api_keys(
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Validate API key configuration (requires authentication).
    
    Returns detailed information about API key availability
    and configuration status for external services.
    """
    try:
        # Get detailed API key status
        api_services = api_key_validator.get_available_services()
        
        # Create detailed report
        validation_report = {
            "timestamp": datetime.now().isoformat(),
            "total_services": len(api_services),
            "configured_services": sum(1 for available in api_services.values() if available),
            "services": {}
        }
        
        # Service categories
        service_categories = {
            "ai_models": ["groq", "openai", "anthropic"],
            "search": ["serp", "brave_search"],
            "crypto": ["binance"]
        }
        
        for category, services in service_categories.items():
            validation_report["services"][category] = {
                service: {
                    "configured": api_services.get(service, False),
                    "status": "available" if api_services.get(service, False) else "missing_key"
                }
                for service in services
            }
        
        # Add recommendations
        missing_services = [
            service for service, available in api_services.items()
            if not available
        ]
        
        if missing_services:
            validation_report["recommendations"] = [
                f"Configure API key for {service}" for service in missing_services
            ]
            validation_report["demo_mode_services"] = missing_services
        else:
            validation_report["recommendations"] = ["All services configured"]
            validation_report["demo_mode_services"] = []
        
        return validation_report
        
    except Exception as e:
        logger.error(f"Error validating API keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate API keys"
        )


@router.get("/security/events")
async def get_security_events(
    hours: int = 24,
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    Get security events summary (requires authentication).
    
    Args:
        hours: Number of hours to look back (default: 24)
    
    Returns security events and statistics for the specified period.
    """
    try:
        if hours < 1 or hours > 168:  # Max 1 week
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hours must be between 1 and 168 (1 week)"
            )
        
        # Get security summary
        summary = security_monitor.get_security_summary(hours)
        
        # Add user context
        summary["requested_by"] = {
            "user_id": current_user.id,
            "username": current_user.username,
            "timestamp": datetime.now().isoformat()
        }
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting security events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security events"
        )


@router.post("/security/validate-request")
async def validate_request_security(
    request: Request,
    current_user: Optional[UserResponse] = Depends(get_optional_user)
):
    """
    Validate current request security context.
    
    This endpoint can be used to check the security status
    of the current request and client.
    """
    try:
        # Validate request security
        security_context = await secure_validator.validate_request_security(request)
        
        # Add user context if authenticated
        if current_user:
            security_context["authenticated_user"] = {
                "user_id": current_user.id,
                "username": current_user.username,
                "is_active": current_user.is_active
            }
        
        # Log security validation
        security_monitor.log_security_event(
            "request_validation",
            {
                "client_id": security_context["client_id"],
                "user": current_user.username if current_user else "anonymous",
                "is_suspicious": security_context["is_suspicious"]
            },
            "warning" if security_context["is_suspicious"] else "info"
        )
        
        return {
            "security_context": security_context,
            "validation_passed": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating request security: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate request security"
        )


@router.get("/security/health")
async def security_health_check():
    """
    Security-focused health check endpoint.
    
    Returns basic security health information without
    requiring authentication.
    """
    try:
        # Basic health info
        health_info = {
            "security_middleware": "active",
            "rate_limiting": "enabled",
            "authentication": "available",
            "api_validation": "active",
            "timestamp": datetime.now().isoformat(),
            "environment": settings.ENVIRONMENT
        }
        
        # Check if critical security features are working
        try:
            # Test API key validator
            api_services = api_key_validator.get_available_services()
            health_info["api_key_validator"] = "operational"
            health_info["configured_services"] = sum(1 for available in api_services.values() if available)
        except Exception:
            health_info["api_key_validator"] = "error"
            health_info["configured_services"] = 0
        
        try:
            # Test security manager
            security_manager.get_security_status()
            health_info["security_manager"] = "operational"
        except Exception:
            health_info["security_manager"] = "error"
        
        return health_info
        
    except Exception as e:
        logger.error(f"Error in security health check: {e}")
        return {
            "security_middleware": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }