"""
Type definitions for security analyzer.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


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
            counts[finding.severity.value] += 1
        return counts

    def get_category_counts(self) -> Dict[str, int]:
        """Get count of findings by category."""
        counts = {}
        for finding in self.findings:
            category = finding.category.value
            counts[category] = counts.get(category, 0) + 1
        return counts

    def get_critical_findings(self) -> List[SecurityFinding]:
        """Get all critical severity findings."""
        return [f for f in self.findings if f.severity == Severity.CRITICAL]

    def get_high_findings(self) -> List[SecurityFinding]:
        """Get all high severity findings."""
        return [f for f in self.findings if f.severity == Severity.HIGH]


class SecretPattern(BaseModel):
    """Pattern for detecting secrets."""

    name: str = Field(..., description="Secret type name")
    pattern: str = Field(..., description="Regex pattern")
    severity: Severity = Field(..., description="Default severity")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    description: str = Field(..., description="What this secret is")
    recommendation: str = Field(..., description="How to remediate")


class InjectionPattern(BaseModel):
    """Pattern for detecting injection vulnerabilities."""

    name: str = Field(..., description="Injection type")
    pattern: str = Field(..., description="Regex pattern")
    category: VulnerabilityCategory = Field(..., description="Vulnerability category")
    severity: Severity = Field(..., description="Default severity")
    cwe_id: int = Field(..., description="Associated CWE ID")
    description: str = Field(..., description="Vulnerability description")
    recommendation: str = Field(..., description="Remediation advice")
