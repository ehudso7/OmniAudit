"""
Dependency Analyzer

Analyzes project dependencies for vulnerabilities,
license compliance, and outdated packages.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .base import BaseAnalyzer


class PackageManager(Enum):
    """Supported package managers."""
    NPM = "npm"
    PIP = "pip"
    POETRY = "poetry"
    CARGO = "cargo"
    GO = "go"
    COMPOSER = "composer"
    MAVEN = "maven"
    GRADLE = "gradle"


@dataclass
class Dependency:
    """Represents a project dependency."""
    name: str
    version: str
    package_manager: PackageManager
    is_dev: bool = False
    is_direct: bool = True
    latest_version: Optional[str] = None
    license: Optional[str] = None
    vulnerabilities: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert dependency to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "package_manager": self.package_manager.value,
            "is_dev": self.is_dev,
            "is_direct": self.is_direct,
            "latest_version": self.latest_version,
            "license": self.license,
            "vulnerabilities": self.vulnerabilities,
            "is_outdated": self.latest_version is not None and self.latest_version != self.version,
        }


@dataclass
class DependencyReport:
    """Dependency analysis report."""
    dependencies: List[Dependency] = field(default_factory=list)
    scan_timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    scan_duration_ms: Optional[int] = None
    total_dependencies: int = 0
    vulnerable_count: int = 0
    outdated_count: int = 0
    license_issues: List[Dict[str, Any]] = field(default_factory=list)

    def add_dependency(self, dependency: Dependency) -> None:
        """Add a dependency to the report."""
        self.dependencies.append(dependency)
        self.total_dependencies += 1
        if dependency.vulnerabilities:
            self.vulnerable_count += 1
        if dependency.latest_version and dependency.latest_version != dependency.version:
            self.outdated_count += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "dependencies": [d.to_dict() for d in self.dependencies],
            "scan_timestamp": self.scan_timestamp,
            "scan_duration_ms": self.scan_duration_ms,
            "total_dependencies": self.total_dependencies,
            "vulnerable_count": self.vulnerable_count,
            "outdated_count": self.outdated_count,
            "license_issues": self.license_issues,
        }


class DependencyAnalyzer(BaseAnalyzer):
    """
    Analyzes project dependencies for security and compliance.

    Capabilities:
    - CVE vulnerability scanning
    - License compliance checking
    - Outdated package detection
    - SBOM (Software Bill of Materials) generation
    - Support for multiple package managers

    Configuration:
        project_path: str - Path to project root (required)
        check_vulnerabilities: bool - Enable CVE scanning (default: True)
        check_licenses: bool - Enable license checking (default: True)
        check_outdated: bool - Enable outdated detection (default: True)
        allowed_licenses: List[str] - List of allowed licenses

    Example:
        >>> analyzer = DependencyAnalyzer({"project_path": "."})
        >>> result = analyzer.analyze({})
    """

    @property
    def name(self) -> str:
        return "dependency_analyzer"

    @property
    def version(self) -> str:
        return "0.1.0"

    def _validate_config(self) -> None:
        """Validate analyzer configuration."""
        # project_path is optional for dependency analyzer
        pass

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze project dependencies.

        Args:
            data: Optional input data containing dependency information

        Returns:
            Dependency analysis results
        """
        report = DependencyReport()

        # Get configuration
        project_path = self.config.get("project_path")
        check_vulnerabilities = self.config.get("check_vulnerabilities", True)
        check_licenses = self.config.get("check_licenses", True)
        check_outdated = self.config.get("check_outdated", True)

        # Detect package managers and collect dependencies
        self._collect_dependencies(data, report)

        # Perform security scans based on configuration
        if check_vulnerabilities:
            self._scan_vulnerabilities(report)

        if check_licenses:
            self._check_licenses(report)

        if check_outdated:
            self._check_outdated(report)

        return self._create_response(report.to_dict())

    def _collect_dependencies(self, data: Dict[str, Any], report: DependencyReport) -> None:
        """Collect dependencies from project files."""
        # Placeholder implementation
        pass

    def _scan_vulnerabilities(self, report: DependencyReport) -> None:
        """Scan dependencies for known vulnerabilities."""
        # Placeholder implementation
        pass

    def _check_licenses(self, report: DependencyReport) -> None:
        """Check dependency licenses for compliance."""
        # Placeholder implementation
        pass

    def _check_outdated(self, report: DependencyReport) -> None:
        """Check for outdated dependencies."""
        # Placeholder implementation
        pass
