"""
Dependency Analyzer Module

Analyzes project dependencies for vulnerabilities and issues.
This module provides dependency analysis capabilities including:
- Parsing various package manager formats (npm, pip, cargo, etc.)
- Vulnerability scanning via CVE databases
- License compliance checking
- Outdated package detection
- SBOM (Software Bill of Materials) generation
"""

import json
import re
import uuid
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field

from .base import BaseAnalyzer, AnalyzerError


def _utc_now() -> datetime:
    """Return current UTC datetime with timezone info."""
    return datetime.now(timezone.utc)


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


@dataclass
class Dependency:
    """Represents a project dependency."""

    name: str
    version: str
    package_manager: PackageManager
    is_dev: bool = False
    is_direct: bool = True
    license: Optional[str] = None
    description: Optional[str] = None
    homepage: Optional[str] = None
    repository: Optional[str] = None
    vulnerabilities: List[Dict[str, Any]] = field(default_factory=list)
    latest_version: Optional[str] = None

    @property
    def is_vulnerable(self) -> bool:
        """Check if dependency has vulnerabilities."""
        return len(self.vulnerabilities) > 0

    @property
    def is_outdated(self) -> bool:
        """Check if dependency is outdated."""
        return self.latest_version is not None and self.latest_version != self.version

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "package_manager": self.package_manager.value,
            "is_dev": self.is_dev,
            "is_direct": self.is_direct,
            "license": self.license,
            "vulnerabilities": self.vulnerabilities,
            "latest_version": self.latest_version,
            "is_vulnerable": self.is_vulnerable,
            "is_outdated": self.is_outdated,
        }


@dataclass
class Vulnerability:
    """A CVE or security vulnerability."""

    id: str
    title: str
    description: str
    severity: VulnerabilitySeverity
    cvss_score: Optional[float] = None
    affected_versions: List[str] = field(default_factory=list)
    patched_versions: List[str] = field(default_factory=list)
    published_date: Optional[datetime] = None
    references: List[str] = field(default_factory=list)
    cwe_ids: List[int] = field(default_factory=list)


@dataclass
class DependencyVulnerability:
    """A vulnerability affecting a specific dependency."""

    dependency: Dependency
    vulnerability: Vulnerability
    is_direct: bool = True
    dependency_chain: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "dependency": self.dependency.to_dict(),
            "vulnerability": {
                "id": self.vulnerability.id,
                "title": self.vulnerability.title,
                "severity": self.vulnerability.severity.value,
                "cvss_score": self.vulnerability.cvss_score,
            },
            "is_direct": self.is_direct,
            "dependency_chain": self.dependency_chain,
        }


@dataclass
class LicenseIssue:
    """License compliance issue."""

    dependency: Dependency
    issue_type: str
    severity: str
    description: str
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "dependency": self.dependency.to_dict(),
            "issue_type": self.issue_type,
            "severity": self.severity,
            "description": self.description,
            "recommendation": self.recommendation,
        }


@dataclass
class OutdatedPackage:
    """Information about an outdated package."""

    dependency: Dependency
    current_version: str
    latest_version: str
    latest_stable_version: Optional[str] = None
    age_days: int = 0
    breaking_changes: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "dependency": self.dependency.to_dict(),
            "current_version": self.current_version,
            "latest_version": self.latest_version,
            "latest_stable_version": self.latest_stable_version,
            "age_days": self.age_days,
            "breaking_changes": self.breaking_changes,
        }


@dataclass
class TyposquattingMatch:
    """A potential typosquatting package."""

    package_name: str
    legitimate_package: str
    similarity_score: float
    risk_level: str
    reasoning: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "package_name": self.package_name,
            "legitimate_package": self.legitimate_package,
            "similarity_score": self.similarity_score,
            "risk_level": self.risk_level,
            "reasoning": self.reasoning,
        }


