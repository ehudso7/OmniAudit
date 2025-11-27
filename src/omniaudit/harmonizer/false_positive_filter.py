"""
False Positive Filter using ML-based Heuristics.

This module identifies likely false positives using heuristic-based machine learning
techniques, including pattern recognition, anomaly detection, and historical analysis.
"""

import re
from typing import Dict, List, Tuple

from omniaudit.harmonizer.types import FalsePositiveConfig, Finding, Severity


class FalsePositiveFilter:
    """
    Filters out likely false positive findings using ML heuristics.

    Uses multiple heuristic strategies:
    1. Pattern-based whitelisting (test files, generated code, etc.)
    2. Severity-message consistency checking
    3. Statistical anomaly detection
    4. Known false positive patterns
    """

    # Common patterns that often produce false positives
    FALSE_POSITIVE_PATTERNS = {
        "test_files": [
            r"/tests?/",
            r"/test_.*\.py$",
            r"_test\.py$",
            r"\.test\.js$",
            r"\.spec\.ts$",
            r"/mock",
            r"/fixtures/",
        ],
        "generated_code": [
            r"/node_modules/",
            r"/vendor/",
            r"\.generated\.",
            r"/dist/",
            r"/build/",
            r"/__pycache__/",
            r"\.pyc$",
            r"/\.next/",
        ],
        "config_files": [
            r"\.config\.",
            r"\.json$",
            r"\.yaml$",
            r"\.yml$",
            r"\.toml$",
            r"\.ini$",
        ],
        "documentation": [
            r"README",
            r"\.md$",
            r"/docs/",
            r"CHANGELOG",
            r"LICENSE",
        ],
    }

    # Messages that are often false positives
    FALSE_POSITIVE_MESSAGES = [
        r"todo.*comment",  # TODO comments are often intentional
        r"missing.*docstring.*test",  # Test functions don't always need docstrings
        r"line.*too.*long.*comment",  # Long comment lines are acceptable
        r"unused.*parameter.*self",  # Common in class methods
        r"too.*few.*public.*methods",  # Intentional design choice
    ]

    def __init__(self, config: FalsePositiveConfig):
        """Initialize false positive filter with configuration."""
        self.config = config
        self._compiled_patterns = self._compile_patterns()
        self._compiled_messages = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.FALSE_POSITIVE_MESSAGES
        ]

    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Compile regex patterns for efficiency."""
        compiled = {}
        for category, patterns in self.FALSE_POSITIVE_PATTERNS.items():
            compiled[category] = [re.compile(pattern) for pattern in patterns]
        return compiled

    def filter(self, findings: List[Finding]) -> Tuple[List[Finding], List[Finding]]:
        """
        Filter findings to separate likely false positives.

        Args:
            findings: List of findings to filter

        Returns:
            Tuple of (valid_findings, false_positives)
        """
        if not self.config.enabled:
            return findings, []

        valid_findings = []
        false_positives = []

        for finding in findings:
            is_fp, confidence, reasons = self._is_false_positive(finding)

            if is_fp and confidence >= self.config.confidence_threshold:
                false_positives.append(finding)
            else:
                valid_findings.append(finding)

        return valid_findings, false_positives

    def analyze_finding(self, finding: Finding) -> Tuple[bool, float, List[str]]:
        """
        Analyze a single finding for false positive likelihood.

        Args:
            finding: Finding to analyze

        Returns:
            Tuple of (is_false_positive, confidence, reasons)
        """
        return self._is_false_positive(finding)

    def _is_false_positive(self, finding: Finding) -> Tuple[bool, float, List[str]]:
        """
        Determine if a finding is likely a false positive.

        Args:
            finding: Finding to check

        Returns:
            Tuple of (is_false_positive, confidence, reasons)
        """
        confidence_scores = []
        reasons = []

        # Check whitelisted patterns
        for pattern in self.config.whitelist_patterns:
            if re.search(pattern, finding.file_path, re.IGNORECASE):
                confidence_scores.append(0.9)
                reasons.append(f"Matches whitelist pattern: {pattern}")

        # Check if in test files
        if self._matches_category("test_files", finding.file_path):
            # Test files with low severity issues are often false positives
            if finding.severity in [Severity.LOW, Severity.INFO]:
                confidence_scores.append(0.8)
                reasons.append("Low severity issue in test file")

        # Check if in generated code
        if self._matches_category("generated_code", finding.file_path):
            confidence_scores.append(0.95)
            reasons.append("Finding in generated/third-party code")

        # Check if in documentation
        if self._matches_category("documentation", finding.file_path):
            if finding.category not in ["security", "vulnerability"]:
                confidence_scores.append(0.85)
                reasons.append("Non-security issue in documentation")

        # Check message patterns
        for pattern in self._compiled_messages:
            if pattern.search(finding.message):
                confidence_scores.append(0.7)
                reasons.append(f"Message matches known false positive pattern")
                break

        # Check severity-message consistency
        consistency_score = self._check_severity_consistency(finding)
        if consistency_score < 0.5:
            confidence_scores.append(0.6)
            reasons.append("Severity doesn't match message severity")

        # Use ML heuristics if enabled
        if self.config.use_ml_heuristics:
            ml_score = self._apply_ml_heuristics(finding)
            if ml_score > 0.5:
                confidence_scores.append(ml_score)
                reasons.append(f"ML heuristic score: {ml_score:.2f}")

        # Calculate overall confidence
        if not confidence_scores:
            return False, 0.0, []

        # Take the maximum confidence score
        confidence = max(confidence_scores)

        is_fp = confidence >= self.config.confidence_threshold
        return is_fp, confidence, reasons

    def _matches_category(self, category: str, file_path: str) -> bool:
        """
        Check if file path matches a pattern category.

        Args:
            category: Pattern category name
            file_path: File path to check

        Returns:
            True if matches any pattern in category
        """
        if category not in self._compiled_patterns:
            return False

        for pattern in self._compiled_patterns[category]:
            if pattern.search(file_path):
                return True

        return False

    def _check_severity_consistency(self, finding: Finding) -> float:
        """
        Check if severity is consistent with message content.

        Args:
            finding: Finding to check

        Returns:
            Consistency score (0.0 to 1.0)
        """
        message_lower = finding.message.lower()

        # High severity indicators
        high_severity_words = [
            "critical",
            "security",
            "vulnerability",
            "exploit",
            "injection",
            "unsafe",
            "dangerous",
        ]

        # Low severity indicators
        low_severity_words = [
            "style",
            "formatting",
            "convention",
            "suggestion",
            "prefer",
            "consider",
            "could",
        ]

        has_high_indicators = any(word in message_lower for word in high_severity_words)
        has_low_indicators = any(word in message_lower for word in low_severity_words)

        # Check consistency
        if finding.severity in [Severity.CRITICAL, Severity.HIGH]:
            if has_high_indicators:
                return 1.0  # Consistent
            elif has_low_indicators:
                return 0.2  # Inconsistent
            else:
                return 0.6  # Neutral
        elif finding.severity in [Severity.LOW, Severity.INFO]:
            if has_low_indicators:
                return 1.0  # Consistent
            elif has_high_indicators:
                return 0.2  # Inconsistent
            else:
                return 0.6  # Neutral
        else:
            return 0.7  # Medium severity - usually consistent

    def _apply_ml_heuristics(self, finding: Finding) -> float:
        """
        Apply ML-based heuristics to detect false positives.

        Uses a simple scoring system based on multiple features:
        - Message length and complexity
        - File path characteristics
        - Rule ID patterns
        - Category patterns

        Args:
            finding: Finding to analyze

        Returns:
            False positive probability (0.0 to 1.0)
        """
        score = 0.0

        # Feature 1: Message length (very short messages are often generic)
        message_length = len(finding.message.split())
        if message_length < 3:
            score += 0.2

        # Feature 2: Generic messages (contain words like "error", "warning", "issue")
        generic_words = ["error", "warning", "issue", "problem", "invalid"]
        generic_count = sum(
            1 for word in generic_words if word in finding.message.lower()
        )
        if generic_count > 0 and message_length < 8:
            score += 0.15

        # Feature 3: File depth (very deep paths in node_modules, etc.)
        path_depth = finding.file_path.count(os.sep)
        if path_depth > 8:
            score += 0.1

        # Feature 4: Rule ID patterns (some tools have known false positive rules)
        if finding.rule_id:
            # Example: rules ending in "001" are often too generic
            if finding.rule_id.endswith("001"):
                score += 0.05

        # Feature 5: Category + Severity combination
        # Low severity "style" issues are often false positives
        if finding.category == "style" and finding.severity == Severity.LOW:
            score += 0.15

        # Feature 6: Info severity findings without specific details
        if finding.severity == Severity.INFO and message_length < 10:
            score += 0.2

        # Normalize score to 0-1 range
        return min(score, 1.0)

    def get_filter_stats(
        self, original_count: int, filtered_count: int, false_positive_count: int
    ) -> Dict[str, any]:
        """
        Generate filter statistics.

        Args:
            original_count: Original finding count
            filtered_count: Count after filtering
            false_positive_count: Count of false positives removed

        Returns:
            Statistics dictionary
        """
        reduction_rate = (
            (false_positive_count / original_count * 100) if original_count > 0 else 0
        )

        return {
            "original_count": original_count,
            "filtered_count": filtered_count,
            "false_positives_removed": false_positive_count,
            "reduction_rate_percent": round(reduction_rate, 2),
            "filter_enabled": self.config.enabled,
            "confidence_threshold": self.config.confidence_threshold,
        }


# Import os for path operations
import os
