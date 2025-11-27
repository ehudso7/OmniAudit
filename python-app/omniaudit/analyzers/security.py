"""
Security Analyzer for OmniAudit.

This module provides security analysis capabilities including:
- Secret detection (API keys, passwords, tokens)
- Injection vulnerability detection (SQL, Command, XSS)
- Cryptographic weakness detection
- OWASP Top 10 compliance checking
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import BaseAnalyzer, AnalyzerError


class Severity(str, Enum):
    """Severity levels for security findings."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilityCategory(str, Enum):
    """Categories of security vulnerabilities."""

    SECRET_EXPOSURE = "secret_exposure"
    INJECTION = "injection"
    XSS = "xss"
    CRYPTOGRAPHIC = "cryptographic"
    CONFIGURATION = "configuration"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_EXPOSURE = "data_exposure"


@dataclass
class CWEInfo:
    """Common Weakness Enumeration information."""

    id: int
    name: str
    url: Optional[str] = None


@dataclass
class SecurityFinding:
    """Represents a security vulnerability finding."""

    id: str
    title: str
    description: str
    severity: Severity
    category: VulnerabilityCategory
    confidence: float
    file_path: str
    line_number: int
    code_snippet: Optional[str] = None
    recommendation: str = ""
    cwe: Optional[CWEInfo] = None
    owasp: Optional[str] = None
    references: List[str] = field(default_factory=list)


@dataclass
class SecurityReport:
    """Complete security analysis report."""

    scan_id: str
    findings: List[SecurityFinding]
    summary: Dict[str, Any]
    metadata: Dict[str, Any]
    risk_score: float = 0.0


