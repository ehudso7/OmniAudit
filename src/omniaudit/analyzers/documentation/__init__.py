"""Documentation analyzer module."""

from .documentation_analyzer import DocumentationAnalyzer
from .types import (
    DocumentationMetrics,
    DocumentationFinding,
    DocCoverage,
    READMEAnalysis,
)

__all__ = [
    "DocumentationAnalyzer",
    "DocumentationMetrics",
    "DocumentationFinding",
    "DocCoverage",
    "READMEAnalysis",
]
