"""
Enhanced Performance Analyzer.

Comprehensive performance analysis including algorithms, queries, memory, and Web Vitals.
"""

from pathlib import Path
from typing import Any, Dict, List

from ..base import AnalyzerError, BaseAnalyzer
from .detectors import (
    AlgorithmAnalyzer,
    MemoryAnalyzer,
    QueryAnalyzer,
    WebVitalsAnalyzer,
)
from .types import PerformanceAnalysisResult, PerformanceImpact


class EnhancedPerformanceAnalyzer(BaseAnalyzer):
    """
    Enhanced Performance Analyzer.

    Analyzes:
    - Algorithm complexity (Big-O detection)
    - N+1 query patterns
    - Memory leak patterns
    - Bundle optimization opportunities
    - Web Vitals impact prediction

    Configuration:
        project_path: str - Path to project root (required)
        language: str - Primary language (default: "python")
        include_patterns: List[str] - File patterns to include
        exclude_patterns: List[str] - File patterns to exclude
        analyze_frontend: bool - Analyze frontend files (default: True)
    """

    @property
    def name(self) -> str:
        return "enhanced_performance_analyzer"

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
        Perform comprehensive performance analysis.

        Args:
            data: Optional input data

        Returns:
            Performance analysis results
        """
        project_path = Path(self.config["project_path"])
        language = self.config.get("language", "python")
        analyze_frontend = self.config.get("analyze_frontend", True)

        # Get files to analyze
        files = self._get_files_to_analyze(project_path, analyze_frontend)

        if not files:
            return self._create_response(
                {
                    "error": "No files found to analyze",
                    "project_path": str(project_path),
                }
            )

        # Initialize analyzers
        algorithm_analyzer = AlgorithmAnalyzer()
        query_analyzer = QueryAnalyzer()
        memory_analyzer = MemoryAnalyzer()
        web_vitals_analyzer = WebVitalsAnalyzer()

        # Run analyses
        algorithm_issues = algorithm_analyzer.analyze_files(files)
        query_issues = query_analyzer.analyze_files(files)
        memory_issues = memory_analyzer.analyze_files(files)
        web_vital_impacts, bundle_opportunities = web_vitals_analyzer.analyze_files(
            files
        )

        # Calculate metrics
        avg_complexity = algorithm_analyzer.calculate_average_complexity(
            algorithm_issues
        )
        n_plus_one_count = query_analyzer.count_n_plus_one_issues(query_issues)
        potential_leaks = memory_analyzer.count_potential_leaks(memory_issues)
        potential_size_reduction = web_vitals_analyzer.calculate_bundle_savings(
            bundle_opportunities
        )

        # Calculate overall performance score
        performance_score = self._calculate_performance_score(
            algorithm_issues=algorithm_issues,
            query_issues=query_issues,
            memory_issues=memory_issues,
            web_vital_impacts=web_vital_impacts,
        )

        # Calculate optimization potential
        optimization_potential = self._calculate_optimization_potential(
            algorithm_issues=algorithm_issues,
            query_issues=query_issues,
            memory_issues=memory_issues,
            bundle_opportunities=bundle_opportunities,
        )

        # Generate summary and recommendations
        summary, critical_issues, recommendations = self._generate_summary(
            performance_score=performance_score,
            algorithm_issues=algorithm_issues,
            query_issues=query_issues,
            memory_issues=memory_issues,
            web_vital_impacts=web_vital_impacts,
        )

        # Create result
        result = PerformanceAnalysisResult(
            project_path=str(project_path),
            language=language,
            total_files=len(files),
            algorithm_issues=algorithm_issues,
            average_complexity=avg_complexity,
            query_issues=query_issues,
            n_plus_one_count=n_plus_one_count,
            memory_issues=memory_issues,
            potential_leaks=potential_leaks,
            bundle_opportunities=bundle_opportunities,
            potential_size_reduction=potential_size_reduction,
            web_vital_impacts=web_vital_impacts,
            performance_score=performance_score,
            optimization_potential=optimization_potential,
            summary=summary,
            critical_issues=critical_issues,
            recommendations=recommendations,
        )

        return self._create_response(result.model_dump())

    def _get_files_to_analyze(
        self, project_path: Path, analyze_frontend: bool
    ) -> List[Path]:
        """Get list of files to analyze.

        Args:
            project_path: Project root path
            analyze_frontend: Whether to include frontend files

        Returns:
            List of file paths
        """
        if analyze_frontend:
            include_patterns = self.config.get(
                "include_patterns",
                ["**/*.py", "**/*.js", "**/*.jsx", "**/*.ts", "**/*.tsx"],
            )
        else:
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
                "**/*.min.js",
            ],
        )

        files = []
        for pattern in include_patterns:
            for file_path in project_path.glob(pattern):
                if file_path.is_file():
                    excluded = False
                    for exclude_pattern in exclude_patterns:
                        if file_path.match(exclude_pattern):
                            excluded = True
                            break

                    if not excluded:
                        files.append(file_path)

        return files

    def _calculate_performance_score(
        self,
        algorithm_issues: List[Any],
        query_issues: List[Any],
        memory_issues: List[Any],
        web_vital_impacts: List[Any],
    ) -> float:
        """Calculate overall performance score (0-100).

        Args:
            algorithm_issues: Algorithm complexity issues
            query_issues: Query performance issues
            memory_issues: Memory issues
            web_vital_impacts: Web Vitals impacts

        Returns:
            Performance score
        """
        score = 100.0

        # Algorithm complexity penalty (max -30 points)
        critical_algo = sum(
            1
            for issue in algorithm_issues
            if issue.impact == PerformanceImpact.CRITICAL
        )
        score -= min(30, critical_algo * 10)

        # Query performance penalty (max -25 points)
        n_plus_one = sum(
            1 for issue in query_issues if "N+1" in str(issue.issue_type)
        )
        score -= min(25, n_plus_one * 5)

        # Memory issues penalty (max -25 points)
        memory_leaks = sum(
            1 for issue in memory_issues if "leak" in str(issue.issue_type).lower()
        )
        score -= min(25, memory_leaks * 5)

        # Web Vitals penalty (max -20 points)
        critical_vitals = sum(
            1
            for impact in web_vital_impacts
            if impact.impact_level == PerformanceImpact.CRITICAL
        )
        score -= min(20, critical_vitals * 5)

        return max(0.0, round(score, 2))

    def _calculate_optimization_potential(
        self,
        algorithm_issues: List[Any],
        query_issues: List[Any],
        memory_issues: List[Any],
        bundle_opportunities: List[Any],
    ) -> float:
        """Calculate optimization potential score (0-100).

        Higher score means more optimization opportunity.

        Args:
            algorithm_issues: Algorithm issues
            query_issues: Query issues
            memory_issues: Memory issues
            bundle_opportunities: Bundle optimizations

        Returns:
            Optimization potential score
        """
        potential = 0.0

        # Each issue type contributes to potential
        potential += min(30, len(algorithm_issues) * 3)
        potential += min(25, len(query_issues) * 5)
        potential += min(25, len(memory_issues) * 5)
        potential += min(20, len(bundle_opportunities) * 2)

        return min(100.0, round(potential, 2))

    def _generate_summary(
        self,
        performance_score: float,
        algorithm_issues: List[Any],
        query_issues: List[Any],
        memory_issues: List[Any],
        web_vital_impacts: List[Any],
    ) -> tuple[str, List[str], List[str]]:
        """Generate summary, critical issues, and recommendations.

        Args:
            performance_score: Overall performance score
            algorithm_issues: Algorithm issues
            query_issues: Query issues
            memory_issues: Memory issues
            web_vital_impacts: Web Vitals impacts

        Returns:
            Tuple of (summary, critical_issues, recommendations)
        """
        # Summary
        if performance_score >= 80:
            perf_level = "excellent"
        elif performance_score >= 60:
            perf_level = "good"
        elif performance_score >= 40:
            perf_level = "fair"
        else:
            perf_level = "poor"

        summary = (
            f"Performance is {perf_level} with a score of {performance_score}/100. "
            f"Found {len(algorithm_issues)} algorithm issues, "
            f"{len(query_issues)} query issues, "
            f"{len(memory_issues)} memory issues, and "
            f"{len(web_vital_impacts)} Web Vitals impacts."
        )

        # Critical issues
        critical_issues = []

        critical_algo = [
            i for i in algorithm_issues if i.impact == PerformanceImpact.CRITICAL
        ]
        if critical_algo:
            critical_issues.append(
                f"{len(critical_algo)} critical algorithm complexity issues"
            )

        critical_queries = [
            i for i in query_issues if i.impact == PerformanceImpact.CRITICAL
        ]
        if critical_queries:
            critical_issues.append(
                f"{len(critical_queries)} critical database query issues"
            )

        memory_leaks = [i for i in memory_issues if "leak" in str(i.issue_type).lower()]
        if memory_leaks:
            critical_issues.append(
                f"{len(memory_leaks)} potential memory leaks detected"
            )

        # Recommendations
        recommendations = []

        if algorithm_issues:
            recommendations.append(
                "Optimize high-complexity algorithms using better data structures"
            )

        if query_issues:
            recommendations.append(
                "Eliminate N+1 queries using select_related/prefetch_related"
            )

        if memory_issues:
            recommendations.append(
                "Fix memory leaks and use context managers for resource cleanup"
            )

        if web_vital_impacts:
            recommendations.append(
                "Improve Core Web Vitals through code splitting and lazy loading"
            )

        if not recommendations:
            recommendations.append("Continue monitoring performance metrics")

        return summary, critical_issues[:5], recommendations[:5]
