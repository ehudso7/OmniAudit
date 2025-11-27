"""
Memory Issue Detection Module.

Detects memory leaks, excessive allocations, and inefficient memory patterns.
"""

import ast
from pathlib import Path
from typing import Any, Dict, List, Set

from ..types import (
    MemoryIssue,
    MemoryIssueType,
    PerformanceImpact,
)


class MemoryAnalyzer:
    """Analyzes memory usage patterns."""

    def __init__(self):
        """Initialize memory analyzer."""
        pass

    def analyze_files(self, file_paths: List[Path]) -> List[MemoryIssue]:
        """Analyze files for memory issues.

        Args:
            file_paths: Files to analyze

        Returns:
            List of memory issues
        """
        issues = []

        for file_path in file_paths:
            if file_path.suffix == ".py":
                issues.extend(self._analyze_python_file(file_path))

        return issues

    def _analyze_python_file(self, file_path: Path) -> List[MemoryIssue]:
        """Analyze Python file for memory issues.

        Args:
            file_path: Python file to analyze

        Returns:
            List of memory issues
        """
        issues = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)

            # Detect unclosed resources
            unclosed = self._detect_unclosed_resources(tree, file_path)
            issues.extend(unclosed)

            # Detect excessive allocations in loops
            excessive = self._detect_excessive_allocations(tree, file_path)
            issues.extend(excessive)

            # Detect global collections that grow unbounded
            unbounded = self._detect_unbounded_growth(tree, file_path, source)
            issues.extend(unbounded)

            # Detect inefficient data structures
            inefficient = self._detect_inefficient_structures(tree, file_path)
            issues.extend(inefficient)

        except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
            pass

        return issues

    def _detect_unclosed_resources(
        self, tree: ast.AST, file_path: Path
    ) -> List[MemoryIssue]:
        """Detect resources opened but not properly closed.

        Args:
            tree: AST tree
            file_path: File path

        Returns:
            List of memory issues
        """
        issues = []

        # Track open() calls not in 'with' statement
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "open":
                    # Check if this call is inside a 'with' statement
                    # This is simplified - proper check would traverse parent nodes
                    in_with = self._is_in_with_statement(node, tree)

                    if not in_with:
                        issues.append(
                            MemoryIssue(
                                file_path=str(file_path),
                                line_start=node.lineno,
                                line_end=node.end_lineno or node.lineno,
                                issue_type=MemoryIssueType.UNCLOSED_RESOURCE,
                                impact=PerformanceImpact.MEDIUM,
                                description="File opened without using context manager",
                                evidence="open() call not in 'with' statement",
                                suggestion=(
                                    "Use 'with open(...) as f:' to ensure "
                                    "file is properly closed"
                                ),
                                potential_leak_size="File descriptors and buffers",
                            )
                        )

        return issues

    def _is_in_with_statement(self, target_node: ast.AST, tree: ast.AST) -> bool:
        """Check if a node is inside a with statement.

        Args:
            target_node: Node to check
            tree: Full AST tree

        Returns:
            True if inside with statement
        """
        # Simplified check - look for With nodes
        for node in ast.walk(tree):
            if isinstance(node, ast.With):
                # Check if target is in the body
                for item in node.items:
                    if isinstance(item.context_expr, ast.Call):
                        if hasattr(target_node, "lineno") and hasattr(
                            item.context_expr, "lineno"
                        ):
                            if target_node.lineno == item.context_expr.lineno:
                                return True

        return False

    def _detect_excessive_allocations(
        self, tree: ast.AST, file_path: Path
    ) -> List[MemoryIssue]:
        """Detect excessive memory allocations in loops.

        Args:
            tree: AST tree
            file_path: File path

        Returns:
            List of memory issues
        """
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                # Check for string concatenation in loops
                has_string_concat = self._has_string_concatenation(node)
                if has_string_concat:
                    issues.append(
                        MemoryIssue(
                            file_path=str(file_path),
                            line_start=node.lineno,
                            line_end=node.end_lineno or node.lineno,
                            issue_type=MemoryIssueType.EXCESSIVE_ALLOCATION,
                            impact=PerformanceImpact.MEDIUM,
                            description="String concatenation in loop",
                            evidence="Using += for string concatenation in loop",
                            suggestion=(
                                "Use a list and ''.join() or io.StringIO "
                                "for efficient string building"
                            ),
                            potential_leak_size="O(n²) memory allocations",
                        )
                    )

                # Check for repeated list copying
                has_list_copy = self._has_list_copying(node)
                if has_list_copy:
                    issues.append(
                        MemoryIssue(
                            file_path=str(file_path),
                            line_start=node.lineno,
                            line_end=node.end_lineno or node.lineno,
                            issue_type=MemoryIssueType.EXCESSIVE_ALLOCATION,
                            impact=PerformanceImpact.MEDIUM,
                            description="List copying in loop",
                            evidence="Creating copies of lists repeatedly",
                            suggestion="Consider using in-place operations or generators",
                            potential_leak_size="O(n²) space complexity",
                        )
                    )

        return issues

    def _has_string_concatenation(self, node: ast.AST) -> bool:
        """Check if loop has string concatenation.

        Args:
            node: Loop node

        Returns:
            True if string concatenation detected
        """
        for child in ast.walk(node):
            if isinstance(child, ast.AugAssign):
                if isinstance(child.op, ast.Add):
                    # Check if target looks like a string
                    # This is a heuristic
                    return True

        return False

    def _has_list_copying(self, node: ast.AST) -> bool:
        """Check if loop copies lists.

        Args:
            node: Loop node

        Returns:
            True if list copying detected
        """
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    if child.func.attr == "copy":
                        return True
                elif isinstance(child.func, ast.Name):
                    if child.func.id == "list":
                        return True

        return False

    def _detect_unbounded_growth(
        self, tree: ast.AST, file_path: Path, source: str
    ) -> List[MemoryIssue]:
        """Detect global collections that can grow unbounded.

        Args:
            tree: AST tree
            file_path: File path
            source: Source code

        Returns:
            List of memory issues
        """
        issues = []

        # Track global/class-level collections
        global_collections: Set[str] = set()

        for node in ast.walk(tree):
            # Find module-level or class-level assignments
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            # Check if value is a list, dict, or set
                            if isinstance(node.value, (ast.List, ast.Dict, ast.Set)):
                                global_collections.add(target.id)

        # Now check if these collections are modified but never cleared
        for collection in global_collections:
            # Search for append/add/update but not clear/pop
            has_growth = collection in source and (
                f"{collection}.append" in source
                or f"{collection}.add" in source
                or f"{collection}.update" in source
            )

            has_cleanup = (
                f"{collection}.clear" in source or f"{collection}.pop" in source
            )

            if has_growth and not has_cleanup:
                issues.append(
                    MemoryIssue(
                        file_path=str(file_path),
                        line_start=1,
                        line_end=1,
                        issue_type=MemoryIssueType.MEMORY_LEAK,
                        impact=PerformanceImpact.HIGH,
                        description=f"Global collection '{collection}' grows unbounded",
                        evidence="Collection is modified but never cleared",
                        suggestion=(
                            "Implement periodic cleanup, use LRU cache, "
                            "or use weak references"
                        ),
                        potential_leak_size="Grows indefinitely with usage",
                    )
                )

        return issues

    def _detect_inefficient_structures(
        self, tree: ast.AST, file_path: Path
    ) -> List[MemoryIssue]:
        """Detect inefficient data structure usage.

        Args:
            tree: AST tree
            file_path: File path

        Returns:
            List of memory issues
        """
        issues = []

        # Pattern: Using list for membership testing
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                # Check for 'x in some_list' pattern
                if any(isinstance(op, ast.In) for op in node.ops):
                    # Check if comparator is a list
                    for comparator in node.comparators:
                        if isinstance(comparator, ast.List):
                            if len(comparator.elts) > 5:  # Arbitrary threshold
                                issues.append(
                                    MemoryIssue(
                                        file_path=str(file_path),
                                        line_start=node.lineno,
                                        line_end=node.end_lineno or node.lineno,
                                        issue_type=MemoryIssueType.INEFFICIENT_STRUCTURE,
                                        impact=PerformanceImpact.LOW,
                                        description="Using list for membership testing",
                                        evidence=f"'in' operator on list with {len(comparator.elts)} items",
                                        suggestion=(
                                            "Use a set instead of list for O(1) "
                                            "membership testing"
                                        ),
                                    )
                                )

        return issues

    def count_potential_leaks(self, issues: List[MemoryIssue]) -> int:
        """Count potential memory leaks.

        Args:
            issues: List of memory issues

        Returns:
            Count of potential leaks
        """
        return sum(
            1 for issue in issues if issue.issue_type == MemoryIssueType.MEMORY_LEAK
        )