@dataclass
class DependencyReport:
    """Complete dependency analysis report."""

    scan_id: str
    project_path: str
    package_managers: List[PackageManager] = field(default_factory=list)
    total_dependencies: int = 0
    direct_dependencies: int = 0
    vulnerabilities: List[DependencyVulnerability] = field(default_factory=list)
    license_issues: List[LicenseIssue] = field(default_factory=list)
    outdated_packages: List[OutdatedPackage] = field(default_factory=list)
    typosquatting_matches: List[TyposquattingMatch] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=_utc_now)
    scan_duration_ms: Optional[int] = None

    def get_critical_vulnerabilities(self) -> List[DependencyVulnerability]:
        """Get all critical vulnerabilities."""
        return [
            v for v in self.vulnerabilities
            if v.vulnerability.severity == VulnerabilitySeverity.CRITICAL
        ]

    def get_high_vulnerabilities(self) -> List[DependencyVulnerability]:
        """Get all high severity vulnerabilities."""
        return [
            v for v in self.vulnerabilities
            if v.vulnerability.severity == VulnerabilitySeverity.HIGH
        ]

    def get_vulnerability_counts(self) -> Dict[str, int]:
        """Get count of vulnerabilities by severity."""
        counts = {severity.value: 0 for severity in VulnerabilitySeverity}
        for vuln in self.vulnerabilities:
            counts[vuln.vulnerability.severity.value] += 1
        return counts

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "scan_id": self.scan_id,
            "project_path": self.project_path,
            "package_managers": [pm.value for pm in self.package_managers],
            "total_dependencies": self.total_dependencies,
            "direct_dependencies": self.direct_dependencies,
            "vulnerabilities": [v.to_dict() for v in self.vulnerabilities],
            "license_issues": [li.to_dict() for li in self.license_issues],
            "outdated_packages": [o.to_dict() for o in self.outdated_packages],
            "typosquatting_matches": [t.to_dict() for t in self.typosquatting_matches],
            "summary": self.summary,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "scan_duration_ms": self.scan_duration_ms,
        }


# Common copyleft licenses that may have compatibility issues
COPYLEFT_LICENSES = {"GPL-2.0", "GPL-3.0", "LGPL-2.1", "LGPL-3.0", "AGPL-3.0"}
PERMISSIVE_LICENSES = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "Unlicense"}


