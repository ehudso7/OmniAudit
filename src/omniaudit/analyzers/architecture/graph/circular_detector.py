"""
Circular Dependency Detection Module.

Detects circular dependencies using cycle detection algorithms.
"""

from collections import defaultdict
from typing import Dict, List, Set

from ..types import CircularDependency


class CircularDependencyDetector:
    """Detects circular dependencies in dependency graphs."""

    def __init__(self, graph: Dict[str, Set[str]]):
        """Initialize circular dependency detector.

        Args:
            graph: Dependency graph (module -> dependencies)
        """
        self.graph = graph
        self.visited: Set[str] = set()
        self.rec_stack: Set[str] = set()
        self.cycles: List[List[str]] = []

    def detect_cycles(self) -> List[CircularDependency]:
        """Detect all circular dependencies.

        Returns:
            List of circular dependencies
        """
        self.visited = set()
        self.rec_stack = set()
        self.cycles = []

        for node in self.graph:
            if node not in self.visited:
                self._dfs(node, [])

        # Convert cycles to CircularDependency objects
        circular_deps = []
        for cycle in self.cycles:
            severity = self._determine_severity(cycle)
            circular_deps.append(
                CircularDependency(
                    cycle=cycle,
                    severity=severity,
                    impact=f"Circular dependency involving {len(cycle)} modules",
                    suggestion=self._generate_suggestion(cycle),
                )
            )

        return circular_deps

    def _dfs(self, node: str, path: List[str]) -> None:
        """Depth-first search to detect cycles.

        Args:
            node: Current node
            path: Current path
        """
        self.visited.add(node)
        self.rec_stack.add(node)
        path.append(node)

        if node in self.graph:
            for neighbor in self.graph[node]:
                if neighbor not in self.visited:
                    self._dfs(neighbor, path.copy())
                elif neighbor in self.rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]

                    # Only add if not duplicate
                    if not self._is_duplicate_cycle(cycle):
                        self.cycles.append(cycle)

        self.rec_stack.remove(node)

    def _is_duplicate_cycle(self, cycle: List[str]) -> bool:
        """Check if cycle is a duplicate.

        Args:
            cycle: Cycle to check

        Returns:
            True if duplicate
        """
        cycle_set = set(cycle)
        for existing in self.cycles:
            if set(existing) == cycle_set:
                return True
        return False

    def _determine_severity(self, cycle: List[str]) -> str:
        """Determine severity of circular dependency.

        Args:
            cycle: Dependency cycle

        Returns:
            Severity level
        """
        if len(cycle) == 2:
            return "high"  # Direct circular dependency
        elif len(cycle) <= 4:
            return "medium"
        else:
            return "low"  # Long cycles are less problematic

    def _generate_suggestion(self, cycle: List[str]) -> str:
        """Generate suggestion for breaking the cycle.

        Args:
            cycle: Dependency cycle

        Returns:
            Suggestion text
        """
        if len(cycle) == 2:
            return (
                f"Direct circular dependency between {cycle[0]} and {cycle[1]}. "
                "Consider using dependency injection or creating an interface."
            )
        else:
            return (
                f"Circular dependency chain with {len(cycle)} modules. "
                "Refactor to create a clear dependency direction or use dependency inversion."
            )
