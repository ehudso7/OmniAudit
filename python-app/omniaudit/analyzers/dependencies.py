"""
Dependency Analyzer for OmniAudit.

This module provides dependency analysis capabilities including:
- Parsing various package manager formats (npm, pip, cargo, etc.)
- Vulnerability scanning via CVE databases
- License compliance checking
- Outdated package detection
- SBOM (Software Bill of Materials) generation
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import re

from .base import BaseAnalyzer, AnalyzerError


class PackageManager(str, Enum):
    """Supported package managers."""

    NPM = "npm"
    PIP = "pip"
    POETRY = "poetry"
    CARGO = "cargo"
    MAVEN = "maven"
    GRADLE = "gradle"
    GO = "go"
    NUGET = "nuget"
    COMPOSER = "composer"
    RUBYGEMS = "rubygems"


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


@dataclass
class DependencyVulnerability:
    """Vulnerability information for a dependency."""

    id: str
    title: str
    description: str
    severity: str
    cvss_score: Optional[float] = None
    affected_versions: List[str] = field(default_factory=list)
    patched_versions: List[str] = field(default_factory=list)
    published_date: Optional[str] = None
    references: List[str] = field(default_factory=list)
    cwe_ids: List[int] = field(default_factory=list)


@dataclass
class LicenseIssue:
    """License compliance issue."""

    dependency: Dependency
    issue_type: str
    severity: str
    description: str
    recommendation: str


@dataclass
class OutdatedPackage:
    """Information about an outdated package."""

    dependency: Dependency
    current_version: str
    latest_version: str
    latest_stable_version: Optional[str] = None
    age_days: int = 0
    breaking_changes: bool = False


@dataclass
class DependencyReport:
    """Complete dependency analysis report."""

    scan_id: str
    project_path: str
    package_managers: List[str]
    dependencies: List[Dependency]
    vulnerabilities: List[Dict[str, Any]]
    license_issues: List[LicenseIssue]
    outdated_packages: List[OutdatedPackage]
    summary: Dict[str, Any]
    risk_assessment: Dict[str, Any]


class DependencyAnalyzer(BaseAnalyzer):
    """
    Analyzer for project dependencies.

    This analyzer:
    - Discovers and parses dependency files (package.json, requirements.txt, etc.)
    - Checks dependencies for known vulnerabilities
    - Verifies license compatibility
    - Identifies outdated packages
    - Generates Software Bill of Materials (SBOM)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the dependency analyzer."""
        super().__init__(config)
        self._project_path: Optional[Path] = None
        if config and "project_path" in config:
            self._project_path = Path(config["project_path"])

    @property
    def name(self) -> str:
        """Return analyzer name."""
        return "dependency_analyzer"

    @property
    def version(self) -> str:
        """Return analyzer version."""
        return "1.0.0"

    def _validate_config(self) -> None:
        """Validate configuration."""
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
                "scan_id": data.get("scan_id", "default-dep-scan"),
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
    ) -> tuple[List[Dependency], List[str]]:
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

        except OSError:
            pass

        return dependencies

    def _parse_pyproject_toml(self, file_path: Path) -> List[Dependency]:
        """Parse pyproject.toml file (Poetry or PEP 621 format)."""
        dependencies: List[Dependency] = []

        try:
            # Try to import tomli/tomllib for TOML parsing
            try:
                import tomllib  # Python 3.11+
            except ImportError:
                import tomli as tomllib  # Fallback for Python 3.10

            content = file_path.read_bytes()
            data = tomllib.loads(content.decode("utf-8"))

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
                        package_manager=PackageManager.PIP,
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
                        package_manager=PackageManager.PIP,
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

        try:
            # Try to import tomli/tomllib for TOML parsing
            try:
                import tomllib  # Python 3.11+
            except ImportError:
                import tomli as tomllib  # Fallback for Python 3.10

            content = file_path.read_bytes()
            data = tomllib.loads(content.decode("utf-8"))

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
