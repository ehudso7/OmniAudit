"""
Base Collector Interface

All collectors must inherit from BaseCollector and implement required methods.
This ensures consistent behavior across all data collection plugins.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime


class BaseCollector(ABC):
    """
    Abstract base class for all collectors.

    Collectors are responsible for fetching data from external sources
    and normalizing it into a standard format for analysis.

    Attributes:
        name: Unique identifier for the collector
        version: Collector version (semantic versioning)
        config: Configuration dictionary

    Example:
        >>> class MyCollector(BaseCollector):
        ...     def collect(self) -> Dict[str, Any]:
        ...         return {"data": "example"}
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the collector with configuration.

        Args:
            config: Optional configuration dictionary

        Raises:
            ValueError: If configuration is invalid
        """
        self.config = config or {}
        self._validate_config()

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the collector's unique name."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Return the collector's version."""
        pass

    @abstractmethod
    def _validate_config(self) -> None:
        """
        Validate the collector's configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        pass

    @abstractmethod
    def collect(self) -> Dict[str, Any]:
        """
        Collect data from the source.

        Returns:
            Dictionary containing collected data in normalized format:
            {
                "collector": str,
                "timestamp": str (ISO 8601),
                "data": Dict[str, Any],
                "metadata": Dict[str, Any]
            }

        Raises:
            CollectorError: If data collection fails
        """
        pass

    def _create_response(self, data: Dict[str, Any],
                        metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a standardized response format.

        Args:
            data: The collected data
            metadata: Optional metadata about the collection

        Returns:
            Standardized response dictionary
        """
        return {
            "collector": self.name,
            "version": self.version,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": data,
            "metadata": metadata or {}
        }


class CollectorError(Exception):
    """Base exception for collector errors."""
    pass


class ConfigurationError(CollectorError):
    """Raised when collector configuration is invalid."""
    pass


class DataCollectionError(CollectorError):
    """Raised when data collection fails."""
    pass
