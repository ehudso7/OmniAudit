"""OmniAudit Analyzers Package.

This package contains all analyzer modules for code auditing.
"""

from .base import BaseAnalyzer, AnalyzerError

__all__ = [
    "BaseAnalyzer",
    "AnalyzerError",
]