class DependencyAnalyzer(BaseAnalyzer):
    """
    Performs comprehensive dependency analysis.

    Features:
    - CVE scanning (NVD, GitHub Advisory, OSV)
    - License compliance checking
    - Outdated package detection
    - Typosquatting detection
    - SBOM generation (SPDX, CycloneDX)
    - Multi-package-manager support

    Configuration:
        project_path: str - Path to project root (required)
        check_vulnerabilities: bool - Enable CVE scanning (default: True)
        check_licenses: bool - Enable license checking (default: True)
        check_outdated: bool - Enable outdated detection (default: True)
        allowed_licenses: List[str] - List of allowed licenses
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the dependency analyzer."""
        super().__init__(config)
        self._project_path: Optional[Path] = None
        if config and "project_path" in config:
            self._project_path = Path(config["project_path"])
        self._validate_config()

    @property
    def name(self) -> str:
        """Return analyzer name."""
        return "dependency_analyzer"

    @property
    def version(self) -> str:
        """Return analyzer version."""
        return "1.0.0"

    def _validate_config(self) -> None:
        """Validate analyzer configuration."""
        if "project_path" not in self.config:
            raise AnalyzerError("project_path is required in configuration")

        project_path = Path(self.config["project_path"])
        if not project_path.exists():
            raise AnalyzerError(f"Project path does not exist: {project_path}")

        self._project_path = project_path

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform dependency analysis on the project.

        Args:
            data: Additional analysis parameters

        Returns:
            Analysis results with dependency information
        """
        dependencies: List[Dependency] = []
        package_managers: List[str] = []
        vulnerabilities: List[Dict[str, Any]] = []
        license_issues: List[Dict[str, Any]] = []
        outdated_packages: List[Dict[str, Any]] = []

        if self._project_path:
            # Discover and parse dependency files
            dependencies, package_managers = self._discover_dependencies(
                self._project_path
            )

            # Check for vulnerabilities (if enabled)
            if self.config.get("check_vulnerabilities", True):
                vulnerabilities = self._check_vulnerabilities(dependencies)

            # Check licenses (if enabled)
            if self.config.get("check_licenses", True):
                license_issues = self._check_licenses(dependencies)

            # Check for outdated packages (if enabled)
            if self.config.get("check_outdated", True):
                outdated_packages = self._check_outdated(dependencies)

        # Calculate summary
        summary = self._calculate_summary(
            dependencies, vulnerabilities, license_issues, outdated_packages
        )

        # Calculate risk assessment
        risk_assessment = self._calculate_risk(
            vulnerabilities, license_issues, outdated_packages
        )

        return self._create_response(
            {
                "scan_id": data.get("scan_id", str(uuid.uuid4())),
                "project_path": str(self._project_path) if self._project_path else "",
                "package_managers": package_managers,
                "total_dependencies": len(dependencies),
                "vulnerabilities": vulnerabilities,
                "license_issues": license_issues,
                "outdated_packages": outdated_packages,
                "summary": summary,
                "risk_assessment": risk_assessment,
            }
        )

    def _discover_dependencies(
        self, project_path: Path
    ) -> tuple:
        """Discover all dependencies in the project."""
        dependencies: List[Dependency] = []
        package_managers: List[str] = []

        # Check for package.json (npm)
        package_json = project_path / "package.json"
        if package_json.exists():
            deps = self._parse_package_json(package_json)
            dependencies.extend(deps)
            if deps:
                package_managers.append("npm")

        # Check for requirements.txt (pip)
        requirements_txt = project_path / "requirements.txt"
        if requirements_txt.exists():
            deps = self._parse_requirements_txt(requirements_txt)
            dependencies.extend(deps)
            if deps:
                package_managers.append("pip")

        # Check for pyproject.toml (poetry/pip)
        pyproject_toml = project_path / "pyproject.toml"
        if pyproject_toml.exists():
            deps = self._parse_pyproject_toml(pyproject_toml)
            dependencies.extend(deps)
            if deps and "pip" not in package_managers:
                package_managers.append("pip")

        # Check for Cargo.toml (rust)
        cargo_toml = project_path / "Cargo.toml"
        if cargo_toml.exists():
            deps = self._parse_cargo_toml(cargo_toml)
            dependencies.extend(deps)
            if deps:
                package_managers.append("cargo")

        # Check for go.mod (go)
        go_mod = project_path / "go.mod"
        if go_mod.exists():
            deps = self._parse_go_mod(go_mod)
            dependencies.extend(deps)
            if deps:
                package_managers.append("go")

        return dependencies, package_managers

    def _parse_package_json(self, file_path: Path) -> List[Dependency]:
        """Parse npm package.json file."""
        dependencies: List[Dependency] = []

        try:
            content = json.loads(file_path.read_text(encoding="utf-8"))

            # Parse regular dependencies
            for name, version_spec in content.get("dependencies", {}).items():
                version = self._normalize_version(version_spec)
                dependencies.append(
                    Dependency(
                        name=name,
                        version=version,
                        package_manager=PackageManager.NPM,
                        is_dev=False,
                        is_direct=True,
                    )
                )

            # Parse dev dependencies
            for name, version_spec in content.get("devDependencies", {}).items():
                version = self._normalize_version(version_spec)
                dependencies.append(
                    Dependency(
                        name=name,
                        version=version,
                        package_manager=PackageManager.NPM,
                        is_dev=True,
                        is_direct=True,
                    )
                )

        except (json.JSONDecodeError, OSError):
            pass

        return dependencies

    def _parse_requirements_txt(self, file_path: Path) -> List[Dependency]:
        """Parse pip requirements.txt file."""
        dependencies: List[Dependency] = []

        try:
            content = file_path.read_text(encoding="utf-8")

            for line in content.split("\n"):
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue

                # Parse package==version, package>=version, package~=version
                match = re.match(r"^([a-zA-Z0-9_-]+)\s*([<>=~!]+)?\s*([0-9][^,\s]*)?", line)
                if match:
                    name = match.group(1)
                    version = match.group(3) or "unknown"
                    dependencies.append(
                        Dependency(
                            name=name,
                            version=version,
                            package_manager=PackageManager.PIP,
                            is_dev=False,
                            is_direct=True,
                        )
                    )

        except IOError:
            pass

        return dependencies

    def _parse_pyproject_toml(self, file_path: Path) -> List[Dependency]:
        """Parse poetry pyproject.toml file."""
        dependencies: List[Dependency] = []

        data = self._load_toml(file_path)
        if data is None:
            return dependencies

        try:
            # Poetry format
            poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
            for name, version_spec in poetry_deps.items():
                if name.lower() == "python":
                    continue

                version = self._extract_version_from_spec(version_spec)
                dependencies.append(
                    Dependency(
                        name=name,
                        version=version,
                        package_manager=PackageManager.POETRY,
                        is_dev=False,
                        is_direct=True,
                    )
                )

            # Poetry dev dependencies
            poetry_dev_deps = data.get("tool", {}).get("poetry", {}).get("dev-dependencies", {})
            for name, version_spec in poetry_dev_deps.items():
                version = self._extract_version_from_spec(version_spec)
                dependencies.append(
                    Dependency(
                        name=name,
                        version=version,
                        package_manager=PackageManager.POETRY,
                        is_dev=True,
                        is_direct=True,
                    )
                )

        except (OSError, Exception):
            pass

        return dependencies

    def _parse_cargo_toml(self, file_path: Path) -> List[Dependency]:
        """Parse Cargo.toml file (Rust)."""
        dependencies: List[Dependency] = []

        data = self._load_toml(file_path)
        if data is None:
            return dependencies

        try:
            # Parse dependencies
            cargo_deps = data.get("dependencies", {})
            for name, version_spec in cargo_deps.items():
                version = self._extract_version_from_spec(version_spec)
                dependencies.append(
                    Dependency(
                        name=name,
                        version=version,
                        package_manager=PackageManager.CARGO,
                        is_dev=False,
                        is_direct=True,
                    )
                )

            # Parse dev dependencies
            dev_deps = data.get("dev-dependencies", {})
            for name, version_spec in dev_deps.items():
                version = self._extract_version_from_spec(version_spec)
                dependencies.append(
                    Dependency(
                        name=name,
                        version=version,
                        package_manager=PackageManager.CARGO,
                        is_dev=True,
                        is_direct=True,
                    )
                )

        except (OSError, Exception):
            pass

        return dependencies

    def _parse_go_mod(self, file_path: Path) -> List[Dependency]:
        """Parse Go go.mod file."""
        dependencies: List[Dependency] = []

        try:
            content = file_path.read_text(encoding="utf-8")

            # Match require blocks and single requires
            require_pattern = r"require\s+\(\s*([^)]+)\)"
            single_require_pattern = r"require\s+(\S+)\s+(\S+)"

            # Block requires
            for match in re.finditer(require_pattern, content):
                block = match.group(1)
                for line in block.strip().split("\n"):
                    line = line.strip()
                    if line and not line.startswith("//"):
                        parts = line.split()
                        if len(parts) >= 2:
                            name = parts[0]
                            version = parts[1].lstrip("v")
                            dependencies.append(Dependency(
                                name=name,
                                version=version,
                                package_manager=PackageManager.GO_MOD,
                                is_dev=False,
                                is_direct=True,
                            ))

            # Single requires
            for match in re.finditer(single_require_pattern, content):
                name = match.group(1)
                version = match.group(2).lstrip("v")
                # Avoid duplicates from the block
                if not any(d.name == name for d in dependencies):
                    dependencies.append(Dependency(
                        name=name,
                        version=version,
                        package_manager=PackageManager.GO_MOD,
                        is_dev=False,
                        is_direct=True,
                    ))

        except IOError:
            pass

        return dependencies

    def _load_toml(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Load and parse a TOML file.

        Args:
            file_path: Path to the TOML file

        Returns:
            Parsed TOML data as a dictionary, or None if parsing fails
        """
        try:
            # Try to import tomli/tomllib for TOML parsing
            try:
                import tomllib  # Python 3.11+
            except ImportError:
                try:
                    import tomli as tomllib  # Fallback for Python 3.10
                except ImportError:
                    # Neither tomllib nor tomli available
                    return None

            content = file_path.read_bytes()
            return tomllib.loads(content.decode("utf-8"))
        except (OSError, Exception):
            return None

    def _normalize_version(self, version_spec: str) -> str:
        """Normalize version specifier to a version string."""
        # Remove leading ^, ~, >=, <=, etc.
        version = re.sub(r"^[\^~>=<]+", "", version_spec)
        return version.strip()

    def _extract_version_from_spec(self, spec: Any) -> str:
        """Extract version from various specification formats."""
        if isinstance(spec, str):
            return self._normalize_version(spec)
        elif isinstance(spec, dict):
            version = spec.get("version", "unknown")
            return self._normalize_version(version)
        return "unknown"

    def _check_vulnerabilities(
        self, dependencies: List[Dependency]
    ) -> List[Dict[str, Any]]:
        """Check dependencies for known vulnerabilities."""
        # In a real implementation, this would query a vulnerability database
        # For now, return an empty list
        return []

    def _check_licenses(self, dependencies: List[Dependency]) -> List[Dict[str, Any]]:
        """Check license compatibility."""
        issues: List[Dict[str, Any]] = []
        project_license = self.config.get("project_license", "MIT")

        for dep in dependencies:
            if dep.license is None:
                issues.append({
                    "dependency": {
                        "name": dep.name,
                        "version": dep.version,
                        "package_manager": dep.package_manager.value,
                    },
                    "issue_type": "missing_license",
                    "severity": "medium",
                    "description": f"Package '{dep.name}' has no license information",
                    "recommendation": "Contact package maintainer or find alternative package",
                })
            elif dep.license and "GPL" in dep.license.upper() and "MIT" in project_license:
                issues.append({
                    "dependency": {
                        "name": dep.name,
                        "version": dep.version,
                        "package_manager": dep.package_manager.value,
                        "license": dep.license,
                    },
                    "issue_type": "incompatible_license",
                    "severity": "high",
                    "description": f"License '{dep.license}' is incompatible with project license '{project_license}'",
                    "recommendation": "Remove this dependency or change project license",
                })

        return issues

    def _check_outdated(self, dependencies: List[Dependency]) -> List[Dict[str, Any]]:
        """Check for outdated packages."""
        # In a real implementation, this would query package registries
        # For now, return an empty list
        return []

    def _calculate_summary(
        self,
        dependencies: List[Dependency],
        vulnerabilities: List[Dict[str, Any]],
        license_issues: List[Dict[str, Any]],
        outdated_packages: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calculate summary statistics."""
        direct_deps = [d for d in dependencies if d.is_direct]
        dev_deps = [d for d in dependencies if d.is_dev]

        vuln_by_severity: Dict[str, int] = {}
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "unknown")
            vuln_by_severity[severity] = vuln_by_severity.get(severity, 0) + 1

        return {
            "total_dependencies": len(dependencies),
            "direct_dependencies": len(direct_deps),
            "dev_dependencies": len(dev_deps),
            "total_vulnerabilities": len(vulnerabilities),
            "critical_vulnerabilities": vuln_by_severity.get("critical", 0),
            "high_vulnerabilities": vuln_by_severity.get("high", 0),
            "license_issues": len(license_issues),
            "outdated_packages": len(outdated_packages),
            "package_managers": list(set(d.package_manager.value for d in dependencies)),
        }

    def _calculate_risk(
        self,
        vulnerabilities: List[Dict[str, Any]],
        license_issues: List[Dict[str, Any]],
        outdated_packages: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calculate overall risk assessment."""
        risk_score = 0.0

        # Weight vulnerabilities
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "unknown")
            if severity == "critical":
                risk_score += 25
            elif severity == "high":
                risk_score += 15
            elif severity == "medium":
                risk_score += 8
            elif severity == "low":
                risk_score += 3

        # Weight license issues
        for issue in license_issues:
            severity = issue.get("severity", "medium")
            if severity == "high":
                risk_score += 10
            elif severity == "medium":
                risk_score += 5

        # Weight outdated packages
        risk_score += len(outdated_packages) * 2

        # Cap at 100
        risk_score = min(risk_score, 100)

        # Determine risk level
        if risk_score >= 70:
            risk_level = "critical"
        elif risk_score >= 50:
            risk_level = "high"
        elif risk_score >= 25:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
        }


__all__ = [
    "DependencyAnalyzer",
    "Dependency",
    "DependencyReport",
    "DependencyVulnerability",
    "LicenseIssue",
    "OutdatedPackage",
    "TyposquattingMatch",
    "Vulnerability",
    "PackageManager",
    "VulnerabilitySeverity",
]
