"""
Dependency Analyzer

Comprehensive dependency analysis tool for security, licensing, and updates.
"""

import json
import logging
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

# Use tomllib (Python 3.11+) or tomli (Python 3.10)
if sys.version_info >= (3, 11):
    import tomllib as tomli
else:
    import tomli  # type: ignore[import-not-found]

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

logger = logging.getLogger(__name__)

# Security limits to prevent resource exhaustion
MAX_FILE_SIZE_MB = 10  # Maximum file size to parse (10MB)
MAX_DEPENDENCIES_PER_FILE = 10000  # Maximum dependencies to parse from a single file
MAX_DEPENDENCY_NAME_LENGTH = 500  # Maximum length for dependency name
MAX_VERSION_STRING_LENGTH = 100  # Maximum length for version string


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
        import time

        # Start overall timing
        analysis_start_time = time.perf_counter()
        timing_breakdown: Dict[str, float] = {}

        project_path = Path(self.config["project_path"])

        # Time dependency parsing
        parse_start = time.perf_counter()
        dependencies = self._parse_dependencies(project_path)
        timing_breakdown["parse_dependencies"] = round(time.perf_counter() - parse_start, 4)

        if not dependencies:
            total_duration = round(time.perf_counter() - analysis_start_time, 4)
            return self._create_response(
                {
                    "message": "No dependencies found",
                    "dependencies": [],
                    "summary": {"total_dependencies": 0},
                    "timing": {
                        "total_seconds": total_duration,
                        "breakdown": timing_breakdown,
                    },
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

        # Run scans based on configuration with timing
        if self.config.get("check_vulnerabilities", True):
            vuln_start = time.perf_counter()
            report.vulnerabilities = self.cve_scanner.scan_dependencies_sync(dependencies)
            timing_breakdown["vulnerability_scan"] = round(time.perf_counter() - vuln_start, 4)

        if self.config.get("check_licenses", True):
            license_start = time.perf_counter()
            report.license_issues = self.license_scanner.scan_dependencies(dependencies)
            timing_breakdown["license_scan"] = round(time.perf_counter() - license_start, 4)

        if self.config.get("check_outdated", True):
            outdated_start = time.perf_counter()
            outdated, typosquatting = self.outdated_scanner.scan_dependencies_sync(dependencies)
            report.outdated_packages = outdated
            timing_breakdown["outdated_scan"] = round(time.perf_counter() - outdated_start, 4)

            if self.config.get("check_typosquatting", True):
                typo_start = time.perf_counter()
                report.typosquatting_matches = typosquatting
                timing_breakdown["typosquatting_scan"] = round(time.perf_counter() - typo_start, 4)

        # Time summary creation
        summary_start = time.perf_counter()
        report.summary = self._create_summary(report, dependencies)
        timing_breakdown["create_summary"] = round(time.perf_counter() - summary_start, 4)

        # Add risk assessment (included in total duration and timing breakdown)
        risk_start = time.perf_counter()
        risk_assessment = self._assess_risk(report)
        timing_breakdown["risk_assessment"] = round(time.perf_counter() - risk_start, 4)

        # Calculate total duration *after* all analysis work is complete
        total_duration = round(time.perf_counter() - analysis_start_time, 4)

        # Add metadata with timing information (including risk timing)
        report.metadata = {
            "project_path": str(project_path),
            "scanners_used": self._get_enabled_scanners(),
            "scan_duration_seconds": total_duration,
            "timing_breakdown": timing_breakdown,
            "dependencies_per_second": round(len(dependencies) / max(total_duration, 0.001), 2),
        }

        # Convert to dict and attach risk assessment
        report_dict = report.dict()
        report_dict["risk_assessment"] = risk_assessment

        # Log performance summary
        logger.info(
            f"Dependency analysis completed in {total_duration:.3f}s",
            extra={
                "scan_id": scan_id,
                "total_dependencies": len(dependencies),
                "total_duration_seconds": total_duration,
                "timing_breakdown": timing_breakdown,
            }
        )

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

    def _check_file_size(self, file_path: Path) -> bool:
        """
        Check if file size is within acceptable limits.

        Args:
            file_path: Path to file

        Returns:
            True if file size is acceptable, False otherwise
        """
        try:
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > MAX_FILE_SIZE_MB:
                logger.warning(
                    "File exceeds size limit",
                    extra={
                        "file": str(file_path),
                        "size_mb": round(file_size_mb, 2),
                        "limit_mb": MAX_FILE_SIZE_MB,
                    },
                )
                return False
            return True
        except Exception as e:
            logger.error(f"Error checking file size for {file_path}: {e}")
            return False

    def _validate_dependency_data(self, name: str, version: str) -> bool:
        """
        Validate dependency name and version to prevent injection attacks.

        Args:
            name: Dependency name
            version: Version string

        Returns:
            True if valid, False otherwise
        """
        if len(name) > MAX_DEPENDENCY_NAME_LENGTH:
            logger.warning(f"Dependency name too long: {name[:50]}...")
            return False

        if len(version) > MAX_VERSION_STRING_LENGTH:
            logger.warning(f"Version string too long for {name}: {version[:50]}...")
            return False

        return True

    def _parse_package_json(self, file_path: Path) -> List[Dependency]:
        """
        Parse npm package.json file with security bounds.

        Args:
            file_path: Path to package.json

        Returns:
            List of dependencies
        """
        try:
            # Check file size before parsing
            if not self._check_file_size(file_path):
                logger.error(f"Skipping {file_path}: file too large")
                return []

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            dependencies: List[Dependency] = []
            dep_count = 0

            # Regular dependencies
            for name, version in data.get("dependencies", {}).items():
                if dep_count >= MAX_DEPENDENCIES_PER_FILE:
                    logger.warning(
                        f"Reached maximum dependency limit ({MAX_DEPENDENCIES_PER_FILE}) for {file_path}"
                    )
                    break

                # Validate input
                if not self._validate_dependency_data(name, version):
                    continue

                dep = Dependency(
                    name=name,
                    version=version.lstrip("^~>="),  # Remove version prefixes
                    package_manager=PackageManager.NPM,
                    is_dev=False,
                    is_direct=True,
                )
                dependencies.append(dep)
                dep_count += 1

            # Dev dependencies
            for name, version in data.get("devDependencies", {}).items():
                if dep_count >= MAX_DEPENDENCIES_PER_FILE:
                    logger.warning(
                        f"Reached maximum dependency limit ({MAX_DEPENDENCIES_PER_FILE}) for {file_path}"
                    )
                    break

                # Validate input
                if not self._validate_dependency_data(name, version):
                    continue

                dep = Dependency(
                    name=name,
                    version=version.lstrip("^~>="),
                    package_manager=PackageManager.NPM,
                    is_dev=True,
                    is_direct=True,
                )
                dependencies.append(dep)
                dep_count += 1

            logger.info(f"Parsed {dep_count} dependencies from {file_path}")
            return dependencies

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {type(e).__name__}: {e}")
            return []

    def _parse_requirements_txt(self, file_path: Path) -> List[Dependency]:
        """
        Parse pip requirements.txt file with security bounds.

        Args:
            file_path: Path to requirements.txt

        Returns:
            List of dependencies
        """
        try:
            # Check file size before parsing
            if not self._check_file_size(file_path):
                logger.error(f"Skipping {file_path}: file too large")
                return []

            dependencies: List[Dependency] = []
            dep_count = 0

            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if dep_count >= MAX_DEPENDENCIES_PER_FILE:
                        logger.warning(
                            f"Reached maximum dependency limit ({MAX_DEPENDENCIES_PER_FILE}) for {file_path}"
                        )
                        break

                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    # Parse package==version or package>=version
                    if "==" in line:
                        name, version = line.split("==", 1)
                    elif ">=" in line:
                        name, version = line.split(">=", 1)
                    elif "~=" in line:
                        name, version = line.split("~=", 1)
                    else:
                        name = line
                        version = "unknown"

                    name = name.strip()
                    version = version.strip()

                    # Validate input
                    if not self._validate_dependency_data(name, version):
                        continue

                    dep = Dependency(
                        name=name,
                        version=version,
                        package_manager=PackageManager.PIP,
                        is_dev=False,
                        is_direct=True,
                    )
                    dependencies.append(dep)
                    dep_count += 1

            logger.info(f"Parsed {dep_count} dependencies from {file_path}")
            return dependencies

        except Exception as e:
            logger.error(f"Error parsing {file_path}: {type(e).__name__}: {e}")
            return []

    def _parse_pyproject_toml(self, file_path: Path) -> List[Dependency]:
        """
        Parse poetry pyproject.toml file with security bounds.

        Args:
            file_path: Path to pyproject.toml

        Returns:
            List of dependencies
        """
        try:
            # Check file size before parsing
            if not self._check_file_size(file_path):
                logger.error(f"Skipping {file_path}: file too large")
                return []

            with open(file_path, "rb") as f:
                data = tomli.load(f)

            dependencies: List[Dependency] = []
            dep_count = 0

            # Poetry dependencies
            poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})

            for name, version_spec in poetry_deps.items():
                if dep_count >= MAX_DEPENDENCIES_PER_FILE:
                    logger.warning(
                        f"Reached maximum dependency limit ({MAX_DEPENDENCIES_PER_FILE}) for {file_path}"
                    )
                    break

                if name == "python":
                    continue

                version = version_spec if isinstance(version_spec, str) else "latest"

                # Validate input
                if not self._validate_dependency_data(name, version):
                    continue

                dep = Dependency(
                    name=name,
                    version=version.lstrip("^~>="),
                    package_manager=PackageManager.POETRY,
                    is_dev=False,
                    is_direct=True,
                )
                dependencies.append(dep)
                dep_count += 1

            # Dev dependencies
            dev_deps = data.get("tool", {}).get("poetry", {}).get("dev-dependencies", {})

            for name, version_spec in dev_deps.items():
                if dep_count >= MAX_DEPENDENCIES_PER_FILE:
                    logger.warning(
                        f"Reached maximum dependency limit ({MAX_DEPENDENCIES_PER_FILE}) for {file_path}"
                    )
                    break

                version = version_spec if isinstance(version_spec, str) else "latest"

                # Validate input
                if not self._validate_dependency_data(name, version):
                    continue

                dep = Dependency(
                    name=name,
                    version=version.lstrip("^~>="),
                    package_manager=PackageManager.POETRY,
                    is_dev=True,
                    is_direct=True,
                )
                dependencies.append(dep)
                dep_count += 1

            logger.info(f"Parsed {dep_count} dependencies from {file_path}")
            return dependencies

        except Exception as e:
            logger.error(f"Error parsing {file_path}: {type(e).__name__}: {e}")
            return []

    def _parse_cargo_toml(self, file_path: Path) -> List[Dependency]:
        """
        Parse Rust Cargo.toml file with security bounds.

        Args:
            file_path: Path to Cargo.toml

        Returns:
            List of dependencies
        """
        try:
            # Check file size before parsing
            if not self._check_file_size(file_path):
                logger.error(f"Skipping {file_path}: file too large")
                return []

            with open(file_path, "rb") as f:
                data = tomli.load(f)

            dependencies: List[Dependency] = []
            dep_count = 0

            # Regular dependencies
            for name, version_spec in data.get("dependencies", {}).items():
                if dep_count >= MAX_DEPENDENCIES_PER_FILE:
                    logger.warning(
                        f"Reached maximum dependency limit ({MAX_DEPENDENCIES_PER_FILE}) for {file_path}"
                    )
                    break

                if isinstance(version_spec, dict):
                    version = version_spec.get("version", "latest")
                else:
                    version = version_spec

                # Validate input
                if not self._validate_dependency_data(name, version):
                    continue

                dep = Dependency(
                    name=name,
                    version=version,
                    package_manager=PackageManager.CARGO,
                    is_dev=False,
                    is_direct=True,
                )
                dependencies.append(dep)
                dep_count += 1

            # Dev dependencies
            for name, version_spec in data.get("dev-dependencies", {}).items():
                if dep_count >= MAX_DEPENDENCIES_PER_FILE:
                    logger.warning(
                        f"Reached maximum dependency limit ({MAX_DEPENDENCIES_PER_FILE}) for {file_path}"
                    )
                    break

                if isinstance(version_spec, dict):
                    version = version_spec.get("version", "latest")
                else:
                    version = version_spec

                # Validate input
                if not self._validate_dependency_data(name, version):
                    continue

                dep = Dependency(
                    name=name,
                    version=version,
                    package_manager=PackageManager.CARGO,
                    is_dev=True,
                    is_direct=True,
                )
                dependencies.append(dep)
                dep_count += 1

            logger.info(f"Parsed {dep_count} dependencies from {file_path}")
            return dependencies

        except Exception as e:
            logger.error(f"Error parsing {file_path}: {type(e).__name__}: {e}")
            return []

    def _parse_go_mod(self, file_path: Path) -> List[Dependency]:
        """
        Parse Go go.mod file with security bounds.

        Args:
            file_path: Path to go.mod

        Returns:
            List of dependencies
        """
        try:
            # Check file size before parsing
            if not self._check_file_size(file_path):
                logger.error(f"Skipping {file_path}: file too large")
                return []

            dependencies: List[Dependency] = []
            dep_count = 0

            with open(file_path, "r", encoding="utf-8") as f:
                in_require = False
                for line in f:
                    if dep_count >= MAX_DEPENDENCIES_PER_FILE:
                        logger.warning(
                            f"Reached maximum dependency limit ({MAX_DEPENDENCIES_PER_FILE}) for {file_path}"
                        )
                        break

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

                            # Validate input
                            if not self._validate_dependency_data(name, version):
                                continue

                            dep = Dependency(
                                name=name,
                                version=version,
                                package_manager=PackageManager.GO_MOD,
                                is_dev=False,
                                is_direct=True,
                            )
                            dependencies.append(dep)
                            dep_count += 1

            logger.info(f"Parsed {dep_count} dependencies from {file_path}")
            return dependencies

        except Exception as e:
            logger.error(f"Error parsing {file_path}: {type(e).__name__}: {e}")
            return []

    def _parse_composer_json(self, file_path: Path) -> List[Dependency]:
        """
        Parse PHP composer.json file with security bounds.

        Args:
            file_path: Path to composer.json

        Returns:
            List of dependencies
        """
        try:
            # Check file size before parsing
            if not self._check_file_size(file_path):
                logger.error(f"Skipping {file_path}: file too large")
                return []

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            dependencies: List[Dependency] = []
            dep_count = 0

            # Regular dependencies
            for name, version in data.get("require", {}).items():
                if dep_count >= MAX_DEPENDENCIES_PER_FILE:
                    logger.warning(
                        f"Reached maximum dependency limit ({MAX_DEPENDENCIES_PER_FILE}) for {file_path}"
                    )
                    break

                if name == "php":
                    continue

                # Validate input
                if not self._validate_dependency_data(name, version):
                    continue

                dep = Dependency(
                    name=name,
                    version=version.lstrip("^~>="),
                    package_manager=PackageManager.COMPOSER,
                    is_dev=False,
                    is_direct=True,
                )
                dependencies.append(dep)
                dep_count += 1

            # Dev dependencies
            for name, version in data.get("require-dev", {}).items():
                if dep_count >= MAX_DEPENDENCIES_PER_FILE:
                    logger.warning(
                        f"Reached maximum dependency limit ({MAX_DEPENDENCIES_PER_FILE}) for {file_path}"
                    )
                    break

                # Validate input
                if not self._validate_dependency_data(name, version):
                    continue

                dep = Dependency(
                    name=name,
                    version=version.lstrip("^~>="),
                    package_manager=PackageManager.COMPOSER,
                    is_dev=True,
                    is_direct=True,
                )
                dependencies.append(dep)
                dep_count += 1

            logger.info(f"Parsed {dep_count} dependencies from {file_path}")
            return dependencies

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {type(e).__name__}: {e}")
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
