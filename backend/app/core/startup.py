"""
Application startup and initialization module.

This module handles application startup, environment validation,
and service initialization with graceful fallback handling.
"""

import logging
from typing import Dict, Any
from fastapi import FastAPI

from .environment import validate_environment, get_health_status
from ..config import settings
from ..database.connection import initialize_database, close_database, check_database_health
from ..database.migrations import run_migrations

logger = logging.getLogger(__name__)


async def startup_handler(app: FastAPI) -> None:
    """
    Handle application startup tasks.
    
    This function is called when the FastAPI application starts up.
    It validates the environment, initializes services, and sets up
    the application state.
    
    Args:
        app: FastAPI application instance
    """
    logger.info("Starting AI Agent Backend...")
    
    # Validate environment configuration
    logger.info("Validating environment configuration...")
    validation_results = validate_environment()
    
    # Store validation results in app state
    app.state.environment_validation = validation_results
    app.state.health_status = get_health_status()
    
    # Log startup summary
    health_status = app.state.health_status
    logger.info(f"Environment validation complete:")
    logger.info(f"  Status: {health_status['status']}")
    logger.info(f"  Health Score: {health_status['health_score']}%")
    logger.info(f"  Available Services: {health_status['available_services']}")
    logger.info(f"  Demo Mode Services: {health_status['demo_services']}")
    
    # Initialize database connections
    await _initialize_database()
    
    # Initialize services based on validation results
    await _initialize_services(app, validation_results)
    
    logger.info("AI Agent Backend startup complete!")


async def shutdown_handler(app: FastAPI) -> None:
    """
    Handle application shutdown tasks.
    
    This function is called when the FastAPI application shuts down.
    It performs cleanup tasks and closes connections.
    
    Args:
        app: FastAPI application instance
    """
    logger.info("Shutting down AI Agent Backend...")
    
    # Close database connections
    await close_database()
    
    # Other cleanup tasks would go here
    # For example: stopping background tasks, etc.
    
    logger.info("AI Agent Backend shutdown complete!")


async def _initialize_services(app: FastAPI, validation_results: Dict[str, Any]) -> None:
    """
    Initialize application services based on validation results.
    
    Args:
        app: FastAPI application instance
        validation_results: Environment validation results
    """
    # Initialize service states
    app.state.services = {
        "ai_models": [],
        "search_providers": [],
        "crypto_providers": [],
        "database_available": False,
        "cache_available": False
    }
    
    # Check AI model availability
    ai_services = ["groq", "openai", "anthropic"]
    for service in ai_services:
        result = validation_results.get(f"ai_{service}")
        if result and result.is_valid:
            app.state.services["ai_models"].append(service)
            logger.info(f"✅ {service.title()} AI service available")
        elif result and result.demo_mode_enabled:
            app.state.services["ai_models"].append(f"{service}_demo")
            logger.info(f"🎭 {service.title()} AI service in demo mode")
    
    # Check search service availability
    search_services = [("serp", "SerpAPI"), ("brave", "Brave Search")]
    for service_key, service_name in search_services:
        result = validation_results.get(f"search_{service_key}")
        if result and result.is_valid:
            app.state.services["search_providers"].append(service_key)
            logger.info(f"✅ {service_name} available")
        elif result and result.demo_mode_enabled:
            app.state.services["search_providers"].append(f"{service_key}_demo")
            logger.info(f"🎭 {service_name} in demo mode")
    
    # Check crypto service availability
    result = validation_results.get("crypto_binance")
    if result and result.is_valid:
        app.state.services["crypto_providers"].append("binance")
        logger.info("✅ Binance crypto service available")
    elif result and result.demo_mode_enabled:
        app.state.services["crypto_providers"].append("binance_demo")
        logger.info("🎭 Binance crypto service in demo mode")
    
    # Check database availability
    postgres_result = validation_results.get("database_postgres")
    if postgres_result and postgres_result.is_valid:
        app.state.services["database_available"] = True
        logger.info("✅ PostgreSQL database available")
    else:
        logger.info("🎭 Database in demo mode (in-memory storage)")
    
    # Check cache availability
    redis_result = validation_results.get("database_redis")
    if redis_result and redis_result.is_valid:
        app.state.services["cache_available"] = True
        logger.info("✅ Redis cache available")
    else:
        logger.info("🎭 Cache in demo mode (in-memory cache)")
    
    # Log service summary
    total_services = len(app.state.services["ai_models"]) + len(app.state.services["search_providers"]) + len(app.state.services["crypto_providers"])
    demo_services = sum(1 for services in app.state.services.values() 
                       if isinstance(services, list) 
                       for service in services 
                       if "_demo" in str(service))
    
    logger.info(f"Service initialization complete:")
    logger.info(f"  Total services: {total_services}")
    logger.info(f"  Demo mode services: {demo_services}")
    logger.info(f"  AI models: {app.state.services['ai_models']}")
    logger.info(f"  Search providers: {app.state.services['search_providers']}")
    logger.info(f"  Crypto providers: {app.state.services['crypto_providers']}")


async def _initialize_database() -> None:
    """Initialize database connections and run migrations."""
    try:
        logger.info("Initializing database connections...")
        
        # Initialize database connections
        await initialize_database()
        
        # Check database health
        health = await check_database_health()
        if health["status"] == "healthy":
            logger.info("✅ Database connections established successfully")
            
            # Run migrations
            logger.info("Running database migrations...")
            await run_migrations()
            logger.info("✅ Database migrations completed")
        else:
            logger.warning(f"⚠️ Database health check failed: {health}")
            
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        logger.info("🎭 Continuing in demo mode without database")


def get_startup_info() -> Dict[str, Any]:
    """
    Get application startup information.
    
    Returns:
        Dictionary containing startup information
    """
    return {
        "application": settings.PROJECT_NAME,
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "demo_mode": settings.ENABLE_DEMO_MODE,
        "api_prefix": settings.API_V1_STR,
        "cors_origins": settings.get_cors_origins(),
        "startup_timestamp": None  # Will be set during startup
    }