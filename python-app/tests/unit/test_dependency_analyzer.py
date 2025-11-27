"""
Unit tests for DependencyAnalyzer and scanners.
"""

import pytest
import json
from pathlib import Path
from src.omniaudit.analyzers.dependencies import (
    DependencyAnalyzer,
    Dependency,
    PackageManager,
)
from src.omniaudit.analyzers.dependencies.scanners import (
    CVEScanner,
    LicenseScanner,
    OutdatedScanner,
    SBOMGenerator,
)
from src.omniaudit.analyzers.dependencies.types import (
    SBOMFormat,
    VulnerabilitySeverity,
)
from src.omniaudit.analyzers.base import AnalyzerError


class TestDependencyAnalyzer:
    """Test DependencyAnalyzer class."""

    def test_analyzer_properties(self, tmp_path):
        """Test analyzer properties."""
        config = {"project_path": str(tmp_path)}
        analyzer = DependencyAnalyzer(config)

        assert analyzer.name == "dependency_analyzer"
        assert analyzer.version == "1.0.0"

    def test_analyzer_missing_project_path(self):
        """Test error when project_path missing."""
        with pytest.raises(AnalyzerError, match="project_path is required"):
            DependencyAnalyzer({})

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
        assert any(d.name == "react" and d.version == "18.0.0" for d in dependencies)
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


class TestLicenseScanner:
    """Test LicenseScanner class."""

    def test_scan_dependencies(self):
        """Test license scanning."""
        scanner = LicenseScanner(project_license="MIT")

        dependencies = [
            Dependency(
                name="package1",
                version="1.0.0",
                package_manager=PackageManager.NPM,
                license="MIT",
            ),
            Dependency(
                name="package2",
                version="2.0.0",
                package_manager=PackageManager.NPM,
                license="GPL-3.0",
            ),
            Dependency(
                name="package3",
                version="3.0.0",
                package_manager=PackageManager.NPM,
                license=None,
            ),
        ]

        issues = scanner.scan_dependencies(dependencies)

        # Should find GPL incompatibility and missing license
        assert len(issues) >= 2

    def test_license_compatibility(self):
        """Test license compatibility checking."""
        scanner = LicenseScanner(project_license="MIT")

        # MIT project using GPL dependency (incompatible)
        gpl_dep = Dependency(
            name="gpl-package",
            version="1.0.0",
            package_manager=PackageManager.NPM,
            license="GPL-3.0",
        )

        issues = scanner.scan_dependencies([gpl_dep])
        assert any("incompatible" in issue.issue_type for issue in issues)

    def test_missing_license_detection(self):
        """Test detection of missing licenses."""
        scanner = LicenseScanner()

        dep = Dependency(
            name="no-license",
            version="1.0.0",
            package_manager=PackageManager.NPM,
            license=None,
        )

        issues = scanner.scan_dependencies([dep])
        assert any(issue.issue_type == "missing_license" for issue in issues)

    def test_license_summary(self):
        """Test license summary generation."""
        scanner = LicenseScanner()

        dependencies = [
            Dependency(
                name="p1",
                version="1.0.0",
                package_manager=PackageManager.NPM,
                license="MIT",
            ),
            Dependency(
                name="p2",
                version="1.0.0",
                package_manager=PackageManager.NPM,
                license="MIT",
            ),
            Dependency(
                name="p3",
                version="1.0.0",
                package_manager=PackageManager.NPM,
                license="Apache-2.0",
            ),
        ]

        summary = scanner.get_license_summary(dependencies)

        assert summary["total_dependencies"] == 3
        assert summary["license_counts"]["MIT"] == 2
        assert summary["license_counts"]["Apache-2.0"] == 1
        assert summary["categories"]["permissive"] == 3


class TestOutdatedScanner:
    """Test OutdatedScanner class."""

    def test_typosquatting_detection(self):
        """Test typosquatting detection."""
        scanner = OutdatedScanner()

        # Similar to "react" but not exact
        dep = Dependency(
            name="react-native",  # This is actually legitimate, but for testing
            version="1.0.0",
            package_manager=PackageManager.NPM,
        )

        matches = scanner._check_typosquatting(dep)
        # react-native is actually a real package, so this might not flag
        # But the method should run without error
        assert isinstance(matches, list)

    def test_similarity_calculation(self):
        """Test string similarity calculation."""
        scanner = OutdatedScanner()

        # Very similar strings
        similarity = scanner._calculate_similarity("react", "reakt")
        assert similarity > 0.8

        # Very different strings
        similarity = scanner._calculate_similarity("react", "angular")
        assert similarity < 0.5

    def test_pattern_analysis(self):
        """Test typosquatting pattern analysis."""
        scanner = OutdatedScanner()

        # Character substitution
        reasoning = scanner._analyze_typosquatting_pattern("reakt", "react")
        assert "character" in reasoning.lower() or "swap" in reasoning.lower()

        # Hyphen substitution
        reasoning = scanner._analyze_typosquatting_pattern("my-package", "mypackage")
        assert "hyphen" in reasoning.lower()


