"""Hardcoded string detector for i18n."""

import re
import ast
from pathlib import Path
from typing import List, Set

from ..types import HardcodedString


class HardcodedStringDetector:
    """Detect hardcoded user-facing strings."""

    # Common technical strings to ignore
    IGNORED_STRINGS: Set[str] = {
        "",
        " ",
        "\n",
        "\t",
        "utf-8",
        "utf8",
        "ascii",
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "true",
        "false",
        "null",
        "undefined",
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "PATCH",
        "HEAD",
        "OPTIONS",
    }

    # Patterns that suggest technical/non-user-facing strings
    TECHNICAL_PATTERNS = [
        r"^[a-z_][a-z0-9_]*$",  # Variable names
        r"^[A-Z_][A-Z0-9_]*$",  # Constants
        r"^\.[a-z]+$",  # File extensions
        r"^#[0-9a-fA-F]{3,6}$",  # Hex colors
        r"^\d+(\.\d+)?$",  # Numbers
        r"^https?://",  # URLs
        r"^/[a-z0-9/_-]*$",  # Paths
        r"^@[a-z]",  # Decorators/annotations
        r"^\$[a-z]",  # Template variables
    ]

    @staticmethod
    def detect_in_python(file_path: Path) -> List[HardcodedString]:
        """
        Detect hardcoded strings in Python files.

        Args:
            file_path: Path to Python file

        Returns:
            List of hardcoded strings found
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(file_path))
        except (IOError, SyntaxError, UnicodeDecodeError):
            return []

        hardcoded = []
        lines = content.split("\n")

        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                string_value = node.value
                line_number = node.lineno

                # Filter out likely non-user-facing strings
                if HardcodedStringDetector._is_user_facing_string(string_value):
                    context = lines[line_number - 1].strip() if line_number <= len(lines) else ""

                    hardcoded.append(
                        HardcodedString(
                            text=string_value[:100],  # Truncate long strings
                            file_path=str(file_path),
                            line_number=line_number,
                            context=context[:200],
                            confidence=HardcodedStringDetector._calculate_confidence(string_value),
                            suggestion=f"Extract to translation file: t('{HardcodedStringDetector._suggest_key(string_value)}')",
                        )
                    )

        return hardcoded

    @staticmethod
    def detect_in_javascript(file_path: Path) -> List[HardcodedString]:
        """
        Detect hardcoded strings in JavaScript/TypeScript files.

        Args:
            file_path: Path to JS/TS file

        Returns:
            List of hardcoded strings found
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except (IOError, UnicodeDecodeError):
            return []

        hardcoded = []
        lines = content.split("\n")

        # Simple regex-based detection for JS strings
        # Matches strings in quotes, excluding imports and technical strings
        string_patterns = [
            r'"([^"\\]*(?:\\.[^"\\]*)*)"',  # Double quotes
            r"'([^'\\]*(?:\\.[^'\\]*)*)'",  # Single quotes
            r"`([^`\\]*(?:\\.[^`\\]*)*)`",  # Template literals (simplified)
        ]

        for line_num, line in enumerate(lines, 1):
            # Skip import/require lines
            if re.match(r"^\s*(?:import|require|from|export)\s", line):
                continue

            # Skip JSX/TSX attributes (className, id, etc.)
            if re.search(r"(?:className|id|name|type|role|for)=", line):
                continue

            for pattern in string_patterns:
                for match in re.finditer(pattern, line):
                    string_value = match.group(1)

                    if HardcodedStringDetector._is_user_facing_string(string_value):
                        hardcoded.append(
                            HardcodedString(
                                text=string_value[:100],
                                file_path=str(file_path),
                                line_number=line_num,
                                context=line.strip()[:200],
                                confidence=HardcodedStringDetector._calculate_confidence(string_value),
                                suggestion=f"Extract to translation: {{t('{HardcodedStringDetector._suggest_key(string_value)}'}}",
                            )
                        )

        return hardcoded

    @staticmethod
    def _is_user_facing_string(text: str) -> bool:
        """Check if string is likely user-facing."""
        if not text or len(text) < 3:
            return False

        if text in HardcodedStringDetector.IGNORED_STRINGS:
            return False

        # Check against technical patterns
        for pattern in HardcodedStringDetector.TECHNICAL_PATTERNS:
            if re.match(pattern, text, re.IGNORECASE):
                return False

        # Must contain at least one letter
        if not re.search(r"[a-zA-Z]", text):
            return False

        # Contains spaces or punctuation (likely sentence/phrase)
        if re.search(r"[\s.,!?]", text):
            return True

        # Capitalized words (likely user-facing)
        if re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$", text):
            return True

        # Long enough and mixed case
        if len(text) > 10 and re.search(r"[a-z]", text) and re.search(r"[A-Z]", text):
            return True

        return False

    @staticmethod
    def _calculate_confidence(text: str) -> float:
        """Calculate confidence that string is user-facing (0-1)."""
        confidence = 0.5  # Base confidence

        # Increase confidence for sentence-like strings
        if re.search(r"\s", text):
            confidence += 0.2

        # Increase for punctuation
        if re.search(r"[.,!?]", text):
            confidence += 0.1

        # Increase for capitalized start
        if re.match(r"^[A-Z]", text):
            confidence += 0.1

        # Increase for reasonable length
        if 10 < len(text) < 100:
            confidence += 0.1

        return min(1.0, confidence)

    @staticmethod
    def _suggest_key(text: str) -> str:
        """Suggest a translation key for the string."""
        # Convert to snake_case key
        key = re.sub(r"[^\w\s]", "", text.lower())
        key = re.sub(r"\s+", "_", key)
        return key[:50]  # Limit key length
