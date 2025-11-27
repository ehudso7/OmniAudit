"""
Secrets Detection Module

Detects hardcoded secrets, API keys, passwords, tokens, and certificates in code.
"""

import re
import uuid
from pathlib import Path
from typing import List, Dict, Any
import yaml

from ..types import SecurityFinding, Severity, VulnerabilityCategory, CWE, SecretPattern


class SecretsDetector:
    """
    Detects secrets and credentials in source code.

    Uses regex patterns to identify:
    - API keys (AWS, Google, Stripe, etc.)
    - Authentication tokens
    - Private keys and certificates
    - Passwords
    - Database connection strings
    """

    def __init__(self, rules_path: Path):
        """Initialize secrets detector with rules."""
        self.rules_path = rules_path
        self.patterns: List[SecretPattern] = []
        self._load_patterns()

    def _load_patterns(self) -> None:
        """Load secret patterns from YAML rules file."""
        try:
            with open(self.rules_path, "r", encoding="utf-8") as f:
                rules = yaml.safe_load(f)

            if "secrets" in rules:
                for rule in rules["secrets"]:
                    pattern = SecretPattern(
                        name=rule["name"],
                        pattern=rule["pattern"],
                        severity=Severity(rule["severity"]),
                        confidence=rule["confidence"],
                        description=rule["description"],
                        recommendation=rule["recommendation"],
                    )
                    self.patterns.append(pattern)
        except Exception as e:
            # If loading fails, use built-in patterns
            self._load_builtin_patterns()

    def _load_builtin_patterns(self) -> None:
        """Load built-in secret patterns as fallback."""
        builtin = [
            SecretPattern(
                name="Generic API Key",
                pattern=r'(?i)(api[_-]?key|apikey)([\'"\s:=]+)?[0-9a-zA-Z\-_]{20,}',
                severity=Severity.HIGH,
                confidence=0.75,
                description="Generic API key pattern detected",
                recommendation="Move API keys to environment variables.",
            ),
            SecretPattern(
                name="Private Key",
                pattern=r"-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----",
                severity=Severity.CRITICAL,
                confidence=1.0,
                description="Private cryptographic key exposed",
                recommendation="Remove private keys from code immediately.",
            ),
            SecretPattern(
                name="AWS Access Key",
                pattern=r"(?i)(AKIA[0-9A-Z]{16})",
                severity=Severity.CRITICAL,
                confidence=0.95,
                description="AWS Access Key ID exposed",
                recommendation="Remove hardcoded AWS credentials.",
            ),
        ]
        self.patterns.extend(builtin)

    def scan_file(self, file_path: Path) -> List[SecurityFinding]:
        """
        Scan a single file for secrets.

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
                        # Check for false positives
                        if self._is_false_positive(line, match.group(0)):
                            continue

                        finding = self._create_finding(
                            pattern=pattern,
                            file_path=str(file_path),
                            line_number=line_num,
                            code_snippet=line.strip(),
                            matched_text=match.group(0),
                        )
                        findings.append(finding)

        except Exception as e:
            # Log error but continue scanning
            pass

        return findings

    def scan_directory(self, directory: Path, extensions: List[str] = None) -> List[SecurityFinding]:
        """
        Recursively scan directory for secrets.

        Args:
            directory: Root directory to scan
            extensions: List of file extensions to scan (e.g., ['.py', '.js'])

        Returns:
            List of all security findings
        """
        if extensions is None:
            extensions = [
                ".py",
                ".js",
                ".jsx",
                ".ts",
                ".tsx",
                ".java",
                ".go",
                ".rb",
                ".php",
                ".env",
                ".config",
                ".yaml",
                ".yml",
                ".json",
                ".xml",
            ]

        findings: List[SecurityFinding] = []

        for ext in extensions:
            for file_path in directory.rglob(f"*{ext}"):
                # Skip common directories
                if any(
                    part in file_path.parts
                    for part in ["node_modules", "venv", "__pycache__", ".git", "dist", "build"]
                ):
                    continue

                file_findings = self.scan_file(file_path)
                findings.extend(file_findings)

        return findings

    def _is_false_positive(self, line: str, matched_text: str) -> bool:
        """
        Check if a match is likely a false positive.

        Args:
            line: The full line of code
            matched_text: The matched secret text

        Returns:
            True if likely false positive
        """
        # Check for common false positive indicators
        false_positive_indicators = [
            "example",
            "sample",
            "test",
            "dummy",
            "fake",
            "placeholder",
            "xxx",
            "your-key-here",
            "your_key_here",
            "INSERT_",
            "TODO",
            "FIXME",
        ]

        line_lower = line.lower()
        matched_lower = matched_text.lower()

        for indicator in false_positive_indicators:
            if indicator in line_lower or indicator in matched_lower:
                return True

        # Check if it's in a comment
        if re.search(r"^\s*#", line) or re.search(r"^\s*//", line):
            # More lenient for comments, but still flag high-confidence patterns
            return False

        return False

    def _create_finding(
        self,
        pattern: SecretPattern,
        file_path: str,
        line_number: int,
        code_snippet: str,
        matched_text: str,
    ) -> SecurityFinding:
        """Create a security finding from a pattern match."""
        # Redact the actual secret in the snippet
        redacted_snippet = code_snippet.replace(matched_text, "[REDACTED]")

        # Map secret types to CWE
        cwe_mapping = {
            "AWS": CWE.create(798, "Use of Hard-coded Credentials"),
            "API": CWE.create(798, "Use of Hard-coded Credentials"),
            "Private Key": CWE.create(321, "Use of Hard-coded Cryptographic Key"),
            "Password": CWE.create(259, "Use of Hard-coded Password"),
            "Token": CWE.create(798, "Use of Hard-coded Credentials"),
            "Secret": CWE.create(798, "Use of Hard-coded Credentials"),
        }

        # Determine CWE based on pattern name
        cwe = None
        for key, value in cwe_mapping.items():
            if key.lower() in pattern.name.lower():
                cwe = value
                break

        if cwe is None:
            cwe = CWE.create(798, "Use of Hard-coded Credentials")

        return SecurityFinding(
            id=str(uuid.uuid4()),
            title=f"Secret Exposure: {pattern.name}",
            description=pattern.description,
            severity=pattern.severity,
            category=VulnerabilityCategory.SECRET_EXPOSURE,
            cwe=cwe,
            owasp="A02:2021-Cryptographic Failures",
            confidence=pattern.confidence,
            file_path=file_path,
            line_number=line_number,
            code_snippet=redacted_snippet,
            recommendation=pattern.recommendation,
            references=[
                "https://owasp.org/www-project-top-ten/2017/A3_2017-Sensitive_Data_Exposure",
                "https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html",
            ],
            metadata={"pattern_name": pattern.name, "matched_length": len(matched_text)},
        )
