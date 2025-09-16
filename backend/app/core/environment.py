"""
Environment validation service for AI Agent Backend.

This module provides comprehensive environment validation, graceful fallback handling,
and demo mode capabilities when API keys are missing.
"""

import os
import logging
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service availability status."""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEMO_MODE = "demo_mode"
    FALLBACK = "fallback"


class ServiceCategory(Enum):
    """Categories of services for validation."""
    AI_MODELS = "ai_models"
    SEARCH = "search"
    CRYPTO = "crypto"
    DATABASE = "database"
    SECURITY = "security"
    CORE = "core"


@dataclass
class ValidationResult:
    """Result of environment validation."""
    is_valid: bool
    service: str
    status: ServiceStatus
    message: str
    fallback_available: bool = False
    demo_mode_enabled: bool = False


class EnvironmentValidator:
    """
    Validates environment configuration and provides graceful fallback handling.
    
    This service checks for required API keys and configuration, enables demo mode
    when keys are missing, and provides fallback mechanisms for external services.
    """
    
    def __init__(self):
        self.validation_results: Dict[str, ValidationResult] = {}
        self.demo_mode_enabled = os.getenv("ENABLE_DEMO_MODE", "true").lower() == "true"
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure logging for environment validation."""
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        logging.basicConfig(
            level=getattr(logging, log_level, logging.INFO),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def validate_all(self) -> Dict[str, ValidationResult]:
        """
        Validate all environment configurations.
        
        Returns:
            Dict mapping service names to validation results
        """
        logger.info("Starting comprehensive environment validation...")
        
        # Validate each service category
        self._validate_core_config()
        self._validate_security_config()
        self._validate_database_config()
        self._validate_ai_models()
        self._validate_search_services()
        self._validate_crypto_services()
        
        # Log summary
        self._log_validation_summary()
        
        return self.validation_results
    
    def _validate_core_config(self):
        """Validate core application configuration."""
        required_vars = {
            "ENVIRONMENT": "development",
            "API_V1_STR": "/api/v1",
            "PROJECT_NAME": "AI Agent API"
        }
        
        for var, default in required_vars.items():
            value = os.getenv(var, default)
            if value:
                self.validation_results[f"core_{var.lower()}"] = ValidationResult(
                    is_valid=True,
                    service=f"core_{var.lower()}",
                    status=ServiceStatus.AVAILABLE,
                    message=f"{var} configured: {value}"
                )
            else:
                self.validation_results[f"core_{var.lower()}"] = ValidationResult(
                    is_valid=False,
                    service=f"core_{var.lower()}",
                    status=ServiceStatus.UNAVAILABLE,
                    message=f"{var} not configured"
                )
    
    def _validate_security_config(self):
        """Validate security configuration."""
        secret_key = os.getenv("SECRET_KEY")
        
        if not secret_key or secret_key == "your-super-secret-key-change-in-production-minimum-32-characters":
            self.validation_results["security_jwt"] = ValidationResult(
                is_valid=False,
                service="security_jwt",
                status=ServiceStatus.UNAVAILABLE,
                message="SECRET_KEY not configured or using default value",
                demo_mode_enabled=self.demo_mode_enabled
            )
            if self.demo_mode_enabled:
                logger.warning("Using default SECRET_KEY in demo mode - NOT suitable for production!")
        elif len(secret_key) < 32:
            self.validation_results["security_jwt"] = ValidationResult(
                is_valid=False,
                service="security_jwt",
                status=ServiceStatus.UNAVAILABLE,
                message="SECRET_KEY too short (minimum 32 characters required)"
            )
        else:
            self.validation_results["security_jwt"] = ValidationResult(
                is_valid=True,
                service="security_jwt",
                status=ServiceStatus.AVAILABLE,
                message="JWT security properly configured"
            )
    
    def _validate_database_config(self):
        """Validate database configuration."""
        database_url = os.getenv("DATABASE_URL")
        redis_url = os.getenv("REDIS_URL")
        
        # PostgreSQL validation
        if database_url and "postgresql" in database_url:
            self.validation_results["database_postgres"] = ValidationResult(
                is_valid=True,
                service="database_postgres",
                status=ServiceStatus.AVAILABLE,
                message="PostgreSQL configuration found"
            )
        else:
            self.validation_results["database_postgres"] = ValidationResult(
                is_valid=False,
                service="database_postgres",
                status=ServiceStatus.DEMO_MODE if self.demo_mode_enabled else ServiceStatus.UNAVAILABLE,
                message="PostgreSQL not configured - using in-memory storage" if self.demo_mode_enabled else "PostgreSQL not configured",
                demo_mode_enabled=self.demo_mode_enabled
            )
        
        # Redis validation
        if redis_url and "redis" in redis_url:
            self.validation_results["database_redis"] = ValidationResult(
                is_valid=True,
                service="database_redis",
                status=ServiceStatus.AVAILABLE,
                message="Redis configuration found"
            )
        else:
            self.validation_results["database_redis"] = ValidationResult(
                is_valid=False,
                service="database_redis",
                status=ServiceStatus.DEMO_MODE if self.demo_mode_enabled else ServiceStatus.UNAVAILABLE,
                message="Redis not configured - using in-memory cache" if self.demo_mode_enabled else "Redis not configured",
                demo_mode_enabled=self.demo_mode_enabled
            )
    
    def _validate_ai_models(self):
        """Validate AI model API configurations."""
        ai_services = {
            "groq": "GROQ_API_KEY",
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY"
        }
        
        available_services = []
        
        for service, env_var in ai_services.items():
            api_key = os.getenv(env_var)
            
            if api_key and api_key != f"your_{service}_api_key_here":
                self.validation_results[f"ai_{service}"] = ValidationResult(
                    is_valid=True,
                    service=f"ai_{service}",
                    status=ServiceStatus.AVAILABLE,
                    message=f"{service.title()} API key configured"
                )
                available_services.append(service)
            else:
                self.validation_results[f"ai_{service}"] = ValidationResult(
                    is_valid=False,
                    service=f"ai_{service}",
                    status=ServiceStatus.DEMO_MODE if self.demo_mode_enabled else ServiceStatus.UNAVAILABLE,
                    message=f"{service.title()} API key not configured - using mock responses" if self.demo_mode_enabled else f"{service.title()} API key not configured",
                    demo_mode_enabled=self.demo_mode_enabled
                )
        
        # Check if at least one AI service is available
        if not available_services and not self.demo_mode_enabled:
            logger.error("No AI model APIs configured and demo mode disabled!")
        elif available_services:
            logger.info(f"Available AI services: {', '.join(available_services)}")
    
    def _validate_search_services(self):
        """Validate search service API configurations."""
        serp_key = os.getenv("SERP_API_KEY")
        brave_key = os.getenv("BRAVE_SEARCH_API_KEY")
        
        # SerpAPI (Primary)
        if serp_key and serp_key != "your_serpapi_key_here":
            self.validation_results["search_serp"] = ValidationResult(
                is_valid=True,
                service="search_serp",
                status=ServiceStatus.AVAILABLE,
                message="SerpAPI configured (primary search service)"
            )
        else:
            fallback_available = brave_key and brave_key != "your_brave_search_api_key_here"
            self.validation_results["search_serp"] = ValidationResult(
                is_valid=False,
                service="search_serp",
                status=ServiceStatus.FALLBACK if fallback_available else (ServiceStatus.DEMO_MODE if self.demo_mode_enabled else ServiceStatus.UNAVAILABLE),
                message="SerpAPI not configured - using Brave Search fallback" if fallback_available else ("SerpAPI not configured - using mock search" if self.demo_mode_enabled else "SerpAPI not configured"),
                fallback_available=fallback_available,
                demo_mode_enabled=self.demo_mode_enabled
            )
        
        # Brave Search (Fallback)
        if brave_key and brave_key != "your_brave_search_api_key_here":
            self.validation_results["search_brave"] = ValidationResult(
                is_valid=True,
                service="search_brave",
                status=ServiceStatus.AVAILABLE,
                message="Brave Search API configured (fallback service)"
            )
        else:
            self.validation_results["search_brave"] = ValidationResult(
                is_valid=False,
                service="search_brave",
                status=ServiceStatus.DEMO_MODE if self.demo_mode_enabled else ServiceStatus.UNAVAILABLE,
                message="Brave Search not configured - using mock search" if self.demo_mode_enabled else "Brave Search not configured",
                demo_mode_enabled=self.demo_mode_enabled
            )
    
    def _validate_crypto_services(self):
        """Validate cryptocurrency service API configurations."""
        binance_key = os.getenv("BINANCE_API_KEY")
        binance_secret = os.getenv("BINANCE_SECRET_KEY")
        
        if (binance_key and binance_key != "your_binance_api_key_here" and 
            binance_secret and binance_secret != "your_binance_secret_key_here"):
            self.validation_results["crypto_binance"] = ValidationResult(
                is_valid=True,
                service="crypto_binance",
                status=ServiceStatus.AVAILABLE,
                message="Binance API configured"
            )
        else:
            self.validation_results["crypto_binance"] = ValidationResult(
                is_valid=False,
                service="crypto_binance",
                status=ServiceStatus.DEMO_MODE if self.demo_mode_enabled else ServiceStatus.UNAVAILABLE,
                message="Binance API not configured - using mock crypto data" if self.demo_mode_enabled else "Binance API not configured",
                demo_mode_enabled=self.demo_mode_enabled
            )
    
    def _log_validation_summary(self):
        """Log a summary of validation results."""
        available = sum(1 for r in self.validation_results.values() if r.status == ServiceStatus.AVAILABLE)
        demo_mode = sum(1 for r in self.validation_results.values() if r.status == ServiceStatus.DEMO_MODE)
        unavailable = sum(1 for r in self.validation_results.values() if r.status == ServiceStatus.UNAVAILABLE)
        fallback = sum(1 for r in self.validation_results.values() if r.status == ServiceStatus.FALLBACK)
        
        logger.info(f"Environment validation complete:")
        logger.info(f"  ✅ Available: {available}")
        logger.info(f"  🔄 Fallback: {fallback}")
        logger.info(f"  🎭 Demo mode: {demo_mode}")
        logger.info(f"  ❌ Unavailable: {unavailable}")
        
        if demo_mode > 0:
            logger.warning(f"Running in demo mode for {demo_mode} services - some features will use mock data")
    
    def get_service_status(self, service_name: str) -> Optional[ValidationResult]:
        """Get validation result for a specific service."""
        return self.validation_results.get(service_name)
    
    def is_service_available(self, service_name: str) -> bool:
        """Check if a service is available (not in demo mode or unavailable)."""
        result = self.get_service_status(service_name)
        return result is not None and result.status == ServiceStatus.AVAILABLE
    
    def is_demo_mode_enabled(self, service_name: str) -> bool:
        """Check if a service is running in demo mode."""
        result = self.get_service_status(service_name)
        return result is not None and result.status == ServiceStatus.DEMO_MODE
    
    def get_available_ai_models(self) -> List[str]:
        """Get list of available AI model services."""
        available_models = []
        ai_services = ["groq", "openai", "anthropic"]
        
        for service in ai_services:
            if self.is_service_available(f"ai_{service}"):
                available_models.append(service)
        
        return available_models
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status."""
        total_services = len(self.validation_results)
        available_services = sum(1 for r in self.validation_results.values() if r.status == ServiceStatus.AVAILABLE)
        demo_services = sum(1 for r in self.validation_results.values() if r.status == ServiceStatus.DEMO_MODE)
        
        health_score = (available_services / total_services) * 100 if total_services > 0 else 0
        
        return {
            "status": "healthy" if health_score >= 70 else "degraded" if health_score >= 30 else "unhealthy",
            "health_score": round(health_score, 2),
            "total_services": total_services,
            "available_services": available_services,
            "demo_services": demo_services,
            "demo_mode_enabled": self.demo_mode_enabled,
            "services": {
                name: {
                    "status": result.status.value,
                    "message": result.message,
                    "demo_mode": result.demo_mode_enabled,
                    "fallback_available": result.fallback_available
                }
                for name, result in self.validation_results.items()
            }
        }


# Global environment validator instance
env_validator = EnvironmentValidator()


def validate_environment() -> Dict[str, ValidationResult]:
    """Validate environment configuration and return results."""
    return env_validator.validate_all()


def get_service_status(service_name: str) -> Optional[ValidationResult]:
    """Get validation result for a specific service."""
    return env_validator.get_service_status(service_name)


def is_service_available(service_name: str) -> bool:
    """Check if a service is available."""
    return env_validator.is_service_available(service_name)


def is_demo_mode_enabled(service_name: str) -> bool:
    """Check if a service is running in demo mode."""
    return env_validator.is_demo_mode_enabled(service_name)


def get_health_status() -> Dict[str, Any]:
    """Get overall system health status."""
    return env_validator.get_health_status()