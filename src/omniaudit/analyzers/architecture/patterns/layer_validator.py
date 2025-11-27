"""
Architecture Layer Validation Module.

Validates layer dependencies in layered architectures.
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Set

from ..types import LayerType, LayerViolation


class LayerValidator:
    """Validates architecture layer dependencies."""

    def __init__(self):
        """Initialize layer validator."""
        # Define allowed dependencies (layer -> allowed to depend on)
        self.allowed_dependencies = {
            LayerType.PRESENTATION: {
                LayerType.APPLICATION,
                LayerType.DOMAIN,
            },
            LayerType.APPLICATION: {
                LayerType.DOMAIN,
                LayerType.INFRASTRUCTURE,
            },
            LayerType.DOMAIN: set(),  # Domain should not depend on anything
            LayerType.INFRASTRUCTURE: {
                LayerType.DOMAIN,
            },
            LayerType.DATABASE: {
                LayerType.DOMAIN,
            },
        }

    def detect_violations(
        self, file_paths: List[Path], project_root: Path
    ) -> List[LayerViolation]:
        """Detect layer dependency violations.

        Args:
            file_paths: Files to analyze
            project_root: Project root

        Returns:
            List of layer violations
        """
        violations = []

        for file_path in file_paths:
            if file_path.suffix == ".py":
                file_violations = self._analyze_file(file_path, project_root)
                violations.extend(file_violations)

        return violations

    def _analyze_file(
        self, file_path: Path, project_root: Path
    ) -> List[LayerViolation]:
        """Analyze a single file for layer violations.

        Args:
            file_path: File to analyze
            project_root: Project root

        Returns:
            List of violations
        """
        violations = []

        try:
            # Determine layer of current file
            from_layer = self._detect_layer(file_path, project_root)

            if from_layer is None:
                return violations

            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)

            # Check imports
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    imported_module = self._get_imported_module(node)

                    if imported_module:
                        to_layer = self._detect_layer_from_import(imported_module)

                        if to_layer and not self._is_allowed_dependency(
                            from_layer, to_layer
                        ):
                            violations.append(
                                LayerViolation(
                                    from_layer=from_layer,
                                    to_layer=to_layer,
                                    from_module=str(file_path.relative_to(project_root)),
                                    to_module=imported_module,
                                    line_number=node.lineno,
                                    description=f"{from_layer.value} layer should not depend on {to_layer.value} layer",
                                    severity="high"
                                    if from_layer == LayerType.DOMAIN
                                    else "medium",
                                    suggestion=self._generate_suggestion(
                                        from_layer, to_layer
                                    ),
                                )
                            )

        except (SyntaxError, UnicodeDecodeError, FileNotFoundError, ValueError):
            pass

        return violations

    def _detect_layer(self, file_path: Path, project_root: Path) -> LayerType | None:
        """Detect layer from file path.

        Args:
            file_path: File path
            project_root: Project root

        Returns:
            Layer type or None
        """
        path_str = str(file_path.relative_to(project_root)).lower()

        # Common layer naming patterns
        if any(
            keyword in path_str
            for keyword in ["views", "controllers", "handlers", "api", "presentation"]
        ):
            return LayerType.PRESENTATION
        elif any(
            keyword in path_str
            for keyword in ["services", "use_cases", "application", "app"]
        ):
            return LayerType.APPLICATION
        elif any(
            keyword in path_str for keyword in ["domain", "models", "entities", "core"]
        ):
            return LayerType.DOMAIN
        elif any(
            keyword in path_str
            for keyword in ["repositories", "infrastructure", "adapters"]
        ):
            return LayerType.INFRASTRUCTURE
        elif any(keyword in path_str for keyword in ["db", "database", "persistence"]):
            return LayerType.DATABASE

        return None

    def _detect_layer_from_import(self, import_path: str) -> LayerType | None:
        """Detect layer from import path.

        Args:
            import_path: Import path

        Returns:
            Layer type or None
        """
        path_lower = import_path.lower()

        if any(
            keyword in path_lower
            for keyword in ["views", "controllers", "handlers", "api", "presentation"]
        ):
            return LayerType.PRESENTATION
        elif any(
            keyword in path_lower
            for keyword in ["services", "use_cases", "application"]
        ):
            return LayerType.APPLICATION
        elif any(
            keyword in path_lower for keyword in ["domain", "models", "entities", "core"]
        ):
            return LayerType.DOMAIN
        elif any(
            keyword in path_lower
            for keyword in ["repositories", "infrastructure", "adapters"]
        ):
            return LayerType.INFRASTRUCTURE
        elif any(keyword in path_lower for keyword in ["db", "database", "persistence"]):
            return LayerType.DATABASE

        return None

    def _get_imported_module(self, node: ast.AST) -> str | None:
        """Get imported module path from import node.

        Args:
            node: Import node

        Returns:
            Module path or None
        """
        if isinstance(node, ast.Import):
            if node.names:
                return node.names[0].name
        elif isinstance(node, ast.ImportFrom):
            return node.module

        return None

    def _is_allowed_dependency(
        self, from_layer: LayerType, to_layer: LayerType
    ) -> bool:
        """Check if dependency is allowed.

        Args:
            from_layer: Source layer
            to_layer: Target layer

        Returns:
            True if allowed
        """
        if from_layer == to_layer:
            return True

        allowed = self.allowed_dependencies.get(from_layer, set())
        return to_layer in allowed

    def _generate_suggestion(self, from_layer: LayerType, to_layer: LayerType) -> str:
        """Generate suggestion for fixing violation.

        Args:
            from_layer: Source layer
            to_layer: Target layer

        Returns:
            Suggestion text
        """
        if from_layer == LayerType.DOMAIN:
            return (
                "Domain layer should not depend on any other layer. "
                "Use dependency inversion principle."
            )
        elif from_layer == LayerType.APPLICATION and to_layer == LayerType.PRESENTATION:
            return "Application layer should not depend on presentation layer. Invert the dependency."
        else:
            return f"Restructure to make {from_layer.value} layer independent of {to_layer.value} layer."
