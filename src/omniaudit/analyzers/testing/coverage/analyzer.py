"""
Test Coverage Analysis Module.

Analyzes test coverage and identifies uncovered code.
"""

import ast
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from ..types import CoverageMetrics, UncoveredCode


class CoverageAnalyzer:
    """Analyzes test coverage."""

    def __init__(self, project_path: Path):
        """Initialize coverage analyzer.

        Args:
            project_path: Project root path
        """
        self.project_path = project_path

    def analyze_coverage(self) -> Optional[CoverageMetrics]:
        """Analyze test coverage.

        Returns:
            Coverage metrics or None
        """
        # Try to read existing coverage data
        coverage_file = self.project_path / ".coverage"
        if not coverage_file.exists():
            # Try to find coverage.json
            coverage_json = self.project_path / "coverage.json"
            if coverage_json.exists():
                return self._parse_coverage_json(coverage_json)
            return None

        # Try to run coverage report
        try:
            result = subprocess.run(
                ["coverage", "json", "-o", "coverage.json"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                coverage_json = self.project_path / "coverage.json"
                if coverage_json.exists():
                    return self._parse_coverage_json(coverage_json)

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return None

    def _parse_coverage_json(self, coverage_file: Path) -> Optional[CoverageMetrics]:
        """Parse coverage JSON file.

        Args:
            coverage_file: Path to coverage.json

        Returns:
            Coverage metrics
        """
        try:
            with open(coverage_file, "r") as f:
                data = json.load(f)

            totals = data.get("totals", {})

            line_coverage = totals.get("percent_covered", 0.0)
            total_lines = totals.get("num_statements", 0)
            covered_lines = totals.get("covered_lines", 0)
            missed_lines = totals.get("missing_lines", 0)

            return CoverageMetrics(
                line_coverage=round(line_coverage, 2),
                branch_coverage=round(totals.get("percent_covered_branches", 0.0), 2),
                function_coverage=0.0,  # Not available in standard coverage
                total_lines=total_lines,
                covered_lines=covered_lines,
                missed_lines=missed_lines,
            )

        except (json.JSONDecodeError, FileNotFoundError):
            return None

    def identify_uncovered_code(
        self, source_files: List[Path]
    ) -> List[UncoveredCode]:
        """Identify critical uncovered code.

        Args:
            source_files: Source files to analyze

        Returns:
            List of uncovered code regions
        """
        uncovered = []

        # This is a simplified heuristic approach
        # In production, parse actual coverage data

        for file_path in source_files:
            if file_path.suffix != ".py":
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    source = f.read()

                tree = ast.parse(source)

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Check if function looks critical (error handling, etc.)
                        if self._is_critical_function(node):
                            uncovered.append(
                                UncoveredCode(
                                    file_path=str(file_path),
                                    line_start=node.lineno,
                                    line_end=node.end_lineno or node.lineno,
                                    function_name=node.name,
                                    complexity=self._calculate_complexity(node),
                                    priority="high",
                                    reason="Critical function with error handling",
                                )
                            )

            except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
                pass

        return uncovered[:10]  # Limit results

    def _is_critical_function(self, node: ast.FunctionDef) -> bool:
        """Check if function is critical.

        Args:
            node: Function node

        Returns:
            True if critical
        """
        # Check for error handling
        has_try = any(isinstance(child, ast.Try) for child in ast.walk(node))

        # Check for important keywords
        source = ast.unparse(node)
        has_critical_keywords = any(
            keyword in source.lower()
            for keyword in ["delete", "remove", "destroy", "drop", "clear"]
        )

        return has_try or has_critical_keywords

    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate complexity.

        Args:
            node: AST node

        Returns:
            Complexity score
        """
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1
        return complexity
