"""
Code Duplication Detection Module.

Detects exact, structural, and semantic code duplication.
"""

import ast
import hashlib
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ..types import DuplicationCluster, DuplicationType


class DuplicationDetector:
    """Detects code duplication using multiple techniques."""

    def __init__(
        self,
        min_lines: int = 6,
        min_tokens: int = 50,
        similarity_threshold: float = 0.85,
    ):
        """Initialize duplication detector.

        Args:
            min_lines: Minimum lines for duplication detection
            min_tokens: Minimum tokens for duplication detection
            similarity_threshold: Minimum similarity for structural duplication
        """
        self.min_lines = min_lines
        self.min_tokens = min_tokens
        self.similarity_threshold = similarity_threshold

    def analyze_files(self, file_paths: List[Path]) -> List[DuplicationCluster]:
        """Analyze multiple files for duplication.

        Args:
            file_paths: List of file paths to analyze

        Returns:
            List of duplication clusters
        """
        clusters = []

        # Detect exact duplication
        exact_clusters = self._detect_exact_duplication(file_paths)
        clusters.extend(exact_clusters)

        # Detect structural duplication
        structural_clusters = self._detect_structural_duplication(file_paths)
        clusters.extend(structural_clusters)

        # Detect semantic duplication (simplified)
        semantic_clusters = self._detect_semantic_duplication(file_paths)
        clusters.extend(semantic_clusters)

        return clusters

    def _detect_exact_duplication(
        self, file_paths: List[Path]
    ) -> List[DuplicationCluster]:
        """Detect exact code duplication using hash-based comparison.

        Args:
            file_paths: Files to analyze

        Returns:
            List of exact duplication clusters
        """
        clusters = []
        # Hash map: code hash -> list of (file, line_start, line_end, code)
        hash_map: Dict[str, List[Tuple[str, int, int, str]]] = defaultdict(list)

        for file_path in file_paths:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                # Sliding window approach
                for i in range(len(lines) - self.min_lines + 1):
                    window = lines[i : i + self.min_lines]
                    # Normalize: remove leading/trailing whitespace
                    normalized = [line.strip() for line in window if line.strip()]

                    if len(normalized) < self.min_lines:
                        continue

                    code_block = "\n".join(normalized)
                    code_hash = hashlib.md5(code_block.encode()).hexdigest()

                    hash_map[code_hash].append(
                        (str(file_path), i + 1, i + self.min_lines, code_block)
                    )

            except (UnicodeDecodeError, FileNotFoundError):
                continue

        # Find duplicates (hash appearing more than once)
        for code_hash, instances in hash_map.items():
            if len(instances) >= 2:
                # Create cluster
                cluster = DuplicationCluster(
                    duplication_type=DuplicationType.EXACT,
                    total_lines=self.min_lines * len(instances),
                    instance_count=len(instances),
                    instances=[
                        {
                            "file_path": file_path,
                            "line_start": line_start,
                            "line_end": line_end,
                        }
                        for file_path, line_start, line_end, _ in instances
                    ],
                    code_snippet=instances[0][3][:200] + "..."
                    if len(instances[0][3]) > 200
                    else instances[0][3],
                    confidence=1.0,
                    suggestions=[
                        "Extract this duplicated code into a reusable function or method",
                        f"Found {len(instances)} exact copies of this code block",
                    ],
                )
                clusters.append(cluster)

        return clusters

    def _detect_structural_duplication(
        self, file_paths: List[Path]
    ) -> List[DuplicationCluster]:
        """Detect structural duplication using AST comparison.

        Args:
            file_paths: Files to analyze

        Returns:
            List of structural duplication clusters
        """
        clusters = []
        python_files = [f for f in file_paths if f.suffix == ".py"]

        if not python_files:
            return clusters

        # Extract AST structures
        structures = []
        for file_path in python_files:
            file_structures = self._extract_structures(file_path)
            structures.extend(file_structures)

        # Compare structures
        compared: Set[Tuple[int, int]] = set()
        for i, struct1 in enumerate(structures):
            for j, struct2 in enumerate(structures[i + 1 :], start=i + 1):
                if (i, j) in compared:
                    continue

                similarity = self._compare_structures(
                    struct1["ast"], struct2["ast"]
                )

                if similarity >= self.similarity_threshold:
                    compared.add((i, j))

                    cluster = DuplicationCluster(
                        duplication_type=DuplicationType.STRUCTURAL,
                        total_lines=struct1["lines"] + struct2["lines"],
                        instance_count=2,
                        instances=[
                            {
                                "file_path": struct1["file"],
                                "line_start": struct1["line_start"],
                                "line_end": struct1["line_end"],
                            },
                            {
                                "file_path": struct2["file"],
                                "line_start": struct2["line_start"],
                                "line_end": struct2["line_end"],
                            },
                        ],
                        code_snippet=struct1["code"][:200] + "..."
                        if len(struct1["code"]) > 200
                        else struct1["code"],
                        confidence=similarity,
                        suggestions=[
                            "These code blocks have similar structure. "
                            "Consider extracting common logic.",
                            f"Structural similarity: {similarity:.0%}",
                        ],
                    )
                    clusters.append(cluster)

        return clusters

    def _extract_structures(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract AST structures from a Python file.

        Args:
            file_path: Python file to analyze

        Returns:
            List of extracted structures
        """
        structures = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
                lines = source.split("\n")

            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    structures.append(
                        {
                            "file": str(file_path),
                            "line_start": node.lineno,
                            "line_end": node.end_lineno or node.lineno,
                            "lines": (node.end_lineno or node.lineno) - node.lineno,
                            "ast": node,
                            "code": "\n".join(
                                lines[node.lineno - 1 : node.end_lineno]
                            ),
                        }
                    )

        except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
            pass

        return structures

    def _compare_structures(self, ast1: ast.AST, ast2: ast.AST) -> float:
        """Compare two AST structures for similarity.

        Args:
            ast1: First AST node
            ast2: Second AST node

        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Convert AST to normalized string representation
        dump1 = self._normalize_ast(ast1)
        dump2 = self._normalize_ast(ast2)

        # Calculate similarity using SequenceMatcher
        matcher = SequenceMatcher(None, dump1, dump2)
        return matcher.ratio()

    def _normalize_ast(self, node: ast.AST) -> str:
        """Normalize AST by removing variable names and literals.

        Args:
            node: AST node to normalize

        Returns:
            Normalized string representation
        """

        class Normalizer(ast.NodeTransformer):
            """Normalizes AST by replacing names and constants."""

            def visit_Name(self, node: ast.Name) -> ast.Name:
                # Replace all names with placeholder
                node.id = "VAR"
                return node

            def visit_Constant(self, node: ast.Constant) -> ast.Constant:
                # Replace constants with type placeholder
                if isinstance(node.value, str):
                    node.value = "STR"
                elif isinstance(node.value, int):
                    node.value = 0
                elif isinstance(node.value, float):
                    node.value = 0.0
                return node

        normalized = Normalizer().visit(ast.parse(ast.unparse(node)))
        return ast.dump(normalized)

    def _detect_semantic_duplication(
        self, file_paths: List[Path]
    ) -> List[DuplicationCluster]:
        """Detect semantic duplication (similar logic, different implementation).

        Note: This is a simplified heuristic-based approach.
        For production, consider using ML-based approaches.

        Args:
            file_paths: Files to analyze

        Returns:
            List of semantic duplication clusters
        """
        # Simplified semantic detection based on:
        # - Similar function signatures
        # - Similar control flow patterns
        # - Similar API usage patterns

        clusters = []
        python_files = [f for f in file_paths if f.suffix == ".py"]

        function_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        for file_path in python_files:
            functions = self._extract_function_signatures(file_path)
            for func in functions:
                # Group by similar signatures (same param count, similar name)
                key = f"{len(func['params'])}_{func['name'][:3]}"
                function_groups[key].append(func)

        # Check groups for semantic similarity
        for group_key, functions in function_groups.items():
            if len(functions) < 2:
                continue

            # Compare functions in group
            for i, func1 in enumerate(functions):
                for func2 in functions[i + 1 :]:
                    similarity = self._calculate_semantic_similarity(func1, func2)

                    if similarity >= self.similarity_threshold:
                        cluster = DuplicationCluster(
                            duplication_type=DuplicationType.SEMANTIC,
                            total_lines=func1["lines"] + func2["lines"],
                            instance_count=2,
                            instances=[
                                {
                                    "file_path": func1["file"],
                                    "line_start": func1["line_start"],
                                    "line_end": func1["line_end"],
                                },
                                {
                                    "file_path": func2["file"],
                                    "line_start": func2["line_start"],
                                    "line_end": func2["line_end"],
                                },
                            ],
                            code_snippet=f"Functions: {func1['name']}, {func2['name']}",
                            confidence=similarity,
                            suggestions=[
                                "These functions appear to implement similar logic. "
                                "Consider creating a unified implementation.",
                                f"Semantic similarity: {similarity:.0%}",
                            ],
                        )
                        clusters.append(cluster)

        return clusters

    def _extract_function_signatures(
        self, file_path: Path
    ) -> List[Dict[str, Any]]:
        """Extract function signatures and metadata.

        Args:
            file_path: Python file to analyze

        Returns:
            List of function metadata
        """
        functions = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.append(
                        {
                            "file": str(file_path),
                            "name": node.name,
                            "line_start": node.lineno,
                            "line_end": node.end_lineno or node.lineno,
                            "lines": (node.end_lineno or node.lineno) - node.lineno,
                            "params": [arg.arg for arg in node.args.args],
                            "ast": node,
                        }
                    )

        except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
            pass

        return functions

    def _calculate_semantic_similarity(
        self, func1: Dict[str, Any], func2: Dict[str, Any]
    ) -> float:
        """Calculate semantic similarity between two functions.

        Args:
            func1: First function metadata
            func2: Second function metadata

        Returns:
            Similarity score (0.0 to 1.0)
        """
        score = 0.0
        weights = []

        # Name similarity
        name_sim = SequenceMatcher(None, func1["name"], func2["name"]).ratio()
        score += name_sim * 0.3
        weights.append(0.3)

        # Parameter count similarity
        param_count_sim = (
            1.0
            - abs(len(func1["params"]) - len(func2["params"]))
            / max(len(func1["params"]), len(func2["params"]), 1)
        )
        score += param_count_sim * 0.2
        weights.append(0.2)

        # AST structure similarity
        try:
            ast_sim = self._compare_structures(func1["ast"], func2["ast"])
            score += ast_sim * 0.5
            weights.append(0.5)
        except Exception:
            pass

        return score / sum(weights) if weights else 0.0

    def calculate_duplication_percentage(
        self, clusters: List[DuplicationCluster], total_lines: int
    ) -> float:
        """Calculate percentage of duplicated code.

        Args:
            clusters: Duplication clusters
            total_lines: Total lines of code

        Returns:
            Duplication percentage
        """
        if total_lines == 0:
            return 0.0

        duplicated_lines = sum(cluster.total_lines for cluster in clusters)
        return round((duplicated_lines / total_lines) * 100, 2)
