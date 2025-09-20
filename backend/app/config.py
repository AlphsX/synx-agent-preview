from pydantic_settings import BaseSettings
from typing import Optional, List
import os
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings with environment validation and fallback support.
    
    This configuration class loads settings from environment variables
    and provides sensible defaults for development and demo mode.
    """
    
    # =============================================================================
    # Environment Configuration
    # =============================================================================
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # =============================================================================
    # Database Configuration
    # =============================================================================
    DATABASE_URL: str = "sqlite+aiosqlite:///./checkmate_spec_preview.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # =============================================================================
    # Security Configuration
    # =============================================================================
    SECRET_KEY: str = "your-super-secret-key-change-in-production-minimum-32-characters"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # =============================================================================
    # AI Model API Keys
    # =============================================================================
    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # =============================================================================
    # Search API Keys
    # =============================================================================
    SERP_API_KEY: Optional[str] = None
    BRAVE_SEARCH_API_KEY: Optional[str] = None
    
    # =============================================================================
    # Cryptocurrency API Keys
    # =============================================================================
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_SECRET_KEY: Optional[str] = None
    
    # =============================================================================
    # Vector Database Configuration
    # =============================================================================
    ARCTIC_MODEL_NAME: str = "Snowflake/snowflake-arctic-embed-m"
    VECTOR_DIMENSION: int = 1024
    MAX_VECTOR_RESULTS: int = 10
    
    # =============================================================================
    # API Configuration
    # =============================================================================
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Agent API"
    API_VERSION: str = "1.0.0"
    
    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    
    # =============================================================================
    # CORS Configuration
    # =============================================================================
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080"
    ]
    
    # =============================================================================
    # Rate Limiting Configuration
    # =============================================================================
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60
    
    # =============================================================================
    # External API Configuration
    # =============================================================================
    EXTERNAL_API_TIMEOUT: int = 30
    SEARCH_API_TIMEOUT: int = 10
    AI_API_TIMEOUT: int = 60
    
    # Retry configuration
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 1
    
    # =============================================================================
    # Logging Configuration
    # =============================================================================
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: str = "logs/ai_agent.log"
    
    # =============================================================================
    # Demo Mode Configuration
    # =============================================================================
    ENABLE_DEMO_MODE: bool = True
    DEMO_RESPONSE_DELAY: float = 1.0
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields from environment
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._setup_logging()
        self._validate_critical_settings()
    
    def _setup_logging(self):
        """Configure application logging."""
        log_level = getattr(logging, self.LOG_LEVEL.upper(), logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(self.LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Configure logging format
        if self.LOG_FORMAT.lower() == "json":
            import json
            class JSONFormatter(logging.Formatter):
                def format(self, record):
                    log_entry = {
                        "timestamp": self.formatTime(record),
                        "level": record.levelname,
                        "logger": record.name,
                        "message": record.getMessage(),
                        "module": record.module,
                        "function": record.funcName,
                        "line": record.lineno
                    }
                    if record.exc_info:
                        log_entry["exception"] = self.formatException(record.exc_info)
                    return json.dumps(log_entry)
            
            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(self.LOG_FILE) if self.LOG_FILE else logging.NullHandler()
            ]
        )
    
    def _validate_critical_settings(self):
        """Validate critical settings and warn about potential issues."""
        # Check SECRET_KEY
        if (self.SECRET_KEY == "your-super-secret-key-change-in-production-minimum-32-characters" 
            and self.ENVIRONMENT == "production"):
            logger.error("CRITICAL: Default SECRET_KEY detected in production environment!")
            raise ValueError("Default SECRET_KEY not allowed in production")
        
        if len(self.SECRET_KEY) < 32:
            logger.warning("SECRET_KEY is shorter than recommended 32 characters")
        
        # Check database URL format
        if not self.DATABASE_URL.startswith(("postgresql://", "postgresql+asyncpg://", "sqlite")):
            logger.warning("DATABASE_URL format not recognized")
        
        # Log environment info
        logger.info(f"Starting {self.PROJECT_NAME} v{self.API_VERSION}")
        logger.info(f"Environment: {self.ENVIRONMENT}")
        logger.info(f"Debug mode: {self.DEBUG}")
        logger.info(f"Demo mode: {self.ENABLE_DEMO_MODE}")
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"
    
    def get_cors_origins(self) -> List[str]:
        """Get CORS origins as a list."""
        if isinstance(self.BACKEND_CORS_ORIGINS, str):
            # Handle string representation of list
            import ast
            try:
                return ast.literal_eval(self.BACKEND_CORS_ORIGINS)
            except (ValueError, SyntaxError):
                return [self.BACKEND_CORS_ORIGINS]
        return self.BACKEND_CORS_ORIGINS


# Global settings instance
settings = Settings()