"""
Base Analyzer Interface

All analyzers must inherit from BaseAnalyzer.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime


class BaseAnalyzer(ABC):
    """
    Abstract base class for all analyzers.

    Analyzers process raw data into insights and metrics.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize analyzer with configuration."""
        self.config = config or {}
        self._validate_config()

    @property
    @abstractmethod
    def name(self) -> str:
        """Return analyzer name."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Return analyzer version."""
        pass

    @abstractmethod
    def _validate_config(self) -> None:
        """Validate configuration."""
        pass

    @abstractmethod
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze data and return insights.

        Args:
            data: Input data to analyze

        Returns:
            Analysis results with metrics
        """
        pass

    def _create_response(self, data: Dict[str, Any],
                        metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create standardized response."""
        return {
            "analyzer": self.name,
            "version": self.version,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": data,
            "metadata": metadata or {}
        }


class AnalyzerError(Exception):
    """Base exception for analyzer errors."""
    pass
