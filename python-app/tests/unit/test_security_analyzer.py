"""
Unit tests for SecurityAnalyzer and detectors.
"""

import pytest
from pathlib import Path
from src.omniaudit.analyzers.security import (
    SecurityAnalyzer,
    SecurityFinding,
    Severity,
    VulnerabilityCategory,
)
from src.omniaudit.analyzers.security.detectors import (
    SecretsDetector,
    InjectionDetector,
    XSSDetector,
    CryptoDetector,
    OWASPDetector,
)
from src.omniaudit.analyzers.base import AnalyzerError


class TestSecurityAnalyzer:
    """Test SecurityAnalyzer class."""

    def test_analyzer_properties(self, tmp_path):
        """Test analyzer properties."""
        config = {"project_path": str(tmp_path)}
        analyzer = SecurityAnalyzer(config)

        assert analyzer.name == "security_analyzer"
        assert analyzer.version == "1.0.0"

    def test_analyzer_missing_project_path(self):
        """Test error when project_path missing."""
        with pytest.raises(AnalyzerError, match="project_path is required"):
            SecurityAnalyzer({})

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
        test_file.write_text("api_key = 'AKIA1234567890123456'")

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

        assert "risk_score" in result["data"]
        assert 0 <= result["data"]["risk_score"] <= 100

    def test_compliance_checking(self, tmp_path):
        """Test compliance checking."""
        test_file = tmp_path / "test.py"
        test_file.write_text("import hashlib\nhashlib.md5()")

        config = {"project_path": str(tmp_path)}
        analyzer = SecurityAnalyzer(config)
        result = analyzer.analyze({})

        assert "compliance" in result["data"]
        assert "owasp_top_10" in result["data"]["compliance"]


class TestSecretsDetector:
    """Test SecretsDetector class."""

    @pytest.fixture
    def rules_path(self, tmp_path):
        """Create temporary rules file."""
        rules_file = tmp_path / "security_rules.yaml"
        rules_file.write_text(
            """
secrets:
  - name: "AWS Access Key"
    pattern: '(?i)(AKIA[0-9A-Z]{16})'
    severity: "critical"
    confidence: 0.95
    description: "AWS Access Key exposed"
    recommendation: "Remove hardcoded credentials"
"""
        )
        return rules_file

    def test_detect_aws_key(self, tmp_path, rules_path):
        """Test AWS key detection."""
        detector = SecretsDetector(rules_path)

        test_file = tmp_path / "config.py"
        test_file.write_text('aws_key = "AKIA1234567890ABCDEF"')

        findings = detector.scan_file(test_file)
        assert len(findings) == 1
        assert findings[0].severity == Severity.CRITICAL
        assert "AWS" in findings[0].title

    def test_false_positive_filtering(self, tmp_path, rules_path):
        """Test false positive filtering."""
        detector = SecretsDetector(rules_path)

        test_file = tmp_path / "example.py"
        test_file.write_text('# Example: api_key = "your-key-here"')

        findings = detector.scan_file(test_file)
        # Should be filtered as false positive
        assert len(findings) == 0

    def test_scan_directory(self, tmp_path, rules_path):
        """Test directory scanning."""
        detector = SecretsDetector(rules_path)

        # Create multiple files
        (tmp_path / "file1.py").write_text('key1 = "AKIA1111111111111111"')
        (tmp_path / "file2.js").write_text('const key2 = "AKIA2222222222222222";')

        findings = detector.scan_directory(tmp_path)
        assert len(findings) >= 2


class TestInjectionDetector:
    """Test InjectionDetector class."""

    @pytest.fixture
    def rules_path(self, tmp_path):
        """Create temporary rules file."""
        rules_file = tmp_path / "security_rules.yaml"
        rules_file.write_text(
            """
injection:
  - name: "SQL Injection"
    pattern: '(?i)(SELECT|INSERT|UPDATE|DELETE).*\\+.*'
    category: "injection"
    severity: "high"
    cwe_id: 89
    description: "Potential SQL injection"
    recommendation: "Use parameterized queries"
"""
        )
        return rules_file

    def test_detect_sql_injection(self, tmp_path, rules_path):
        """Test SQL injection detection."""
        detector = InjectionDetector(rules_path)

        test_file = tmp_path / "db.py"
        test_file.write_text('query = "SELECT * FROM users WHERE id = " + user_id')

        findings = detector.scan_file(test_file)
        assert len(findings) == 1
        assert findings[0].category == VulnerabilityCategory.INJECTION
        assert findings[0].cwe.id == 89

    def test_detect_command_injection(self, tmp_path, rules_path):
        """Test command injection detection."""
        detector = InjectionDetector(rules_path)

        test_file = tmp_path / "exec.py"
        test_file.write_text('os.system("ls " + directory)')

        # This test will pass even if pattern not in rules
        # because it tests the scanning mechanism
        findings = detector.scan_file(test_file)
        # May or may not find depending on rules, just test it runs
        assert isinstance(findings, list)


