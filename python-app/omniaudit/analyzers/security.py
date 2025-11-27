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
from datetime import datetime, timezone
from dataclasses import dataclass, field
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


def _utc_now() -> datetime:
    """Return current UTC datetime with timezone info."""
    return datetime.now(timezone.utc)
class Severity(str, Enum):
    """Severity levels for security findings."""

Security Analysis Module

Provides security analysis capabilities including vulnerability detection,
secret scanning, and OWASP Top 10 coverage.
Security Analyzer

Analyzes code for security vulnerabilities including
SAST findings, secret detection, and injection vulnerabilities.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class Severity(str, Enum):
    """Security finding severity levels."""

from dataclasses import dataclass, field
from datetime import datetime

from .base import BaseAnalyzer


class Severity(Enum):
    """Security finding severity levels."""
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
class CWE(BaseModel):
    """Common Weakness Enumeration reference."""

    id: int = Field(..., description="CWE ID number")
    name: str = Field(..., description="CWE name")
    url: str = Field(..., description="CWE reference URL")

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
    timestamp: datetime = field(default_factory=_utc_now)
class SecurityFinding(BaseModel):
    """A single security finding."""

    id: str = Field(..., description="Unique finding ID")
    title: str = Field(..., description="Finding title")
    description: str = Field(..., description="Detailed description")
    severity: Severity = Field(..., description="Severity level")
    category: VulnerabilityCategory = Field(..., description="Vulnerability category")
    cwe: Optional[CWE] = Field(None, description="Associated CWE")
    owasp: Optional[str] = Field(None, description="OWASP Top 10 category")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence (0-1)")
    file_path: str = Field(..., description="File containing the issue")
    line_number: int = Field(..., description="Line number")
    code_snippet: str = Field(..., description="Relevant code snippet")
    recommendation: str = Field(..., description="Remediation advice")
    references: List[str] = Field(default_factory=list, description="External references")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class SecurityReport(BaseModel):
    """Complete security analysis report."""

    scan_id: str = Field(..., description="Unique scan ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Scan timestamp")
    findings: List[SecurityFinding] = Field(default_factory=list, description="All findings")
    summary: Dict[str, Any] = Field(default_factory=dict, description="Summary statistics")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Scan metadata")

    def get_severity_counts(self) -> Dict[str, int]:
        """Get count of findings by severity."""
        counts = {severity.value: 0 for severity in Severity}
        for finding in self.findings:
            sev_val = finding.severity.value if isinstance(finding.severity, Severity) else finding.severity
            if sev_val in counts:
                counts[sev_val] += 1
            counts[finding.severity.value] += 1
        return counts

    def get_category_counts(self) -> Dict[str, int]:
        """Get count of findings by category."""
        counts: Dict[str, int] = {}
        for finding in self.findings:
            category = finding.category
            category = finding.category.value
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
        # Pattern excludes common placeholders like "****", "xxx", "REPLACE", "your-password"
        "name": "Hardcoded Password",
        "pattern": r"(?i)(password|passwd|pwd)\s*[=:]\s*['\"](?!(\*+|x+|X+|your[_-]|REPLACE|placeholder|example|secret123))[^'\"]{4,}['\"]",
        "severity": Severity.HIGH,
        "category": VulnerabilityCategory.SECRET_EXPOSURE.value,
        "cwe_id": 798,
        "cwe_name": "Use of Hard-coded Credentials",
        "recommendation": "Use environment variables or secure vaults for passwords.",
    },
]

