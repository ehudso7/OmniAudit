"""
Anti-Pattern and SOLID Violation Detection Module.

Detects common anti-patterns, SOLID violations, and design patterns.
"""

import ast
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from ..types import (
    AntiPatternInstance,
    AntiPatternType,
    DesignPattern,
    DesignPatternInstance,
    SOLIDPrinciple,
    SOLIDViolation,
)


class AntiPatternDetector:
    """Detects anti-patterns, SOLID violations, and design patterns."""

    def __init__(self):
        """Initialize anti-pattern detector."""
        pass

    def analyze_files(
        self, file_paths: List[Path]
    ) -> Tuple[
        List[AntiPatternInstance],
        List[SOLIDViolation],
        List[DesignPatternInstance],
    ]:
        """Analyze files for anti-patterns and violations.

        Args:
            file_paths: List of files to analyze

        Returns:
            Tuple of (anti_patterns, solid_violations, design_patterns)
        """
        python_files = [f for f in file_paths if f.suffix == ".py"]

        anti_patterns = []
        solid_violations = []
        design_patterns = []

        for file_path in python_files:
            ap, sv = self._analyze_file(file_path)
            anti_patterns.extend(ap)
            solid_violations.extend(sv)

        # Detect design patterns across files
        design_patterns = self._detect_design_patterns(python_files)

        return anti_patterns, solid_violations, design_patterns

    def _analyze_file(
        self, file_path: Path
    ) -> Tuple[List[AntiPatternInstance], List[SOLIDViolation]]:
        """Analyze a single file.

        Args:
            file_path: Python file to analyze

        Returns:
            Tuple of (anti_patterns, solid_violations)
        """
        anti_patterns = []
        solid_violations = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
                lines = source.split("\n")

            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check for God Class
                    if self._is_god_class(node):
                        anti_patterns.append(
                            self._create_anti_pattern(
                                AntiPatternType.GOD_CLASS,
                                file_path,
                                node,
                                "Class has too many responsibilities",
                                {
                                    "methods": len(
                                        [
                                            n
                                            for n in node.body
                                            if isinstance(n, ast.FunctionDef)
                                        ]
                                    ),
                                    "attributes": len(
                                        [
                                            n
                                            for n in node.body
                                            if isinstance(n, ast.Assign)
                                        ]
                                    ),
                                },
                                "Break this class into multiple smaller classes, "
                                "each with a single responsibility",
                            )
                        )

                    # Check SRP violation
                    if self._violates_srp(node):
                        solid_violations.append(
                            SOLIDViolation(
                                principle=SOLIDPrinciple.SINGLE_RESPONSIBILITY,
                                file_path=str(file_path),
                                line_start=node.lineno,
                                entity_name=node.name,
                                description="Class appears to have multiple responsibilities",
                                severity="high",
                                suggestion="Split into focused classes with single purposes",
                            )
                        )

                    # Check for Lazy Class
                    if self._is_lazy_class(node):
                        anti_patterns.append(
                            self._create_anti_pattern(
                                AntiPatternType.LAZY_CLASS,
                                file_path,
                                node,
                                "Class does too little to justify its existence",
                                {"methods": len(node.body)},
                                "Inline this class or merge it with related functionality",
                            )
                        )

                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Check for Long Method
                    if self._is_long_method(node, lines):
                        anti_patterns.append(
                            self._create_anti_pattern(
                                AntiPatternType.LONG_METHOD,
                                file_path,
                                node,
                                "Method is too long and complex",
                                {
                                    "lines": (node.end_lineno or node.lineno)
                                    - node.lineno
                                },
                                "Extract smaller methods for better readability",
                            )
                        )

                    # Check for Feature Envy
                    if self._has_feature_envy(node):
                        anti_patterns.append(
                            self._create_anti_pattern(
                                AntiPatternType.FEATURE_ENVY,
                                file_path,
                                node,
                                "Method uses data from other objects more than its own",
                                {},
                                "Move this method to the class it's most interested in",
                            )
                        )

                    # Check for too many parameters (Data Clumps)
                    if len(node.args.args) > 5:
                        anti_patterns.append(
                            self._create_anti_pattern(
                                AntiPatternType.DATA_CLUMPS,
                                file_path,
                                node,
                                "Too many parameters suggest data clumps",
                                {"param_count": len(node.args.args)},
                                "Introduce parameter object to group related data",
                            )
                        )

                    # Check for Primitive Obsession
                    if self._has_primitive_obsession(node):
                        anti_patterns.append(
                            self._create_anti_pattern(
                                AntiPatternType.PRIMITIVE_OBSESSION,
                                file_path,
                                node,
                                "Overuse of primitives instead of small objects",
                                {},
                                "Replace primitives with small objects for domain concepts",
                            )
                        )

                # Check for Switch Statements (if-elif chains)
                if isinstance(node, ast.If) and self._is_switch_statement(node):
                    anti_patterns.append(
                        self._create_anti_pattern(
                            AntiPatternType.SWITCH_STATEMENTS,
                            file_path,
                            node,
                            "Long if-elif chain suggests missing polymorphism",
                            {"branches": self._count_if_branches(node)},
                            "Replace with polymorphism or strategy pattern",
                        )
                    )

        except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
            pass

        return anti_patterns, solid_violations

    def _is_god_class(self, node: ast.ClassDef) -> bool:
        """Check if class is a God Class (too many responsibilities).

        Args:
            node: Class node to check

        Returns:
            True if God Class detected
        """
        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
        attributes = [n for n in node.body if isinstance(n, ast.Assign)]

        # Heuristic: >15 methods or >10 attributes
        return len(methods) > 15 or len(attributes) > 10

    def _violates_srp(self, node: ast.ClassDef) -> bool:
        """Check if class violates Single Responsibility Principle.

        Args:
            node: Class node to check

        Returns:
            True if SRP violation detected
        """
        # Analyze method names for different concerns
        methods = [
            n.name for n in node.body if isinstance(n, ast.FunctionDef)
        ]

        # Group methods by common prefixes (concerns)
        concerns = set()
        common_prefixes = ["get_", "set_", "save_", "load_", "validate_", "calculate_", "send_", "receive_"]

        for prefix in common_prefixes:
            if any(m.startswith(prefix) for m in methods):
                concerns.add(prefix)

        # If more than 3 different concerns, likely SRP violation
        return len(concerns) > 3

    def _is_lazy_class(self, node: ast.ClassDef) -> bool:
        """Check if class is too small (Lazy Class).

        Args:
            node: Class node to check

        Returns:
            True if Lazy Class detected
        """
        # Only count non-dunder methods
        methods = [
            n
            for n in node.body
            if isinstance(n, ast.FunctionDef)
            and not n.name.startswith("__")
        ]

        return len(methods) <= 1

    def _is_long_method(self, node: ast.FunctionDef, lines: List[str]) -> bool:
        """Check if method is too long.

        Args:
            node: Function node to check
            lines: Source lines

        Returns:
            True if Long Method detected
        """
        loc = (node.end_lineno or node.lineno) - node.lineno
        return loc > 50

    def _has_feature_envy(self, node: ast.FunctionDef) -> bool:
        """Check for Feature Envy anti-pattern.

        Args:
            node: Function node to check

        Returns:
            True if Feature Envy detected
        """
        # Count attribute accesses on other objects vs self
        external_accesses = 0
        self_accesses = 0

        for child in ast.walk(node):
            if isinstance(child, ast.Attribute):
                if isinstance(child.value, ast.Name):
                    if child.value.id == "self":
                        self_accesses += 1
                    else:
                        external_accesses += 1

        # If more external than self accesses, might be feature envy
        return external_accesses > self_accesses and external_accesses > 5

    def _has_primitive_obsession(self, node: ast.FunctionDef) -> bool:
        """Check for Primitive Obsession.

        Args:
            node: Function node to check

        Returns:
            True if Primitive Obsession detected
        """
        # Count primitive type hints
        primitive_count = 0

        if node.returns:
            if isinstance(node.returns, ast.Name) and node.returns.id in [
                "int",
                "str",
                "float",
                "bool",
            ]:
                primitive_count += 1

        for arg in node.args.args:
            if arg.annotation and isinstance(arg.annotation, ast.Name):
                if arg.annotation.id in ["int", "str", "float", "bool"]:
                    primitive_count += 1

        # Heuristic: many primitive types suggest obsession
        return primitive_count > 4

    def _is_switch_statement(self, node: ast.If) -> bool:
        """Check if if-elif chain is effectively a switch statement.

        Args:
            node: If node to check

        Returns:
            True if switch-like structure detected
        """
        return self._count_if_branches(node) >= 4

    def _count_if_branches(self, node: ast.If) -> int:
        """Count branches in if-elif chain.

        Args:
            node: If node

        Returns:
            Number of branches
        """
        count = 1  # Initial if

        current = node
        while current.orelse:
            if len(current.orelse) == 1 and isinstance(
                current.orelse[0], ast.If
            ):
                count += 1
                current = current.orelse[0]
            else:
                if current.orelse:
                    count += 1  # else clause
                break

        return count

    def _create_anti_pattern(
        self,
        pattern_type: AntiPatternType,
        file_path: Path,
        node: ast.AST,
        description: str,
        evidence: Dict[str, Any],
        suggestion: str,
    ) -> AntiPatternInstance:
        """Create an anti-pattern instance.

        Args:
            pattern_type: Type of anti-pattern
            file_path: File containing the pattern
            node: AST node
            description: Description
            evidence: Supporting evidence
            suggestion: Fix suggestion

        Returns:
            AntiPatternInstance
        """
        # Determine severity based on evidence
        severity = "medium"
        if "methods" in evidence and evidence["methods"] > 20:
            severity = "high"
        elif "lines" in evidence and evidence["lines"] > 100:
            severity = "high"

        return AntiPatternInstance(
            pattern_type=pattern_type,
            file_path=str(file_path),
            line_start=getattr(node, "lineno", 1),
            line_end=getattr(node, "end_lineno", getattr(node, "lineno", 1)),
            entity_name=getattr(node, "name", "unknown"),
            description=description,
            severity=severity,
            evidence=evidence,
            refactoring_suggestion=suggestion,
        )

    def _detect_design_patterns(
        self, file_paths: List[Path]
    ) -> List[DesignPatternInstance]:
        """Detect design pattern usage across files.

        Args:
            file_paths: Python files to analyze

        Returns:
            List of detected design patterns
        """
        patterns = []

        # Simple heuristics for common patterns
        for file_path in file_paths:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    source = f.read()

                # Singleton pattern detection
                if "instance = None" in source and "__new__" in source:
                    patterns.append(
                        DesignPatternInstance(
                            pattern=DesignPattern.SINGLETON,
                            file_paths=[str(file_path)],
                            confidence=0.7,
                            components={"type": "class-level"},
                            quality_score=75.0,
                            notes="Singleton pattern detected via __new__ override",
                        )
                    )

                # Factory pattern detection
                if "create_" in source or "make_" in source or "Factory" in source:
                    patterns.append(
                        DesignPatternInstance(
                            pattern=DesignPattern.FACTORY,
                            file_paths=[str(file_path)],
                            confidence=0.6,
                            components={"type": "factory-methods"},
                            quality_score=70.0,
                            notes="Factory pattern suggested by naming conventions",
                        )
                    )

                # Observer pattern detection
                if "subscribe" in source and "notify" in source:
                    patterns.append(
                        DesignPatternInstance(
                            pattern=DesignPattern.OBSERVER,
                            file_paths=[str(file_path)],
                            confidence=0.7,
                            components={"type": "observer"},
                            quality_score=80.0,
                            notes="Observer pattern detected via subscribe/notify methods",
                        )
                    )

                # Strategy pattern detection
                if "Strategy" in source or "algorithm" in source.lower():
                    tree = ast.parse(source)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            if "Strategy" in node.name:
                                patterns.append(
                                    DesignPatternInstance(
                                        pattern=DesignPattern.STRATEGY,
                                        file_paths=[str(file_path)],
                                        confidence=0.8,
                                        components={"class": node.name},
                                        quality_score=85.0,
                                        notes="Strategy pattern detected via class naming",
                                    )
                                )

            except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
                pass

        return patterns
