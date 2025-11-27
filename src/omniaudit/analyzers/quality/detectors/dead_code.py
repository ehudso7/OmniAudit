"""
Dead Code Detection Module.

Identifies unused functions, classes, variables, and imports.
"""

import ast
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set

from ..types import DeadCodeItem


class DeadCodeDetector:
    """Detects dead/unused code."""

    def __init__(self):
        """Initialize dead code detector."""
        self.definitions: Dict[str, Dict[str, Any]] = {}
        self.usages: Dict[str, Set[str]] = defaultdict(set)

    def analyze_files(self, file_paths: List[Path]) -> List[DeadCodeItem]:
        """Analyze files for dead code.

        Args:
            file_paths: List of files to analyze

        Returns:
            List of dead code items
        """
        python_files = [f for f in file_paths if f.suffix == ".py"]

        if not python_files:
            return []

        # First pass: collect all definitions
        for file_path in python_files:
            self._collect_definitions(file_path)

        # Second pass: collect all usages
        for file_path in python_files:
            self._collect_usages(file_path)

        # Identify dead code
        return self._identify_dead_code()

    def _collect_definitions(self, file_path: Path) -> None:
        """Collect all definitions from a file.

        Args:
            file_path: Python file to analyze
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source, filename=str(file_path))

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    key = f"func:{node.name}"
                    self.definitions[key] = {
                        "type": "function",
                        "name": node.name,
                        "file": str(file_path),
                        "line_start": node.lineno,
                        "line_end": node.end_lineno or node.lineno,
                    }

                elif isinstance(node, ast.ClassDef):
                    key = f"class:{node.name}"
                    self.definitions[key] = {
                        "type": "class",
                        "name": node.name,
                        "file": str(file_path),
                        "line_start": node.lineno,
                        "line_end": node.end_lineno or node.lineno,
                    }

                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.asname or alias.name
                        key = f"import:{name}"
                        self.definitions[key] = {
                            "type": "import",
                            "name": name,
                            "file": str(file_path),
                            "line_start": node.lineno,
                            "line_end": node.lineno,
                        }

                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        if alias.name != "*":
                            name = alias.asname or alias.name
                            key = f"import:{name}"
                            self.definitions[key] = {
                                "type": "import",
                                "name": name,
                                "file": str(file_path),
                                "line_start": node.lineno,
                                "line_end": node.lineno,
                            }

        except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
            pass

    def _collect_usages(self, file_path: Path) -> None:
        """Collect all name usages from a file.

        Args:
            file_path: Python file to analyze
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source, filename=str(file_path))

            class UsageCollector(ast.NodeVisitor):
                """AST visitor to collect name usages."""

                def __init__(self, detector: "DeadCodeDetector"):
                    self.detector = detector
                    self.current_scope: List[str] = []

                def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                    # Record function call if used
                    self.current_scope.append(node.name)
                    self.generic_visit(node)
                    self.current_scope.pop()

                def visit_ClassDef(self, node: ast.ClassDef) -> None:
                    self.current_scope.append(node.name)
                    self.generic_visit(node)
                    self.current_scope.pop()

                def visit_Name(self, node: ast.Name) -> None:
                    # Record usage of a name
                    name = node.id
                    self.detector.usages[f"func:{name}"].add(str(file_path))
                    self.detector.usages[f"class:{name}"].add(str(file_path))
                    self.detector.usages[f"import:{name}"].add(str(file_path))
                    self.generic_visit(node)

                def visit_Call(self, node: ast.Call) -> None:
                    # Record function/method calls
                    if isinstance(node.func, ast.Name):
                        name = node.func.id
                        self.detector.usages[f"func:{name}"].add(str(file_path))
                    self.generic_visit(node)

                def visit_Attribute(self, node: ast.Attribute) -> None:
                    # Record attribute access (could be method calls)
                    self.detector.usages[f"func:{node.attr}"].add(str(file_path))
                    self.generic_visit(node)

            collector = UsageCollector(self)
            collector.visit(tree)

        except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
            pass

    def _identify_dead_code(self) -> List[DeadCodeItem]:
        """Identify dead code from definitions and usages.

        Returns:
            List of dead code items
        """
        dead_items = []

        for key, definition in self.definitions.items():
            # Skip if used in any file
            if key in self.usages and self.usages[key]:
                continue

            # Skip special methods and magic names
            name = definition["name"]
            if name.startswith("_") and name.endswith("_"):
                continue

            # Skip main entry points
            if name == "main":
                continue

            # Skip test functions
            if name.startswith("test_"):
                continue

            # Determine confidence based on type
            confidence = 0.7  # Default confidence

            if definition["type"] == "import":
                confidence = 0.9  # High confidence for unused imports
                reason = "Import is never used in the code"
            elif definition["type"] == "function":
                if name.startswith("_"):
                    confidence = 0.6  # Lower for private functions
                    reason = "Private function appears to be unused"
                else:
                    confidence = 0.8
                    reason = "Function is defined but never called"
            elif definition["type"] == "class":
                if name.startswith("_"):
                    confidence = 0.6
                    reason = "Private class appears to be unused"
                else:
                    confidence = 0.8
                    reason = "Class is defined but never instantiated"
            else:
                reason = "Definition appears to be unused"

            dead_items.append(
                DeadCodeItem(
                    file_path=definition["file"],
                    line_start=definition["line_start"],
                    line_end=definition["line_end"],
                    entity_type=definition["type"],
                    entity_name=name,
                    reason=reason,
                    confidence=confidence,
                )
            )

        return dead_items

    def analyze_single_file(self, file_path: Path) -> List[DeadCodeItem]:
        """Analyze a single file for dead code.

        This is less accurate than multi-file analysis but faster.

        Args:
            file_path: Python file to analyze

        Returns:
            List of dead code items
        """
        if file_path.suffix != ".py":
            return []

        dead_items = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)

            # Collect definitions and usages within the file
            definitions = {}
            usages: Set[str] = set()

            # Collect definitions
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    definitions[node.name] = {
                        "type": "function",
                        "line_start": node.lineno,
                        "line_end": node.end_lineno or node.lineno,
                    }
                elif isinstance(node, ast.ClassDef):
                    definitions[node.name] = {
                        "type": "class",
                        "line_start": node.lineno,
                        "line_end": node.end_lineno or node.lineno,
                    }

            # Collect usages
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    usages.add(node.id)
                elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    usages.add(node.func.id)

            # Find dead code
            for name, info in definitions.items():
                if name not in usages and not name.startswith("_"):
                    dead_items.append(
                        DeadCodeItem(
                            file_path=str(file_path),
                            line_start=info["line_start"],
                            line_end=info["line_end"],
                            entity_type=info["type"],
                            entity_name=name,
                            reason=f"{info['type'].capitalize()} defined but not used in this file",
                            confidence=0.6,  # Lower confidence for single-file analysis
                        )
                    )

        except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
            pass

        return dead_items

    def calculate_dead_code_lines(self, items: List[DeadCodeItem]) -> int:
        """Calculate total lines of dead code.

        Args:
            items: Dead code items

        Returns:
            Total lines of dead code
        """
        return sum(item.line_end - item.line_start + 1 for item in items)
