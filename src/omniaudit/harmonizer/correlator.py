"""
Finding Correlator for Cross-File Analysis.

This module identifies correlations between findings across different files,
helping to understand systemic issues and related problems.
"""

import os
from collections import defaultdict
from typing import Dict, List, Set, Tuple

from omniaudit.harmonizer.types import CorrelationConfig, Finding


class Correlator:
    """
    Identifies correlations between findings across files.

    Correlations are based on:
    - File proximity (same directory/module)
    - Rule similarity (same or related rules)
    - Category matching
    - Temporal proximity (if timestamps available)
    """

    def __init__(self, config: CorrelationConfig):
        """Initialize correlator with configuration."""
        self.config = config

    def correlate(self, findings: List[Finding]) -> Dict[str, List[str]]:
        """
        Find correlations between findings.

        Args:
            findings: List of findings to analyze

        Returns:
            Dict mapping finding IDs to lists of correlated finding IDs
        """
        if not self.config.enabled or len(findings) < 2:
            return {}

        correlations: Dict[str, Set[str]] = defaultdict(set)

        # Build indexes for efficient lookup
        by_category = self._index_by_category(findings)
        by_directory = self._index_by_directory(findings)
        by_rule = self._index_by_rule(findings)

        # Find correlations
        for finding in findings:
            correlated = set()

            # Correlate by file proximity
            if self.config.file_proximity_threshold > 0:
                correlated.update(self._find_proximity_correlations(finding, by_directory))

            # Correlate by rule similarity
            correlated.update(self._find_rule_correlations(finding, by_rule))

            # Correlate by category
            correlated.update(self._find_category_correlations(finding, by_category))

            # Remove self and limit
            correlated.discard(finding.id)
            if len(correlated) > self.config.max_correlated_findings:
                # Keep only the most relevant (by same rule > same directory > same category)
                correlated = self._prioritize_correlations(
                    finding, correlated, findings, by_rule, by_directory
                )

            correlations[finding.id] = correlated

        # Convert sets to lists
        return {k: list(v) for k, v in correlations.items()}

    def _index_by_category(self, findings: List[Finding]) -> Dict[str, List[Finding]]:
        """Index findings by category."""
        index: Dict[str, List[Finding]] = defaultdict(list)
        for finding in findings:
            index[finding.category].append(finding)
        return index

    def _index_by_directory(self, findings: List[Finding]) -> Dict[str, List[Finding]]:
        """Index findings by directory."""
        index: Dict[str, List[Finding]] = defaultdict(list)
        for finding in findings:
            directory = self._get_directory_key(finding.file_path, self.config.file_proximity_threshold)
            index[directory].append(finding)
        return index

    def _index_by_rule(self, findings: List[Finding]) -> Dict[str, List[Finding]]:
        """Index findings by rule ID."""
        index: Dict[str, List[Finding]] = defaultdict(list)
        for finding in findings:
            if finding.rule_id:
                index[finding.rule_id].append(finding)
        return index

    def _get_directory_key(self, file_path: str, depth: int) -> str:
        """
        Get directory key for a file path at specified depth.

        Args:
            file_path: Full file path
            depth: Directory depth (0 = exact directory, 1 = parent, etc.)

        Returns:
            Directory key string
        """
        # Normalize path
        path = os.path.normpath(file_path)
        parts = path.split(os.sep)

        # Get directory path (exclude file name)
        if len(parts) > 1:
            dir_parts = parts[:-1]
        else:
            return "root"

        # Limit depth
        if depth == 0:
            # Exact directory
            return os.sep.join(dir_parts)
        elif depth > 0 and len(dir_parts) > depth:
            # Parent directory at specified depth
            return os.sep.join(dir_parts[:-depth])
        else:
            # Root or shallow path
            return os.sep.join(dir_parts[:1]) if dir_parts else "root"

    def _find_proximity_correlations(
        self, finding: Finding, by_directory: Dict[str, List[Finding]]
    ) -> Set[str]:
        """Find findings in the same or nearby directories."""
        correlated = set()

        # Check at different depth levels
        for depth in range(self.config.file_proximity_threshold + 1):
            dir_key = self._get_directory_key(finding.file_path, depth)
            if dir_key in by_directory:
                for other in by_directory[dir_key]:
                    if other.id != finding.id:
                        correlated.add(other.id)

        return correlated

    def _find_rule_correlations(
        self, finding: Finding, by_rule: Dict[str, List[Finding]]
    ) -> Set[str]:
        """Find findings with the same or similar rule IDs."""
        correlated = set()

        if not finding.rule_id:
            return correlated

        # Exact rule match
        if finding.rule_id in by_rule:
            for other in by_rule[finding.rule_id]:
                if other.id != finding.id:
                    correlated.add(other.id)

        # Similar rule IDs (e.g., same prefix)
        if self.config.rule_similarity_threshold < 1.0:
            for rule_id, findings in by_rule.items():
                if rule_id == finding.rule_id:
                    continue

                similarity = self._compute_rule_similarity(finding.rule_id, rule_id)
                if similarity >= self.config.rule_similarity_threshold:
                    for other in findings:
                        if other.id != finding.id:
                            correlated.add(other.id)

        return correlated

    def _find_category_correlations(
        self, finding: Finding, by_category: Dict[str, List[Finding]]
    ) -> Set[str]:
        """Find findings in the same category."""
        correlated = set()

        if finding.category in by_category:
            for other in by_category[finding.category]:
                if other.id != finding.id:
                    correlated.add(other.id)

        return correlated

    def _compute_rule_similarity(self, rule1: str, rule2: str) -> float:
        """
        Compute similarity between two rule IDs.

        Args:
            rule1: First rule ID
            rule2: Second rule ID

        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Simple prefix matching
        # E.g., "S001" and "S002" have high similarity
        # "security/S001" and "security/S002" have high similarity

        # Split on common separators
        parts1 = rule1.replace("-", "/").replace("_", "/").split("/")
        parts2 = rule2.replace("-", "/").replace("_", "/").split("/")

        # Count matching parts
        max_len = max(len(parts1), len(parts2))
        if max_len == 0:
            return 0.0

        matching = sum(1 for p1, p2 in zip(parts1, parts2) if p1 == p2)
        return matching / max_len

    def _prioritize_correlations(
        self,
        finding: Finding,
        correlated_ids: Set[str],
        all_findings: List[Finding],
        by_rule: Dict[str, List[Finding]],
        by_directory: Dict[str, List[Finding]],
    ) -> Set[str]:
        """
        Prioritize correlations when there are too many.

        Priority order:
        1. Same rule ID
        2. Same directory
        3. Closest line number (if same file)
        4. Same category

        Args:
            finding: The finding to correlate
            correlated_ids: Set of correlated finding IDs
            all_findings: All findings
            by_rule: Rule index
            by_directory: Directory index

        Returns:
            Prioritized set of correlation IDs (limited to max)
        """
        # Create finding ID -> Finding map
        finding_map = {f.id: f for f in all_findings}

        # Score each correlation
        scored: List[Tuple[str, float]] = []
        for corr_id in correlated_ids:
            if corr_id not in finding_map:
                continue

            correlated_finding = finding_map[corr_id]
            score = 0.0

            # Same rule: +10
            if finding.rule_id and correlated_finding.rule_id == finding.rule_id:
                score += 10.0

            # Same exact directory: +5
            if os.path.dirname(finding.file_path) == os.path.dirname(correlated_finding.file_path):
                score += 5.0

            # Same file: +3
            if finding.file_path == correlated_finding.file_path:
                score += 3.0

                # Close line numbers: +2
                if finding.line_number and correlated_finding.line_number:
                    distance = abs(finding.line_number - correlated_finding.line_number)
                    if distance <= 50:
                        score += 2.0 * (1.0 - distance / 50.0)

            # Same category: +1
            if finding.category == correlated_finding.category:
                score += 1.0

            scored.append((corr_id, score))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)

        # Take top N
        top_n = scored[: self.config.max_correlated_findings]
        return {corr_id for corr_id, _ in top_n}

    def get_correlation_graph(
        self, correlations: Dict[str, List[str]]
    ) -> Dict[str, Dict[str, any]]:
        """
        Build a correlation graph structure.

        Args:
            correlations: Correlation map

        Returns:
            Graph structure with nodes and edges
        """
        nodes = set(correlations.keys())
        for corr_list in correlations.values():
            nodes.update(corr_list)

        edges = []
        for source, targets in correlations.items():
            for target in targets:
                # Only add edge if it's bidirectional (stronger correlation)
                if source in correlations.get(target, []):
                    # Avoid duplicates by ordering
                    edge = tuple(sorted([source, target]))
                    if edge not in edges:
                        edges.append(edge)

        return {
            "nodes": list(nodes),
            "edges": [{"source": e[0], "target": e[1]} for e in edges],
            "node_count": len(nodes),
            "edge_count": len(edges),
        }