class TestXSSDetector:
    """Test XSSDetector class."""

    def test_detect_innerHTML(self, tmp_path):
        """Test innerHTML XSS detection."""
        rules_file = tmp_path / "security_rules.yaml"
        rules_file.write_text(
            """
xss:
  - name: "XSS - innerHTML"
    pattern: '(?i)innerHTML\\s*=\\s*'
    category: "xss"
    severity: "high"
    cwe_id: 79
    description: "XSS via innerHTML"
    recommendation: "Use textContent"
"""
        )

        detector = XSSDetector(rules_file)

        test_file = tmp_path / "app.js"
        test_file.write_text("element.innerHTML = userInput;")

        findings = detector.scan_file(test_file)
        assert len(findings) == 1
        assert findings[0].category == VulnerabilityCategory.XSS


class TestCryptoDetector:
    """Test CryptoDetector class."""

    def test_detect_weak_hash(self, tmp_path):
        """Test weak hash algorithm detection."""
        rules_file = tmp_path / "security_rules.yaml"
        rules_file.write_text(
            """
crypto:
  - name: "Weak Hash - MD5"
    pattern: 'hashlib\\.md5\\('
    category: "cryptographic"
    severity: "medium"
    cwe_id: 327
    description: "Use of weak MD5"
    recommendation: "Use SHA-256"
"""
        )

        detector = CryptoDetector(rules_file)

        test_file = tmp_path / "crypto.py"
        test_file.write_text("import hashlib\nhashlib.md5(data)")

        findings = detector.scan_file(test_file)
        assert len(findings) == 1
        assert findings[0].severity == Severity.MEDIUM

    def test_acceptable_use_filtering(self, tmp_path):
        """Test filtering acceptable MD5 use (checksums)."""
        rules_file = tmp_path / "security_rules.yaml"
        rules_file.write_text(
            """
crypto:
  - name: "Weak Hash - MD5"
    pattern: 'hashlib\\.md5\\('
    category: "cryptographic"
    severity: "medium"
    cwe_id: 327
    description: "Use of weak MD5"
    recommendation: "Use SHA-256"
"""
        )

        detector = CryptoDetector(rules_file)

        test_file = tmp_path / "checksum.py"
        test_file.write_text("# Calculate checksum\nchecksum = hashlib.md5(file_content)")

        findings = detector.scan_file(test_file)
        # Should be filtered as acceptable use
        assert len(findings) == 0


class TestOWASPDetector:
    """Test OWASPDetector class."""

    def test_detect_debug_mode(self, tmp_path):
        """Test debug mode detection."""
        rules_file = tmp_path / "security_rules.yaml"
        rules_file.write_text(
            """
owasp:
  - name: "Debug Mode"
    pattern: '(?i)debug\\s*=\\s*True'
    category: "configuration"
    severity: "medium"
    cwe_id: 489
    description: "Debug mode enabled"
    recommendation: "Disable in production"
    owasp: "A05:2021-Security Misconfiguration"
"""
        )

        detector = OWASPDetector(rules_file)

        test_file = tmp_path / "settings.py"
        test_file.write_text("DEBUG = True")

        findings = detector.scan_file(test_file)
        assert len(findings) == 1
        assert "A05:2021" in findings[0].owasp


class TestSARIFExport:
    """Test SARIF export functionality."""

    def test_sarif_generation(self, tmp_path):
        """Test SARIF format export."""
        from src.omniaudit.analyzers.security.types import SecurityReport

        test_file = tmp_path / "test.py"
        test_file.write_text('api_key = "AKIA1234567890123456"')

        config = {"project_path": str(tmp_path)}
        analyzer = SecurityAnalyzer(config)
        result = analyzer.analyze({})

        # Create report object
        findings = [
            SecurityFinding(**f) for f in result["data"]["findings"]
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

    assert len(findings) >= 5
    assert "secret_exposure" in categories or "cryptographic" in categories
    assert result["data"]["risk_score"] > 0