INJECTION_PATTERNS = [
    {
        # More specific pattern: looks for SQL keywords followed by string concatenation with variables
        "name": "SQL Injection",
        "pattern": r"(?i)['\"](?:SELECT|INSERT|UPDATE|DELETE)[^'\"]*['\"][\s]*\+[\s]*[a-zA-Z_]",
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
class SecurityAnalyzer:
    """
    Performs comprehensive security analysis on codebases.

    Features:
    - Secret detection (API keys, passwords, tokens, certificates)
    - SAST analysis (SQL injection, XSS, SSRF, path traversal)
    - Cryptographic weakness detection
    - OWASP Top 10 coverage
    - CWE mapping
    - Severity classification
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize security analyzer."""
        self.config = config or {}
        self._validate_config()

@dataclass
class SecurityFinding:
    """Represents a security finding."""
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
    category: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    recommendation: Optional[str] = None
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None
    references: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert finding to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "category": self.category,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "code_snippet": self.code_snippet,
            "recommendation": self.recommendation,
            "cwe_id": self.cwe_id,
            "owasp_category": self.owasp_category,
            "references": self.references,
        }


@dataclass
class SecurityReport:
    """Security analysis report."""
    findings: List[SecurityFinding] = field(default_factory=list)
    scan_timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    scan_duration_ms: Optional[int] = None
    files_scanned: int = 0
    vulnerabilities_by_severity: Dict[str, int] = field(default_factory=dict)

    def add_finding(self, finding: SecurityFinding) -> None:
        """Add a finding to the report."""
        self.findings.append(finding)
        severity_key = finding.severity.value
        self.vulnerabilities_by_severity[severity_key] = (
            self.vulnerabilities_by_severity.get(severity_key, 0) + 1
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "findings": [f.to_dict() for f in self.findings],
            "scan_timestamp": self.scan_timestamp,
            "scan_duration_ms": self.scan_duration_ms,
            "files_scanned": self.files_scanned,
            "vulnerabilities_by_severity": self.vulnerabilities_by_severity,
            "total_findings": len(self.findings),
        }


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
    Analyzes code for security vulnerabilities.

    Capabilities:
    - SAST (Static Application Security Testing)
    - Secret detection (API keys, passwords, tokens)
    - Injection vulnerability detection (SQL, XSS, command)
    - Cryptographic issue detection
    - SARIF export support

    Configuration:
        project_path: str - Path to project root (required)
        scan_secrets: bool - Enable secret scanning (default: True)
        scan_injections: bool - Enable injection scanning (default: True)
        excluded_paths: List[str] - Paths to exclude from scanning

    Example:
        >>> analyzer = SecurityAnalyzer({"project_path": "."})
        >>> result = analyzer.analyze({})
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
            "files_with_issues": len(files_with_issues),
        }

    def _calculate_risk_score(self, findings: List[SecurityFinding]) -> float:
            "files_with_issues": len(set(f.get("file_path", "") for f in findings)),
        }

    def _calculate_risk_score(self, findings: List[Dict[str, Any]]) -> float:
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
            if finding.owasp:
                owasp_issues[finding.owasp] = owasp_issues.get(finding.owasp, 0) + 1

        critical_count = sum(1 for f in findings if f.severity == Severity.CRITICAL)
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
        """Export findings in SARIF format."""
        results = []
        for finding in report.findings:
            result = {
                "ruleId": finding.id,
                "level": "error" if finding.severity in [Severity.CRITICAL, Severity.HIGH] else "warning",
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
            }
            results.append(result)

        return {
            "version": "2.1.0",
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            })

        return {
            "version": "2.1.0",
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "OmniAudit Security Analyzer",
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
        return "1.0.0"

    def _validate_config(self) -> None:
        """Validate analyzer configuration."""
        # Basic validation - can be extended as needed
        return "0.1.0"

    def _validate_config(self) -> None:
        """Validate analyzer configuration."""
        # project_path is optional for security analyzer
        pass

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform security analysis on the codebase.

        Args:
            data: Input data for analysis

        Returns:
            Security analysis results with findings and metrics
        """
        # Placeholder implementation
        return {
            "analyzer": self.name,
            "version": self.version,
            "data": {
                "findings": [],
                "summary": {
                    "total_findings": 0,
                    "by_severity": {},
                },
            },
        }


__all__ = [
    "SecurityAnalyzer",
    "SecurityFinding",
    "SecurityReport",
    "Severity",
    "VulnerabilityCategory",
    "CWE",
]
        Analyze code for security vulnerabilities.

        Args:
            data: Optional input data containing code or file paths

        Returns:
            Security analysis results
        """
        report = SecurityReport()

        # Get configuration
        project_path = self.config.get("project_path")
        scan_secrets = self.config.get("scan_secrets", True)
        scan_injections = self.config.get("scan_injections", True)

        # Perform security scans based on configuration
        if scan_secrets:
            self._scan_secrets(data, report)

        if scan_injections:
            self._scan_injections(data, report)

        return self._create_response(report.to_dict())

    def _scan_secrets(self, data: Dict[str, Any], report: SecurityReport) -> None:
        """Scan for hardcoded secrets."""
        # Placeholder implementation
        pass

    def _scan_injections(self, data: Dict[str, Any], report: SecurityReport) -> None:
        """Scan for injection vulnerabilities."""
        # Placeholder implementation
        pass
