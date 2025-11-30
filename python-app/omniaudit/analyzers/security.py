"""
Security Analyzer Module

Analyzes code for security vulnerabilities and issues.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
import re

from .base import BaseAnalyzer, AnalyzerError


class Severity(Enum):
    """Security finding severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class SecurityFinding:
    """Represents a security issue found during analysis."""
    rule_id: str
    severity: Severity
    title: str
    description: str
    file_path: str
    line_number: int
    code_snippet: str = ""
    remediation: str = ""
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert finding to dictionary."""
        return {
            "rule_id": self.rule_id,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "code_snippet": self.code_snippet,
            "remediation": self.remediation,
            "cwe_id": self.cwe_id,
            "owasp_category": self.owasp_category,
        }


@dataclass
class SecurityReport:
    """Security analysis report."""
    findings: List[SecurityFinding] = field(default_factory=list)
    files_scanned: int = 0
    scan_duration_ms: float = 0

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.HIGH)

    @property
    def medium_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.MEDIUM)

    @property
    def low_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.LOW)

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "findings": [f.to_dict() for f in self.findings],
            "files_scanned": self.files_scanned,
            "scan_duration_ms": self.scan_duration_ms,
            "summary": {
                "critical": self.critical_count,
                "high": self.high_count,
                "medium": self.medium_count,
                "low": self.low_count,
                "total": len(self.findings),
            }
        }


class SecurityAnalyzer(BaseAnalyzer):
    """
    Analyzes code for security vulnerabilities.

    Checks for common security issues like:
    - SQL injection
    - Command injection
    - XSS vulnerabilities
    - Hardcoded secrets
    - Insecure configurations
    """

    # Patterns for detecting security issues
    SECURITY_PATTERNS = {
        "hardcoded_secret": {
            "pattern": r'(?:password|secret|api_key|apikey|token|auth)\s*=\s*["\'][^"\']{8,}["\']',
            "severity": Severity.HIGH,
            "title": "Hardcoded Secret Detected",
            "description": "A hardcoded secret or credential was found in the code.",
            "remediation": "Use environment variables or a secrets manager.",
            "cwe_id": "CWE-798",
        },
        "sql_injection": {
            "pattern": r'(?:execute|cursor\.execute)\s*\(\s*["\'].*?\%s.*?["\'].*?\%',
            "severity": Severity.CRITICAL,
            "title": "Potential SQL Injection",
            "description": "String formatting in SQL query may allow injection attacks.",
            "remediation": "Use parameterized queries instead of string formatting.",
            "cwe_id": "CWE-89",
            "owasp_category": "A03:2021-Injection",
        },
        "command_injection": {
            "pattern": r'(?:os\.system|subprocess\.call|subprocess\.run|eval|exec)\s*\([^)]*\+',
            "severity": Severity.CRITICAL,
            "title": "Potential Command Injection",
            "description": "User input may be executed as system commands.",
            "remediation": "Validate and sanitize all user input before execution.",
            "cwe_id": "CWE-78",
            "owasp_category": "A03:2021-Injection",
        },
        "insecure_deserialization": {
            "pattern": r'pickle\.loads?\s*\(|yaml\.load\s*\([^)]*\)',
            "severity": Severity.HIGH,
            "title": "Insecure Deserialization",
            "description": "Deserializing untrusted data can lead to code execution.",
            "remediation": "Use safe_load for YAML, avoid pickle for untrusted data.",
            "cwe_id": "CWE-502",
            "owasp_category": "A08:2021-Software and Data Integrity Failures",
        },
        "weak_crypto": {
            "pattern": r'(?:md5|sha1)\s*\(',
            "severity": Severity.MEDIUM,
            "title": "Weak Cryptographic Algorithm",
            "description": "MD5 and SHA1 are considered cryptographically weak.",
            "remediation": "Use SHA-256 or stronger hash algorithms.",
            "cwe_id": "CWE-327",
        },
        "debug_enabled": {
            "pattern": r'DEBUG\s*=\s*True|app\.run\s*\([^)]*debug\s*=\s*True',
            "severity": Severity.MEDIUM,
            "title": "Debug Mode Enabled",
            "description": "Debug mode may expose sensitive information in production.",
            "remediation": "Disable debug mode in production environments.",
            "cwe_id": "CWE-489",
        },
    }

    def __init__(self):
        """Initialize security analyzer."""
        self.compiled_patterns = {
            name: re.compile(rule["pattern"], re.IGNORECASE)
            for name, rule in self.SECURITY_PATTERNS.items()
        }

    async def analyze(self, code: str, filename: str = "unknown") -> SecurityReport:
        """
        Analyze code for security vulnerabilities.

        Args:
            code: Source code to analyze
            filename: Name of the file being analyzed

        Returns:
            SecurityReport with findings
        """
        import time
        start_time = time.time()

        findings: List[SecurityFinding] = []
        lines = code.split('\n')

        for line_num, line in enumerate(lines, 1):
            for rule_name, pattern in self.compiled_patterns.items():
                if pattern.search(line):
                    rule = self.SECURITY_PATTERNS[rule_name]
                    findings.append(SecurityFinding(
                        rule_id=rule_name,
                        severity=rule["severity"],
                        title=rule["title"],
                        description=rule["description"],
                        file_path=filename,
                        line_number=line_num,
                        code_snippet=line.strip()[:200],
                        remediation=rule["remediation"],
                        cwe_id=rule.get("cwe_id"),
                        owasp_category=rule.get("owasp_category"),
                    ))

        duration_ms = (time.time() - start_time) * 1000

        return SecurityReport(
            findings=findings,
            files_scanned=1,
            scan_duration_ms=duration_ms,
        )

    async def analyze_files(self, files: Dict[str, str]) -> SecurityReport:
        """
        Analyze multiple files for security vulnerabilities.

        Args:
            files: Dictionary mapping filename to content

        Returns:
            Combined SecurityReport
        """
        import time
        start_time = time.time()

        all_findings: List[SecurityFinding] = []

        for filename, content in files.items():
            report = await self.analyze(content, filename)
            all_findings.extend(report.findings)

        duration_ms = (time.time() - start_time) * 1000

        return SecurityReport(
            findings=all_findings,
            files_scanned=len(files),
            scan_duration_ms=duration_ms,
        )