class TestSBOMGenerator:
    """Test SBOMGenerator class."""

    @pytest.fixture
    def sample_dependencies(self):
        """Create sample dependencies."""
        return [
            Dependency(
                name="react",
                version="18.2.0",
                package_manager=PackageManager.NPM,
                license="MIT",
                description="A JavaScript library for building user interfaces",
                homepage="https://reactjs.org/",
                repository="https://github.com/facebook/react",
            ),
            Dependency(
                name="axios",
                version="1.4.0",
                package_manager=PackageManager.NPM,
                license="MIT",
                description="Promise based HTTP client",
            ),
        ]

    def test_generate_spdx_json(self, sample_dependencies):
        """Test SPDX JSON generation."""
        generator = SBOMGenerator("test-project", "1.0.0")
        sbom = generator.generate(sample_dependencies, SBOMFormat.SPDX_JSON)

        assert sbom.format == SBOMFormat.SPDX_JSON
        assert sbom.spec_version == "SPDX-2.3"
        assert len(sbom.components) == 2

        # Verify component structure
        assert sbom.components[0]["name"] == "react"
        assert sbom.components[0]["versionInfo"] == "18.2.0"

    def test_generate_cyclonedx_json(self, sample_dependencies):
        """Test CycloneDX JSON generation."""
        generator = SBOMGenerator("test-project", "1.0.0")
        sbom = generator.generate(sample_dependencies, SBOMFormat.CYCLONEDX_JSON)

        assert sbom.format == SBOMFormat.CYCLONEDX_JSON
        assert sbom.spec_version == "1.4"
        assert len(sbom.components) == 2

        # Verify component structure
        assert sbom.components[0]["name"] == "react"
        assert sbom.components[0]["type"] == "library"

    def test_export_spdx_json(self, sample_dependencies):
        """Test SPDX JSON export."""
        generator = SBOMGenerator("test-project", "1.0.0")
        sbom = generator.generate(sample_dependencies, SBOMFormat.SPDX_JSON)

        json_str = generator.export_spdx_json(sbom)
        data = json.loads(json_str)

        assert data["spdxVersion"] == "SPDX-2.3"
        assert data["name"] == "test-project"
        assert len(data["packages"]) == 2

    def test_export_cyclonedx_json(self, sample_dependencies):
        """Test CycloneDX JSON export."""
        generator = SBOMGenerator("test-project", "1.0.0")
        sbom = generator.generate(sample_dependencies, SBOMFormat.CYCLONEDX_JSON)

        json_str = generator.export_cyclonedx_json(sbom)
        data = json.loads(json_str)

        assert data["bomFormat"] == "CycloneDX"
        assert data["specVersion"] == "1.4"
        assert len(data["components"]) == 2

    def test_purl_generation(self, sample_dependencies):
        """Test Package URL generation."""
        generator = SBOMGenerator("test-project", "1.0.0")

        purl = generator._generate_purl(sample_dependencies[0])
        assert purl == "pkg:npm/react@18.2.0"

        # Test different package manager
        pip_dep = Dependency(
            name="django",
            version="4.2.0",
            package_manager=PackageManager.PIP,
        )
        purl = generator._generate_purl(pip_dep)
        assert purl == "pkg:pypi/django@4.2.0"

    def test_export_spdx_xml(self, sample_dependencies):
        """Test SPDX XML export."""
        generator = SBOMGenerator("test-project", "1.0.0")
        sbom = generator.generate(sample_dependencies, SBOMFormat.SPDX_XML)

        xml_str = generator.export_spdx_xml(sbom)

        assert "<?xml" in xml_str
        assert "Document" in xml_str
        assert "react" in xml_str

    def test_export_cyclonedx_xml(self, sample_dependencies):
        """Test CycloneDX XML export."""
        generator = SBOMGenerator("test-project", "1.0.0")
        sbom = generator.generate(sample_dependencies, SBOMFormat.CYCLONEDX_XML)

        xml_str = generator.export_cyclonedx_xml(sbom)

        assert "<?xml" in xml_str
        assert "bom" in xml_str
        assert "react" in xml_str


class TestDependencyTypes:
    """Test dependency type models."""

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

    def test_vulnerability_severity(self):
        """Test vulnerability severity enum."""
        assert VulnerabilitySeverity.CRITICAL.value == "critical"
        assert VulnerabilitySeverity.HIGH.value == "high"
        assert VulnerabilitySeverity.MEDIUM.value == "medium"


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


def test_risk_assessment(tmp_path):
    """Test dependency risk assessment."""
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"lodash": "4.17.20"}})  # Older version
    )

    config = {
        "project_path": str(tmp_path),
        "check_vulnerabilities": False,
        "check_licenses": False,
        "check_outdated": False,
    }
    analyzer = DependencyAnalyzer(config)
    result = analyzer.analyze({})

    assert "risk_assessment" in result["data"]
    assert "risk_score" in result["data"]["risk_assessment"]
    assert "risk_level" in result["data"]["risk_assessment"]
