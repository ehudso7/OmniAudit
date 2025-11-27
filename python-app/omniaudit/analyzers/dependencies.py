"""
Dependency Analysis Module

This module provides dependency analysis capabilities including
vulnerability scanning, license checking, and SBOM generation.
"""

import json
import re
import uuid
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

from .base import BaseAnalyzer, AnalyzerError


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
    """A package dependency."""

    name: str
    version: str
    package_manager: PackageManager
    is_dev: bool = False
    is_direct: bool = True
    license: Optional[str] = None
    description: Optional[str] = None
    homepage: Optional[str] = None
    repository: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "package_manager": self.package_manager.value,
            "is_dev": self.is_dev,
            "is_direct": self.is_direct,
            "license": self.license,
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
    """A license compliance issue."""

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
    """An outdated package."""

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
    timestamp: datetime = field(default_factory=datetime.utcnow)

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


# Common copyleft licenses that may have compatibility issues
COPYLEFT_LICENSES = {"GPL-2.0", "GPL-3.0", "LGPL-2.1", "LGPL-3.0", "AGPL-3.0"}
PERMISSIVE_LICENSES = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "Unlicense"}


class DependencyAnalyzer(BaseAnalyzer):
    """
    Performs comprehensive dependency analysis on projects.

    Analyzes:
    - Package vulnerabilities (CVEs)
    - License compliance
    - Outdated packages
    - Potential typosquatting

    Configuration:
        project_path: str - Path to project root (required)
        check_vulnerabilities: bool - Check for CVEs (default: True)
        check_licenses: bool - Check license compliance (default: True)
        check_outdated: bool - Check for outdated packages (default: True)
        project_license: str - Project's license for compatibility checking
    """

    @property
    def name(self) -> str:
        return "dependency_analyzer"

    @property
    def version(self) -> str:
        return "1.0.0"

    def _validate_config(self) -> None:
        """Validate analyzer configuration."""
        if "project_path" not in self.config:
            raise AnalyzerError("project_path is required")

        path = Path(self.config["project_path"])
        if not path.exists():
            raise AnalyzerError(f"Project path does not exist: {path}")

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze project dependencies.

        Args:
            data: Optional input data

        Returns:
            Dependency analysis results
        """
        project_path = Path(self.config["project_path"])
        check_vulnerabilities = self.config.get("check_vulnerabilities", True)
        check_licenses = self.config.get("check_licenses", True)
        check_outdated = self.config.get("check_outdated", True)
        project_license = self.config.get("project_license", "MIT")

        scan_id = str(uuid.uuid4())

        # Detect package managers and parse dependencies
        dependencies: List[Dependency] = []
        package_managers: List[PackageManager] = []

        # Check for npm/yarn/pnpm (package.json)
        package_json = project_path / "package.json"
        if package_json.exists():
            npm_deps = self._parse_package_json(package_json)
            dependencies.extend(npm_deps)
            package_managers.append(PackageManager.NPM)

        # Check for pip (requirements.txt)
        requirements_txt = project_path / "requirements.txt"
        if requirements_txt.exists():
            pip_deps = self._parse_requirements_txt(requirements_txt)
            dependencies.extend(pip_deps)
            package_managers.append(PackageManager.PIP)

        # Check for poetry (pyproject.toml)
        pyproject_toml = project_path / "pyproject.toml"
        if pyproject_toml.exists():
            poetry_deps = self._parse_pyproject_toml(pyproject_toml)
            dependencies.extend(poetry_deps)
            if PackageManager.POETRY not in package_managers:
                package_managers.append(PackageManager.POETRY)

        # Check for cargo (Cargo.toml)
        cargo_toml = project_path / "Cargo.toml"
        if cargo_toml.exists():
            cargo_deps = self._parse_cargo_toml(cargo_toml)
            dependencies.extend(cargo_deps)
            package_managers.append(PackageManager.CARGO)

        # Check for go modules (go.mod)
        go_mod = project_path / "go.mod"
        if go_mod.exists():
            go_deps = self._parse_go_mod(go_mod)
            dependencies.extend(go_deps)
            package_managers.append(PackageManager.GO_MOD)

        # Analyze for issues
        vulnerabilities: List[DependencyVulnerability] = []
        license_issues: List[LicenseIssue] = []
        outdated: List[OutdatedPackage] = []
        typosquatting: List[TyposquattingMatch] = []

        if check_licenses:
            license_issues = self._check_licenses(dependencies, project_license)

        # Generate summary
        direct_deps = [d for d in dependencies if d.is_direct]
        dev_deps = [d for d in dependencies if d.is_dev]

        summary = {
            "total_dependencies": len(dependencies),
            "direct_dependencies": len(direct_deps),
            "dev_dependencies": len(dev_deps),
            "total_vulnerabilities": len(vulnerabilities),
            "critical_vulnerabilities": len([v for v in vulnerabilities if v.vulnerability.severity == VulnerabilitySeverity.CRITICAL]),
            "high_vulnerabilities": len([v for v in vulnerabilities if v.vulnerability.severity == VulnerabilitySeverity.HIGH]),
            "license_issues": len(license_issues),
            "outdated_packages": len(outdated),
            "typosquatting_alerts": len(typosquatting),
            "package_managers": [pm.value for pm in package_managers],
        }

        # Risk assessment
        risk_score = self._calculate_risk_score(vulnerabilities, license_issues)
        risk_level = "low"
        if risk_score >= 70:
            risk_level = "critical"
        elif risk_score >= 50:
            risk_level = "high"
        elif risk_score >= 30:
            risk_level = "medium"

        results = {
            "scan_id": scan_id,
            "project_path": str(project_path),
            "package_managers": [pm.value for pm in package_managers],
            "total_dependencies": len(dependencies),
            "vulnerabilities": [v.to_dict() for v in vulnerabilities],
            "license_issues": [li.to_dict() for li in license_issues],
            "outdated_packages": [o.to_dict() for o in outdated],
            "typosquatting_matches": [t.to_dict() for t in typosquatting],
            "summary": summary,
            "risk_assessment": {
                "risk_score": risk_score,
                "risk_level": risk_level,
            },
        }

        return self._create_response(results)

    def _parse_package_json(self, path: Path) -> List[Dependency]:
        """Parse npm package.json file."""
        dependencies = []
        try:
            with open(path) as f:
                data = json.load(f)

            # Regular dependencies
            for name, version_spec in data.get("dependencies", {}).items():
                version = self._clean_version(version_spec)
                dependencies.append(Dependency(
                    name=name,
                    version=version,
                    package_manager=PackageManager.NPM,
                    is_dev=False,
                    is_direct=True,
                ))

            # Dev dependencies
            for name, version_spec in data.get("devDependencies", {}).items():
                version = self._clean_version(version_spec)
                dependencies.append(Dependency(
                    name=name,
                    version=version,
                    package_manager=PackageManager.NPM,
                    is_dev=True,
                    is_direct=True,
                ))

        except (json.JSONDecodeError, IOError):
            pass

        return dependencies

    def _parse_requirements_txt(self, path: Path) -> List[Dependency]:
        """Parse pip requirements.txt file."""
        dependencies = []
        try:
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith("#") or line.startswith("-"):
                        continue

                    # Parse package==version, package>=version, etc.
                    match = re.match(r"^([a-zA-Z0-9_-]+)([<>=~!]+)?(.+)?$", line)
                    if match:
                        name = match.group(1)
                        version = match.group(3) or "unknown"
                        dependencies.append(Dependency(
                            name=name,
                            version=version.strip(),
                            package_manager=PackageManager.PIP,
                            is_dev=False,
                            is_direct=True,
                        ))

        except IOError:
            pass

        return dependencies

    def _parse_pyproject_toml(self, path: Path) -> List[Dependency]:
        """Parse poetry pyproject.toml file."""
        dependencies = []
        try:
            # Try to use tomllib (Python 3.11+) or tomli
            try:
                import tomllib
                with open(path, "rb") as f:
                    data = tomllib.load(f)
            except ImportError:
                try:
                    import tomli
                    with open(path, "rb") as f:
                        data = tomli.load(f)
                except ImportError:
                    return dependencies

            # Poetry dependencies
            poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
            for name, version_spec in poetry_deps.items():
                if name == "python":
                    continue
                if isinstance(version_spec, str):
                    version = self._clean_version(version_spec)
                else:
                    version = self._clean_version(version_spec.get("version", "unknown"))

                dependencies.append(Dependency(
                    name=name,
                    version=version,
                    package_manager=PackageManager.POETRY,
                    is_dev=False,
                    is_direct=True,
                ))

            # Dev dependencies
            dev_deps = data.get("tool", {}).get("poetry", {}).get("dev-dependencies", {})
            for name, version_spec in dev_deps.items():
                if isinstance(version_spec, str):
                    version = self._clean_version(version_spec)
                else:
                    version = self._clean_version(version_spec.get("version", "unknown"))

                dependencies.append(Dependency(
                    name=name,
                    version=version,
                    package_manager=PackageManager.POETRY,
                    is_dev=True,
                    is_direct=True,
                ))

        except (IOError, KeyError):
            pass

        return dependencies

    def _parse_cargo_toml(self, path: Path) -> List[Dependency]:
        """Parse Rust Cargo.toml file."""
        dependencies = []
        try:
            try:
                import tomllib
                with open(path, "rb") as f:
                    data = tomllib.load(f)
            except ImportError:
                try:
                    import tomli
                    with open(path, "rb") as f:
                        data = tomli.load(f)
                except ImportError:
                    return dependencies

            for name, version_spec in data.get("dependencies", {}).items():
                if isinstance(version_spec, str):
                    version = version_spec
                else:
                    version = version_spec.get("version", "unknown")

                dependencies.append(Dependency(
                    name=name,
                    version=version,
                    package_manager=PackageManager.CARGO,
                    is_dev=False,
                    is_direct=True,
                ))

        except (IOError, KeyError):
            pass

        return dependencies

    def _parse_go_mod(self, path: Path) -> List[Dependency]:
        """Parse Go go.mod file."""
        dependencies = []
        try:
            with open(path) as f:
                content = f.read()

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

    def _clean_version(self, version_spec: str) -> str:
        """Clean version specifier to get version number."""
        # Remove common prefixes like ^, ~, >=, etc.
        version = re.sub(r"^[\^~>=<]+", "", version_spec.strip())
        return version

    def _check_licenses(self, dependencies: List[Dependency], project_license: str) -> List[LicenseIssue]:
        """Check for license compliance issues."""
        issues = []
        is_permissive_project = project_license in PERMISSIVE_LICENSES

        for dep in dependencies:
            if dep.license is None:
                issues.append(LicenseIssue(
                    dependency=dep,
                    issue_type="missing_license",
                    severity="medium",
                    description=f"Package '{dep.name}' has no license information",
                    recommendation="Contact package maintainer or find alternative package",
                ))
            elif is_permissive_project and dep.license in COPYLEFT_LICENSES:
                issues.append(LicenseIssue(
                    dependency=dep,
                    issue_type="incompatible_license",
                    severity="high",
                    description=f"License '{dep.license}' is incompatible with project license '{project_license}'",
                    recommendation="Remove this dependency or change project license",
                ))

        return issues

    def _calculate_risk_score(self, vulnerabilities: List[DependencyVulnerability], license_issues: List[LicenseIssue]) -> float:
        """Calculate overall dependency risk score (0-100)."""
        score = 0.0

        # Vulnerability scoring
        for vuln in vulnerabilities:
            if vuln.vulnerability.severity == VulnerabilitySeverity.CRITICAL:
                score += 25
            elif vuln.vulnerability.severity == VulnerabilitySeverity.HIGH:
                score += 15
            elif vuln.vulnerability.severity == VulnerabilitySeverity.MEDIUM:
                score += 8
            elif vuln.vulnerability.severity == VulnerabilitySeverity.LOW:
                score += 3

        # License issue scoring
        for issue in license_issues:
            if issue.severity == "high":
                score += 10
            elif issue.severity == "medium":
                score += 5

        return min(100.0, score)


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
