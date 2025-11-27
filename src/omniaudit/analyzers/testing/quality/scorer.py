"""
Test Quality Scoring Module.

Scores test quality based on best practices.
"""

import ast
import re
from pathlib import Path
from typing import List

from ..types import MissingEdgeCase, TestQualityIssue, TestQualityIssueInstance


class TestQualityScorer:
    """Scores test quality."""

    def __init__(self):
        """Initialize test quality scorer."""
        pass

    def analyze_test_files(self, test_files: List[Path]) -> tuple[
        List[TestQualityIssueInstance], List[MissingEdgeCase], float
    ]:
        """Analyze test files for quality issues.

        Args:
            test_files: Test files to analyze

        Returns:
            Tuple of (quality_issues, missing_edge_cases, average_quality)
        """
        quality_issues = []
        edge_cases = []
        quality_scores = []

        for test_file in test_files:
            if test_file.suffix != ".py":
                continue

            file_issues, file_edge_cases, score = self._analyze_test_file(test_file)
            quality_issues.extend(file_issues)
            edge_cases.extend(file_edge_cases)
            quality_scores.append(score)

        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0

        return quality_issues, edge_cases, round(avg_quality, 2)

    def _analyze_test_file(
        self, test_file: Path
    ) -> tuple[List[TestQualityIssueInstance], List[MissingEdgeCase], float]:
        """Analyze a single test file.

        Args:
            test_file: Test file path

        Returns:
            Tuple of (issues, edge_cases, quality_score)
        """
        issues = []
        edge_cases = []
        test_count = 0
        quality_deductions = 0.0

        try:
            with open(test_file, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    test_count += 1

                    # Check for assertions
                    has_assertions = self._has_assertions(node)
                    if not has_assertions:
                        issues.append(
                            TestQualityIssueInstance(
                                test_file=str(test_file),
                                test_function=node.name,
                                line_number=node.lineno,
                                issue_type=TestQualityIssue.NO_ASSERTIONS,
                                description="Test has no assertions",
                                severity="high",
                                suggestion="Add assertions to verify expected behavior",
                                quality_impact=8.0,
                            )
                        )
                        quality_deductions += 8.0

                    # Check for multiple assertions
                    assertion_count = self._count_assertions(node)
                    if assertion_count > 3:
                        issues.append(
                            TestQualityIssueInstance(
                                test_file=str(test_file),
                                test_function=node.name,
                                line_number=node.lineno,
                                issue_type=TestQualityIssue.SINGLE_ASSERTION_PRINCIPLE_VIOLATION,
                                description=f"Test has {assertion_count} assertions",
                                severity="low",
                                suggestion="Consider splitting into multiple focused tests",
                                quality_impact=2.0,
                            )
                        )
                        quality_deductions += 2.0

                    # Check for poor naming
                    if len(node.name) < 10:
                        issues.append(
                            TestQualityIssueInstance(
                                test_file=str(test_file),
                                test_function=node.name,
                                line_number=node.lineno,
                                issue_type=TestQualityIssue.POOR_NAMING,
                                description="Test name is too short/unclear",
                                severity="low",
                                suggestion="Use descriptive names: test_<method>_<scenario>_<expected>",
                                quality_impact=1.0,
                            )
                        )
                        quality_deductions += 1.0

        except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
            pass

        # Calculate quality score
        max_possible_deductions = test_count * 11.0 if test_count > 0 else 1.0
        quality_score = max(
            0.0, 100.0 - (quality_deductions / max_possible_deductions * 100)
        )

        return issues, edge_cases, quality_score

    def _has_assertions(self, node: ast.FunctionDef) -> bool:
        """Check if test has assertions.

        Args:
            node: Test function node

        Returns:
            True if has assertions
        """
        for child in ast.walk(node):
            if isinstance(child, ast.Assert):
                return True
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    if child.func.attr.startswith("assert"):
                        return True
        return False

    def _count_assertions(self, node: ast.FunctionDef) -> int:
        """Count assertions in test.

        Args:
            node: Test function node

        Returns:
            Assertion count
        """
        count = 0
        for child in ast.walk(node):
            if isinstance(child, ast.Assert):
                count += 1
            elif isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    if child.func.attr.startswith("assert"):
                        count += 1
        return count
