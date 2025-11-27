"""
Deduplication Engine using Semantic Similarity.

This module identifies duplicate findings across different analyzers using
semantic similarity algorithms and location-based matching.
"""

import hashlib
import re
from collections import defaultdict
from typing import Dict, List, Set, Tuple

from omniaudit.harmonizer.types import DeduplicationConfig, Finding


class Deduplicator:
    """
    Identifies and removes duplicate findings using semantic similarity.

    Uses a combination of:
    - Exact message matching
    - TF-IDF based semantic similarity
    - Location-based proximity matching
    - Rule ID matching
    """

    def __init__(self, config: DeduplicationConfig):
        """Initialize deduplicator with configuration."""
        self.config = config
        self._similarity_cache: Dict[Tuple[str, str], float] = {}

    def deduplicate(self, findings: List[Finding]) -> Tuple[List[Finding], Dict[str, str]]:
        """
        Deduplicate a list of findings.

        Args:
            findings: List of findings to deduplicate

        Returns:
            Tuple of (unique_findings, duplicate_map)
            - unique_findings: List of unique findings
            - duplicate_map: Dict mapping duplicate IDs to primary IDs
        """
        if not self.config.enabled or not findings:
            return findings, {}

        # Build similarity groups
        groups = self._build_similarity_groups(findings)

        # Select primary finding from each group
        unique_findings = []
        duplicate_map = {}

        for group in groups:
            if not group:
                continue

            # Primary is the first finding (could be enhanced with better selection)
            primary = group[0]
            unique_findings.append(primary)

            # Map duplicates to primary
            for finding in group[1:]:
                duplicate_map[finding.id] = primary.id

        return unique_findings, duplicate_map

    def _build_similarity_groups(self, findings: List[Finding]) -> List[List[Finding]]:
        """
        Build groups of similar findings.

        Args:
            findings: List of findings

        Returns:
            List of groups, where each group contains similar findings
        """
        # Track which findings have been grouped
        grouped_ids: Set[str] = set()
        groups: List[List[Finding]] = []

        for i, finding1 in enumerate(findings):
            if finding1.id in grouped_ids:
                continue

            # Start a new group
            group = [finding1]
            grouped_ids.add(finding1.id)

            # Find all similar findings
            for finding2 in findings[i + 1 :]:
                if finding2.id in grouped_ids:
                    continue

                if self._are_similar(finding1, finding2):
                    group.append(finding2)
                    grouped_ids.add(finding2.id)

            groups.append(group)

        return groups

    def _are_similar(self, finding1: Finding, finding2: Finding) -> bool:
        """
        Determine if two findings are similar enough to be duplicates.

        Args:
            finding1: First finding
            finding2: Second finding

        Returns:
            True if findings should be considered duplicates
        """
        # Quick checks first
        # Different categories are unlikely to be duplicates
        if finding1.category != finding2.category:
            return False

        # Same rule ID is a strong signal
        if finding1.rule_id and finding2.rule_id and finding1.rule_id == finding2.rule_id:
            # If same rule, check location proximity
            if self.config.consider_location:
                return self._are_locations_similar(finding1, finding2)
            return True

        # Check message similarity
        similarity = self._compute_similarity(finding1.message, finding2.message)

        if similarity < self.config.similarity_threshold:
            return False

        # Check location if enabled
        if self.config.consider_location:
            return self._are_locations_similar(finding1, finding2)

        return True

    def _are_locations_similar(self, finding1: Finding, finding2: Finding) -> bool:
        """
        Check if two findings are at similar locations.

        Args:
            finding1: First finding
            finding2: Second finding

        Returns:
            True if locations are similar
        """
        # Must be in the same file
        if finding1.file_path != finding2.file_path:
            return False

        # If no line numbers, consider them similar
        if finding1.line_number is None or finding2.line_number is None:
            return True

        # Check line distance
        line_distance = abs(finding1.line_number - finding2.line_number)
        return line_distance <= self.config.max_distance_lines

    def _compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute semantic similarity between two texts.

        Uses TF-IDF based approach for efficiency (no external dependencies).

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Check cache
        cache_key = self._get_cache_key(text1, text2)
        if cache_key in self._similarity_cache:
            return self._similarity_cache[cache_key]

        # Exact match
        if text1 == text2:
            similarity = 1.0
        elif not self.config.use_semantic:
            # Non-semantic mode: just check if one contains the other
            t1_lower = text1.lower()
            t2_lower = text2.lower()
            if t1_lower in t2_lower or t2_lower in t1_lower:
                similarity = 0.9
            else:
                similarity = 0.0
        else:
            # Semantic similarity using token-based Jaccard similarity
            similarity = self._jaccard_similarity(text1, text2)

        # Cache the result
        self._similarity_cache[cache_key] = similarity
        return similarity

    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """
        Compute Jaccard similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Jaccard similarity score (0.0 to 1.0)
        """
        # Tokenize and normalize
        tokens1 = set(self._tokenize(text1.lower()))
        tokens2 = set(self._tokenize(text2.lower()))

        if not tokens1 or not tokens2:
            return 0.0

        # Jaccard similarity: |intersection| / |union|
        intersection = tokens1 & tokens2
        union = tokens1 | tokens2

        return len(intersection) / len(union)

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words.

        Args:
            text: Text to tokenize

        Returns:
            List of tokens
        """
        # Remove special characters and split on whitespace
        text = re.sub(r"[^\w\s]", " ", text)
        tokens = text.split()

        # Filter out very short tokens
        return [t for t in tokens if len(t) > 1]

    def _get_cache_key(self, text1: str, text2: str) -> Tuple[str, str]:
        """
        Generate cache key for similarity lookup.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Tuple representing cache key (ordered)
        """
        # Use hash for efficiency with long texts
        hash1 = hashlib.md5(text1.encode()).hexdigest()
        hash2 = hashlib.md5(text2.encode()).hexdigest()

        # Always order consistently
        return tuple(sorted([hash1, hash2]))

    def get_stats(self) -> Dict[str, any]:
        """
        Get deduplication statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "cache_size": len(self._similarity_cache),
            "config": self.config.model_dump(),
        }

    def clear_cache(self) -> None:
        """Clear similarity cache."""
        self._similarity_cache.clear()
