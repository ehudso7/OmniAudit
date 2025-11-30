"""
Unit tests for SecurityAnalyzer.

Tests the security analysis functionality available in security.py.
"""

import pytest
from pathlib import Path
from omniaudit.analyzers.security import (
    SecurityAnalyzer,
    SecurityFinding,
    SecurityReport,
    Severity,
    VulnerabilityCategory,
    CWE,
)
from omniaudit.analyzers.base import AnalyzerError


class TestSecurityAnalyzer:
    """Test SecurityAnalyzer class."""

    def test_analyzer_properties(self, tmp_path):
        """Test analyzer properties."""
        config = {"project_path": str(tmp_path)}
        analyzer = SecurityAnalyzer(config)

        assert analyzer.name == "security_analyzer"
        assert analyzer.version == "1.0.0"

    def test_analyzer_nonexistent_path(self):
        """Test error when project path doesn't exist."""
        with pytest.raises(AnalyzerError, match="does not exist"):
            SecurityAnalyzer({"project_path": "/nonexistent"})

    def test_basic_analysis(self, tmp_path):
        """Test basic security analysis."""
        # Create test file with vulnerabilities
        test_file = tmp_path / "test.py"
        test_file.write_text(
            """
import os
api_key = "AKIA1234567890123456"
password = "hardcoded_password"
os.system("rm -rf " + user_input)
query = "SELECT * FROM users WHERE id = " + user_id
"""
        )

        config = {"project_path": str(tmp_path)}
        analyzer = SecurityAnalyzer(config)
        result = analyzer.analyze({})

        assert result["analyzer"] == "security_analyzer"
        assert "data" in result
        assert "findings" in result["data"]
        assert "summary" in result["data"]

        # Should find multiple issues
        findings = result["data"]["findings"]
        assert len(findings) > 0

    def test_severity_filtering(self, tmp_path):
        """Test filtering by minimum severity."""
        test_file = tmp_path / "test.py"
        test_file.write_text('api_key = "AKIA1234567890123456"')

        config = {"project_path": str(tmp_path), "min_severity": "high"}
        analyzer = SecurityAnalyzer(config)
        result = analyzer.analyze({})

        # Should only return high+ severity issues
        findings = result["data"]["findings"]
        for finding in findings:
            assert finding["severity"] in ["high", "critical"]

    def test_risk_score_calculation(self, tmp_path):
        """Test risk score calculation."""
        test_file = tmp_path / "test.py"
        test_file.write_text(
            """
api_key = "AKIA1234567890123456"
password = "secret123"
"""
        )

        config = {"project_path": str(tmp_path)}
        analyzer = SecurityAnalyzer(config)
        result = analyzer.analyze({})

        assert "metadata" in result["data"]
        assert "risk_score" in result["data"]["metadata"]
        assert 0 <= result["data"]["metadata"]["risk_score"] <= 100

    def test_compliance_checking(self, tmp_path):
        """Test compliance checking."""
        test_file = tmp_path / "test.py"
        test_file.write_text("import hashlib\nhashlib.md5()")

        config = {"project_path": str(tmp_path)}
        analyzer = SecurityAnalyzer(config)
        result = analyzer.analyze({})

        assert "metadata" in result["data"]
        assert "compliance" in result["data"]["metadata"]
        assert "owasp_top_10" in result["data"]["metadata"]["compliance"]


class TestSecurityFinding:
    """Test SecurityFinding dataclass."""

    def test_finding_creation(self):
        """Test creating a security finding."""
        finding = SecurityFinding(
            id="test-finding-1",
            title="Test Finding",
            description="A test security finding",
            severity=Severity.HIGH,
            category=VulnerabilityCategory.SECRET_EXPOSURE,
            confidence=0.9,
            file_path="test.py",
            line_number=10,
            code_snippet="api_key = 'secret'",
            recommendation="Remove hardcoded secrets",
        )

        assert finding.id == "test-finding-1"
        assert finding.severity == Severity.HIGH
        assert finding.category == VulnerabilityCategory.SECRET_EXPOSURE

    def test_finding_to_dict(self):
        """Test converting finding to dictionary."""
        cwe = CWE.create(798, "Use of Hard-coded Credentials")
        finding = SecurityFinding(
            id="test-1",
            title="Hardcoded Credential",
            description="Credential found in code",
            severity=Severity.CRITICAL,
            category=VulnerabilityCategory.SECRET_EXPOSURE,
            confidence=0.95,
            file_path="config.py",
            line_number=5,
            cwe=cwe,
            owasp="A07:2021-Identification and Authentication Failures",
        )

        result = finding.to_dict()

        assert result["id"] == "test-1"
        assert result["severity"] == "critical"
        assert result["category"] == "secret_exposure"
        assert result["cwe"]["id"] == 798
        assert result["owasp"] == "A07:2021-Identification and Authentication Failures"


