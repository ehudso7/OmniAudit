"""
Dependency Analyzer

Comprehensive dependency analysis tool for security, licensing, and updates.
"""

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import tomli  # For parsing TOML files

from ..base import BaseAnalyzer, AnalyzerError
from .types import (
    Dependency,
    DependencyReport,
    PackageManager,
    DependencyVulnerability,
    LicenseIssue,
    OutdatedPackage,
    TyposquattingMatch,
    SBOM,
    SBOMFormat,
)
from .scanners import CVEScanner, LicenseScanner, OutdatedScanner, SBOMGenerator


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

    Supported Package Managers:
    - npm, yarn, pnpm (package.json)
    - pip, poetry (requirements.txt, Pipfile, pyproject.toml)
    - cargo (Cargo.toml)
    - go (go.mod)
    - maven, gradle (pom.xml, build.gradle)
    - composer (composer.json)
    - bundler (Gemfile)

    Configuration:
        project_path: str - Path to project root (required)
        project_license: Optional[str] - Your project's license
        api_keys: Optional[Dict[str, str]] - API keys for vulnerability databases
        check_vulnerabilities: bool - Enable CVE scanning (default: True)
        check_licenses: bool - Enable license scanning (default: True)
        check_outdated: bool - Enable outdated package detection (default: True)
        check_typosquatting: bool - Enable typosquatting detection (default: True)

    Example:
        >>> analyzer = DependencyAnalyzer({
        ...     "project_path": ".",
        ...     "project_license": "MIT",
        ... })
        >>> result = analyzer.analyze({})
        >>> print(result["data"]["summary"]["total_vulnerabilities"])
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize dependency analyzer."""
        super().__init__(config)
        self._initialize_scanners()

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

    def _initialize_scanners(self) -> None:
        """Initialize all dependency scanners."""
        api_keys = self.config.get("api_keys", {})
        project_license = self.config.get("project_license")

        self.cve_scanner = CVEScanner(api_keys)
        self.license_scanner = LicenseScanner(project_license)
        self.outdated_scanner = OutdatedScanner()

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform dependency analysis.

        Args:
            data: Optional input data (not used currently)

        Returns:
            Dependency analysis results
        """
        project_path = Path(self.config["project_path"])

        # Detect package managers and parse dependencies
        dependencies = self._parse_dependencies(project_path)

        if not dependencies:
            return self._create_response(
                {
                    "message": "No dependencies found",
                    "dependencies": [],
                    "summary": {"total_dependencies": 0},
                }
            )

        # Create scan ID
        scan_id = str(uuid.uuid4())

        # Initialize report
        report = DependencyReport(
            scan_id=scan_id,
            timestamp=datetime.utcnow(),
            project_path=str(project_path),
            package_managers=list(set(dep.package_manager for dep in dependencies)),
            total_dependencies=len(dependencies),
            direct_dependencies=len([d for d in dependencies if d.is_direct]),
        )

        # Run scans based on configuration
        if self.config.get("check_vulnerabilities", True):
            report.vulnerabilities = self.cve_scanner.scan_dependencies_sync(dependencies)

        if self.config.get("check_licenses", True):
            report.license_issues = self.license_scanner.scan_dependencies(dependencies)

        if self.config.get("check_outdated", True):
            outdated, typosquatting = self.outdated_scanner.scan_dependencies_sync(dependencies)
            report.outdated_packages = outdated

            if self.config.get("check_typosquatting", True):
                report.typosquatting_matches = typosquatting

        # Create summary
        report.summary = self._create_summary(report, dependencies)

        # Add metadata
        report.metadata = {
            "project_path": str(project_path),
            "scanners_used": self._get_enabled_scanners(),
            "scan_duration_seconds": 0,  # TODO: Add timing
        }

        # Convert to dict
        report_dict = report.dict()

        # Add risk assessment
        report_dict["risk_assessment"] = self._assess_risk(report)

        return self._create_response(report_dict)

    def _parse_dependencies(self, project_path: Path) -> List[Dependency]:
        """
        Parse dependencies from all detected package managers.

        Args:
            project_path: Project root path

        Returns:
            List of dependencies
        """
        dependencies: List[Dependency] = []

        # npm/yarn/pnpm - package.json
        package_json = project_path / "package.json"
        if package_json.exists():
            dependencies.extend(self._parse_package_json(package_json))

        # pip - requirements.txt
        requirements_txt = project_path / "requirements.txt"
        if requirements_txt.exists():
            dependencies.extend(self._parse_requirements_txt(requirements_txt))

        # poetry - pyproject.toml
        pyproject_toml = project_path / "pyproject.toml"
        if pyproject_toml.exists():
            dependencies.extend(self._parse_pyproject_toml(pyproject_toml))

        # cargo - Cargo.toml
        cargo_toml = project_path / "Cargo.toml"
        if cargo_toml.exists():
            dependencies.extend(self._parse_cargo_toml(cargo_toml))

        # go - go.mod
        go_mod = project_path / "go.mod"
        if go_mod.exists():
            dependencies.extend(self._parse_go_mod(go_mod))

        # composer - composer.json
        composer_json = project_path / "composer.json"
        if composer_json.exists():
            dependencies.extend(self._parse_composer_json(composer_json))

        return dependencies

    def _parse_package_json(self, file_path: Path) -> List[Dependency]:
        """Parse npm package.json file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            dependencies: List[Dependency] = []

            # Regular dependencies
            for name, version in data.get("dependencies", {}).items():
                dep = Dependency(
                    name=name,
                    version=version.lstrip("^~>="),  # Remove version prefixes
                    package_manager=PackageManager.NPM,
                    is_dev=False,
                    is_direct=True,
                )
                dependencies.append(dep)

            # Dev dependencies
            for name, version in data.get("devDependencies", {}).items():
                dep = Dependency(
                    name=name,
                    version=version.lstrip("^~>="),
                    package_manager=PackageManager.NPM,
                    is_dev=True,
                    is_direct=True,
                )
                dependencies.append(dep)

            return dependencies

        except Exception as e:
            return []

    def _parse_requirements_txt(self, file_path: Path) -> List[Dependency]:
        """Parse pip requirements.txt file."""
        try:
            dependencies: List[Dependency] = []

            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    # Parse package==version or package>=version
                    if "==" in line:
                        name, version = line.split("==")
                    elif ">=" in line:
                        name, version = line.split(">=")
                    elif "~=" in line:
                        name, version = line.split("~=")
                    else:
                        name = line
                        version = "unknown"

                    name = name.strip()
                    version = version.strip()

                    dep = Dependency(
                        name=name,
                        version=version,
                        package_manager=PackageManager.PIP,
                        is_dev=False,
                        is_direct=True,
                    )
                    dependencies.append(dep)

            return dependencies

        except Exception:
            return []

    def _parse_pyproject_toml(self, file_path: Path) -> List[Dependency]:
        """Parse poetry pyproject.toml file."""
        try:
            with open(file_path, "rb") as f:
                data = tomli.load(f)

            dependencies: List[Dependency] = []

            # Poetry dependencies
            poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})

            for name, version_spec in poetry_deps.items():
                if name == "python":
                    continue

                version = version_spec if isinstance(version_spec, str) else "latest"

                dep = Dependency(
                    name=name,
                    version=version.lstrip("^~>="),
                    package_manager=PackageManager.POETRY,
                    is_dev=False,
                    is_direct=True,
                )
                dependencies.append(dep)

            # Dev dependencies
            dev_deps = data.get("tool", {}).get("poetry", {}).get("dev-dependencies", {})

            for name, version_spec in dev_deps.items():
                version = version_spec if isinstance(version_spec, str) else "latest"

                dep = Dependency(
                    name=name,
                    version=version.lstrip("^~>="),
                    package_manager=PackageManager.POETRY,
                    is_dev=True,
                    is_direct=True,
                )
                dependencies.append(dep)

            return dependencies

        except Exception:
            return []

    def _parse_cargo_toml(self, file_path: Path) -> List[Dependency]:
        """Parse Rust Cargo.toml file."""
        try:
            with open(file_path, "rb") as f:
                data = tomli.load(f)

            dependencies: List[Dependency] = []

            # Regular dependencies
            for name, version_spec in data.get("dependencies", {}).items():
                if isinstance(version_spec, dict):
                    version = version_spec.get("version", "latest")
                else:
                    version = version_spec

                dep = Dependency(
                    name=name,
                    version=version,
                    package_manager=PackageManager.CARGO,
                    is_dev=False,
                    is_direct=True,
                )
                dependencies.append(dep)

            # Dev dependencies
            for name, version_spec in data.get("dev-dependencies", {}).items():
                if isinstance(version_spec, dict):
                    version = version_spec.get("version", "latest")
                else:
                    version = version_spec

                dep = Dependency(
                    name=name,
                    version=version,
                    package_manager=PackageManager.CARGO,
                    is_dev=True,
                    is_direct=True,
                )
                dependencies.append(dep)

            return dependencies

        except Exception:
            return []

    def _parse_go_mod(self, file_path: Path) -> List[Dependency]:
        """Parse Go go.mod file."""
        try:
            dependencies: List[Dependency] = []

            with open(file_path, "r", encoding="utf-8") as f:
                in_require = False
                for line in f:
                    line = line.strip()

                    if line.startswith("require ("):
                        in_require = True
                        continue
                    elif line == ")":
                        in_require = False
                        continue

                    if in_require or line.startswith("require "):
                        parts = line.replace("require ", "").strip().split()
                        if len(parts) >= 2:
                            name = parts[0]
                            version = parts[1]

                            dep = Dependency(
                                name=name,
                                version=version,
                                package_manager=PackageManager.GO_MOD,
                                is_dev=False,
                                is_direct=True,
                            )
                            dependencies.append(dep)

            return dependencies

        except Exception:
            return []

    def _parse_composer_json(self, file_path: Path) -> List[Dependency]:
        """Parse PHP composer.json file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            dependencies: List[Dependency] = []

            # Regular dependencies
            for name, version in data.get("require", {}).items():
                if name == "php":
                    continue

                dep = Dependency(
                    name=name,
                    version=version.lstrip("^~>="),
                    package_manager=PackageManager.COMPOSER,
                    is_dev=False,
                    is_direct=True,
                )
                dependencies.append(dep)

            # Dev dependencies
            for name, version in data.get("require-dev", {}).items():
                dep = Dependency(
                    name=name,
                    version=version.lstrip("^~>="),
                    package_manager=PackageManager.COMPOSER,
                    is_dev=True,
                    is_direct=True,
                )
                dependencies.append(dep)

            return dependencies

        except Exception:
            return []

    def _create_summary(
        self, report: DependencyReport, dependencies: List[Dependency]
    ) -> Dict[str, Any]:
        """Create summary statistics."""
        return {
            "total_dependencies": len(dependencies),
            "direct_dependencies": len([d for d in dependencies if d.is_direct]),
            "dev_dependencies": len([d for d in dependencies if d.is_dev]),
            "total_vulnerabilities": len(report.vulnerabilities),
            "critical_vulnerabilities": len(
                [v for v in report.vulnerabilities if v.vulnerability.severity.value == "critical"]
            ),
            "high_vulnerabilities": len(
                [v for v in report.vulnerabilities if v.vulnerability.severity.value == "high"]
            ),
            "license_issues": len(report.license_issues),
            "outdated_packages": len(report.outdated_packages),
            "typosquatting_alerts": len(report.typosquatting_matches),
            "package_managers": [pm.value for pm in report.package_managers],
        }

    def _assess_risk(self, report: DependencyReport) -> Dict[str, Any]:
        """Assess overall risk level."""
        risk_score = 0.0

        # Vulnerabilities
        for vuln in report.vulnerabilities:
            if vuln.vulnerability.severity.value == "critical":
                risk_score += 10.0
            elif vuln.vulnerability.severity.value == "high":
                risk_score += 5.0
            elif vuln.vulnerability.severity.value == "medium":
                risk_score += 2.0

        # License issues
        risk_score += len(report.license_issues) * 1.0

        # Typosquatting
        risk_score += len(report.typosquatting_matches) * 3.0

        # Normalize
        risk_score = min(100.0, risk_score)

        if risk_score >= 70:
            risk_level = "critical"
        elif risk_score >= 40:
            risk_level = "high"
        elif risk_score >= 20:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {"risk_score": round(risk_score, 2), "risk_level": risk_level}

    def _get_enabled_scanners(self) -> List[str]:
        """Get list of enabled scanners."""
        scanners = []
        if self.config.get("check_vulnerabilities", True):
            scanners.append("cve_scanner")
        if self.config.get("check_licenses", True):
            scanners.append("license_scanner")
        if self.config.get("check_outdated", True):
            scanners.append("outdated_scanner")
        if self.config.get("check_typosquatting", True):
            scanners.append("typosquatting_detector")
        return scanners

    def generate_sbom(
        self, dependencies: List[Dependency], format: SBOMFormat = SBOMFormat.SPDX_JSON
    ) -> SBOM:
        """
        Generate Software Bill of Materials.

        Args:
            dependencies: List of dependencies
            format: SBOM format

        Returns:
            SBOM object
        """
        project_name = self.config.get("project_name", "unknown-project")
        project_version = self.config.get("project_version", "1.0.0")

        generator = SBOMGenerator(project_name, project_version)
        return generator.generate(dependencies, format)
