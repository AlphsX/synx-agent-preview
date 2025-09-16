"""
Health check and system status endpoints.

This module provides endpoints for monitoring system health,
service availability, and environment configuration status.
"""

from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any
import logging
from datetime import datetime

from ..core.environment import get_health_status, get_service_status
from ..core.startup import get_startup_info
from ..config import settings
from ..database.connection import check_database_health

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=Dict[str, Any])
async def health_check(request: Request) -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns:
        Basic health status information
    """
    try:
        health_status = get_health_status()
        
        return {
            "status": "healthy" if health_status["status"] == "healthy" else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.API_VERSION,
            "environment": settings.ENVIRONMENT
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@router.get("/health/detailed", response_model=Dict[str, Any])
async def detailed_health_check(request: Request) -> Dict[str, Any]:
    """
    Detailed health check with service status information.
    
    Returns:
        Comprehensive health and service status information
    """
    try:
        health_status = get_health_status()
        startup_info = get_startup_info()
        
        # Get service availability from app state if available
        services_info = {}
        if hasattr(request.app.state, 'services'):
            services_info = request.app.state.services
        
        # Check database health
        database_health = None
        try:
            database_health = await check_database_health()
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
            database_health = {"status": "unavailable", "error": str(e)}

        return {
            "status": health_status["status"],
            "health_score": health_status["health_score"],
            "timestamp": datetime.utcnow().isoformat(),
            "application": {
                "name": settings.PROJECT_NAME,
                "version": settings.API_VERSION,
                "environment": settings.ENVIRONMENT,
                "debug": settings.DEBUG,
                "demo_mode": settings.ENABLE_DEMO_MODE
            },
            "database": database_health,
            "services": {
                "total": health_status["total_services"],
                "available": health_status["available_services"],
                "demo_mode": health_status["demo_services"],
                "details": health_status["services"]
            },
            "runtime_services": services_info,
            "configuration": {
                "api_prefix": settings.API_V1_STR,
                "cors_enabled": len(settings.get_cors_origins()) > 0,
                "rate_limiting": {
                    "requests_per_minute": settings.RATE_LIMIT_REQUESTS,
                    "window_seconds": settings.RATE_LIMIT_WINDOW
                }
            }
        }
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@router.get("/health/services", response_model=Dict[str, Any])
async def services_status(request: Request) -> Dict[str, Any]:
    """
    Get status of individual services.
    
    Returns:
        Status information for each service category
    """
    try:
        health_status = get_health_status()
        
        # Organize services by category
        services_by_category = {
            "ai_models": {},
            "search": {},
            "crypto": {},
            "database": {},
            "security": {},
            "core": {}
        }
        
        for service_name, service_info in health_status["services"].items():
            # Categorize services based on name prefix
            if service_name.startswith("ai_"):
                category = "ai_models"
            elif service_name.startswith("search_"):
                category = "search"
            elif service_name.startswith("crypto_"):
                category = "crypto"
            elif service_name.startswith("database_"):
                category = "database"
            elif service_name.startswith("security_"):
                category = "security"
            elif service_name.startswith("core_"):
                category = "core"
            else:
                category = "core"
            
            services_by_category[category][service_name] = service_info
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": health_status["status"],
            "categories": services_by_category,
            "summary": {
                "total_services": health_status["total_services"],
                "available_services": health_status["available_services"],
                "demo_services": health_status["demo_services"],
                "health_score": health_status["health_score"]
            }
        }
    except Exception as e:
        logger.error(f"Services status check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@router.get("/health/service/{service_name}", response_model=Dict[str, Any])
async def individual_service_status(service_name: str) -> Dict[str, Any]:
    """
    Get status of a specific service.
    
    Args:
        service_name: Name of the service to check
        
    Returns:
        Status information for the specified service
    """
    try:
        service_status = get_service_status(service_name)
        
        if not service_status:
            raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
        
        return {
            "service": service_name,
            "status": service_status.status.value,
            "available": service_status.is_valid,
            "message": service_status.message,
            "demo_mode": service_status.demo_mode_enabled,
            "fallback_available": service_status.fallback_available,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Individual service status check failed for {service_name}: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@router.get("/health/ready", response_model=Dict[str, Any])
async def readiness_check(request: Request) -> Dict[str, Any]:
    """
    Kubernetes-style readiness check.
    
    Returns:
        Readiness status for load balancer health checks
    """
    try:
        health_status = get_health_status()
        
        # Consider the service ready if health score is above 30%
        # or if demo mode is enabled (for development)
        is_ready = (
            health_status["health_score"] >= 30 or 
            settings.ENABLE_DEMO_MODE
        )
        
        if not is_ready:
            raise HTTPException(
                status_code=503, 
                detail="Service not ready - insufficient healthy services"
            )
        
        return {
            "status": "ready",
            "health_score": health_status["health_score"],
            "demo_mode": settings.ENABLE_DEMO_MODE,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")


@router.get("/health/live", response_model=Dict[str, Any])
async def liveness_check() -> Dict[str, Any]:
    """
    Kubernetes-style liveness check.
    
    Returns:
        Basic liveness status for container health checks
    """
    try:
        return {
            "status": "alive",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": "unknown"  # Could be enhanced to track actual uptime
        }
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not alive")