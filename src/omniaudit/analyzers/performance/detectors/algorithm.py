"""
Algorithm Complexity Analysis Module.

Detects time and space complexity (Big-O) of algorithms.
"""

import ast
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..types import (
    AlgorithmComplexity,
    AlgorithmComplexityIssue,
    PerformanceImpact,
)


class AlgorithmAnalyzer:
    """Analyzes algorithm complexity."""

    def __init__(self):
        """Initialize algorithm analyzer."""
        pass

    def analyze_files(self, file_paths: List[Path]) -> List[AlgorithmComplexityIssue]:
        """Analyze files for algorithm complexity.

        Args:
            file_paths: Files to analyze

        Returns:
            List of complexity issues
        """
        issues = []

        for file_path in file_paths:
            if file_path.suffix == ".py":
                issues.extend(self._analyze_python_file(file_path))

        return issues

    def _analyze_python_file(
        self, file_path: Path
    ) -> List[AlgorithmComplexityIssue]:
        """Analyze Python file for algorithm complexity.

        Args:
            file_path: Python file to analyze

        Returns:
            List of complexity issues
        """
        issues = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    complexity, space_complexity, evidence = self._analyze_function(
                        node
                    )

                    # Only report if complexity is concerning
                    if complexity in (
                        AlgorithmComplexity.O_N2,
                        AlgorithmComplexity.O_N3,
                        AlgorithmComplexity.O_2N,
                        AlgorithmComplexity.O_N_FACTORIAL,
                    ):
                        impact = self._determine_impact(complexity)
                        suggestion = self._generate_suggestion(complexity, evidence)

                        issues.append(
                            AlgorithmComplexityIssue(
                                file_path=str(file_path),
                                function_name=node.name,
                                line_start=node.lineno,
                                line_end=node.end_lineno or node.lineno,
                                detected_complexity=complexity,
                                space_complexity=space_complexity,
                                impact=impact,
                                evidence=evidence,
                                suggestion=suggestion,
                                confidence=0.7,
                            )
                        )

        except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
            pass

        return issues

    def _analyze_function(
        self, node: ast.FunctionDef
    ) -> tuple[AlgorithmComplexity, Optional[AlgorithmComplexity], str]:
        """Analyze a function's time and space complexity.

        Args:
            node: Function AST node

        Returns:
            Tuple of (time_complexity, space_complexity, evidence)
        """
        # Analyze loop nesting
        loop_depth = self._count_nested_loops(node)
        recursive = self._is_recursive(node)
        has_sorting = self._has_sorting_operation(node)
        has_set_dict = self._uses_set_or_dict(node)

        evidence_parts = []

        # Determine time complexity
        if recursive:
            # Check for exponential recursion (e.g., naive Fibonacci)
            if self._is_exponential_recursion(node):
                time_complexity = AlgorithmComplexity.O_2N
                evidence_parts.append("Exponential recursion without memoization")
            # Check for factorial recursion
            elif self._is_factorial_recursion(node):
                time_complexity = AlgorithmComplexity.O_N_FACTORIAL
                evidence_parts.append("Factorial recursion pattern")
            else:
                time_complexity = AlgorithmComplexity.O_N_LOG_N
                evidence_parts.append("Recursive with divide-and-conquer pattern")
        elif loop_depth >= 3:
            time_complexity = AlgorithmComplexity.O_N3
            evidence_parts.append(f"Triple nested loops (depth: {loop_depth})")
        elif loop_depth == 2:
            time_complexity = AlgorithmComplexity.O_N2
            evidence_parts.append("Double nested loops")
        elif has_sorting:
            time_complexity = AlgorithmComplexity.O_N_LOG_N
            evidence_parts.append("Contains sorting operation")
        elif loop_depth == 1:
            time_complexity = AlgorithmComplexity.O_N
            evidence_parts.append("Single loop iteration")
        else:
            time_complexity = AlgorithmComplexity.O_1
            evidence_parts.append("No loops or recursion")

        # Determine space complexity
        if self._creates_large_data_structures(node):
            space_complexity = AlgorithmComplexity.O_N
            evidence_parts.append("Creates data structures proportional to input")
        elif recursive:
            space_complexity = AlgorithmComplexity.O_N
            evidence_parts.append("Recursion uses call stack space")
        else:
            space_complexity = AlgorithmComplexity.O_1
            evidence_parts.append("Constant space usage")

        evidence = "; ".join(evidence_parts)

        return time_complexity, space_complexity, evidence

    def _count_nested_loops(self, node: ast.AST) -> int:
        """Count maximum nesting depth of loops.

        Args:
            node: AST node to analyze

        Returns:
            Maximum loop nesting depth
        """
        max_depth = 0

        def count_depth(node: ast.AST, current_depth: int) -> None:
            nonlocal max_depth

            if isinstance(node, (ast.For, ast.While, ast.ListComp, ast.SetComp)):
                current_depth += 1
                max_depth = max(max_depth, current_depth)

            for child in ast.iter_child_nodes(node):
                count_depth(child, current_depth)

        count_depth(node, 0)
        return max_depth

    def _is_recursive(self, node: ast.FunctionDef) -> bool:
        """Check if function is recursive.

        Args:
            node: Function node

        Returns:
            True if recursive
        """
        func_name = node.name

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name) and child.func.id == func_name:
                    return True

        return False

    def _is_exponential_recursion(self, node: ast.FunctionDef) -> bool:
        """Check if recursion is exponential (multiple recursive calls).

        Args:
            node: Function node

        Returns:
            True if exponential recursion
        """
        func_name = node.name
        recursive_calls = 0

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name) and child.func.id == func_name:
                    recursive_calls += 1

        # If multiple recursive calls in same function, likely exponential
        return recursive_calls >= 2

    def _is_factorial_recursion(self, node: ast.FunctionDef) -> bool:
        """Check for factorial-like recursion pattern.

        Args:
            node: Function node

        Returns:
            True if factorial pattern
        """
        # Look for n * factorial(n-1) pattern
        # This is a simplified heuristic
        source = ast.unparse(node)
        return "factorial" in source.lower() or (
            "*" in source and self._is_recursive(node)
        )

    def _has_sorting_operation(self, node: ast.AST) -> bool:
        """Check if code uses sorting.

        Args:
            node: AST node

        Returns:
            True if sorting is used
        """
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    if child.func.attr == "sort":
                        return True
                elif isinstance(child.func, ast.Name):
                    if child.func.id == "sorted":
                        return True

        return False

    def _uses_set_or_dict(self, node: ast.AST) -> bool:
        """Check if code uses sets or dicts for lookup.

        Args:
            node: AST node

        Returns:
            True if using hash-based structures
        """
        for child in ast.walk(node):
            if isinstance(child, (ast.Set, ast.Dict)):
                return True

        return False

    def _creates_large_data_structures(self, node: ast.AST) -> bool:
        """Check if function creates data structures proportional to input.

        Args:
            node: AST node

        Returns:
            True if large structures created
        """
        # Look for list comprehensions, dict comprehensions in loops
        for child in ast.walk(node):
            if isinstance(child, (ast.ListComp, ast.DictComp, ast.SetComp)):
                return True

            # Look for append in loops
            if isinstance(child, (ast.For, ast.While)):
                for inner in ast.walk(child):
                    if isinstance(inner, ast.Call):
                        if isinstance(inner.func, ast.Attribute):
                            if inner.func.attr in ("append", "extend", "add"):
                                return True

        return False

    def _determine_impact(self, complexity: AlgorithmComplexity) -> PerformanceImpact:
        """Determine performance impact based on complexity.

        Args:
            complexity: Algorithm complexity

        Returns:
            Performance impact level
        """
        impact_map = {
            AlgorithmComplexity.O_1: PerformanceImpact.NEGLIGIBLE,
            AlgorithmComplexity.O_LOG_N: PerformanceImpact.LOW,
            AlgorithmComplexity.O_N: PerformanceImpact.LOW,
            AlgorithmComplexity.O_N_LOG_N: PerformanceImpact.MEDIUM,
            AlgorithmComplexity.O_N2: PerformanceImpact.HIGH,
            AlgorithmComplexity.O_N3: PerformanceImpact.CRITICAL,
            AlgorithmComplexity.O_2N: PerformanceImpact.CRITICAL,
            AlgorithmComplexity.O_N_FACTORIAL: PerformanceImpact.CRITICAL,
        }

        return impact_map.get(complexity, PerformanceImpact.MEDIUM)

    def _generate_suggestion(
        self, complexity: AlgorithmComplexity, evidence: str
    ) -> str:
        """Generate optimization suggestion.

        Args:
            complexity: Detected complexity
            evidence: Evidence string

        Returns:
            Optimization suggestion
        """
        if complexity == AlgorithmComplexity.O_N2:
            return (
                "Consider using hash-based data structures (dict/set) "
                "to reduce from O(n²) to O(n)"
            )
        elif complexity == AlgorithmComplexity.O_N3:
            return (
                "Triple nested loops are very expensive. "
                "Consider algorithmic optimization or data structure changes"
            )
        elif complexity == AlgorithmComplexity.O_2N:
            return (
                "Exponential complexity detected. "
                "Use memoization, dynamic programming, or iterative approach"
            )
        elif complexity == AlgorithmComplexity.O_N_FACTORIAL:
            return (
                "Factorial complexity is extremely expensive. "
                "Consider pruning, memoization, or approximate algorithms"
            )
        else:
            return "Consider optimizing this algorithm if it's performance-critical"

    def calculate_average_complexity(
        self, issues: List[AlgorithmComplexityIssue]
    ) -> str:
        """Calculate average complexity across all issues.

        Args:
            issues: List of complexity issues

        Returns:
            Average complexity as string
        """
        if not issues:
            return "O(n)"  # Default assumption

        # Count occurrences
        complexity_counts = {}
        for issue in issues:
            complexity = issue.detected_complexity
            complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1

        # Return most common
        if complexity_counts:
            most_common = max(complexity_counts.items(), key=lambda x: x[1])
            return most_common[0].value

        return "O(n)"
