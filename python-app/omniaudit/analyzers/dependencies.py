"""
Dependency Analysis Module

Provides dependency analysis capabilities including CVE scanning,
license compliance, and outdated package detection.
Dependency Analyzer

Analyzes project dependencies for vulnerabilities,
license compliance, and outdated packages.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class PackageManager(str, Enum):
    """Supported package managers."""

    NPM = "npm"
    YARN = "yarn"
    PNPM = "pnpm"
    PIP = "pip"
    POETRY = "poetry"
    CARGO = "cargo"
    GO_MOD = "go"
    MAVEN = "maven"
    GRADLE = "gradle"
    COMPOSER = "composer"
    BUNDLER = "bundler"


class VulnerabilitySeverity(str, Enum):
    """CVE severity levels (CVSS-based)."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class Dependency(BaseModel):
    """A package dependency."""

    name: str = Field(..., description="Package name")
    version: str = Field(..., description="Installed version")
    package_manager: PackageManager = Field(..., description="Package manager")
    is_dev: bool = Field(default=False, description="Is development dependency")
    is_direct: bool = Field(default=True, description="Is direct dependency")
    license: Optional[str] = Field(None, description="Package license")
    description: Optional[str] = Field(None, description="Package description")
    homepage: Optional[str] = Field(None, description="Package homepage URL")
    repository: Optional[str] = Field(None, description="Package repository URL")


class Vulnerability(BaseModel):
    """A CVE or security vulnerability."""

    id: str = Field(..., description="Vulnerability ID (e.g., CVE-2021-12345)")
    title: str = Field(..., description="Vulnerability title")
    description: str = Field(..., description="Detailed description")
    severity: VulnerabilitySeverity = Field(..., description="Severity level")
    cvss_score: Optional[float] = Field(None, ge=0.0, le=10.0, description="CVSS score")
    affected_versions: List[str] = Field(
        default_factory=list, description="Affected version ranges"
    )
    patched_versions: List[str] = Field(
        default_factory=list, description="Patched version ranges"
    )
    published_date: Optional[datetime] = Field(None, description="Publication date")
    references: List[str] = Field(default_factory=list, description="Reference URLs")
    cwe_ids: List[int] = Field(default_factory=list, description="Associated CWE IDs")


class DependencyVulnerability(BaseModel):
    """A vulnerability affecting a specific dependency."""

    dependency: Dependency = Field(..., description="Affected dependency")
    vulnerability: Vulnerability = Field(..., description="Vulnerability details")
    is_direct: bool = Field(..., description="Is this a direct dependency")
    dependency_chain: List[str] = Field(
        default_factory=list, description="Dependency chain to vulnerable package"
    )


class LicenseIssue(BaseModel):
    """A license compliance issue."""

    dependency: Dependency = Field(..., description="Dependency with license issue")
    issue_type: str = Field(..., description="Type of license issue")
    severity: str = Field(..., description="Issue severity")
    description: str = Field(..., description="Issue description")
    recommendation: str = Field(..., description="Remediation advice")


class OutdatedPackage(BaseModel):
    """An outdated package."""

    dependency: Dependency = Field(..., description="Outdated dependency")
    current_version: str = Field(..., description="Currently installed version")
    latest_version: str = Field(..., description="Latest available version")
    latest_stable_version: Optional[str] = Field(None, description="Latest stable version")
    age_days: int = Field(..., description="Days since last update")
    breaking_changes: bool = Field(
        default=False, description="Does update include breaking changes"
    )


class TyposquattingMatch(BaseModel):
    """A potential typosquatting package."""

    package_name: str = Field(..., description="Suspicious package name")
    legitimate_package: str = Field(..., description="Legitimate package it resembles")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    risk_level: str = Field(..., description="Risk level")
    reasoning: str = Field(..., description="Why this is flagged")


class DependencyReport(BaseModel):
    """Complete dependency analysis report."""

    scan_id: str = Field(..., description="Unique scan ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Scan timestamp")
    project_path: str = Field(..., description="Project root path")
    package_managers: List[PackageManager] = Field(
        default_factory=list, description="Detected package managers"
    )
    total_dependencies: int = Field(default=0, description="Total dependency count")
    direct_dependencies: int = Field(default=0, description="Direct dependency count")
    vulnerabilities: List[DependencyVulnerability] = Field(
        default_factory=list, description="Found vulnerabilities"
    )
    license_issues: List[LicenseIssue] = Field(
        default_factory=list, description="License compliance issues"
    )
    outdated_packages: List[OutdatedPackage] = Field(
        default_factory=list, description="Outdated packages"
    )
    typosquatting_matches: List[TyposquattingMatch] = Field(
        default_factory=list, description="Potential typosquatting"
    )
    summary: Dict[str, Any] = Field(default_factory=dict, description="Summary statistics")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Scan metadata")

    def get_critical_vulnerabilities(self) -> List[DependencyVulnerability]:
        """Get all critical vulnerabilities."""
        return [
            v
            for v in self.vulnerabilities
            if v.vulnerability.severity == VulnerabilitySeverity.CRITICAL
        ]

    def get_high_vulnerabilities(self) -> List[DependencyVulnerability]:
        """Get all high severity vulnerabilities."""
        return [
            v
            for v in self.vulnerabilities
            if v.vulnerability.severity == VulnerabilitySeverity.HIGH
        ]

    def get_vulnerability_counts(self) -> Dict[str, int]:
        """Get count of vulnerabilities by severity."""
        counts = {severity.value: 0 for severity in VulnerabilitySeverity}
        for vuln in self.vulnerabilities:
            counts[vuln.vulnerability.severity.value] += 1
        return counts


class DependencyAnalyzer:
    """
    Performs comprehensive dependency analysis.

    Features:
    - CVE scanning (NVD, GitHub Advisory, OSV)
    - License compliance checking
    - Outdated package detection
    - Typosquatting detection
    - SBOM generation (SPDX, CycloneDX)
    - Multi-package-manager support
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize dependency analyzer."""
        self.config = config or {}
        self._validate_config()

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
        return "1.0.0"

    def _validate_config(self) -> None:
        """Validate analyzer configuration."""
        # Basic validation - can be extended as needed
        return "0.1.0"

    def _validate_config(self) -> None:
        """Validate analyzer configuration."""
        # project_path is optional for dependency analyzer
        pass

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform dependency analysis.

        Args:
            data: Input data for analysis
        Analyze project dependencies.

        Args:
            data: Optional input data containing dependency information

        Returns:
            Dependency analysis results
        """
        # Placeholder implementation
        return {
            "analyzer": self.name,
            "version": self.version,
            "data": {
                "dependencies": [],
                "summary": {
                    "total_dependencies": 0,
                    "vulnerabilities": 0,
                },
            },
        }


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
    "Vulnerability",
]
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
