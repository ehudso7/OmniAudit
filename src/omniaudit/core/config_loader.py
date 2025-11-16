"""
Configuration Loader

Loads and validates YAML/JSON configuration files.
Supports multiple config sources with priority hierarchy.
"""

from typing import Any, Dict, Optional
from pathlib import Path
import yaml
import json
import os

from .exceptions import ConfigurationError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ConfigLoader:
    """
    Loads configuration from multiple sources.

    Priority (highest to lowest):
    1. Environment variables
    2. Config file (YAML/JSON)
    3. Default values

    Example:
        >>> loader = ConfigLoader()
        >>> config = loader.load("config.yaml")
        >>> db_url = loader.get("database.url")
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration loader.

        Args:
            config_path: Optional path to config file
        """
        self._config: Dict[str, Any] = {}
        self._config_path = config_path

        if config_path:
            self.load(config_path)

    def load(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from file.

        Args:
            config_path: Path to YAML or JSON config file

        Returns:
            Loaded configuration dictionary

        Raises:
            ConfigurationError: If file cannot be loaded
        """
        path = Path(config_path)

        if not path.exists():
            raise ConfigurationError(f"Config file not found: {config_path}")

        try:
            with open(path, 'r') as f:
                if path.suffix in ['.yaml', '.yml']:
                    config = yaml.safe_load(f)
                elif path.suffix == '.json':
                    config = json.load(f)
                else:
                    raise ConfigurationError(
                        f"Unsupported config format: {path.suffix}"
                    )

            self._config = config or {}
            self._config_path = config_path
            logger.info(f"Loaded configuration from: {config_path}")

            return self._config

        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML: {e}")
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value with dot notation.

        Checks environment variables first, then config file.

        Args:
            key: Configuration key (supports dot notation: "db.host")
            default: Default value if key not found

        Returns:
            Configuration value or default

        Example:
            >>> config.get("database.host", "localhost")
        """
        # Check environment variable (uppercase, underscores)
        env_key = key.upper().replace('.', '_')
        env_value = os.getenv(env_key)
        if env_value is not None:
            return env_value

        # Navigate nested dict with dot notation
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value with dot notation.

        Args:
            key: Configuration key
            value: Value to set
        """
        keys = key.split('.')
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def to_dict(self) -> Dict[str, Any]:
        """Return full configuration as dictionary."""
        return self._config.copy()

    def save(self, output_path: Optional[str] = None) -> None:
        """
        Save configuration to file.

        Args:
            output_path: Optional output path (uses original if not provided)

        Raises:
            ConfigurationError: If save fails
        """
        path = output_path or self._config_path
        if not path:
            raise ConfigurationError("No output path specified")

        path_obj = Path(path)

        try:
            with open(path_obj, 'w') as f:
                if path_obj.suffix in ['.yaml', '.yml']:
                    yaml.safe_dump(self._config, f, default_flow_style=False)
                elif path_obj.suffix == '.json':
                    json.dump(self._config, f, indent=2)
                else:
                    raise ConfigurationError(f"Unsupported format: {path_obj.suffix}")

            logger.info(f"Saved configuration to: {path}")

        except Exception as e:
            raise ConfigurationError(f"Failed to save config: {e}")
