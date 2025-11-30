"""
Dependency Analyzer Module

Analyzes project dependencies for vulnerabilities and issues.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
import re

from .base import BaseAnalyzer, AnalyzerError


class PackageManager(Enum):
    """Supported package managers."""
    NPM = "npm"
    PIP = "pip"
    POETRY = "poetry"
    CARGO = "cargo"
    GO = "go"
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
    vulnerabilities: List[Dict[str, Any]] = field(default_factory=list)
    latest_version: Optional[str] = None

    @property
    def is_vulnerable(self) -> bool:
        return len(self.vulnerabilities) > 0

    @property
    def is_outdated(self) -> bool:
        return self.latest_version and self.latest_version != self.version

    def to_dict(self) -> Dict[str, Any]:
        """Convert dependency to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "package_manager": self.package_manager.value,
            "is_dev": self.is_dev,
            "is_direct": self.is_direct,
            "vulnerabilities": self.vulnerabilities,
            "latest_version": self.latest_version,
            "is_vulnerable": self.is_vulnerable,
            "is_outdated": self.is_outdated,
        }


@dataclass
class DependencyReport:
    """Dependency analysis report."""
    dependencies: List[Dependency] = field(default_factory=list)
    total_dependencies: int = 0
    vulnerable_count: int = 0
    outdated_count: int = 0
    scan_duration_ms: float = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "dependencies": [d.to_dict() for d in self.dependencies],
            "summary": {
                "total": self.total_dependencies,
                "vulnerable": self.vulnerable_count,
                "outdated": self.outdated_count,
                "direct": sum(1 for d in self.dependencies if d.is_direct),
                "dev": sum(1 for d in self.dependencies if d.is_dev),
            },
            "scan_duration_ms": self.scan_duration_ms,
        }


class DependencyAnalyzer(BaseAnalyzer):
    """
    Analyzes project dependencies.

    Parses various dependency files:
    - package.json (npm)
    - requirements.txt (pip)
    - pyproject.toml (poetry)
    - Cargo.toml (rust)
    - go.mod (go)
    """

    def __init__(self):
        """Initialize dependency analyzer."""
        pass

    async def analyze(self, content: str, filename: str = "unknown") -> DependencyReport:
        """
        Analyze dependency file content.

        Args:
            content: Content of dependency file
            filename: Name of the dependency file

        Returns:
            DependencyReport with parsed dependencies
        """
        import time
        start_time = time.time()

        dependencies: List[Dependency] = []

        if "package.json" in filename:
            dependencies = self._parse_package_json(content)
        elif "requirements" in filename and filename.endswith(".txt"):
            dependencies = self._parse_requirements_txt(content)
        elif "pyproject.toml" in filename:
            dependencies = self._parse_pyproject_toml(content)
        elif "Cargo.toml" in filename:
            dependencies = self._parse_cargo_toml(content)
        elif "go.mod" in filename:
            dependencies = self._parse_go_mod(content)

        duration_ms = (time.time() - start_time) * 1000

        return DependencyReport(
            dependencies=dependencies,
            total_dependencies=len(dependencies),
            vulnerable_count=sum(1 for d in dependencies if d.is_vulnerable),
            outdated_count=sum(1 for d in dependencies if d.is_outdated),
            scan_duration_ms=duration_ms,
        )

    def _parse_package_json(self, content: str) -> List[Dependency]:
        """Parse npm package.json file."""
        import json
        dependencies = []

        try:
            data = json.loads(content)

            # Production dependencies
            for name, version in data.get("dependencies", {}).items():
                dependencies.append(Dependency(
                    name=name,
                    version=version.lstrip("^~>=<"),
                    package_manager=PackageManager.NPM,
                    is_dev=False,
                ))

            # Dev dependencies
            for name, version in data.get("devDependencies", {}).items():
                dependencies.append(Dependency(
                    name=name,
                    version=version.lstrip("^~>=<"),
                    package_manager=PackageManager.NPM,
                    is_dev=True,
                ))

        except json.JSONDecodeError:
            pass

        return dependencies

    def _parse_requirements_txt(self, content: str) -> List[Dependency]:
        """Parse pip requirements.txt file."""
        dependencies = []

        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('-'):
                continue

            # Parse package==version or package>=version
            match = re.match(r'^([a-zA-Z0-9_-]+)(?:[=<>!]+(.+))?', line)
            if match:
                name = match.group(1)
                version = match.group(2) or "latest"
                dependencies.append(Dependency(
                    name=name,
                    version=version,
                    package_manager=PackageManager.PIP,
                ))

        return dependencies

    def _parse_pyproject_toml(self, content: str) -> List[Dependency]:
        """Parse Poetry pyproject.toml file."""
        dependencies = []

        # Simple regex-based parsing for dependencies
        in_deps = False
        in_dev_deps = False

        for line in content.split('\n'):
            line = line.strip()

            if "[tool.poetry.dependencies]" in line:
                in_deps = True
                in_dev_deps = False
            elif "[tool.poetry.dev-dependencies]" in line or "[tool.poetry.group.dev.dependencies]" in line:
                in_deps = False
                in_dev_deps = True
            elif line.startswith('['):
                in_deps = False
                in_dev_deps = False
            elif (in_deps or in_dev_deps) and '=' in line:
                match = re.match(r'^([a-zA-Z0-9_-]+)\s*=\s*["\']?([^"\']+)["\']?', line)
                if match:
                    name = match.group(1)
                    version = match.group(2).strip()
                    if name != "python":
                        dependencies.append(Dependency(
                            name=name,
                            version=version,
                            package_manager=PackageManager.POETRY,
                            is_dev=in_dev_deps,
                        ))

        return dependencies

    def _parse_cargo_toml(self, content: str) -> List[Dependency]:
        """Parse Rust Cargo.toml file."""
        dependencies = []

        in_deps = False
        in_dev_deps = False

        for line in content.split('\n'):
            line = line.strip()

            if "[dependencies]" in line:
                in_deps = True
                in_dev_deps = False
            elif "[dev-dependencies]" in line:
                in_deps = False
                in_dev_deps = True
            elif line.startswith('['):
                in_deps = False
                in_dev_deps = False
            elif (in_deps or in_dev_deps) and '=' in line:
                match = re.match(r'^([a-zA-Z0-9_-]+)\s*=\s*["\']?([^"\']+)["\']?', line)
                if match:
                    dependencies.append(Dependency(
                        name=match.group(1),
                        version=match.group(2).strip(),
                        package_manager=PackageManager.CARGO,
                        is_dev=in_dev_deps,
                    ))

        return dependencies

    def _parse_go_mod(self, content: str) -> List[Dependency]:
        """Parse Go go.mod file."""
        dependencies = []

        for line in content.split('\n'):
            line = line.strip()

            # Match: require github.com/foo/bar v1.2.3
            # Or lines inside require block
            match = re.match(r'^(?:require\s+)?([a-zA-Z0-9._/-]+)\s+v?(\d+\.\d+\.\d+)', line)
            if match:
                dependencies.append(Dependency(
                    name=match.group(1),
                    version=match.group(2),
                    package_manager=PackageManager.GO,
                ))

        return dependencies
