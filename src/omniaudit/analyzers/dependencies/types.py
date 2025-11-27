"""
Type definitions for dependency analyzer.
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


class LicenseType(str, Enum):
    """Common license types."""

    MIT = "MIT"
    APACHE_2 = "Apache-2.0"
    GPL_3 = "GPL-3.0"
    LGPL_3 = "LGPL-3.0"
    BSD_2 = "BSD-2-Clause"
    BSD_3 = "BSD-3-Clause"
    MPL_2 = "MPL-2.0"
    ISC = "ISC"
    UNLICENSE = "Unlicense"
    PROPRIETARY = "Proprietary"
    UNKNOWN = "Unknown"


class LicenseCompatibility(str, Enum):
    """License compatibility levels."""

    PERMISSIVE = "permissive"
    WEAK_COPYLEFT = "weak_copyleft"
    STRONG_COPYLEFT = "strong_copyleft"
    PROPRIETARY = "proprietary"
    UNKNOWN = "unknown"


class VulnerabilitySeverity(str, Enum):
    """CVE severity levels (CVSS-based)."""

    CRITICAL = "critical"  # 9.0-10.0
    HIGH = "high"  # 7.0-8.9
    MEDIUM = "medium"  # 4.0-6.9
    LOW = "low"  # 0.1-3.9
    NONE = "none"  # 0.0


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


class SBOMFormat(str, Enum):
    """SBOM output formats."""

    SPDX_JSON = "spdx-json"
    SPDX_XML = "spdx-xml"
    CYCLONEDX_JSON = "cyclonedx-json"
    CYCLONEDX_XML = "cyclonedx-xml"


class SBOM(BaseModel):
    """Software Bill of Materials."""

    format: SBOMFormat = Field(..., description="SBOM format")
    spec_version: str = Field(..., description="Specification version")
    created: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    creator: str = Field(default="OmniAudit", description="SBOM creator")
    components: List[Dict[str, Any]] = Field(
        default_factory=list, description="Software components"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


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