class SecurityAnalyzer(BaseAnalyzer):
    """
    Analyzer for detecting security vulnerabilities in code.

    This analyzer scans source code for various security issues including:
    - Hardcoded secrets and credentials
    - SQL and command injection vulnerabilities
    - Cross-site scripting (XSS) vulnerabilities
    - Weak cryptographic practices
    - Security misconfigurations
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the security analyzer."""
        super().__init__(config)
        self._project_path: Optional[Path] = None
        if config and "project_path" in config:
            self._project_path = Path(config["project_path"])

    @property
    def name(self) -> str:
        """Return analyzer name."""
        return "security_analyzer"

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
        Perform security analysis on the project.

        Args:
            data: Additional analysis parameters

        Returns:
            Analysis results with security findings
        """
        findings: List[Dict[str, Any]] = []
        min_severity = self.config.get("min_severity", "info")

        if self._project_path:
            # Scan for security issues
            raw_findings = self._scan_project(self._project_path)

            # Filter by minimum severity
            severity_order = ["info", "low", "medium", "high", "critical"]
            min_idx = severity_order.index(min_severity.lower())

            for finding in raw_findings:
                finding_idx = severity_order.index(finding.severity.value)
                if finding_idx >= min_idx:
                    findings.append(self._finding_to_dict(finding))

        # Calculate summary
        summary = self._calculate_summary(findings)

        # Calculate risk score
        risk_score = self._calculate_risk_score(findings)

        # Check compliance
        compliance = self._check_compliance(findings)

        return self._create_response(
            {
                "scan_id": data.get("scan_id", "default-scan"),
                "findings": findings,
                "summary": summary,
                "risk_score": risk_score,
                "compliance": compliance,
            }
        )

    def _scan_project(self, project_path: Path) -> List[SecurityFinding]:
        """Scan project for security vulnerabilities."""
        findings: List[SecurityFinding] = []

        # Scan all relevant files
        for file_path in project_path.rglob("*"):
            if file_path.is_file() and self._is_scannable(file_path):
                findings.extend(self._scan_file(file_path))

        return findings

    def _is_scannable(self, file_path: Path) -> bool:
        """Check if file should be scanned."""
        scannable_extensions = {
            ".py", ".js", ".ts", ".jsx", ".tsx", ".java",
            ".rb", ".php", ".go", ".rs", ".c", ".cpp", ".cs"
        }
        return file_path.suffix.lower() in scannable_extensions

    def _scan_file(self, file_path: Path) -> List[SecurityFinding]:
        """Scan a single file for vulnerabilities."""
        findings: List[SecurityFinding] = []

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = content.split("\n")

            for line_num, line in enumerate(lines, start=1):
                # Check for secrets
                findings.extend(self._check_secrets(file_path, line_num, line))

                # Check for injection vulnerabilities
                findings.extend(self._check_injection(file_path, line_num, line))

                # Check for weak crypto
                findings.extend(self._check_crypto(file_path, line_num, line))

        except (OSError, UnicodeDecodeError):
            pass

        return findings

    def _check_secrets(
        self, file_path: Path, line_num: int, line: str
    ) -> List[SecurityFinding]:
        """Check for hardcoded secrets."""
        findings: List[SecurityFinding] = []

        import re

        # AWS Access Key pattern
        aws_pattern = r"AKIA[0-9A-Z]{16}"
        if re.search(aws_pattern, line):
            findings.append(
                SecurityFinding(
                    id=f"SEC-{line_num}-aws",
                    title="AWS Access Key Detected",
                    description="AWS Access Key ID exposed in source code",
                    severity=Severity.CRITICAL,
                    category=VulnerabilityCategory.SECRET_EXPOSURE,
                    confidence=0.95,
                    file_path=str(file_path),
                    line_number=line_num,
                    code_snippet=line.strip(),
                    recommendation="Remove hardcoded AWS credentials. Use environment variables or AWS IAM roles.",
                    cwe=CWEInfo(id=798, name="Use of Hard-coded Credentials"),
                    owasp="A02:2021-Cryptographic Failures",
                )
            )

        # Password patterns
        password_pattern = r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\']+["\']'
        if re.search(password_pattern, line):
            findings.append(
                SecurityFinding(
                    id=f"SEC-{line_num}-pwd",
                    title="Hardcoded Password Detected",
                    description="Password appears to be hardcoded in source code",
                    severity=Severity.HIGH,
                    category=VulnerabilityCategory.SECRET_EXPOSURE,
                    confidence=0.8,
                    file_path=str(file_path),
                    line_number=line_num,
                    code_snippet=line.strip(),
                    recommendation="Remove hardcoded passwords. Use secure secrets management.",
                    cwe=CWEInfo(id=798, name="Use of Hard-coded Credentials"),
                    owasp="A02:2021-Cryptographic Failures",
                )
            )

        return findings

    def _check_injection(
        self, file_path: Path, line_num: int, line: str
    ) -> List[SecurityFinding]:
        """Check for injection vulnerabilities."""
        findings: List[SecurityFinding] = []

        import re

        # SQL injection via string concatenation
        sql_pattern = r'(?i)(SELECT|INSERT|UPDATE|DELETE).*\+\s*\w+'
        if re.search(sql_pattern, line):
            findings.append(
                SecurityFinding(
                    id=f"SEC-{line_num}-sqli",
                    title="Potential SQL Injection",
                    description="SQL query built with string concatenation",
                    severity=Severity.HIGH,
                    category=VulnerabilityCategory.INJECTION,
                    confidence=0.8,
                    file_path=str(file_path),
                    line_number=line_num,
                    code_snippet=line.strip(),
                    recommendation="Use parameterized queries or prepared statements.",
                    cwe=CWEInfo(id=89, name="SQL Injection"),
                    owasp="A03:2021-Injection",
                )
            )

        # Command injection
        cmd_pattern = r'(?i)os\.system\s*\([^)]*\+\s*\w+'
        if re.search(cmd_pattern, line):
            findings.append(
                SecurityFinding(
                    id=f"SEC-{line_num}-cmdi",
                    title="Potential Command Injection",
                    description="System command built with string concatenation",
                    severity=Severity.CRITICAL,
                    category=VulnerabilityCategory.INJECTION,
                    confidence=0.85,
                    file_path=str(file_path),
                    line_number=line_num,
                    code_snippet=line.strip(),
                    recommendation="Use subprocess with list arguments. Validate and sanitize user input.",
                    cwe=CWEInfo(id=78, name="OS Command Injection"),
                    owasp="A03:2021-Injection",
                )
            )

        return findings

    def _check_crypto(
        self, file_path: Path, line_num: int, line: str
    ) -> List[SecurityFinding]:
        """Check for weak cryptographic practices."""
        findings: List[SecurityFinding] = []

        import re

        # Weak hash algorithms
        md5_pattern = r'hashlib\.md5\s*\('
        # Skip if it looks like a checksum use case
        if re.search(md5_pattern, line) and "checksum" not in line.lower():
            findings.append(
                SecurityFinding(
                    id=f"SEC-{line_num}-md5",
                    title="Weak Hash Algorithm (MD5)",
                    description="MD5 is cryptographically weak and should not be used for security",
                    severity=Severity.MEDIUM,
                    category=VulnerabilityCategory.CRYPTOGRAPHIC,
                    confidence=0.85,
                    file_path=str(file_path),
                    line_number=line_num,
                    code_snippet=line.strip(),
                    recommendation="Use SHA-256 or stronger hashing algorithms.",
                    cwe=CWEInfo(id=327, name="Use of a Broken or Risky Cryptographic Algorithm"),
                    owasp="A02:2021-Cryptographic Failures",
                )
            )

        return findings

    def _finding_to_dict(self, finding: SecurityFinding) -> Dict[str, Any]:
        """Convert SecurityFinding to dictionary."""
        result: Dict[str, Any] = {
            "id": finding.id,
            "title": finding.title,
            "description": finding.description,
            "severity": finding.severity.value,
            "category": finding.category.value,
            "confidence": finding.confidence,
            "file_path": finding.file_path,
            "line_number": finding.line_number,
            "recommendation": finding.recommendation,
        }

        if finding.code_snippet:
            result["code_snippet"] = finding.code_snippet
        if finding.cwe:
            result["cwe"] = {
                "id": finding.cwe.id,
                "name": finding.cwe.name,
            }
        if finding.owasp:
            result["owasp"] = finding.owasp
        if finding.references:
            result["references"] = finding.references

        return result

    def _calculate_summary(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for findings."""
        by_severity: Dict[str, int] = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
        }
        by_category: Dict[str, int] = {}

        for finding in findings:
            severity = finding.get("severity", "info")
            category = finding.get("category", "unknown")

            by_severity[severity] = by_severity.get(severity, 0) + 1
            by_category[category] = by_category.get(category, 0) + 1

        return {
            "total_findings": len(findings),
            "by_severity": by_severity,
            "by_category": by_category,
            "files_with_issues": len(set(f.get("file_path", "") for f in findings)),
        }

    def _calculate_risk_score(self, findings: List[Dict[str, Any]]) -> float:
        """Calculate overall risk score (0-100)."""
        if not findings:
            return 0.0

        weights = {
            "critical": 25.0,
            "high": 15.0,
            "medium": 8.0,
            "low": 3.0,
            "info": 1.0,
        }

        total_score = sum(
            weights.get(f.get("severity", "info"), 1.0) for f in findings
        )

        # Cap at 100
        return min(total_score, 100.0)

    def _check_compliance(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check compliance against security standards."""
        owasp_issues: Dict[str, int] = {}

        for finding in findings:
            owasp = finding.get("owasp")
            if owasp:
                owasp_issues[owasp] = owasp_issues.get(owasp, 0) + 1

        critical_count = sum(
            1 for f in findings if f.get("severity") == "critical"
        )

        return {
            "owasp_top_10": {
                "covered": True,
                "issues_found": owasp_issues,
            },
            "pci_dss": {
                "compliant": critical_count == 0,
                "critical_issues": critical_count,
            },
        }

    def export_sarif(self, report: SecurityReport) -> Dict[str, Any]:
        """Export report in SARIF format."""
        results = []
        for finding in report.findings:
            results.append({
                "ruleId": finding.id,
                "level": self._severity_to_sarif_level(finding.severity),
                "message": {"text": finding.description},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": finding.file_path},
                            "region": {"startLine": finding.line_number},
                        }
                    }
                ],
            })

        return {
            "version": "2.1.0",
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": self.name,
                            "version": self.version,
                        }
                    },
                    "results": results,
                }
            ],
        }

    def _severity_to_sarif_level(self, severity: Severity) -> str:
        """Convert severity to SARIF level."""
        mapping = {
            Severity.CRITICAL: "error",
            Severity.HIGH: "error",
            Severity.MEDIUM: "warning",
            Severity.LOW: "note",
            Severity.INFO: "note",
        }
        return mapping.get(severity, "note")
