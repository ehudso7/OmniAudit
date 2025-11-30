"""
Unit tests for DependencyAnalyzer.

Tests the dependency analysis functionality available in dependencies.py.
"""

import pytest
import json
from pathlib import Path
from omniaudit.analyzers.dependencies import (
    DependencyAnalyzer,
    Dependency,
    DependencyReport,
    PackageManager,
)
from omniaudit.analyzers.base import AnalyzerError


class TestDependencyAnalyzer:
    """Test DependencyAnalyzer class."""

    def test_analyzer_properties(self, tmp_path):
        """Test analyzer properties."""
        config = {"project_path": str(tmp_path)}
        analyzer = DependencyAnalyzer(config)

        assert analyzer.name == "dependency_analyzer"
        assert analyzer.version == "1.0.0"

    def test_analyzer_nonexistent_path(self):
        """Test error when project path doesn't exist."""
        with pytest.raises(AnalyzerError, match="does not exist"):
            DependencyAnalyzer({"project_path": "/nonexistent"})

    def test_parse_package_json(self, tmp_path):
        """Test parsing npm package.json."""
        package_json = tmp_path / "package.json"
        package_json.write_text(
            json.dumps(
                {
                    "dependencies": {"react": "^18.0.0", "axios": "~1.0.0"},
                    "devDependencies": {"jest": ">=29.0.0"},
                }
            )
        )

        config = {"project_path": str(tmp_path)}
        analyzer = DependencyAnalyzer(config)

        dependencies = analyzer._parse_package_json(package_json)

        assert len(dependencies) == 3
        assert any(d.name == "react" for d in dependencies)
        assert any(d.name == "jest" and d.is_dev for d in dependencies)

    def test_parse_requirements_txt(self, tmp_path):
        """Test parsing pip requirements.txt."""
        requirements = tmp_path / "requirements.txt"
        requirements.write_text(
            """
# Dependencies
django==4.2.0
requests>=2.28.0
pytest~=7.3.0
"""
        )

        config = {"project_path": str(tmp_path)}
        analyzer = DependencyAnalyzer(config)

        dependencies = analyzer._parse_requirements_txt(requirements)

        assert len(dependencies) == 3
        assert any(d.name == "django" and d.version == "4.2.0" for d in dependencies)
        assert any(d.package_manager == PackageManager.PIP for d in dependencies)

    def test_parse_pyproject_toml(self, tmp_path):
        """Test parsing poetry pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[tool.poetry.dependencies]
python = "^3.10"
fastapi = "^0.100.0"
pydantic = "^2.0.0"

[tool.poetry.dev-dependencies]
pytest = "^7.0.0"
"""
        )

        config = {"project_path": str(tmp_path)}
        analyzer = DependencyAnalyzer(config)

        dependencies = analyzer._parse_pyproject_toml(pyproject)

        # Should exclude python
        assert all(d.name != "python" for d in dependencies)
        assert any(d.name == "fastapi" for d in dependencies)
        assert any(d.name == "pytest" and d.is_dev for d in dependencies)

    def test_basic_analysis(self, tmp_path):
        """Test basic dependency analysis."""
        package_json = tmp_path / "package.json"
        package_json.write_text(
            json.dumps(
                {
                    "dependencies": {"lodash": "4.17.21"},
                }
            )
        )

        config = {
            "project_path": str(tmp_path),
            "check_vulnerabilities": False,  # Disable network calls
            "check_outdated": False,
        }
        analyzer = DependencyAnalyzer(config)
        result = analyzer.analyze({})

        assert result["analyzer"] == "dependency_analyzer"
        assert "data" in result
        assert "summary" in result["data"]
        assert result["data"]["summary"]["total_dependencies"] >= 1

    def test_no_dependencies_found(self, tmp_path):
        """Test handling when no dependencies found."""
        config = {"project_path": str(tmp_path)}
        analyzer = DependencyAnalyzer(config)
        result = analyzer.analyze({})

        assert "data" in result
        assert result["data"]["summary"]["total_dependencies"] == 0


