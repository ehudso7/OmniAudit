"""
Security Analysis Module

This module provides security analysis capabilities including
vulnerability detection, secret scanning, and compliance checking.
"""

import re
import uuid
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

from .base import BaseAnalyzer, AnalyzerError


class Severity(str, Enum):
    """Security finding severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilityCategory(str, Enum):
    """Categories of security vulnerabilities."""

    INJECTION = "injection"
    XSS = "xss"
    SSRF = "ssrf"
    PATH_TRAVERSAL = "path_traversal"
    SECRET_EXPOSURE = "secret_exposure"
    CRYPTOGRAPHIC = "cryptographic"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    CONFIGURATION = "configuration"
    DATA_EXPOSURE = "data_exposure"
    DESERIALIZATION = "deserialization"
    XXE = "xxe"
    CSRF = "csrf"
    INSECURE_DEPENDENCIES = "insecure_dependencies"


@dataclass
class CWE:
    """Common Weakness Enumeration reference."""

    id: int
    name: str
    url: str = ""

    def __post_init__(self):
        if not self.url:
            self.url = f"https://cwe.mitre.org/data/definitions/{self.id}.html"

    @classmethod
    def create(cls, cwe_id: int, name: str) -> "CWE":
        """Create CWE with auto-generated URL."""
        return cls(
            id=cwe_id,
            name=name,
            url=f"https://cwe.mitre.org/data/definitions/{cwe_id}.html",
        )


@dataclass
class SecurityFinding:
    """A single security finding."""

    id: str
    title: str
    description: str
    severity: Severity
    category: str  # VulnerabilityCategory value
    confidence: float
    file_path: str
    line_number: int
    code_snippet: str
    recommendation: str
    cwe: Optional[CWE] = None
    owasp: Optional[str] = None
    references: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert finding to dictionary."""
        result = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value if isinstance(self.severity, Severity) else self.severity,
            "category": self.category,
            "confidence": self.confidence,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "code_snippet": self.code_snippet,
            "recommendation": self.recommendation,
            "references": self.references,
        }
        if self.cwe:
            result["cwe"] = {"id": self.cwe.id, "name": self.cwe.name, "url": self.cwe.url}
        if self.owasp:
            result["owasp"] = self.owasp
        return result


@dataclass
class SecurityReport:
    """Complete security analysis report."""

    scan_id: str
    findings: List[SecurityFinding] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def get_severity_counts(self) -> Dict[str, int]:
        """Get count of findings by severity."""
        counts = {severity.value: 0 for severity in Severity}
        for finding in self.findings:
            sev_val = finding.severity.value if isinstance(finding.severity, Severity) else finding.severity
            if sev_val in counts:
                counts[sev_val] += 1
        return counts

    def get_category_counts(self) -> Dict[str, int]:
        """Get count of findings by category."""
        counts: Dict[str, int] = {}
        for finding in self.findings:
            category = finding.category
            counts[category] = counts.get(category, 0) + 1
        return counts

    def get_critical_findings(self) -> List[SecurityFinding]:
        """Get all critical severity findings."""
        return [f for f in self.findings if f.severity == Severity.CRITICAL]

    def get_high_findings(self) -> List[SecurityFinding]:
        """Get all high severity findings."""
        return [f for f in self.findings if f.severity == Severity.HIGH]


# Common patterns for security detection
SECRET_PATTERNS = [
    {
        "name": "AWS Access Key",
        "pattern": r"(?i)(AKIA[0-9A-Z]{16})",
        "severity": Severity.CRITICAL,
        "category": VulnerabilityCategory.SECRET_EXPOSURE.value,
        "cwe_id": 798,
        "cwe_name": "Use of Hard-coded Credentials",
        "recommendation": "Remove hardcoded AWS credentials. Use environment variables or AWS IAM roles.",
    },
    {
        "name": "Generic API Key",
        "pattern": r"(?i)(api[_-]?key|apikey)\s*[=:]\s*['\"][a-zA-Z0-9]{16,}['\"]",
        "severity": Severity.HIGH,
        "category": VulnerabilityCategory.SECRET_EXPOSURE.value,
        "cwe_id": 798,
        "cwe_name": "Use of Hard-coded Credentials",
        "recommendation": "Use environment variables for API keys.",
    },
    {
        "name": "Hardcoded Password",
        "pattern": r"(?i)(password|passwd|pwd)\s*[=:]\s*['\"][^'\"]{4,}['\"]",
        "severity": Severity.HIGH,
        "category": VulnerabilityCategory.SECRET_EXPOSURE.value,
        "cwe_id": 798,
        "cwe_name": "Use of Hard-coded Credentials",
        "recommendation": "Use environment variables or secure vaults for passwords.",
    },
]

