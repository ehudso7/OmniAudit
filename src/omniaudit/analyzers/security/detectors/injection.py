"""
Injection Vulnerability Detection Module

Detects SQL injection, command injection, and other injection vulnerabilities.
"""

import re
import uuid
from pathlib import Path
from typing import List, Dict, Any
import yaml

from ..types import (
    SecurityFinding,
    Severity,
    VulnerabilityCategory,
    CWE,
    InjectionPattern,
)


class InjectionDetector:
    """
    Detects injection vulnerabilities in source code.

    Covers:
    - SQL Injection (CWE-89)
    - Command Injection (CWE-78)
    - Code Injection (CWE-94)
    - LDAP Injection (CWE-90)
    - XPath Injection (CWE-643)
    """

    def __init__(self, rules_path: Path):
        """Initialize injection detector with rules."""
        self.rules_path = rules_path
        self.patterns: List[InjectionPattern] = []
        self._load_patterns()

    def _load_patterns(self) -> None:
        """Load injection patterns from YAML rules file."""
        try:
            with open(self.rules_path, "r", encoding="utf-8") as f:
                rules = yaml.safe_load(f)

            if "injection" in rules:
                for rule in rules["injection"]:
                    pattern = InjectionPattern(
                        name=rule["name"],
                        pattern=rule["pattern"],
                        category=VulnerabilityCategory(rule["category"]),
                        severity=Severity(rule["severity"]),
                        cwe_id=rule["cwe_id"],
                        description=rule["description"],
                        recommendation=rule["recommendation"],
                    )
                    self.patterns.append(pattern)
        except Exception as e:
            self._load_builtin_patterns()

    def _load_builtin_patterns(self) -> None:
        """Load built-in injection patterns as fallback."""
        builtin = [
            InjectionPattern(
                name="SQL Injection - String Concatenation",
                pattern=r'(?i)(execute|exec|query|select|insert|update|delete).*\+.*[\'"]',
                category=VulnerabilityCategory.INJECTION,
                severity=Severity.HIGH,
                cwe_id=89,
                description="Potential SQL injection via string concatenation",
                recommendation="Use parameterized queries or prepared statements.",
            ),
            InjectionPattern(
                name="Command Injection - os.system",
                pattern=r"os\.system\([^)]*\+[^)]*\)",
                category=VulnerabilityCategory.INJECTION,
                severity=Severity.CRITICAL,
                cwe_id=78,
                description="Command injection via os.system",
                recommendation="Use subprocess with argument lists.",
            ),
        ]
        self.patterns.extend(builtin)

    def scan_file(self, file_path: Path) -> List[SecurityFinding]:
        """
        Scan a single file for injection vulnerabilities.

        Args:
            file_path: Path to file to scan

        Returns:
            List of security findings
        """
        findings: List[SecurityFinding] = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, start=1):
                for pattern in self.patterns:
                    matches = re.finditer(pattern.pattern, line)
                    for match in matches:
                        if self._is_false_positive(line, pattern):
                            continue

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
        """
        Recursively scan directory for injection vulnerabilities.

        Args:
            directory: Root directory to scan
            extensions: List of file extensions to scan

        Returns:
            List of all security findings
        """
        if extensions is None:
            extensions = [".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".php", ".rb", ".go"]

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

    def _is_false_positive(self, line: str, pattern: InjectionPattern) -> bool:
        """
        Check if a match is likely a false positive.

        Args:
            line: The full line of code
            pattern: The injection pattern

        Returns:
            True if likely false positive
        """
        # Check for parameterized queries (which are safe)
        if "?" in line or "%s" in line or "$1" in line:
            # Could be parameterized, but need more context
            # For now, still flag but with lower confidence
            return False

        # Skip test files (less critical)
        if "test_" in line.lower() or "_test" in line.lower():
            return True

        return False

    def _create_finding(
        self,
        pattern: InjectionPattern,
        file_path: str,
        line_number: int,
        code_snippet: str,
    ) -> SecurityFinding:
        """Create a security finding from a pattern match."""
        cwe = CWE.create(pattern.cwe_id, self._get_cwe_name(pattern.cwe_id))

        # Determine OWASP category
        owasp_mapping = {
            89: "A03:2021-Injection",  # SQL Injection
            78: "A03:2021-Injection",  # Command Injection
            94: "A03:2021-Injection",  # Code Injection
            95: "A03:2021-Injection",  # Code Injection
        }

        owasp = owasp_mapping.get(pattern.cwe_id, "A03:2021-Injection")

        return SecurityFinding(
            id=str(uuid.uuid4()),
            title=pattern.name,
            description=pattern.description,
            severity=pattern.severity,
            category=pattern.category,
            cwe=cwe,
            owasp=owasp,
            confidence=0.8,  # Medium-high confidence for pattern matching
            file_path=file_path,
            line_number=line_number,
            code_snippet=code_snippet,
            recommendation=pattern.recommendation,
            references=[
                "https://owasp.org/www-community/attacks/SQL_Injection",
                "https://owasp.org/www-community/attacks/Command_Injection",
                "https://cheatsheetseries.owasp.org/cheatsheets/Injection_Prevention_Cheat_Sheet.html",
            ],
            metadata={"pattern_name": pattern.name, "cwe_id": pattern.cwe_id},
        )

    def _get_cwe_name(self, cwe_id: int) -> str:
        """Get CWE name from ID."""
        cwe_names = {
            89: "SQL Injection",
            78: "OS Command Injection",
            94: "Improper Control of Generation of Code",
            95: "Improper Neutralization of Directives in Dynamically Evaluated Code",
            90: "LDAP Injection",
            643: "XPath Injection",
        }
        return cwe_names.get(cwe_id, "Injection Vulnerability")
