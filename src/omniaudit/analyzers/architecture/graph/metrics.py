"""
Architecture Metrics Calculation Module.

Calculates coupling, cohesion, and other architecture metrics.
"""

import ast
from pathlib import Path
from typing import Dict, List, Set

from ..types import CouplingMetrics, ModuleMetrics


class MetricsCalculator:
    """Calculates architecture metrics."""

    def __init__(self, graph: Dict[str, Set[str]], reverse_graph: Dict[str, Set[str]]):
        """Initialize metrics calculator.

        Args:
            graph: Dependency graph
            reverse_graph: Reverse dependency graph
        """
        self.graph = graph
        self.reverse_graph = reverse_graph

    def calculate_module_metrics(
        self, file_paths: List[Path], project_root: Path
    ) -> List[ModuleMetrics]:
        """Calculate metrics for all modules.

        Args:
            file_paths: List of files
            project_root: Project root

        Returns:
            List of module metrics
        """
        metrics = []

        for file_path in file_paths:
            if file_path.suffix == ".py":
                rel_path = file_path.relative_to(project_root)
                module_path = str(rel_path).replace("/", ".").replace("\\", ".").replace(".py", "")

                coupling = self._calculate_coupling(module_path)
                cohesion = self._calculate_cohesion(file_path)
                loc = self._count_lines(file_path)
                complexity = self._calculate_avg_complexity(file_path)

                metrics.append(
                    ModuleMetrics(
                        module_path=module_path,
                        coupling=coupling,
                        cohesion_score=cohesion,
                        lines_of_code=loc,
                        complexity=complexity,
                    )
                )

        return metrics

    def _calculate_coupling(self, module_path: str) -> CouplingMetrics:
        """Calculate coupling metrics for a module.

        Args:
            module_path: Module path

        Returns:
            Coupling metrics
        """
        # Afferent coupling: number of modules that depend on this module
        afferent = len(self.reverse_graph.get(module_path, set()))

        # Efferent coupling: number of modules this module depends on
        efferent = len(self.graph.get(module_path, set()))

        # Instability: Ce / (Ca + Ce)
        total = afferent + efferent
        instability = efferent / total if total > 0 else 0.0

        # Abstractness (simplified - would need to analyze classes)
        abstractness = 0.0

        return CouplingMetrics(
            afferent_coupling=afferent,
            efferent_coupling=efferent,
            instability=round(instability, 2),
            abstractness=abstractness,
        )

    def _calculate_cohesion(self, file_path: Path) -> float:
        """Calculate cohesion score for a module.

        Simplified LCOM (Lack of Cohesion of Methods) metric.

        Args:
            file_path: File path

        Returns:
            Cohesion score (0-100, higher is better)
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)

            # Find classes and analyze method cohesion
            total_cohesion = 0.0
            class_count = 0

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_count += 1
                    cohesion = self._calculate_class_cohesion(node)
                    total_cohesion += cohesion

            if class_count > 0:
                return round(total_cohesion / class_count, 2)
            else:
                return 50.0  # Neutral score for non-OOP modules

        except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
            return 50.0

    def _calculate_class_cohesion(self, class_node: ast.ClassDef) -> float:
        """Calculate cohesion for a single class.

        Args:
            class_node: Class AST node

        Returns:
            Cohesion score
        """
        methods = [n for n in class_node.body if isinstance(n, ast.FunctionDef)]

        if len(methods) <= 1:
            return 100.0  # Single method is perfectly cohesive

        # Simplified: check how many methods access instance variables
        methods_using_self = 0
        for method in methods:
            uses_self = False
            for node in ast.walk(method):
                if isinstance(node, ast.Attribute):
                    if isinstance(node.value, ast.Name) and node.value.id == "self":
                        uses_self = True
                        break
            if uses_self:
                methods_using_self += 1

        # Higher percentage = better cohesion
        cohesion_pct = (methods_using_self / len(methods)) * 100
        return round(cohesion_pct, 2)

    def _count_lines(self, file_path: Path) -> int:
        """Count lines of code.

        Args:
            file_path: File path

        Returns:
            Line count
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return sum(1 for line in f if line.strip())
        except (UnicodeDecodeError, FileNotFoundError):
            return 0

    def _calculate_avg_complexity(self, file_path: Path) -> float:
        """Calculate average complexity.

        Args:
            file_path: File path

        Returns:
            Average complexity
        """
        # Simplified - just count decision points
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)

            total_complexity = 0
            function_count = 0

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    function_count += 1
                    complexity = self._count_decision_points(node)
                    total_complexity += complexity

            if function_count > 0:
                return round(total_complexity / function_count, 2)
            else:
                return 1.0

        except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
            return 1.0

    def _count_decision_points(self, node: ast.AST) -> int:
        """Count decision points in a function.

        Args:
            node: AST node

        Returns:
            Decision point count
        """
        count = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                count += 1
        return count

    def calculate_average_coupling(self, metrics: List[ModuleMetrics]) -> float:
        """Calculate average coupling across modules.

        Args:
            metrics: List of module metrics

        Returns:
            Average coupling
        """
        if not metrics:
            return 0.0

        total = sum(
            m.coupling.afferent_coupling + m.coupling.efferent_coupling for m in metrics
        )
        return round(total / len(metrics), 2)

    def calculate_average_cohesion(self, metrics: List[ModuleMetrics]) -> float:
        """Calculate average cohesion across modules.

        Args:
            metrics: List of module metrics

        Returns:
            Average cohesion
        """
        if not metrics:
            return 0.0

        total = sum(m.cohesion_score for m in metrics)
        return round(total / len(metrics), 2)