INJECTION_PATTERNS = [
    {
        "name": "SQL Injection",
        "pattern": r"(?i)(SELECT|INSERT|UPDATE|DELETE).*\+\s*\w+",
        "severity": Severity.HIGH,
        "category": VulnerabilityCategory.INJECTION.value,
        "cwe_id": 89,
        "cwe_name": "SQL Injection",
        "owasp": "A03:2021-Injection",
        "recommendation": "Use parameterized queries or prepared statements.",
    },
    {
        "name": "Command Injection",
        "pattern": r"(?i)(os\.system|subprocess\.(call|run|Popen))\s*\([^)]*\+",
        "severity": Severity.CRITICAL,
        "category": VulnerabilityCategory.INJECTION.value,
        "cwe_id": 78,
        "cwe_name": "OS Command Injection",
        "owasp": "A03:2021-Injection",
        "recommendation": "Use subprocess with shell=False and avoid string concatenation.",
    },
]

CRYPTO_PATTERNS = [
    {
        "name": "Weak Hash - MD5",
        "pattern": r"hashlib\.md5\s*\(",
        "severity": Severity.MEDIUM,
        "category": VulnerabilityCategory.CRYPTOGRAPHIC.value,
        "cwe_id": 327,
        "cwe_name": "Use of a Broken or Risky Cryptographic Algorithm",
        "owasp": "A02:2021-Cryptographic Failures",
        "recommendation": "Use SHA-256 or stronger hashing algorithms.",
    },
    {
        "name": "Weak Hash - SHA1",
        "pattern": r"hashlib\.sha1\s*\(",
        "severity": Severity.MEDIUM,
        "category": VulnerabilityCategory.CRYPTOGRAPHIC.value,
        "cwe_id": 327,
        "cwe_name": "Use of a Broken or Risky Cryptographic Algorithm",
        "owasp": "A02:2021-Cryptographic Failures",
        "recommendation": "Use SHA-256 or stronger hashing algorithms.",
    },
]

CONFIG_PATTERNS = [
    {
        "name": "Debug Mode Enabled",
        "pattern": r"(?i)debug\s*=\s*True",
        "severity": Severity.MEDIUM,
        "category": VulnerabilityCategory.CONFIGURATION.value,
        "cwe_id": 489,
        "cwe_name": "Active Debug Code",
        "owasp": "A05:2021-Security Misconfiguration",
        "recommendation": "Disable debug mode in production environments.",
    },
]

XSS_PATTERNS = [
    {
        "name": "XSS - innerHTML",
        "pattern": r"\.innerHTML\s*=",
        "severity": Severity.HIGH,
        "category": VulnerabilityCategory.XSS.value,
        "cwe_id": 79,
        "cwe_name": "Cross-site Scripting (XSS)",
        "owasp": "A03:2021-Injection",
        "recommendation": "Use textContent or properly escape HTML. Consider using DOMPurify.",
    },
]


