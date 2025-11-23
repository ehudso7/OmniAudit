"""
Base Reporter Interface

All reporters must inherit from BaseReporter.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseReporter(ABC):
    """Abstract base class for all reporters."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize reporter with configuration."""
        self.config = config or {}

    @property
    @abstractmethod
    def name(self) -> str:
        """Return reporter name."""
        pass

    @property
    @abstractmethod
    def format(self) -> str:
        """Return output format."""
        pass

    @abstractmethod
    def generate(self, data: Dict[str, Any], output_path: str) -> None:
        """
        Generate report from data.

        Args:
            data: Audit results data
            output_path: Path to save report
        """
        pass


class ReporterError(Exception):
    """Base exception for reporter errors."""
    pass
