"""
OWASP Top 10 Detection Module

Detects vulnerabilities from the OWASP Top 10.
"""

import re
import uuid
from pathlib import Path
from typing import List, Optional
import yaml

from ..types import SecurityFinding, Severity, VulnerabilityCategory, CWE


class OWASPDetector:
    """
    Detects OWASP Top 10 vulnerabilities.

    Covers:
    - A01:2021 - Broken Access Control
    - A02:2021 - Cryptographic Failures
    - A03:2021 - Injection
    - A04:2021 - Insecure Design
    - A05:2021 - Security Misconfiguration
    - A06:2021 - Vulnerable and Outdated Components
    - A07:2021 - Identification and Authentication Failures
    - A08:2021 - Software and Data Integrity Failures
    - A09:2021 - Security Logging and Monitoring Failures
    - A10:2021 - Server-Side Request Forgery (SSRF)
    """

    def __init__(self, rules_path: Path):
        """Initialize OWASP detector with rules."""
        self.rules_path = rules_path
        self.patterns: List[dict] = []
        self._load_patterns()

    def _load_patterns(self) -> None:
        """Load OWASP patterns from YAML rules file."""
        try:
            with open(self.rules_path, "r", encoding="utf-8") as f:
                rules = yaml.safe_load(f)

            # Combine patterns from multiple categories
            for category in ["owasp", "ssrf", "path_traversal", "authentication"]:
                if category in rules:
                    self.patterns.extend(rules[category])

        except Exception:
            self._load_builtin_patterns()

    def _load_builtin_patterns(self) -> None:
        """Load built-in OWASP patterns as fallback."""
        self.patterns = [
            {
                "name": "Debug Mode Enabled",
                "pattern": r"(?i)debug\s*=\s*True",
                "category": "configuration",
                "severity": "medium",
                "cwe_id": 489,
                "description": "Debug mode enabled - may leak sensitive information",
                "recommendation": "Disable debug mode in production.",
                "owasp": "A05:2021-Security Misconfiguration",
            },
            {
                "name": "SSRF - Unvalidated URL",
                "pattern": r"requests\.(get|post|put|delete)\([^)]*input[^)]*\)",
                "category": "ssrf",
                "severity": "high",
                "cwe_id": 918,
                "description": "Potential SSRF via unvalidated URL",
                "recommendation": "Validate and whitelist allowed domains.",
                "owasp": "A10:2021-Server-Side Request Forgery",
            },
        ]

    def scan_file(self, file_path: Path) -> List[SecurityFinding]:
        """Scan a single file for OWASP Top 10 vulnerabilities."""
        findings: List[SecurityFinding] = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, start=1):
                for pattern in self.patterns:
                    matches = re.finditer(pattern["pattern"], line)
                    for match in matches:
                        finding = self._create_finding(
                            pattern=pattern,
                            file_path=str(file_path),
                            line_number=line_num,
                            code_snippet=line.strip(),
                        )
                        findings.append(finding)

        except Exception:
            pass

        return findings

    def scan_directory(
        self, directory: Path, extensions: List[str] = None
    ) -> List[SecurityFinding]:
        """Recursively scan directory for OWASP vulnerabilities."""
        if extensions is None:
            extensions = [
                ".py",
                ".js",
                ".jsx",
                ".ts",
                ".tsx",
                ".java",
                ".php",
                ".rb",
                ".go",
                ".config",
                ".yaml",
                ".yml",
            ]

        findings: List[SecurityFinding] = []

        for ext in extensions:
            for file_path in directory.rglob(f"*{ext}"):
                if any(
                    part in file_path.parts
                    for part in ["node_modules", "venv", "__pycache__", ".git", "dist", "build"]
                ):
                    continue

                file_findings = self.scan_file(file_path)
                findings.extend(file_findings)

        return findings

    def _create_finding(
        self, pattern: dict, file_path: str, line_number: int, code_snippet: str
    ) -> SecurityFinding:
        """Create a security finding from a pattern match."""
        cwe = CWE.create(pattern["cwe_id"], self._get_cwe_name(pattern["cwe_id"]))

        # Determine category
        category_map = {
            "configuration": VulnerabilityCategory.CONFIGURATION,
            "ssrf": VulnerabilityCategory.SSRF,
            "path_traversal": VulnerabilityCategory.PATH_TRAVERSAL,
            "authentication": VulnerabilityCategory.AUTHENTICATION,
            "authorization": VulnerabilityCategory.AUTHORIZATION,
            "deserialization": VulnerabilityCategory.DESERIALIZATION,
            "xxe": VulnerabilityCategory.XXE,
            "csrf": VulnerabilityCategory.CSRF,
            "data_exposure": VulnerabilityCategory.DATA_EXPOSURE,
        }

        category = category_map.get(
            pattern.get("category", "configuration"), VulnerabilityCategory.CONFIGURATION
        )

        owasp = pattern.get("owasp", "OWASP Top 10")

        return SecurityFinding(
            id=str(uuid.uuid4()),
            title=pattern["name"],
            description=pattern["description"],
            severity=Severity(pattern["severity"]),
            category=category,
            cwe=cwe,
            owasp=owasp,
            confidence=0.75,
            file_path=file_path,
            line_number=line_number,
            code_snippet=code_snippet,
            recommendation=pattern["recommendation"],
            references=[
                "https://owasp.org/www-project-top-ten/",
                f"https://owasp.org/Top10/",
            ],
            metadata={"pattern_name": pattern["name"], "owasp_category": owasp},
        )

    def _get_cwe_name(self, cwe_id: int) -> str:
        """Get CWE name from ID."""
        cwe_names = {
            22: "Path Traversal",
            78: "OS Command Injection",
            79: "Cross-site Scripting",
            89: "SQL Injection",
            259: "Hard-coded Password",
            307: "Improper Restriction of Excessive Authentication Attempts",
            319: "Cleartext Transmission of Sensitive Information",
            321: "Use of Hard-coded Cryptographic Key",
            352: "Cross-Site Request Forgery",
            489: "Active Debug Code",
            502: "Deserialization of Untrusted Data",
            521: "Weak Password Requirements",
            611: "XML External Entity Reference",
            639: "Insecure Direct Object Reference",
            778: "Insufficient Logging",
            918: "Server-Side Request Forgery",
        }
        return cwe_names.get(cwe_id, "Security Vulnerability")