class SecurityAnalyzer(BaseAnalyzer):
    """
    Performs comprehensive security analysis on codebases.

    Detects:
    - Hardcoded secrets and credentials
    - Injection vulnerabilities (SQL, command, XSS)
    - Weak cryptography usage
    - Security misconfigurations

    Configuration:
        project_path: str - Path to project root (required)
        min_severity: str - Minimum severity to report (default: "low")
        exclude_patterns: List[str] - Patterns to exclude from scanning
    """

    @property
    def name(self) -> str:
        return "security_analyzer"

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
        Analyze security of codebase.

        Args:
            data: Optional input data

        Returns:
            Security analysis results
        """
        project_path = Path(self.config["project_path"])
        min_severity = self.config.get("min_severity", "low")
        exclude_patterns = self.config.get("exclude_patterns", [])

        scan_id = str(uuid.uuid4())
        findings: List[SecurityFinding] = []

        # Get severity threshold
        severity_order = [Severity.INFO, Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
        try:
            min_sev_idx = severity_order.index(Severity(min_severity))
        except ValueError:
            min_sev_idx = 0

        # Scan all code files
        for file_path in self._get_code_files(project_path, exclude_patterns):
            file_findings = self._scan_file(file_path, project_path)
            findings.extend(file_findings)

        # Filter by minimum severity
        filtered_findings = [
            f for f in findings
            if severity_order.index(f.severity) >= min_sev_idx
        ]

        # Generate summary
        summary = self._generate_summary(filtered_findings)

        # Calculate risk score
        risk_score = self._calculate_risk_score(filtered_findings)

        # Check compliance
        compliance = self._check_compliance(filtered_findings)

        results = {
            "scan_id": scan_id,
            "findings": [f.to_dict() for f in filtered_findings],
            "summary": summary,
            "risk_score": risk_score,
            "compliance": compliance,
        }

        return self._create_response(results)

    def _get_code_files(self, path: Path, exclude_patterns: List[str]) -> List[Path]:
        """Get all code files to scan."""
        code_extensions = {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rb", ".php"}
        files = []

        skip_dirs = {"node_modules", "venv", "__pycache__", ".git", "dist", "build", ".venv", "env"}

        for file_path in path.rglob("*"):
            if file_path.is_file() and file_path.suffix in code_extensions:
                # Skip common non-source directories
                if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
                    continue
                # Skip excluded patterns
                if any(re.search(pattern, str(file_path)) for pattern in exclude_patterns):
                    continue
                files.append(file_path)

        return files

    def _scan_file(self, file_path: Path, project_root: Path) -> List[SecurityFinding]:
        """Scan a single file for security issues."""
        findings = []

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return findings

        lines = content.split("\n")
        relative_path = str(file_path.relative_to(project_root))

        # All pattern groups
        all_patterns = SECRET_PATTERNS + INJECTION_PATTERNS + CRYPTO_PATTERNS + CONFIG_PATTERNS + XSS_PATTERNS

        for line_num, line in enumerate(lines, 1):
            for pattern_info in all_patterns:
                if re.search(pattern_info["pattern"], line):
                    finding = SecurityFinding(
                        id=f"finding-{uuid.uuid4().hex[:8]}",
                        title=pattern_info["name"],
                        description=f"Potential {pattern_info['name'].lower()} detected",
                        severity=pattern_info["severity"],
                        category=pattern_info["category"],
                        confidence=0.8,
                        file_path=relative_path,
                        line_number=line_num,
                        code_snippet=line.strip()[:100],
                        recommendation=pattern_info["recommendation"],
                        cwe=CWE.create(pattern_info["cwe_id"], pattern_info["cwe_name"]),
                        owasp=pattern_info.get("owasp"),
                    )
                    findings.append(finding)

        return findings

    def _generate_summary(self, findings: List[SecurityFinding]) -> Dict[str, Any]:
        """Generate summary statistics."""
        by_severity: Dict[str, int] = {s.value: 0 for s in Severity}
        by_category: Dict[str, int] = {}
        files_with_issues: set = set()

        for finding in findings:
            sev_val = finding.severity.value if isinstance(finding.severity, Severity) else finding.severity
            by_severity[sev_val] = by_severity.get(sev_val, 0) + 1
            by_category[finding.category] = by_category.get(finding.category, 0) + 1
            files_with_issues.add(finding.file_path)

        return {
            "total_findings": len(findings),
            "by_severity": by_severity,
            "by_category": by_category,
            "files_with_issues": len(files_with_issues),
        }

    def _calculate_risk_score(self, findings: List[SecurityFinding]) -> float:
        """Calculate overall risk score (0-100)."""
        if not findings:
            return 0.0

        severity_weights = {
            Severity.CRITICAL: 25,
            Severity.HIGH: 15,
            Severity.MEDIUM: 8,
            Severity.LOW: 3,
            Severity.INFO: 1,
        }

        total_score = 0
        for finding in findings:
            total_score += severity_weights.get(finding.severity, 0)

        # Cap at 100
        return min(100.0, total_score)

    def _check_compliance(self, findings: List[SecurityFinding]) -> Dict[str, Any]:
        """Check compliance against security standards."""
        owasp_issues: Dict[str, int] = {}

        for finding in findings:
            if finding.owasp:
                owasp_issues[finding.owasp] = owasp_issues.get(finding.owasp, 0) + 1

        critical_count = sum(1 for f in findings if f.severity == Severity.CRITICAL)

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
        """Export findings in SARIF format."""
        results = []
        for finding in report.findings:
            result = {
                "ruleId": finding.id,
                "level": "error" if finding.severity in [Severity.CRITICAL, Severity.HIGH] else "warning",
                "message": {"text": finding.description},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": finding.file_path},
                            "region": {"startLine": finding.line_number},
                        }
                    }
                ],
            }
            results.append(result)

        return {
            "version": "2.1.0",
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "OmniAudit Security Analyzer",
                            "version": self.version,
                        }
                    },
                    "results": results,
                }
            ],
        }


__all__ = [
    "SecurityAnalyzer",
    "SecurityFinding",
    "SecurityReport",
    "Severity",
    "VulnerabilityCategory",
    "CWE",
]
