"""
Dependency Graph Generation Module.

Builds and analyzes dependency graphs from code.
"""

import ast
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

from ..types import DependencyNode


class DependencyGraphBuilder:
    """Builds dependency graphs from source code."""

    def __init__(self):
        """Initialize dependency graph builder."""
        self.graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_graph: Dict[str, Set[str]] = defaultdict(set)
        self.module_info: Dict[str, Dict] = {}

    def build_graph(self, file_paths: List[Path], project_root: Path) -> List[DependencyNode]:
        """Build dependency graph from files.

        Args:
            file_paths: List of Python files
            project_root: Project root path

        Returns:
            List of dependency nodes
        """
        # First pass: collect all modules and their imports
        for file_path in file_paths:
            if file_path.suffix == ".py":
                self._process_file(file_path, project_root)

        # Build nodes
        nodes = []
        for module_path, dependencies in self.graph.items():
            imported_by_count = len(self.reverse_graph.get(module_path, set()))

            node = DependencyNode(
                module_path=module_path,
                module_type="file",
                imports_count=len(dependencies),
                imported_by_count=imported_by_count,
                dependencies=list(dependencies),
            )
            nodes.append(node)

        return nodes

    def _process_file(self, file_path: Path, project_root: Path) -> None:
        """Process a Python file to extract dependencies.

        Args:
            file_path: File to process
            project_root: Project root
        """
        try:
            # Convert file path to module path
            rel_path = file_path.relative_to(project_root)
            module_path = str(rel_path).replace("/", ".").replace("\\", ".").replace(".py", "")

            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)

            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self._add_dependency(module_path, alias.name)

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self._add_dependency(module_path, node.module)

        except (SyntaxError, UnicodeDecodeError, FileNotFoundError, ValueError):
            pass

    def _add_dependency(self, from_module: str, to_module: str) -> None:
        """Add a dependency to the graph.

        Args:
            from_module: Source module
            to_module: Target module
        """
        self.graph[from_module].add(to_module)
        self.reverse_graph[to_module].add(from_module)

    def get_total_dependencies(self) -> int:
        """Get total number of dependencies.

        Returns:
            Total dependency count
        """
        return sum(len(deps) for deps in self.graph.values())
