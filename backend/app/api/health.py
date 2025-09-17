"""
Health check endpoints for monitoring system status.

This module provides comprehensive health check endpoints for:
- Overall system health
- Individual service health
- Error metrics and monitoring
- Performance statistics
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..core.health_checks import health_check_service, HealthStatus
from ..core.error_handling import error_metrics, ServiceType, ErrorSeverity
from ..core.logging_middleware import performance_logger

router = APIRouter()


@router.get("/health", summary="Overall system health check")
async def get_system_health(
    force_refresh: bool = Query(False, description="Force refresh of cached health data")
) -> Dict[str, Any]:
    """
    Get overall system health status.
    
    Returns comprehensive health information including:
    - Overall system status
    - Individual service statuses
    - Health summary and metrics
    """
    try:
        health_data = await health_check_service.check_all_services(force_refresh=force_refresh)
        
        return {
            "status": "success",
            "data": health_data,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Health check failed",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@router.get("/health/services/{service_name}", summary="Individual service health check")
async def get_service_health(
    service_name: str,
    force_refresh: bool = Query(False, description="Force refresh of cached health data")
) -> Dict[str, Any]:
    """
    Get health status for a specific service.
    
    Args:
        service_name: Name of the service to check (e.g., 'ai_groq', 'search_serpapi')
        force_refresh: Whether to force refresh cached data
    """
    try:
        health_check = await health_check_service.check_service(service_name, force_refresh=force_refresh)
        
        return {
            "status": "success",
            "data": health_check.to_dict(),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"Health check failed for service {service_name}",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@router.get("/health/ai", summary="AI services health check")
async def get_ai_services_health(
    force_refresh: bool = Query(False, description="Force refresh of cached health data")
) -> Dict[str, Any]:
    """Get health status for all AI services."""
    try:
        all_health = await health_check_service.check_all_services(force_refresh=force_refresh)
        
        # Filter AI services
        ai_services = {
            name: service for name, service in all_health["services"].items()
            if name.startswith("ai_")
        }
        
        # Calculate AI-specific overall status
        ai_statuses = [service["status"] for service in ai_services.values()]
        healthy_count = sum(1 for status in ai_statuses if status == "healthy")
        
        if healthy_count == len(ai_statuses):
            overall_status = "healthy"
        elif healthy_count > 0:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        return {
            "status": "success",
            "data": {
                "overall_status": overall_status,
                "services": ai_services,
                "summary": {
                    "total_services": len(ai_services),
                    "healthy_services": healthy_count,
                    "available_models": sum(
                        service.get("details", {}).get("model_count", 0)
                        for service in ai_services.values()
                        if service["status"] == "healthy"
                    )
                }
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "AI services health check failed",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@router.get("/health/search", summary="Search services health check")
async def get_search_services_health(
    force_refresh: bool = Query(False, description="Force refresh of cached health data")
) -> Dict[str, Any]:
    """Get health status for all search services."""
    try:
        all_health = await health_check_service.check_all_services(force_refresh=force_refresh)
        
        # Filter search services
        search_services = {
            name: service for name, service in all_health["services"].items()
            if name.startswith("search_")
        }
        
        # Calculate search-specific overall status
        search_statuses = [service["status"] for service in search_services.values()]
        healthy_count = sum(1 for status in search_statuses if status == "healthy")
        
        if healthy_count == len(search_statuses):
            overall_status = "healthy"
        elif healthy_count > 0:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        return {
            "status": "success",
            "data": {
                "overall_status": overall_status,
                "services": search_services,
                "summary": {
                    "total_services": len(search_services),
                    "healthy_services": healthy_count,
                    "primary_provider": "serpapi" if search_services.get("search_serpapi", {}).get("status") == "healthy" else "brave",
                    "fallback_available": search_services.get("search_brave", {}).get("status") == "healthy"
                }
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Search services health check failed",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@router.get("/health/database", summary="Database services health check")
async def get_database_services_health(
    force_refresh: bool = Query(False, description="Force refresh of cached health data")
) -> Dict[str, Any]:
    """Get health status for all database services."""
    try:
        all_health = await health_check_service.check_all_services(force_refresh=force_refresh)
        
        # Filter database services
        database_services = {
            name: service for name, service in all_health["services"].items()
            if name.startswith(("database_", "vector_"))
        }
        
        return {
            "status": "success",
            "data": {
                "services": database_services,
                "summary": {
                    "postgresql_available": database_services.get("database_postgresql", {}).get("status") == "healthy",
                    "redis_available": database_services.get("database_redis", {}).get("status") == "healthy",
                    "vector_db_available": database_services.get("vector_database", {}).get("status") == "healthy"
                }
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Database services health check failed",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@router.get("/health/errors", summary="Error metrics and monitoring")
async def get_error_metrics(
    hours: int = Query(24, ge=1, le=168, description="Number of hours to include in error summary")
) -> Dict[str, Any]:
    """
    Get error metrics and monitoring data.
    
    Args:
        hours: Number of hours to include in the error summary (1-168 hours)
    """
    try:
        error_summary = error_metrics.get_error_summary(hours=hours)
        service_health = error_metrics.get_service_health()
        
        return {
            "status": "success",
            "data": {
                "error_summary": error_summary,
                "service_health": service_health,
                "monitoring_period_hours": hours
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Error metrics retrieval failed",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@router.post("/health/errors/reset", summary="Reset error metrics")
async def reset_error_metrics() -> Dict[str, Any]:
    """Reset all error metrics and health tracking."""
    try:
        error_metrics.reset_metrics()
        health_check_service.clear_cache()
        
        return {
            "status": "success",
            "message": "Error metrics and health cache reset successfully",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Error metrics reset failed",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@router.get("/health/performance", summary="Performance metrics")
async def get_performance_metrics() -> Dict[str, Any]:
    """Get system performance metrics."""
    try:
        # This is a placeholder for performance metrics
        # In a real implementation, you would collect metrics from various sources
        
        return {
            "status": "success",
            "data": {
                "message": "Performance metrics endpoint - implementation depends on your monitoring setup",
                "suggestions": [
                    "Integrate with Prometheus for metrics collection",
                    "Use APM tools like New Relic or DataDog",
                    "Implement custom metrics collection in performance_logger",
                    "Add database query performance tracking",
                    "Monitor AI model response times",
                    "Track external API latencies"
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Performance metrics retrieval failed",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@router.get("/health/status", summary="Simple health status")
async def get_simple_health_status() -> Dict[str, Any]:
    """
    Simple health status endpoint for load balancers and monitoring tools.
    
    Returns a simple status that can be used by external monitoring systems.
    """
    try:
        health_data = await health_check_service.check_all_services()
        overall_status = health_data["overall_status"]
        
        # Map internal status to simple HTTP status codes
        if overall_status == "healthy":
            status_code = 200
            message = "System is healthy"
        elif overall_status == "degraded":
            status_code = 200  # Still operational but degraded
            message = "System is operational but degraded"
        else:
            status_code = 503  # Service unavailable
            message = "System is unhealthy"
        
        return {
            "status": overall_status,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "uptime": "Available",  # Could be calculated from startup time
            "version": "1.0.0"  # Could be from settings
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "message": f"Health check failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )


@router.get("/health/readiness", summary="Readiness probe")
async def readiness_probe() -> Dict[str, Any]:
    """
    Kubernetes-style readiness probe.
    
    Checks if the application is ready to serve traffic.
    """
    try:
        # Check critical services only
        health_data = await health_check_service.check_all_services()
        
        # Define critical services that must be healthy for readiness
        critical_services = ["database_postgresql"]  # Add other critical services as needed
        
        critical_health = {}
        for service_name in critical_services:
            if service_name in health_data["services"]:
                critical_health[service_name] = health_data["services"][service_name]["status"]
        
        # Check if all critical services are healthy
        all_critical_healthy = all(
            status == "healthy" for status in critical_health.values()
        )
        
        if all_critical_healthy:
            return {
                "status": "ready",
                "message": "Application is ready to serve traffic",
                "critical_services": critical_health,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "not_ready",
                    "message": "Critical services are not healthy",
                    "critical_services": critical_health,
                    "timestamp": datetime.now().isoformat()
                }
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "message": f"Readiness check failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )


@router.get("/health/liveness", summary="Liveness probe")
async def liveness_probe() -> Dict[str, Any]:
    """
    Kubernetes-style liveness probe.
    
    Checks if the application is alive and should not be restarted.
    """
    try:
        # Simple check to ensure the application is responsive
        # This should be a lightweight check
        
        return {
            "status": "alive",
            "message": "Application is alive and responsive",
            "timestamp": datetime.now().isoformat(),
            "pid": "available"  # Could include actual process ID
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Liveness check failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )