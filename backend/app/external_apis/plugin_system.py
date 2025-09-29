import asyncio
import importlib
import inspect
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type, Callable, Union
from datetime import datetime
from pathlib import Path
from app.config import settings
from ..core.error_handling import (
    retry_with_backoff, RetryConfig, ServiceType, ErrorCode, ErrorSeverity, error_metrics
)
from ..core.logging_middleware import external_api_logger

logger = logging.getLogger(__name__)


class DataSourcePlugin(ABC):
    """
    Abstract base class for data source plugins.
    All custom data source plugins must inherit from this class.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = self.__class__.__name__
        self.version = getattr(self, 'VERSION', '1.0.0')
        self.description = getattr(self, 'DESCRIPTION', 'Custom data source plugin')
        self.author = getattr(self, 'AUTHOR', 'Unknown')
        
        # Plugin metadata
        self.metadata = {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'supported_operations': self.get_supported_operations(),
            'required_config': self.get_required_config(),
            'optional_config': self.get_optional_config()
        }
        
        # Initialize plugin
        self._initialize()
    
    @abstractmethod
    async def fetch_data(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Fetch data from the external source.
        
        Args:
            query: The search query or identifier
            **kwargs: Additional parameters specific to the data source
            
        Returns:
            Dictionary containing the fetched data
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the data source is available and properly configured.
        
        Returns:
            True if available, False otherwise
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the data source.
        
        Returns:
            Health status information
        """
        pass
    
    def get_supported_operations(self) -> List[str]:
        """
        Get list of supported operations for this plugin.
        Override in subclass to specify supported operations.
        
        Returns:
            List of operation names
        """
        return ['fetch_data']
    
    def get_required_config(self) -> List[str]:
        """
        Get list of required configuration keys.
        Override in subclass to specify required config.
        
        Returns:
            List of required configuration keys
        """
        return []
    
    def get_optional_config(self) -> List[str]:
        """
        Get list of optional configuration keys.
        Override in subclass to specify optional config.
        
        Returns:
            List of optional configuration keys
        """
        return []
    
    def _initialize(self):
        """
        Initialize the plugin. Override in subclass for custom initialization.
        """
        pass
    
    def validate_config(self) -> bool:
        """
        Validate the plugin configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        required_keys = self.get_required_config()
        
        for key in required_keys:
            if key not in self.config:
                logger.error(f"Plugin {self.name}: Missing required config key '{key}'")
                return False
        
        return True
    
    async def execute_with_retry(
        self, 
        operation: Callable, 
        *args, 
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute an operation with retry logic.
        
        Args:
            operation: The operation to execute
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            Operation result
        """
        retry_config = RetryConfig(
            max_retries=3,
            base_delay=1.0,
            max_delay=30.0,
            exponential_base=2.0,
            jitter=True
        )
        
        try:
            return await retry_with_backoff(
                operation,
                retry_config,
                ServiceType.EXTERNAL_API,
                *args,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Plugin {self.name} operation failed: {str(e)}")
            raise


class PluginManager:
    """
    Manager for data source plugins. Handles plugin loading, registration,
    and execution of plugin operations.
    """
    
    def __init__(self):
        self.plugins: Dict[str, DataSourcePlugin] = {}
        self.plugin_configs: Dict[str, Dict[str, Any]] = {}
        self.plugin_directory = Path(__file__).parent / "plugins"
        
        # Create plugins directory if it doesn't exist
        self.plugin_directory.mkdir(exist_ok=True)
        
        # Load plugin configurations
        self._load_plugin_configs()
        
        # Auto-load plugins
        self._auto_load_plugins()
    
    def register_plugin(self, plugin: DataSourcePlugin, name: str = None) -> bool:
        """
        Register a data source plugin.
        
        Args:
            plugin: The plugin instance to register
            name: Optional custom name for the plugin
            
        Returns:
            True if registration successful, False otherwise
        """
        plugin_name = name or plugin.name
        
        try:
            # Validate plugin
            if not isinstance(plugin, DataSourcePlugin):
                logger.error(f"Plugin {plugin_name} must inherit from DataSourcePlugin")
                return False
            
            if not plugin.validate_config():
                logger.error(f"Plugin {plugin_name} configuration validation failed")
                return False
            
            # Check if plugin is available
            if not plugin.is_available():
                logger.warning(f"Plugin {plugin_name} is not available, registering anyway")
            
            # Register plugin
            self.plugins[plugin_name] = plugin
            logger.info(f"Successfully registered plugin: {plugin_name}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to register plugin {plugin_name}: {str(e)}")
            return False
    
    def unregister_plugin(self, name: str) -> bool:
        """
        Unregister a data source plugin.
        
        Args:
            name: Name of the plugin to unregister
            
        Returns:
            True if unregistration successful, False otherwise
        """
        if name in self.plugins:
            del self.plugins[name]
            logger.info(f"Successfully unregistered plugin: {name}")
            return True
        else:
            logger.warning(f"Plugin {name} not found for unregistration")
            return False
    
    async def execute_plugin(
        self, 
        plugin_name: str, 
        operation: str, 
        *args, 
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute an operation on a specific plugin.
        
        Args:
            plugin_name: Name of the plugin to execute
            operation: Operation to perform
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            Operation result
        """
        if plugin_name not in self.plugins:
            return {"error": f"Plugin '{plugin_name}' not found"}
        
        plugin = self.plugins[plugin_name]
        
        if not plugin.is_available():
            return {"error": f"Plugin '{plugin_name}' is not available"}
        
        # Start external API call tracking
        call_id = external_api_logger.start_call(
            service_name=f"plugin_{plugin_name}",
            method="EXECUTE",
            url=operation,
            request_data={"args": args, "kwargs": kwargs}
        )
        
        try:
            # Check if operation is supported
            if operation not in plugin.get_supported_operations():
                return {"error": f"Operation '{operation}' not supported by plugin '{plugin_name}'"}
            
            # Execute operation
            if operation == "fetch_data":
                result = await plugin.fetch_data(*args, **kwargs)
            elif operation == "health_check":
                result = await plugin.health_check()
            else:
                # Try to call the operation method directly
                if hasattr(plugin, operation):
                    method = getattr(plugin, operation)
                    if asyncio.iscoroutinefunction(method):
                        result = await method(*args, **kwargs)
                    else:
                        result = method(*args, **kwargs)
                else:
                    return {"error": f"Operation '{operation}' not implemented by plugin '{plugin_name}'"}
            
            # Add plugin metadata to result
            if isinstance(result, dict) and "error" not in result:
                result["_plugin_info"] = {
                    "name": plugin_name,
                    "version": plugin.version,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Finish tracking successful call
            external_api_logger.finish_call(
                call_id=call_id,
                status_code=200,
                response_data={"plugin": plugin_name, "operation": operation}
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Plugin {plugin_name} operation {operation} failed: {str(e)}")
            
            # Record error metrics
            error_metrics.record_error(
                service=ServiceType.EXTERNAL_API,
                error_code=ErrorCode.API_UNAVAILABLE,
                severity=ErrorSeverity.MEDIUM,
                details={
                    "plugin": plugin_name,
                    "operation": operation,
                    "error": str(e)
                }
            )
            
            # Finish tracking failed call
            external_api_logger.finish_call(call_id=call_id, error=e)
            
            return {"error": f"Plugin execution failed: {str(e)}"}
    
    async def execute_all_plugins(
        self, 
        operation: str, 
        *args, 
        **kwargs
    ) -> Dict[str, Dict[str, Any]]:
        """
        Execute an operation on all available plugins.
        
        Args:
            operation: Operation to perform
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            Dictionary with plugin names as keys and results as values
        """
        results = {}
        
        # Get available plugins that support the operation
        available_plugins = [
            (name, plugin) for name, plugin in self.plugins.items()
            if plugin.is_available() and operation in plugin.get_supported_operations()
        ]
        
        if not available_plugins:
            return {"error": "No available plugins support this operation"}
        
        # Execute operation on all plugins concurrently
        tasks = [
            self.execute_plugin(name, operation, *args, **kwargs)
            for name, plugin in available_plugins
        ]
        
        plugin_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        for i, (name, plugin) in enumerate(available_plugins):
            result = plugin_results[i]
            if isinstance(result, Exception):
                results[name] = {"error": f"Plugin execution failed: {str(result)}"}
            else:
                results[name] = result
        
        return results
    
    def get_plugin_info(self, plugin_name: str = None) -> Dict[str, Any]:
        """
        Get information about plugins.
        
        Args:
            plugin_name: Specific plugin name, or None for all plugins
            
        Returns:
            Plugin information
        """
        if plugin_name:
            if plugin_name in self.plugins:
                plugin = self.plugins[plugin_name]
                return {
                    "name": plugin_name,
                    "metadata": plugin.metadata,
                    "available": plugin.is_available(),
                    "config_valid": plugin.validate_config()
                }
            else:
                return {"error": f"Plugin '{plugin_name}' not found"}
        else:
            # Return info for all plugins
            plugins_info = {}
            for name, plugin in self.plugins.items():
                plugins_info[name] = {
                    "metadata": plugin.metadata,
                    "available": plugin.is_available(),
                    "config_valid": plugin.validate_config()
                }
            
            return {
                "total_plugins": len(self.plugins),
                "available_plugins": sum(1 for p in self.plugins.values() if p.is_available()),
                "plugins": plugins_info
            }
    
    async def health_check_all_plugins(self) -> Dict[str, Any]:
        """
        Perform health checks on all plugins.
        
        Returns:
            Health status for all plugins
        """
        health_results = {}
        
        for name, plugin in self.plugins.items():
            try:
                health_result = await plugin.health_check()
                health_results[name] = health_result
            except Exception as e:
                health_results[name] = {
                    "status": "error",
                    "message": f"Health check failed: {str(e)}",
                    "service": name
                }
        
        # Calculate overall health
        healthy_count = sum(
            1 for result in health_results.values()
            if result.get("status") == "healthy"
        )
        total_count = len(health_results)
        
        if healthy_count == total_count:
            overall_status = "healthy"
        elif healthy_count > 0:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        return {
            "overall_status": overall_status,
            "total_plugins": total_count,
            "healthy_plugins": healthy_count,
            "plugin_health": health_results,
            "timestamp": datetime.now().isoformat()
        }
    
    def _load_plugin_configs(self):
        """Load plugin configurations from settings."""
        # Load from environment or config file
        plugin_configs = getattr(settings, 'PLUGIN_CONFIGS', {})
        self.plugin_configs = plugin_configs
        logger.info(f"Loaded configurations for {len(plugin_configs)} plugins")
    
    def _auto_load_plugins(self):
        """Automatically load plugins from the plugins directory."""
        if not self.plugin_directory.exists():
            return
        
        # Look for Python files in the plugins directory
        for plugin_file in self.plugin_directory.glob("*.py"):
            if plugin_file.name.startswith("__"):
                continue
            
            try:
                self._load_plugin_from_file(plugin_file)
            except Exception as e:
                logger.error(f"Failed to load plugin from {plugin_file}: {str(e)}")
    
    def _load_plugin_from_file(self, plugin_file: Path):
        """Load a plugin from a Python file."""
        module_name = plugin_file.stem
        spec = importlib.util.spec_from_file_location(module_name, plugin_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find plugin classes in the module
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, DataSourcePlugin) and 
                obj != DataSourcePlugin):
                
                # Get plugin config
                plugin_config = self.plugin_configs.get(name, {})
                
                # Create plugin instance
                plugin_instance = obj(plugin_config)
                
                # Register plugin
                self.register_plugin(plugin_instance, name)
                logger.info(f"Auto-loaded plugin: {name} from {plugin_file}")


# Example plugin implementations

class NewsAPIPlugin(DataSourcePlugin):
    """Example plugin for News API integration."""
    
    VERSION = "1.0.0"
    DESCRIPTION = "News API data source plugin"
    AUTHOR = "AI Agent Team"
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.api_key = self.config.get('api_key')
        self.base_url = "https://newsapi.org/v2"
    
    async def fetch_data(self, query: str, **kwargs) -> Dict[str, Any]:
        """Fetch news articles from News API."""
        if not self.is_available():
            return {"error": "News API key not configured"}
        
        try:
            import aiohttp
            
            params = {
                "q": query,
                "apiKey": self.api_key,
                "pageSize": kwargs.get("limit", 10),
                "sortBy": kwargs.get("sort_by", "publishedAt")
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/everything", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        articles = []
                        for article in data.get("articles", []):
                            articles.append({
                                "title": article.get("title", ""),
                                "description": article.get("description", ""),
                                "url": article.get("url", ""),
                                "published_at": article.get("publishedAt", ""),
                                "source": article.get("source", {}).get("name", ""),
                                "author": article.get("author", "")
                            })
                        
                        return {
                            "query": query,
                            "articles": articles,
                            "total_results": data.get("totalResults", 0),
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        return {"error": f"News API returned status {response.status}"}
        
        except Exception as e:
            return {"error": f"Failed to fetch news data: {str(e)}"}
    
    def is_available(self) -> bool:
        """Check if News API is available."""
        return bool(self.api_key)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on News API."""
        if not self.is_available():
            return {
                "status": "unavailable",
                "message": "API key not configured",
                "service": "News API"
            }
        
        try:
            import aiohttp
            
            params = {
                "q": "test",
                "apiKey": self.api_key,
                "pageSize": 1
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{self.base_url}/everything", params=params) as response:
                    if response.status == 200:
                        return {
                            "status": "healthy",
                            "message": "Service operational",
                            "service": "News API"
                        }
                    else:
                        return {
                            "status": "error",
                            "message": f"HTTP {response.status}",
                            "service": "News API"
                        }
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Health check failed: {str(e)}",
                "service": "News API"
            }
    
    def get_required_config(self) -> List[str]:
        """Get required configuration keys."""
        return ["api_key"]
    
    def get_supported_operations(self) -> List[str]:
        """Get supported operations."""
        return ["fetch_data", "health_check"]


# Global plugin manager instance
plugin_manager = PluginManager()