class TestDependency:
    """Test Dependency dataclass."""

    def test_dependency_creation(self):
        """Test Dependency model creation."""
        dep = Dependency(
            name="test-package",
            version="1.0.0",
            package_manager=PackageManager.NPM,
            is_dev=False,
            is_direct=True,
        )

        assert dep.name == "test-package"
        assert dep.version == "1.0.0"
        assert dep.package_manager == PackageManager.NPM

    def test_dependency_with_license(self):
        """Test Dependency with license."""
        dep = Dependency(
            name="express",
            version="4.18.0",
            package_manager=PackageManager.NPM,
            license="MIT",
        )

        assert dep.license == "MIT"

    def test_dependency_dev_flag(self):
        """Test dev dependency flag."""
        dep = Dependency(
            name="pytest",
            version="7.4.0",
            package_manager=PackageManager.PIP,
            is_dev=True,
        )

        assert dep.is_dev is True


class TestDependencyReport:
    """Test DependencyReport dataclass."""

    def test_report_creation(self):
        """Test creating a dependency report."""
        report = DependencyReport(scan_id="test-scan", project_path="/test/path")

        assert report.scan_id == "test-scan"
        assert report.project_path == "/test/path"
        assert report.total_dependencies == 0

    def test_report_with_vulnerabilities(self):
        """Test report with vulnerabilities."""
        report = DependencyReport(
            scan_id="test",
            project_path="/test/path",
            total_dependencies=5,
            direct_dependencies=3,
        )

        assert report.total_dependencies == 5
        assert report.direct_dependencies == 3

    def test_report_to_dict(self):
        """Test converting report to dictionary."""
        report = DependencyReport(
            scan_id="test-scan",
            project_path="/test/path",
            total_dependencies=1,
        )

        result = report.to_dict()

        assert result["scan_id"] == "test-scan"
        assert result["project_path"] == "/test/path"


class TestPackageManager:
    """Test PackageManager enum."""

    def test_package_manager_values(self):
        """Test package manager enum values."""
        assert PackageManager.NPM.value == "npm"
        assert PackageManager.PIP.value == "pip"
        assert PackageManager.POETRY.value == "poetry"
        assert PackageManager.CARGO.value == "cargo"
        assert PackageManager.GO_MOD.value == "go"


def test_integration_multi_package_manager(tmp_path):
    """Test analysis with multiple package managers."""
    # Create package.json
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"react": "18.0.0"}})
    )

    # Create requirements.txt
    (tmp_path / "requirements.txt").write_text("django==4.2.0\n")

    # Create Cargo.toml
    (tmp_path / "Cargo.toml").write_text(
        """
[dependencies]
serde = "1.0"
"""
    )

    config = {
        "project_path": str(tmp_path),
        "check_vulnerabilities": False,
        "check_outdated": False,
    }
    analyzer = DependencyAnalyzer(config)
    result = analyzer.analyze({})

    # Should detect multiple package managers
    assert len(result["data"]["package_managers"]) >= 2
    assert result["data"]["summary"]["total_dependencies"] >= 3


def test_empty_project(tmp_path):
    """Test analysis on empty project."""
    config = {
        "project_path": str(tmp_path),
    }
    analyzer = DependencyAnalyzer(config)
    result = analyzer.analyze({})

    assert result["data"]["summary"]["total_dependencies"] == 0
    assert len(result["data"]["package_managers"]) == 0


def test_package_json_with_version_ranges(tmp_path):
    """Test parsing various version range formats."""
    (tmp_path / "package.json").write_text(
        json.dumps({
            "dependencies": {
                "exact": "1.0.0",
                "caret": "^2.0.0",
                "tilde": "~3.0.0",
                "gte": ">=4.0.0",
                "star": "*",
            }
        })
    )

    config = {"project_path": str(tmp_path)}
    analyzer = DependencyAnalyzer(config)
    deps = analyzer._parse_package_json(tmp_path / "package.json")

    assert len(deps) == 5
    # Check that version ranges are parsed
    exact_dep = next((d for d in deps if d.name == "exact"), None)
    assert exact_dep is not None
    assert exact_dep.version == "1.0.0"
