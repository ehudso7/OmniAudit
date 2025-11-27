"""
Architecture Analyzer.

Analyzes project architecture including dependencies, layers, and patterns.
"""

from pathlib import Path
from typing import Any, Dict, List

from ..base import AnalyzerError, BaseAnalyzer
from .graph import CircularDependencyDetector, DependencyGraphBuilder, MetricsCalculator
from .patterns import CleanArchitectureValidator, LayerValidator
from .types import ArchitectureAnalysisResult


class ArchitectureAnalyzer(BaseAnalyzer):
    """
    Architecture Analyzer.

    Analyzes:
    - Dependency graph generation
    - Circular dependency detection
    - Layer violation detection
    - Module coupling/cohesion analysis
    - Architecture pattern validation (Clean, Hexagonal, Onion)

    Configuration:
        project_path: str - Path to project root (required)
        include_patterns: List[str] - File patterns to include (default: ["**/*.py"])
        exclude_patterns: List[str] - File patterns to exclude
        validate_clean_arch: bool - Validate Clean Architecture (default: True)
    """

    @property
    def name(self) -> str:
        return "architecture_analyzer"

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
        Perform architecture analysis.

        Args:
            data: Optional input data

        Returns:
            Architecture analysis results
        """
        project_path = Path(self.config["project_path"])

        # Get files to analyze
        files = self._get_files_to_analyze(project_path)

        if not files:
            return self._create_response(
                {
                    "error": "No files found to analyze",
                    "project_path": str(project_path),
                }
            )

        # Build dependency graph
        graph_builder = DependencyGraphBuilder()
        dependency_nodes = graph_builder.build_graph(files, project_path)
        total_dependencies = graph_builder.get_total_dependencies()

        # Detect circular dependencies
        circular_detector = CircularDependencyDetector(graph_builder.graph)
        circular_dependencies = circular_detector.detect_cycles()

        # Detect layer violations
        layer_validator = LayerValidator()
        layer_violations = layer_validator.detect_violations(files, project_path)

        # Calculate module metrics
        metrics_calculator = MetricsCalculator(
            graph_builder.graph, graph_builder.reverse_graph
        )
        module_metrics = metrics_calculator.calculate_module_metrics(
            files, project_path
        )
        average_coupling = metrics_calculator.calculate_average_coupling(module_metrics)
        average_cohesion = metrics_calculator.calculate_average_cohesion(module_metrics)

        # Validate architecture pattern
        architecture_validation = None
        if self.config.get("validate_clean_arch", True):
            clean_validator = CleanArchitectureValidator()
            architecture_validation = clean_validator.validate(
                project_path, layer_violations, module_metrics
            )

        # Calculate overall architecture score
        architecture_score = self._calculate_architecture_score(
            circular_count=len(circular_dependencies),
            layer_violation_count=len(layer_violations),
            average_coupling=average_coupling,
            average_cohesion=average_cohesion,
        )

        # Calculate maintainability score
        maintainability_score = self._calculate_maintainability_score(
            architecture_score, average_coupling, average_cohesion
        )

        # Generate summary and recommendations
        summary, critical_issues, recommendations = self._generate_summary(
            architecture_score=architecture_score,
            circular_dependencies=circular_dependencies,
            layer_violations=layer_violations,
            module_metrics=module_metrics,
        )

        # Create result
        result = ArchitectureAnalysisResult(
            project_path=str(project_path),
            total_modules=len(dependency_nodes),
            dependency_nodes=dependency_nodes,
            total_dependencies=total_dependencies,
            circular_dependencies=circular_dependencies,
            circular_count=len(circular_dependencies),
            layer_violations=layer_violations,
            module_metrics=module_metrics,
            average_coupling=average_coupling,
            average_cohesion=average_cohesion,
            architecture_validation=architecture_validation,
            architecture_score=architecture_score,
            maintainability_score=maintainability_score,
            summary=summary,
            critical_issues=critical_issues,
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

    def _calculate_architecture_score(
        self,
        circular_count: int,
        layer_violation_count: int,
        average_coupling: float,
        average_cohesion: float,
    ) -> float:
        """Calculate overall architecture score (0-100).

        Args:
            circular_count: Number of circular dependencies
            layer_violation_count: Number of layer violations
            average_coupling: Average coupling metric
            average_cohesion: Average cohesion score

        Returns:
            Architecture score
        """
        score = 100.0

        # Circular dependency penalty (max -30 points)
        score -= min(30, circular_count * 10)

        # Layer violation penalty (max -25 points)
        score -= min(25, layer_violation_count * 5)

        # Coupling penalty (max -25 points)
        if average_coupling > 5:
            score -= min(25, (average_coupling - 5) * 2.5)

        # Cohesion bonus/penalty (max -20 points)
        if average_cohesion < 50:
            score -= min(20, (50 - average_cohesion) * 0.4)

        return max(0.0, round(score, 2))

    def _calculate_maintainability_score(
        self, architecture_score: float, average_coupling: float, average_cohesion: float
    ) -> float:
        """Calculate maintainability score.

        Args:
            architecture_score: Overall architecture score
            average_coupling: Average coupling
            average_cohesion: Average cohesion

        Returns:
            Maintainability score (0-100)
        """
        # Weighted combination
        maintainability = (
            architecture_score * 0.5
            + (100 - min(100, average_coupling * 5)) * 0.25
            + average_cohesion * 0.25
        )

        return max(0.0, min(100.0, round(maintainability, 2)))

    def _generate_summary(
        self,
        architecture_score: float,
        circular_dependencies: List,
        layer_violations: List,
        module_metrics: List,
    ) -> tuple[str, List[str], List[str]]:
        """Generate summary, critical issues, and recommendations.

        Args:
            architecture_score: Architecture score
            circular_dependencies: Circular dependencies
            layer_violations: Layer violations
            module_metrics: Module metrics

        Returns:
            Tuple of (summary, critical_issues, recommendations)
        """
        # Summary
        if architecture_score >= 80:
            arch_level = "excellent"
        elif architecture_score >= 60:
            arch_level = "good"
        elif architecture_score >= 40:
            arch_level = "fair"
        else:
            arch_level = "poor"

        summary = (
            f"Architecture is {arch_level} with a score of {architecture_score}/100. "
            f"Found {len(circular_dependencies)} circular dependencies, "
            f"{len(layer_violations)} layer violations across {len(module_metrics)} modules."
        )

        # Critical issues
        critical_issues = []

        high_severity_circular = [c for c in circular_dependencies if c.severity == "high"]
        if high_severity_circular:
            critical_issues.append(
                f"{len(high_severity_circular)} high-severity circular dependencies"
            )

        if layer_violations:
            critical_issues.append(f"{len(layer_violations)} architecture layer violations")

        # Recommendations
        recommendations = []

        if circular_dependencies:
            recommendations.append(
                "Break circular dependencies using dependency injection or interfaces"
            )

        if layer_violations:
            recommendations.append(
                "Enforce layer separation and use dependency inversion principle"
            )

        if module_metrics:
            high_coupling = [m for m in module_metrics if m.coupling.efferent_coupling > 10]
            if high_coupling:
                recommendations.append(
                    f"Reduce coupling in {len(high_coupling)} highly coupled modules"
                )

        if not recommendations:
            recommendations.append("Continue maintaining architecture standards")

        return summary, critical_issues[:5], recommendations[:5]
