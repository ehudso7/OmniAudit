"""
Plugin Manager - Core Orchestration

Manages the lifecycle of all plugins (collectors, analyzers, reporters).
Handles loading, validation, execution, and unloading.
"""

from typing import Dict, Any, List, Optional, Type
from pathlib import Path
import importlib
import inspect
from datetime import datetime

from .exceptions import PluginError, PluginLoadError, PluginExecutionError
from ..collectors.base import BaseCollector
from ..utils.logger import get_logger

logger = get_logger(__name__)


class PluginManager:
    """
    Manages plugin lifecycle and execution.

    Responsibilities:
    - Discover and load plugins
    - Validate plugin interfaces
    - Execute plugins with dependency injection
    - Handle plugin errors gracefully
    - Unload plugins and cleanup resources

    Example:
        >>> manager = PluginManager()
        >>> manager.register_plugin(GitCollector)
        >>> result = manager.execute_plugin("git_collector", config)
    """

    def __init__(self):
        """Initialize the plugin manager."""
        self._plugins: Dict[str, Type[BaseCollector]] = {}
        self._loaded_instances: Dict[str, BaseCollector] = {}
        logger.info("PluginManager initialized")

    def register_plugin(self, plugin_class: Type[BaseCollector]) -> None:
        """
        Register a plugin class.

        Args:
            plugin_class: Class that inherits from BaseCollector

        Raises:
            PluginError: If plugin is invalid
        """
        # Validate plugin interface
        if not inspect.isclass(plugin_class):
            raise PluginError(f"Plugin must be a class: {plugin_class}")

        if not issubclass(plugin_class, BaseCollector):
            raise PluginError(
                f"Plugin must inherit from BaseCollector: {plugin_class.__name__}"
            )

        # Try to get plugin name without full instantiation
        # Use class name as fallback if instantiation fails
        plugin_name = plugin_class.__name__.lower().replace("collector", "_collector")

        try:
            # Try to create instance to get proper name
            temp_instance = plugin_class({})
            plugin_name = temp_instance.name
            version = temp_instance.version
        except Exception:
            # If instantiation fails, we'll get name/version later
            version = "unknown"

        # Register
        self._plugins[plugin_name] = plugin_class
        logger.info(f"Registered plugin: {plugin_name} v{version}")

    def load_plugin(self, plugin_name: str, config: Dict[str, Any]) -> None:
        """
        Load and initialize a plugin instance.

        Args:
            plugin_name: Name of the plugin to load
            config: Configuration dictionary

        Raises:
            PluginLoadError: If plugin cannot be loaded
        """
        if plugin_name not in self._plugins:
            raise PluginLoadError(f"Plugin not registered: {plugin_name}")

        if plugin_name in self._loaded_instances:
            logger.warning(f"Plugin already loaded: {plugin_name}")
            return

        try:
            plugin_class = self._plugins[plugin_name]
            instance = plugin_class(config)
            self._loaded_instances[plugin_name] = instance
            logger.info(f"Loaded plugin: {plugin_name}")
        except Exception as e:
            raise PluginLoadError(f"Failed to load plugin {plugin_name}: {e}")

    def execute_plugin(self, plugin_name: str,
                       config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a plugin and return results.

        Args:
            plugin_name: Name of the plugin to execute
            config: Optional configuration (loads plugin if not loaded)

        Returns:
            Plugin execution results

        Raises:
            PluginExecutionError: If execution fails
        """
        # Load plugin if not already loaded
        if plugin_name not in self._loaded_instances:
            if config is None:
                raise PluginExecutionError(
                    f"Plugin not loaded and no config provided: {plugin_name}"
                )
            self.load_plugin(plugin_name, config)

        instance = self._loaded_instances[plugin_name]

        try:
            logger.info(f"Executing plugin: {plugin_name}")
            start_time = datetime.now()

            result = instance.collect()

            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Plugin executed successfully: {plugin_name} "
                f"({execution_time:.2f}s)"
            )

            return result

        except Exception as e:
            logger.error(f"Plugin execution failed: {plugin_name} - {e}")
            raise PluginExecutionError(f"Plugin {plugin_name} failed: {e}")

    def unload_plugin(self, plugin_name: str) -> None:
        """
        Unload a plugin and cleanup resources.

        Args:
            plugin_name: Name of the plugin to unload
        """
        if plugin_name in self._loaded_instances:
            del self._loaded_instances[plugin_name]
            logger.info(f"Unloaded plugin: {plugin_name}")

    def list_plugins(self) -> List[Dict[str, str]]:
        """
        List all registered plugins.

        Returns:
            List of plugin metadata dictionaries
        """
        plugins = []
        for name, plugin_class in self._plugins.items():
            try:
                temp = plugin_class({})
                plugins.append({
                    "name": name,
                    "version": temp.version,
                    "class": plugin_class.__name__
                })
            except Exception:
                # Skip plugins that can't be instantiated with empty config
                plugins.append({
                    "name": name,
                    "version": "unknown",
                    "class": plugin_class.__name__
                })
        return plugins

    def is_loaded(self, plugin_name: str) -> bool:
        """Check if a plugin is loaded."""
        return plugin_name in self._loaded_instances
