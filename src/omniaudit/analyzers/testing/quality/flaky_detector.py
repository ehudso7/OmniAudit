"""
Flaky Test Detection Module.

Detects patterns that suggest flaky tests.
"""

import ast
import re
from pathlib import Path
from typing import List

from ..types import FlakyTestPattern


class FlakyTestDetector:
    """Detects potential flaky test patterns."""

    def __init__(self):
        """Initialize flaky test detector."""
        pass

    def detect_flaky_patterns(self, test_files: List[Path]) -> List[FlakyTestPattern]:
        """Detect flaky test patterns.

        Args:
            test_files: Test files to analyze

        Returns:
            List of flaky test patterns
        """
        patterns = []

        for test_file in test_files:
            if test_file.suffix != ".py":
                continue

            file_patterns = self._analyze_test_file(test_file)
            patterns.extend(file_patterns)

        return patterns

    def _analyze_test_file(self, test_file: Path) -> List[FlakyTestPattern]:
        """Analyze a test file for flaky patterns.

        Args:
            test_file: Test file path

        Returns:
            List of flaky patterns
        """
        patterns = []

        try:
            with open(test_file, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    # Check for timing-based patterns
                    if self._has_timing_dependency(node, source):
                        patterns.append(
                            FlakyTestPattern(
                                test_file=str(test_file),
                                test_function=node.name,
                                pattern_type="timing",
                                description="Test uses sleep or time-based conditions",
                                evidence="time.sleep() or datetime operations found",
                                suggestion="Use explicit waits or mock time",
                                flakiness_score=7.0,
                            )
                        )

                    # Check for randomness
                    if self._uses_randomness(node, source):
                        patterns.append(
                            FlakyTestPattern(
                                test_file=str(test_file),
                                test_function=node.name,
                                pattern_type="randomness",
                                description="Test uses random values",
                                evidence="random module usage detected",
                                suggestion="Use fixed seeds or deterministic values",
                                flakiness_score=8.0,
                            )
                        )

                    # Check for external dependencies
                    if self._has_external_dependency(node, source):
                        patterns.append(
                            FlakyTestPattern(
                                test_file=str(test_file),
                                test_function=node.name,
                                pattern_type="external_dependency",
                                description="Test depends on external services",
                                evidence="Network calls or file system operations",
                                suggestion="Mock external dependencies",
                                flakiness_score=6.0,
                            )
                        )

        except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
            pass

        return patterns

    def _has_timing_dependency(self, node: ast.FunctionDef, source: str) -> bool:
        """Check for timing dependencies.

        Args:
            node: Test function node
            source: Full source code

        Returns:
            True if timing dependency detected
        """
        func_source = ast.unparse(node)

        # Check for sleep calls
        if "sleep" in func_source.lower():
            return True

        # Check for datetime operations
        if "datetime.now()" in func_source or "time.time()" in func_source:
            return True

        return False

    def _uses_randomness(self, node: ast.FunctionDef, source: str) -> bool:
        """Check for random value usage.

        Args:
            node: Test function node
            source: Full source code

        Returns:
            True if randomness detected
        """
        func_source = ast.unparse(node)

        # Check for random module usage
        if "random." in func_source:
            return True

        # Check for uuid without fixed seed
        if "uuid" in func_source.lower():
            return True

        return False

    def _has_external_dependency(self, node: ast.FunctionDef, source: str) -> bool:
        """Check for external dependencies.

        Args:
            node: Test function node
            source: Full source code

        Returns:
            True if external dependency detected
        """
        func_source = ast.unparse(node)

        # Check for HTTP requests
        if any(
            keyword in func_source.lower()
            for keyword in ["requests.", "urllib", "http"]
        ):
            # Check if mocked
            if "mock" not in func_source.lower():
                return True

        # Check for file operations
        if "open(" in func_source and "mock" not in func_source.lower():
            return True

        return False
