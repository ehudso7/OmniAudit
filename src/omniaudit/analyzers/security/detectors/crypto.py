"""
Cryptographic Weakness Detection Module

Detects weak cryptographic algorithms, insecure random number generation,
and other crypto-related vulnerabilities.
"""

import re
import uuid
from pathlib import Path
from typing import List
import yaml

from ..types import SecurityFinding, Severity, VulnerabilityCategory, CWE


class CryptoDetector:
    """
    Detects cryptographic weaknesses in source code.

    Covers:
    - Weak hashing algorithms (MD5, SHA1)
    - Weak encryption (DES, 3DES, RC4)
    - Insecure random number generation
    - Hard-coded cryptographic keys
    - Weak TLS/SSL versions
    """

    def __init__(self, rules_path: Path):
        """Initialize crypto detector with rules."""
        self.rules_path = rules_path
        self.patterns: List[dict] = []
        self._load_patterns()

    def _load_patterns(self) -> None:
        """Load crypto patterns from YAML rules file."""
        try:
            with open(self.rules_path, "r", encoding="utf-8") as f:
                rules = yaml.safe_load(f)

            if "crypto" in rules:
                self.patterns = rules["crypto"]
        except Exception:
            self._load_builtin_patterns()

    def _load_builtin_patterns(self) -> None:
        """Load built-in crypto patterns as fallback."""
        self.patterns = [
            {
                "name": "Weak Hash - MD5",
                "pattern": r"hashlib\.md5\(",
                "category": "cryptographic",
                "severity": "medium",
                "cwe_id": 327,
                "description": "Use of weak MD5 hashing algorithm",
                "recommendation": "Use SHA-256 or stronger hashing algorithms.",
            },
            {
                "name": "Weak Hash - SHA1",
                "pattern": r"hashlib\.sha1\(",
                "category": "cryptographic",
                "severity": "medium",
                "cwe_id": 327,
                "description": "Use of weak SHA-1 hashing algorithm",
                "recommendation": "Use SHA-256 or SHA-3 for cryptographic hashing.",
            },
            {
                "name": "Insecure Random",
                "pattern": r"random\.(random|randint|choice)",
                "category": "cryptographic",
                "severity": "low",
                "cwe_id": 338,
                "description": "Use of predictable random number generator",
                "recommendation": "Use secrets module for cryptographic operations.",
            },
        ]

    def scan_file(self, file_path: Path) -> List[SecurityFinding]:
        """Scan a single file for cryptographic weaknesses."""
        findings: List[SecurityFinding] = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, start=1):
                for pattern in self.patterns:
                    matches = re.finditer(pattern["pattern"], line)
                    for match in matches:
                        # Check context to reduce false positives
                        if self._is_acceptable_use(line, pattern):
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
        """Recursively scan directory for cryptographic weaknesses."""
        if extensions is None:
            extensions = [".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rb", ".php"]

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

    def _is_acceptable_use(self, line: str, pattern: dict) -> bool:
        """
        Check if the crypto usage is acceptable in context.

        Args:
            line: The full line of code
            pattern: The crypto pattern

        Returns:
            True if usage is acceptable (e.g., for checksums, not security)
        """
        # MD5/SHA1 are acceptable for checksums/ETags
        if "md5" in pattern["name"].lower() or "sha1" in pattern["name"].lower():
            acceptable_uses = [
                "checksum",
                "etag",
                "cache",
                "hash_object",
                "content_hash",
                # Git uses SHA1 for commit hashes
                "git",
                "object_id",
            ]
            line_lower = line.lower()
            if any(use in line_lower for use in acceptable_uses):
                return True

        # random module is acceptable for non-security purposes
        if "random" in pattern["name"].lower():
            non_security_uses = ["shuffle", "sample", "choice", "test", "mock"]
            if any(use in line.lower() for use in non_security_uses):
                # Still flag but with lower severity
                return False

        return False

    def _create_finding(
        self, pattern: dict, file_path: str, line_number: int, code_snippet: str
    ) -> SecurityFinding:
        """Create a security finding from a pattern match."""
        cwe = CWE.create(pattern["cwe_id"], self._get_cwe_name(pattern["cwe_id"]))

        return SecurityFinding(
            id=str(uuid.uuid4()),
            title=pattern["name"],
            description=pattern["description"],
            severity=Severity(pattern["severity"]),
            category=VulnerabilityCategory(pattern["category"]),
            cwe=cwe,
            owasp="A02:2021-Cryptographic Failures",
            confidence=0.85,
            file_path=file_path,
            line_number=line_number,
            code_snippet=code_snippet,
            recommendation=pattern["recommendation"],
            references=[
                "https://owasp.org/www-project-top-ten/2017/A3_2017-Sensitive_Data_Exposure",
                "https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html",
            ],
            metadata={"pattern_name": pattern["name"]},
        )

    def _get_cwe_name(self, cwe_id: int) -> str:
        """Get CWE name from ID."""
        cwe_names = {
            327: "Use of a Broken or Risky Cryptographic Algorithm",
            326: "Inadequate Encryption Strength",
            338: "Use of Cryptographically Weak Pseudo-Random Number Generator",
            321: "Use of Hard-coded Cryptographic Key",
        }
        return cwe_names.get(cwe_id, "Cryptographic Weakness")
