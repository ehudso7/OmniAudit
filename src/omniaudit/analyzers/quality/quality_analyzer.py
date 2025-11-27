"""
Enhanced Code Quality Analyzer.

Comprehensive code quality analysis using multiple detection techniques.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import AnalyzerError, BaseAnalyzer
from .detectors import (
    AntiPatternDetector,
    ComplexityDetector,
    DeadCodeDetector,
    DuplicationDetector,
)
from .types import QualityAnalysisResult


class QualityAnalyzer(BaseAnalyzer):
    """
    Enhanced Code Quality Analyzer.

    Analyzes code for:
    - Cyclomatic and cognitive complexity
    - Code duplication (exact, structural, semantic)
    - Dead code detection
    - Anti-pattern detection
    - SOLID violations
    - Design pattern recognition

    Configuration:
        project_path: str - Path to project root (required)
        language: str - Language to analyze (default: "python")
        min_duplication_lines: int - Min lines for duplication (default: 6)
        complexity_threshold: int - Max acceptable complexity (default: 10)
        include_patterns: List[str] - File patterns to include (default: ["**/*.py"])
        exclude_patterns: List[str] - File patterns to exclude (default: standard excludes)
    """

    @property
    def name(self) -> str:
        return "quality_analyzer"

    @property
    def version(self) -> str:
        return "2.0.0"

    def _validate_config(self) -> None:
        """Validate analyzer configuration."""
        if "project_path" not in self.config:
            raise AnalyzerError("project_path is required")

        path = Path(self.config["project_path"])
        if not path.exists():
            raise AnalyzerError(f"Project path does not exist: {path}")

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive quality analysis.

        Args:
            data: Optional input data (not used currently)

        Returns:
            Quality analysis results
        """
        project_path = Path(self.config["project_path"])
        language = self.config.get("language", "python")

        # Get files to analyze
        files = self._get_files_to_analyze(project_path)

        if not files:
            return self._create_response(
                {
                    "error": "No files found to analyze",
                    "project_path": str(project_path),
                }
            )

        # Count total lines
        total_lines = self._count_total_lines(files)

        # Initialize detectors
        complexity_detector = ComplexityDetector(language=language)
        duplication_detector = DuplicationDetector(
            min_lines=self.config.get("min_duplication_lines", 6)
        )
        dead_code_detector = DeadCodeDetector()
        antipattern_detector = AntiPatternDetector()

        # Run analyses
        complexity_results = []
        for file_path in files:
            complexity_results.extend(complexity_detector.analyze_file(file_path))

        duplication_clusters = duplication_detector.analyze_files(files)
        dead_code_items = dead_code_detector.analyze_files(files)
        (
            anti_patterns,
            solid_violations,
            design_patterns,
        ) = antipattern_detector.analyze_files(files)

        # Calculate metrics
        avg_complexity = complexity_detector.calculate_average_complexity(
            complexity_results
        )
        high_complexity_count = complexity_detector.count_high_complexity(
            complexity_results
        )
        duplication_pct = duplication_detector.calculate_duplication_percentage(
            duplication_clusters, total_lines
        )
        dead_code_lines = dead_code_detector.calculate_dead_code_lines(
            dead_code_items
        )

        # Calculate overall quality score
        quality_score = self._calculate_quality_score(
            avg_complexity=avg_complexity,
            duplication_pct=duplication_pct,
            dead_code_pct=(dead_code_lines / total_lines * 100)
            if total_lines > 0
            else 0,
            anti_pattern_count=len(anti_patterns),
            solid_violation_count=len(solid_violations),
            total_files=len(files),
        )

        # Calculate maintainability index
        maintainability = self._calculate_maintainability_index(
            quality_score, avg_complexity, duplication_pct
        )

        # Generate summary and recommendations
        summary, top_issues, recommendations = self._generate_summary(
            quality_score=quality_score,
            complexity_results=complexity_results,
            duplication_clusters=duplication_clusters,
            dead_code_items=dead_code_items,
            anti_patterns=anti_patterns,
            solid_violations=solid_violations,
        )

        # Create result
        result = QualityAnalysisResult(
            project_path=str(project_path),
            language=language,
            total_files=len(files),
            total_lines=total_lines,
            complexity_results=complexity_results,
            average_complexity=avg_complexity,
            high_complexity_count=high_complexity_count,
            duplication_clusters=duplication_clusters,
            duplication_percentage=duplication_pct,
            dead_code_items=dead_code_items,
            dead_code_lines=dead_code_lines,
            anti_patterns=anti_patterns,
            solid_violations=solid_violations,
            design_patterns=design_patterns,
            quality_score=quality_score,
            maintainability_index=maintainability,
            summary=summary,
            top_issues=top_issues,
            recommendations=recommendations,
        )

        return self._create_response(result.model_dump())

    def _get_files_to_analyze(self, project_path: Path) -> List[Path]:
        """Get list of files to analyze.

        Args:
            project_path: Project root path

        Returns:
            List of file paths
        """
        include_patterns = self.config.get("include_patterns", ["**/*.py"])
        exclude_patterns = self.config.get(
            "exclude_patterns",
            [
                "**/__pycache__/**",
                "**/venv/**",
                "**/env/**",
                "**/.venv/**",
                "**/node_modules/**",
                "**/.git/**",
                "**/dist/**",
                "**/build/**",
                "**/*.pyc",
                "**/test_*.py",  # Optional: exclude tests
            ],
        )

        files = []
        for pattern in include_patterns:
            for file_path in project_path.glob(pattern):
                if file_path.is_file():
                    # Check if excluded
                    excluded = False
                    for exclude_pattern in exclude_patterns:
                        if file_path.match(exclude_pattern):
                            excluded = True
                            break

                    if not excluded:
                        files.append(file_path)

        return files

    def _count_total_lines(self, files: List[Path]) -> int:
        """Count total lines of code.

        Args:
            files: List of file paths

        Returns:
            Total line count
        """
        total = 0
        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    total += sum(1 for line in f if line.strip())
            except (UnicodeDecodeError, FileNotFoundError):
                pass

        return total

    def _calculate_quality_score(
        self,
        avg_complexity: float,
        duplication_pct: float,
        dead_code_pct: float,
        anti_pattern_count: int,
        solid_violation_count: int,
        total_files: int,
    ) -> float:
        """Calculate overall quality score (0-100).

        Args:
            avg_complexity: Average cyclomatic complexity
            duplication_pct: Duplication percentage
            dead_code_pct: Dead code percentage
            anti_pattern_count: Number of anti-patterns
            solid_violation_count: Number of SOLID violations
            total_files: Total files analyzed

        Returns:
            Quality score
        """
        score = 100.0

        # Complexity penalty (max -30 points)
        if avg_complexity > 5:
            score -= min(30, (avg_complexity - 5) * 3)

        # Duplication penalty (max -25 points)
        score -= min(25, duplication_pct * 2)

        # Dead code penalty (max -20 points)
        score -= min(20, dead_code_pct * 4)

        # Anti-pattern penalty (max -15 points)
        anti_patterns_per_file = (
            anti_pattern_count / total_files if total_files > 0 else 0
        )
        score -= min(15, anti_patterns_per_file * 10)

        # SOLID violation penalty (max -10 points)
        violations_per_file = (
            solid_violation_count / total_files if total_files > 0 else 0
        )
        score -= min(10, violations_per_file * 10)

        return max(0.0, round(score, 2))

    def _calculate_maintainability_index(
        self, quality_score: float, avg_complexity: float, duplication_pct: float
    ) -> float:
        """Calculate maintainability index.

        Based on Microsoft's maintainability index formula, adapted.

        Args:
            quality_score: Overall quality score
            avg_complexity: Average complexity
            duplication_pct: Duplication percentage

        Returns:
            Maintainability index (0-100)
        """
        # Simplified maintainability formula
        # Higher is better
        import math

        if avg_complexity == 0:
            complexity_factor = 0
        else:
            complexity_factor = max(0, 171 - 5.2 * math.log(avg_complexity))

        duplication_factor = max(0, 100 - duplication_pct * 5)

        maintainability = (
            quality_score * 0.4 + complexity_factor * 0.3 + duplication_factor * 0.3
        )

        return max(0.0, min(100.0, round(maintainability, 2)))

    def _generate_summary(
        self,
        quality_score: float,
        complexity_results: List[Any],
        duplication_clusters: List[Any],
        dead_code_items: List[Any],
        anti_patterns: List[Any],
        solid_violations: List[Any],
    ) -> tuple[str, List[str], List[str]]:
        """Generate summary, top issues, and recommendations.

        Args:
            quality_score: Overall quality score
            complexity_results: Complexity analysis results
            duplication_clusters: Duplication clusters
            dead_code_items: Dead code items
            anti_patterns: Anti-patterns
            solid_violations: SOLID violations

        Returns:
            Tuple of (summary, top_issues, recommendations)
        """
        # Summary
        if quality_score >= 80:
            quality_level = "excellent"
        elif quality_score >= 60:
            quality_level = "good"
        elif quality_score >= 40:
            quality_level = "fair"
        else:
            quality_level = "poor"

        summary = (
            f"Code quality is {quality_level} with an overall score of {quality_score}/100. "
            f"Found {len(complexity_results)} functions, "
            f"{len(duplication_clusters)} duplication clusters, "
            f"{len(dead_code_items)} dead code items, "
            f"{len(anti_patterns)} anti-patterns, and "
            f"{len(solid_violations)} SOLID violations."
        )

        # Top issues
        top_issues = []
        if len(duplication_clusters) > 0:
            top_issues.append(
                f"Code duplication: {len(duplication_clusters)} clusters detected"
            )
        if len(dead_code_items) > 0:
            top_issues.append(
                f"Dead code: {len(dead_code_items)} unused items found"
            )
        if len(anti_patterns) > 0:
            top_issues.append(
                f"Anti-patterns: {len(anti_patterns)} instances detected"
            )
        if len(solid_violations) > 0:
            top_issues.append(
                f"SOLID violations: {len(solid_violations)} violations found"
            )

        # Recommendations
        recommendations = []
        if duplication_clusters:
            recommendations.append(
                "Reduce code duplication by extracting common logic into reusable functions"
            )
        if dead_code_items:
            recommendations.append(
                "Remove dead code to improve codebase clarity and reduce maintenance burden"
            )
        if anti_patterns:
            recommendations.append(
                "Refactor anti-patterns to improve code design and maintainability"
            )
        if solid_violations:
            recommendations.append(
                "Address SOLID violations to improve code flexibility and testability"
            )
        if not recommendations:
            recommendations.append("Continue maintaining current code quality standards")

        return summary, top_issues[:5], recommendations[:5]
