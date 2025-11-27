"""
Complexity Detection Module.

Analyzes cyclomatic and cognitive complexity of code.
"""

import ast
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..types import (
    ComplexityLevel,
    ComplexityMetrics,
    FunctionComplexity,
)


class ComplexityDetector:
    """Detects and analyzes code complexity."""

    def __init__(self, language: str = "python"):
        """Initialize complexity detector.

        Args:
            language: Programming language to analyze
        """
        self.language = language

    def analyze_file(self, file_path: Path) -> List[FunctionComplexity]:
        """Analyze complexity of all functions in a file.

        Args:
            file_path: Path to source file

        Returns:
            List of function complexity results
        """
        if self.language == "python":
            return self._analyze_python_file(file_path)
        elif self.language in ("javascript", "typescript"):
            return self._analyze_js_file(file_path)
        else:
            return []

    def _analyze_python_file(self, file_path: Path) -> List[FunctionComplexity]:
        """Analyze Python file complexity using AST.

        Args:
            file_path: Path to Python file

        Returns:
            List of function complexity results
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source, filename=str(file_path))
            results = []

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    complexity = self._calculate_python_complexity(node)
                    results.append(
                        FunctionComplexity(
                            name=node.name,
                            file_path=str(file_path),
                            line_start=node.lineno,
                            line_end=node.end_lineno or node.lineno,
                            metrics=complexity,
                            suggestions=self._generate_suggestions(complexity),
                        )
                    )

            return results

        except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
            return []

    def _calculate_python_complexity(
        self, node: ast.FunctionDef
    ) -> ComplexityMetrics:
        """Calculate complexity metrics for a Python function.

        Args:
            node: AST node representing the function

        Returns:
            Complexity metrics
        """
        cyclomatic = self._calculate_cyclomatic(node)
        cognitive = self._calculate_cognitive(node)
        loc = self._count_lines(node)
        params = len(node.args.args) + len(node.args.kwonlyargs)
        nesting = self._calculate_nesting_depth(node)

        # Determine complexity level
        if cyclomatic <= 5:
            level = ComplexityLevel.LOW
        elif cyclomatic <= 10:
            level = ComplexityLevel.MODERATE
        elif cyclomatic <= 20:
            level = ComplexityLevel.HIGH
        else:
            level = ComplexityLevel.VERY_HIGH

        return ComplexityMetrics(
            cyclomatic_complexity=cyclomatic,
            cognitive_complexity=cognitive,
            complexity_level=level,
            lines_of_code=loc,
            parameters_count=params,
            nesting_depth=nesting,
        )

    def _calculate_cyclomatic(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity.

        Cyclomatic complexity measures the number of linearly
        independent paths through the code.

        Args:
            node: AST node to analyze

        Returns:
            Cyclomatic complexity value
        """
        complexity = 1  # Start with 1 for the function itself

        decision_points = (
            ast.If,
            ast.While,
            ast.For,
            ast.ExceptHandler,
            ast.With,
            ast.Assert,
        )

        for child in ast.walk(node):
            if isinstance(child, decision_points):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # Each boolean operator adds a path
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.ListComp, ast.DictComp, ast.SetComp)):
                # Comprehensions add complexity
                complexity += 1

        return complexity

    def _calculate_cognitive(self, node: ast.AST) -> int:
        """Calculate cognitive complexity.

        Cognitive complexity measures how difficult code is to understand,
        with penalties for nesting and breaking linear flow.

        Args:
            node: AST node to analyze

        Returns:
            Cognitive complexity value
        """
        complexity = 0
        nesting_level = 0

        def visit(node: ast.AST, nesting: int) -> int:
            nonlocal complexity
            nonlocal nesting_level

            # Increment for control flow structures
            if isinstance(node, (ast.If, ast.While, ast.For)):
                complexity += 1 + nesting
                new_nesting = nesting + 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1 + nesting
                new_nesting = nesting + 1
            elif isinstance(node, (ast.BoolOp,)):
                # Logical operators in conditions
                complexity += 1
                new_nesting = nesting
            elif isinstance(node, (ast.Break, ast.Continue)):
                # Flow breaking statements
                complexity += 1
                new_nesting = nesting
            else:
                new_nesting = nesting

            # Recursively visit children
            for child in ast.iter_child_nodes(node):
                visit(child, new_nesting)

            return complexity

        visit(node, 0)
        return complexity

    def _count_lines(self, node: ast.AST) -> int:
        """Count lines of code in a node.

        Args:
            node: AST node

        Returns:
            Number of lines
        """
        if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
            return (node.end_lineno or node.lineno) - node.lineno + 1
        return 0

    def _calculate_nesting_depth(self, node: ast.AST) -> int:
        """Calculate maximum nesting depth.

        Args:
            node: AST node to analyze

        Returns:
            Maximum nesting depth
        """
        max_depth = 0

        def visit(node: ast.AST, depth: int) -> None:
            nonlocal max_depth
            max_depth = max(max_depth, depth)

            # Nesting structures
            if isinstance(
                node,
                (
                    ast.If,
                    ast.While,
                    ast.For,
                    ast.With,
                    ast.Try,
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.ClassDef,
                ),
            ):
                new_depth = depth + 1
            else:
                new_depth = depth

            for child in ast.iter_child_nodes(node):
                visit(child, new_depth)

        visit(node, 0)
        return max_depth

    def _generate_suggestions(self, metrics: ComplexityMetrics) -> List[str]:
        """Generate refactoring suggestions based on complexity.

        Args:
            metrics: Complexity metrics

        Returns:
            List of suggestions
        """
        suggestions = []

        if metrics.cyclomatic_complexity > 10:
            suggestions.append(
                f"High cyclomatic complexity ({metrics.cyclomatic_complexity}). "
                "Consider breaking this function into smaller functions."
            )

        if metrics.cognitive_complexity > 15:
            suggestions.append(
                f"High cognitive complexity ({metrics.cognitive_complexity}). "
                "Simplify control flow and reduce nesting."
            )

        if metrics.lines_of_code > 50:
            suggestions.append(
                f"Function is long ({metrics.lines_of_code} lines). "
                "Consider using Extract Method refactoring."
            )

        if metrics.parameters_count > 5:
            suggestions.append(
                f"Too many parameters ({metrics.parameters_count}). "
                "Consider using a parameter object or builder pattern."
            )

        if metrics.nesting_depth > 4:
            suggestions.append(
                f"Deep nesting ({metrics.nesting_depth} levels). "
                "Use early returns or extract nested logic."
            )

        return suggestions

    def _analyze_js_file(self, file_path: Path) -> List[FunctionComplexity]:
        """Analyze JavaScript/TypeScript file complexity.

        Note: This is a simplified implementation. For production,
        use a proper JS parser like esprima or babel.

        Args:
            file_path: Path to JS/TS file

        Returns:
            List of function complexity results
        """
        # Placeholder for JS analysis
        # In production, integrate with esprima, acorn, or babel
        return []

    def calculate_average_complexity(
        self, results: List[FunctionComplexity]
    ) -> float:
        """Calculate average cyclomatic complexity.

        Args:
            results: List of function complexity results

        Returns:
            Average complexity
        """
        if not results:
            return 0.0

        total = sum(r.metrics.cyclomatic_complexity for r in results)
        return round(total / len(results), 2)

    def count_high_complexity(self, results: List[FunctionComplexity]) -> int:
        """Count functions with high or very high complexity.

        Args:
            results: List of function complexity results

        Returns:
            Count of high complexity functions
        """
        return sum(
            1
            for r in results
            if r.metrics.complexity_level
            in (ComplexityLevel.HIGH, ComplexityLevel.VERY_HIGH)
        )
