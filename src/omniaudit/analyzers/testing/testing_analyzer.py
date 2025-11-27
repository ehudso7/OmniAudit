"""
Testing Analyzer.

Analyzes test coverage, quality, and identifies potential issues.
"""

from pathlib import Path
from typing import Any, Dict, List

from ..base import AnalyzerError, BaseAnalyzer
from .coverage import CoverageAnalyzer
from .quality import FlakyTestDetector, TestQualityScorer
from .types import TestingAnalysisResult


class TestingAnalyzer(BaseAnalyzer):
    """
    Testing Analyzer.

    Analyzes:
    - Coverage analysis (line, branch, function)
    - Missing edge case identification
    - Test quality scoring
    - Flaky test detection patterns

    Configuration:
        project_path: str - Path to project root (required)
        test_patterns: List[str] - Test file patterns (default: ["**/test_*.py", "**/*_test.py"])
        source_patterns: List[str] - Source file patterns (default: ["**/*.py"])
        exclude_patterns: List[str] - Patterns to exclude
        min_coverage: float - Minimum acceptable coverage (default: 80.0)
    """

    @property
    def name(self) -> str:
        return "testing_analyzer"

    @property
    def version(self) -> str:
        return "1.0.0"

    def _validate_config(self) -> None:
        """Validate analyzer configuration."""
        if "project_path" not in self.config:
            raise AnalyzerError("project_path is required")

        path = Path(self.config["project_path"])
        if not path.exists():
            raise AnalyzerError(f"Project path does not exist: {path}")

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform testing analysis.

        Args:
            data: Optional input data

        Returns:
            Testing analysis results
        """
        project_path = Path(self.config["project_path"])

        # Get test and source files
        test_files = self._get_test_files(project_path)
        source_files = self._get_source_files(project_path)

        # Analyze coverage
        coverage_analyzer = CoverageAnalyzer(project_path)
        coverage_metrics = coverage_analyzer.analyze_coverage()
        uncovered_code = coverage_analyzer.identify_uncovered_code(source_files)

        # Calculate coverage score
        if coverage_metrics:
            coverage_score = coverage_metrics.line_coverage
        else:
            coverage_score = 0.0

        # Analyze test quality
        quality_scorer = TestQualityScorer()
        (
            quality_issues,
            missing_edge_cases,
            avg_quality,
        ) = quality_scorer.analyze_test_files(test_files)

        # Detect flaky test patterns
        flaky_detector = FlakyTestDetector()
        flaky_patterns = flaky_detector.detect_flaky_patterns(test_files)

        # Count tests
        total_tests = self._count_tests(test_files)

        # Calculate overall testing score
        testing_score = self._calculate_testing_score(
            coverage_score=coverage_score,
            avg_quality=avg_quality,
            total_tests=total_tests,
            flaky_count=len(flaky_patterns),
        )

        # Determine test maturity
        test_maturity = self._determine_maturity(testing_score, coverage_score)

        # Generate summary and recommendations
        summary, critical_gaps, recommendations = self._generate_summary(
            testing_score=testing_score,
            coverage_metrics=coverage_metrics,
            quality_issues=quality_issues,
            flaky_patterns=flaky_patterns,
            total_tests=total_tests,
        )

        # Create result
        result = TestingAnalysisResult(
            project_path=str(project_path),
            total_test_files=len(test_files),
            total_tests=total_tests,
            coverage_metrics=coverage_metrics,
            uncovered_code=uncovered_code,
            coverage_score=coverage_score,
            missing_edge_cases=missing_edge_cases,
            test_quality_issues=quality_issues,
            average_test_quality=avg_quality,
            flaky_test_patterns=flaky_patterns,
            potential_flaky_count=len(flaky_patterns),
            testing_score=testing_score,
            test_maturity=test_maturity,
            summary=summary,
            critical_gaps=critical_gaps,
            recommendations=recommendations,
        )

        return self._create_response(result.model_dump())

    def _get_test_files(self, project_path: Path) -> List[Path]:
        """Get test files.

        Args:
            project_path: Project root

        Returns:
            List of test file paths
        """
        test_patterns = self.config.get(
            "test_patterns", ["**/test_*.py", "**/*_test.py", "**/tests/*.py"]
        )
        exclude_patterns = self.config.get("exclude_patterns", ["**/venv/**", "**/.venv/**"])

        files = []
        for pattern in test_patterns:
            for file_path in project_path.glob(pattern):
                if file_path.is_file():
                    excluded = any(file_path.match(ep) for ep in exclude_patterns)
                    if not excluded:
                        files.append(file_path)

        return files

    def _get_source_files(self, project_path: Path) -> List[Path]:
        """Get source files.

        Args:
            project_path: Project root

        Returns:
            List of source file paths
        """
        source_patterns = self.config.get("source_patterns", ["**/*.py"])
        exclude_patterns = self.config.get(
            "exclude_patterns",
            [
                "**/test_*.py",
                "**/*_test.py",
                "**/tests/**",
                "**/venv/**",
                "**/.venv/**",
                "**/__pycache__/**",
            ],
        )

        files = []
        for pattern in source_patterns:
            for file_path in project_path.glob(pattern):
                if file_path.is_file():
                    excluded = any(file_path.match(ep) for ep in exclude_patterns)
                    if not excluded:
                        files.append(file_path)

        return files

    def _count_tests(self, test_files: List[Path]) -> int:
        """Count total number of tests.

        Args:
            test_files: Test files

        Returns:
            Test count
        """
        import ast

        total = 0
        for test_file in test_files:
            try:
                with open(test_file, "r", encoding="utf-8") as f:
                    source = f.read()

                tree = ast.parse(source)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                        total += 1

            except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
                pass

        return total

    def _calculate_testing_score(
        self,
        coverage_score: float,
        avg_quality: float,
        total_tests: int,
        flaky_count: int,
    ) -> float:
        """Calculate overall testing score (0-100).

        Args:
            coverage_score: Coverage percentage
            avg_quality: Average test quality
            total_tests: Total number of tests
            flaky_count: Number of flaky patterns

        Returns:
            Testing score
        """
        score = 0.0

        # Coverage contribution (40%)
        score += coverage_score * 0.4

        # Quality contribution (35%)
        score += avg_quality * 0.35

        # Test existence contribution (15%)
        if total_tests == 0:
            test_existence_score = 0.0
        elif total_tests < 10:
            test_existence_score = 30.0
        elif total_tests < 50:
            test_existence_score = 70.0
        else:
            test_existence_score = 100.0

        score += test_existence_score * 0.15

        # Flaky test penalty (10%)
        flaky_penalty = min(100.0, flaky_count * 10)
        score += (100.0 - flaky_penalty) * 0.10

        return round(score, 2)

    def _determine_maturity(self, testing_score: float, coverage_score: float) -> str:
        """Determine test maturity level.

        Args:
            testing_score: Overall testing score
            coverage_score: Coverage score

        Returns:
            Maturity level
        """
        if testing_score >= 90 and coverage_score >= 80:
            return "mature"
        elif testing_score >= 70 and coverage_score >= 60:
            return "developing"
        elif testing_score >= 50:
            return "basic"
        else:
            return "immature"

    def _generate_summary(
        self,
        testing_score: float,
        coverage_metrics: Any,
        quality_issues: List,
        flaky_patterns: List,
        total_tests: int,
    ) -> tuple[str, List[str], List[str]]:
        """Generate summary, critical gaps, and recommendations.

        Args:
            testing_score: Testing score
            coverage_metrics: Coverage metrics
            quality_issues: Quality issues
            flaky_patterns: Flaky patterns
            total_tests: Total tests

        Returns:
            Tuple of (summary, critical_gaps, recommendations)
        """
        # Summary
        coverage_pct = (
            coverage_metrics.line_coverage if coverage_metrics else 0.0
        )

        summary = (
            f"Testing score: {testing_score}/100. "
            f"Found {total_tests} tests with {coverage_pct:.1f}% line coverage, "
            f"{len(quality_issues)} quality issues, and "
            f"{len(flaky_patterns)} potential flaky patterns."
        )

        # Critical gaps
        critical_gaps = []

        if coverage_pct < 60:
            critical_gaps.append(f"Low test coverage ({coverage_pct:.1f}%)")

        if total_tests < 10:
            critical_gaps.append("Insufficient number of tests")

        high_quality_issues = [i for i in quality_issues if i.severity == "high"]
        if high_quality_issues:
            critical_gaps.append(
                f"{len(high_quality_issues)} high-severity test quality issues"
            )

        # Recommendations
        recommendations = []

        if coverage_pct < 80:
            recommendations.append(
                f"Increase test coverage from {coverage_pct:.1f}% to at least 80%"
            )

        if quality_issues:
            recommendations.append(
                "Improve test quality by adding assertions and better naming"
            )

        if flaky_patterns:
            recommendations.append(
                "Eliminate flaky test patterns by mocking external dependencies"
            )

        if total_tests == 0:
            recommendations.append("Start writing tests for critical functionality")

        if not recommendations:
            recommendations.append("Continue maintaining high testing standards")

        return summary, critical_gaps[:5], recommendations[:5]