class TestSecurityReport:
    """Test SecurityReport dataclass."""

    def test_report_creation(self):
        """Test creating a security report."""
        report = SecurityReport(scan_id="test-scan-1")

        assert report.scan_id == "test-scan-1"
        assert len(report.findings) == 0
        assert report.files_scanned == 0

    def test_add_finding(self):
        """Test adding finding to report."""
        report = SecurityReport(scan_id="test-scan")
        finding = SecurityFinding(
            id="f1",
            title="Test",
            description="Test finding",
            severity=Severity.MEDIUM,
            category=VulnerabilityCategory.CONFIGURATION,
            confidence=0.8,
            file_path="test.py",
            line_number=1,
        )

        report.add_finding(finding)

        assert len(report.findings) == 1
        assert report.findings[0].id == "f1"

    def test_severity_counts(self):
        """Test getting severity counts."""
        report = SecurityReport(scan_id="test")
        report.add_finding(
            SecurityFinding(
                id="1",
                title="",
                description="",
                severity=Severity.HIGH,
                category=VulnerabilityCategory.INJECTION,
                confidence=0.9,
                file_path="",
                line_number=1,
            )
        )
        report.add_finding(
            SecurityFinding(
                id="2",
                title="",
                description="",
                severity=Severity.HIGH,
                category=VulnerabilityCategory.INJECTION,
                confidence=0.9,
                file_path="",
                line_number=2,
            )
        )
        report.add_finding(
            SecurityFinding(
                id="3",
                title="",
                description="",
                severity=Severity.LOW,
                category=VulnerabilityCategory.CONFIGURATION,
                confidence=0.9,
                file_path="",
                line_number=3,
            )
        )

        counts = report.get_severity_counts()

        assert counts["high"] == 2
        assert counts["low"] == 1
        assert counts["critical"] == 0

    def test_report_to_dict(self):
        """Test converting report to dictionary."""
        report = SecurityReport(
            scan_id="test-scan",
            files_scanned=10,
            scan_duration_ms=150.5,
        )

        result = report.to_dict()

        assert result["scan_id"] == "test-scan"
        assert result["files_scanned"] == 10
        assert result["scan_duration_ms"] == 150.5
        assert result["total_findings"] == 0


class TestCWE:
    """Test CWE dataclass."""

    def test_cwe_creation(self):
        """Test creating a CWE reference."""
        cwe = CWE(id=89, name="SQL Injection")

        assert cwe.id == 89
        assert cwe.name == "SQL Injection"
        assert "89" in cwe.url

    def test_cwe_factory_method(self):
        """Test CWE factory method."""
        cwe = CWE.create(79, "Cross-site Scripting")

        assert cwe.id == 79
        assert cwe.name == "Cross-site Scripting"
        assert cwe.url == "https://cwe.mitre.org/data/definitions/79.html"


class TestSARIFExport:
    """Test SARIF export functionality."""

    def test_sarif_generation(self, tmp_path):
        """Test SARIF format export."""
        test_file = tmp_path / "test.py"
        test_file.write_text('api_key = "AKIA1234567890123456"')

        config = {"project_path": str(tmp_path)}
        analyzer = SecurityAnalyzer(config)
        result = analyzer.analyze({})

        # Create report object
        findings = [
            SecurityFinding(
                id=f["id"],
                title=f["title"],
                description=f["description"],
                severity=Severity(f["severity"]),
                category=VulnerabilityCategory(f["category"]),
                confidence=f["confidence"],
                file_path=f["file_path"],
                line_number=f["line_number"],
            )
            for f in result["data"]["findings"]
        ]
        report = SecurityReport(
            scan_id="test-scan",
            findings=findings,
            summary={},
            metadata={},
        )

        # Export SARIF
        sarif = analyzer.export_sarif(report)

        assert sarif["version"] == "2.1.0"
        assert "runs" in sarif
        assert len(sarif["runs"]) > 0
        assert "results" in sarif["runs"][0]


def test_integration_full_scan(tmp_path):
    """Test full security scan integration."""
    # Create a project with multiple vulnerabilities
    (tmp_path / "app.py").write_text(
        """
import os
import hashlib

# Secrets
aws_key = "AKIA1234567890123456"
db_password = "mypassword123"

# Injection
user_id = request.args.get('id')
query = "SELECT * FROM users WHERE id = " + user_id
os.system("cat " + filename)

# Crypto
hash_val = hashlib.md5(data)

# Debug
DEBUG = True
"""
    )

    config = {"project_path": str(tmp_path)}
    analyzer = SecurityAnalyzer(config)
    result = analyzer.analyze({})

    # Should find multiple categories of issues
    findings = result["data"]["findings"]
    categories = set(f["category"] for f in findings)

    assert len(findings) >= 3
    assert result["data"]["metadata"]["risk_score"] > 0
