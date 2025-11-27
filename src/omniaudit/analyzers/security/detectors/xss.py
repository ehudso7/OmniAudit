"""
Cross-Site Scripting (XSS) Detection Module

Detects XSS vulnerabilities in web applications.
"""

import re
import uuid
from pathlib import Path
from typing import List
import yaml

from ..types import SecurityFinding, Severity, VulnerabilityCategory, CWE


class XSSDetector:
    """
    Detects XSS vulnerabilities in source code.

    Covers:
    - Reflected XSS
    - Stored XSS
    - DOM-based XSS
    - Template injection
    """

    def __init__(self, rules_path: Path):
        """Initialize XSS detector with rules."""
        self.rules_path = rules_path
        self.patterns: List[dict] = []
        self._load_patterns()

    def _load_patterns(self) -> None:
        """Load XSS patterns from YAML rules file."""
        try:
            with open(self.rules_path, "r", encoding="utf-8") as f:
                rules = yaml.safe_load(f)

            if "xss" in rules:
                self.patterns = rules["xss"]
        except Exception:
            self._load_builtin_patterns()

    def _load_builtin_patterns(self) -> None:
        """Load built-in XSS patterns as fallback."""
        self.patterns = [
            {
                "name": "XSS - innerHTML",
                "pattern": r"(?i)(innerHTML|outerHTML)\s*=\s*[^'\"']",
                "severity": "high",
                "cwe_id": 79,
                "description": "Potential XSS via innerHTML",
                "recommendation": "Use textContent or properly escape HTML.",
            }
        ]

    def scan_file(self, file_path: Path) -> List[SecurityFinding]:
        """Scan a single file for XSS vulnerabilities."""
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
        """Recursively scan directory for XSS vulnerabilities."""
        if extensions is None:
            extensions = [".js", ".jsx", ".ts", ".tsx", ".html", ".vue", ".py", ".php", ".rb"]

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
        cwe = CWE.create(pattern["cwe_id"], "Cross-site Scripting (XSS)")

        return SecurityFinding(
            id=str(uuid.uuid4()),
            title=pattern["name"],
            description=pattern["description"],
            severity=Severity(pattern["severity"]),
            category=VulnerabilityCategory(pattern["category"]),
            cwe=cwe,
            owasp="A03:2021-Injection",
            confidence=0.75,
            file_path=file_path,
            line_number=line_number,
            code_snippet=code_snippet,
            recommendation=pattern["recommendation"],
            references=[
                "https://owasp.org/www-community/attacks/xss/",
                "https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html",
            ],
            metadata={"pattern_name": pattern["name"]},
        )
