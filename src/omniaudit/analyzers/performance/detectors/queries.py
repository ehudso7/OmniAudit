"""
Database Query Performance Analysis Module.

Detects N+1 queries, missing indexes, and inefficient query patterns.
"""

import ast
import re
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from ..types import (
    PerformanceImpact,
    QueryIssueType,
    QueryPerformanceIssue,
)


class QueryAnalyzer:
    """Analyzes database query performance."""

    def __init__(self):
        """Initialize query analyzer."""
        # Common ORM patterns
        self.orm_patterns = {
            "django": {
                "query": r"\.objects\.",
                "filter": r"\.filter\(",
                "get": r"\.get\(",
                "all": r"\.all\(",
                "select_related": r"\.select_related\(",
                "prefetch_related": r"\.prefetch_related\(",
            },
            "sqlalchemy": {
                "query": r"session\.query\(",
                "filter": r"\.filter\(",
                "all": r"\.all\(",
                "joinedload": r"joinedload\(",
                "subqueryload": r"subqueryload\(",
            },
        }

    def analyze_files(self, file_paths: List[Path]) -> List[QueryPerformanceIssue]:
        """Analyze files for query performance issues.

        Args:
            file_paths: Files to analyze

        Returns:
            List of query performance issues
        """
        issues = []

        for file_path in file_paths:
            if file_path.suffix == ".py":
                issues.extend(self._analyze_python_file(file_path))

        return issues

    def _analyze_python_file(self, file_path: Path) -> List[QueryPerformanceIssue]:
        """Analyze Python file for query issues.

        Args:
            file_path: Python file to analyze

        Returns:
            List of query issues
        """
        issues = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)

            # Detect N+1 queries
            n_plus_one_issues = self._detect_n_plus_one(tree, file_path, source)
            issues.extend(n_plus_one_issues)

            # Detect missing select_related/prefetch_related
            missing_optimization = self._detect_missing_optimization(
                tree, file_path, source
            )
            issues.extend(missing_optimization)

            # Detect inefficient patterns
            inefficient = self._detect_inefficient_patterns(tree, file_path, source)
            issues.extend(inefficient)

        except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
            pass

        return issues

    def _detect_n_plus_one(
        self, tree: ast.AST, file_path: Path, source: str
    ) -> List[QueryPerformanceIssue]:
        """Detect N+1 query patterns.

        Args:
            tree: AST tree
            file_path: File path
            source: Source code

        Returns:
            List of N+1 query issues
        """
        issues = []

        # Pattern: Loop over queryset, then access related objects
        # for item in Model.objects.all():
        #     item.related_set.all()  # N+1!

        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                # Check if iterating over a queryset
                has_query_iteration = self._is_queryset_iteration(node)

                if has_query_iteration:
                    # Check if accessing related objects in loop body
                    has_related_access = self._has_related_object_access(node)

                    if has_related_access:
                        issues.append(
                            QueryPerformanceIssue(
                                file_path=str(file_path),
                                line_start=node.lineno,
                                line_end=node.end_lineno or node.lineno,
                                issue_type=QueryIssueType.N_PLUS_ONE,
                                query_pattern=self._extract_code_snippet(
                                    source, node.lineno, node.end_lineno or node.lineno
                                ),
                                impact=PerformanceImpact.CRITICAL,
                                description=(
                                    "N+1 query pattern detected: "
                                    "accessing related objects inside loop"
                                ),
                                suggestion=(
                                    "Use select_related() for foreign keys or "
                                    "prefetch_related() for reverse relations "
                                    "to fetch related data in a single query"
                                ),
                                estimated_improvement="10-100x faster",
                            )
                        )

        return issues

    def _is_queryset_iteration(self, node: ast.AST) -> bool:
        """Check if node iterates over a queryset.

        Args:
            node: AST node (For or While)

        Returns:
            True if iterating over queryset
        """
        if isinstance(node, ast.For):
            # Check if iter contains .objects.all() or similar
            iter_code = ast.unparse(node.iter)
            return bool(
                re.search(r"\.objects\.", iter_code)
                or re.search(r"session\.query\(", iter_code)
                or re.search(r"\.filter\(", iter_code)
            )

        return False

    def _has_related_object_access(self, node: ast.AST) -> bool:
        """Check if loop body accesses related objects.

        Args:
            node: Loop node

        Returns:
            True if accessing related objects
        """
        # Look for attribute access patterns like:
        # item.related_set, item.foreign_key.field
        for child in ast.walk(node):
            if isinstance(child, ast.Attribute):
                # Check for chained attribute access (indicates relationship)
                if isinstance(child.value, ast.Attribute):
                    return True

                # Check for _set suffix (Django reverse relation)
                if child.attr.endswith("_set"):
                    return True

                # Check for common relation methods
                if child.attr in ("all", "filter", "get", "first"):
                    return True

        return False

    def _detect_missing_optimization(
        self, tree: ast.AST, file_path: Path, source: str
    ) -> List[QueryPerformanceIssue]:
        """Detect queries missing select_related or prefetch_related.

        Args:
            tree: AST tree
            file_path: File path
            source: Source code

        Returns:
            List of query issues
        """
        issues = []

        # Look for .objects.all() or .objects.filter() without optimization
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_str = ast.unparse(node)

                # Check for ORM query calls
                if ".objects." in call_str or "session.query(" in call_str:
                    # Check if missing select_related or prefetch_related
                    has_optimization = (
                        "select_related" in call_str
                        or "prefetch_related" in call_str
                        or "joinedload" in call_str
                        or "subqueryload" in call_str
                    )

                    # Check if this query is used in a loop or accesses relations
                    # (simplified check)
                    if not has_optimization and len(call_str) > 50:
                        issues.append(
                            QueryPerformanceIssue(
                                file_path=str(file_path),
                                line_start=node.lineno,
                                line_end=node.end_lineno or node.lineno,
                                issue_type=QueryIssueType.SUBOPTIMAL_QUERY,
                                query_pattern=call_str[:100] + "..."
                                if len(call_str) > 100
                                else call_str,
                                impact=PerformanceImpact.MEDIUM,
                                description=(
                                    "Query may benefit from eager loading optimization"
                                ),
                                suggestion=(
                                    "Consider using select_related() or prefetch_related() "
                                    "if this query accesses related objects"
                                ),
                                estimated_improvement="2-10x faster",
                            )
                        )

        return issues

    def _detect_inefficient_patterns(
        self, tree: ast.AST, file_path: Path, source: str
    ) -> List[QueryPerformanceIssue]:
        """Detect inefficient query patterns.

        Args:
            tree: AST tree
            file_path: File path
            source: Source code

        Returns:
            List of query issues
        """
        issues = []

        # Pattern 1: Calling .count() then iterating
        # bad: if Model.objects.filter(...).count() > 0: iterate
        # good: if Model.objects.filter(...).exists()

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_str = ast.unparse(node)

                # Check for .count() usage
                if ".count()" in call_str and ".objects." in call_str:
                    issues.append(
                        QueryPerformanceIssue(
                            file_path=str(file_path),
                            line_start=node.lineno,
                            line_end=node.end_lineno or node.lineno,
                            issue_type=QueryIssueType.SUBOPTIMAL_QUERY,
                            query_pattern=call_str[:100] + "..."
                            if len(call_str) > 100
                            else call_str,
                            impact=PerformanceImpact.LOW,
                            description="Using .count() for existence check",
                            suggestion=(
                                "Use .exists() instead of .count() > 0 "
                                "for existence checks"
                            ),
                            estimated_improvement="Faster and less memory",
                        )
                    )

        return issues

    def _extract_code_snippet(
        self, source: str, line_start: int, line_end: int
    ) -> str:
        """Extract code snippet from source.

        Args:
            source: Full source code
            line_start: Starting line (1-indexed)
            line_end: Ending line (1-indexed)

        Returns:
            Code snippet
        """
        lines = source.split("\n")
        snippet_lines = lines[line_start - 1 : line_end]
        snippet = "\n".join(snippet_lines)

        if len(snippet) > 150:
            return snippet[:150] + "..."

        return snippet

    def count_n_plus_one_issues(self, issues: List[QueryPerformanceIssue]) -> int:
        """Count N+1 query issues.

        Args:
            issues: List of query issues

        Returns:
            Count of N+1 issues
        """
        return sum(
            1 for issue in issues if issue.issue_type == QueryIssueType.N_PLUS_ONE
        )
