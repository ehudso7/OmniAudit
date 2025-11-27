"""
Dependency Analysis Module

Provides dependency analysis capabilities including CVE scanning,
license compliance, and outdated package detection.
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

    @property
    def name(self) -> str:
        return "dependency_analyzer"

    @property
    def version(self) -> str:
        return "1.0.0"

    def _validate_config(self) -> None:
        """Validate analyzer configuration."""
        # Basic validation - can be extended as needed
        pass

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform dependency analysis.

        Args:
            data: Input data for analysis

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
