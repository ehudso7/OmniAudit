"""Dependency Analysis Module"""

from .dependency_analyzer import DependencyAnalyzer
from .types import (
    Dependency,
    DependencyReport,
    DependencyVulnerability,
    LicenseIssue,
    OutdatedPackage,
    TyposquattingMatch,
    PackageManager,
    VulnerabilitySeverity,
)

__all__ = [
    "DependencyAnalyzer",
    "Dependency",
    "DependencyReport",
    "DependencyVulnerability",
    "LicenseIssue",
    "OutdatedPackage",
    "TyposquattingMatch",
    "PackageManager",
    "VulnerabilitySeverity",
]
