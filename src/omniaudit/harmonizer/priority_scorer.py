"""
Priority Scorer with Business Context.

This module assigns priority scores to findings based on multiple factors including
severity, frequency, business impact, and issue age.
"""

import os
from collections import Counter
from datetime import datetime
from typing import Dict, List

from omniaudit.harmonizer.types import Finding, ImpactLevel, PriorityConfig, Severity


class PriorityScorer:
    """
    Scores findings based on multiple factors to determine remediation priority.

    Scoring factors:
    1. Severity (CRITICAL > HIGH > MEDIUM > LOW > INFO)
    2. Frequency (how many times the same issue appears)
    3. Business impact (based on file location)
    4. Issue age (older issues may be less critical if not exploited)
    """

    # Severity score mapping
    SEVERITY_SCORES = {
        Severity.CRITICAL: 100.0,
        Severity.HIGH: 75.0,
        Severity.MEDIUM: 50.0,
        Severity.LOW: 25.0,
        Severity.INFO: 10.0,
    }

    # Impact level mapping
    IMPACT_LEVELS = {
        (90, 100): ImpactLevel.CRITICAL,
        (70, 90): ImpactLevel.HIGH,
        (40, 70): ImpactLevel.MEDIUM,
        (20, 40): ImpactLevel.LOW,
        (0, 20): ImpactLevel.NEGLIGIBLE,
    }

    def __init__(self, config: PriorityConfig):
        """Initialize priority scorer with configuration."""
        self.config = config
        self._validate_weights()

    def _validate_weights(self) -> None:
        """Ensure weights sum to approximately 1.0."""
        total = (
            self.config.severity_weight
            + self.config.frequency_weight
            + self.config.impact_weight
            + self.config.age_weight
        )

        # Allow small tolerance for floating point
        if abs(total - 1.0) > 0.01:
            raise ValueError(
                f"Priority weights must sum to 1.0, got {total}. "
                f"Adjust severity_weight, frequency_weight, impact_weight, and age_weight."
            )

    def score_findings(
        self, findings: List[Finding]
    ) -> Dict[str, tuple[float, ImpactLevel, str]]:
        """
        Score all findings and assign priority.

        Args:
            findings: List of findings to score

        Returns:
            Dict mapping finding IDs to (priority_score, impact_level, business_impact)
        """
        if not findings:
            return {}

        # Calculate frequency of each rule/category
        rule_frequency = self._calculate_frequency(findings, "rule_id")
        category_frequency = self._calculate_frequency(findings, "category")

        scores = {}
        for finding in findings:
            priority_score = self._calculate_priority_score(
                finding, rule_frequency, category_frequency
            )

            impact_level = self._get_impact_level(priority_score)
            business_impact = self._assess_business_impact(finding)

            scores[finding.id] = (priority_score, impact_level, business_impact)

        return scores

    def score_finding(self, finding: Finding, all_findings: List[Finding]) -> float:
        """
        Score a single finding.

        Args:
            finding: Finding to score
            all_findings: All findings (for frequency calculation)

        Returns:
            Priority score (0-100)
        """
        rule_frequency = self._calculate_frequency(all_findings, "rule_id")
        category_frequency = self._calculate_frequency(all_findings, "category")

        return self._calculate_priority_score(finding, rule_frequency, category_frequency)

    def _calculate_priority_score(
        self,
        finding: Finding,
        rule_frequency: Counter,
        category_frequency: Counter,
    ) -> float:
        """
        Calculate priority score for a finding.

        Args:
            finding: Finding to score
            rule_frequency: Frequency counter for rule IDs
            category_frequency: Frequency counter for categories

        Returns:
            Priority score (0-100)
        """
        # Component 1: Severity score
        severity_score = self.SEVERITY_SCORES.get(finding.severity, 50.0)

        # Component 2: Frequency score
        frequency_score = self._calculate_frequency_score(
            finding, rule_frequency, category_frequency
        )

        # Component 3: Business impact score
        impact_score = self._calculate_impact_score(finding)

        # Component 4: Age score (penalize very old or very new issues differently)
        age_score = self._calculate_age_score(finding)

        # Weighted combination
        total_score = (
            severity_score * self.config.severity_weight
            + frequency_score * self.config.frequency_weight
            + impact_score * self.config.impact_weight
            + age_score * self.config.age_weight
        )

        # Ensure score is in 0-100 range
        return max(0.0, min(100.0, total_score))

    def _calculate_frequency(self, findings: List[Finding], field: str) -> Counter:
        """
        Calculate frequency of values for a field.

        Args:
            findings: List of findings
            field: Field name to count

        Returns:
            Counter of field values
        """
        values = []
        for finding in findings:
            value = getattr(finding, field, None)
            if value:
                values.append(value)

        return Counter(values)

    def _calculate_frequency_score(
        self,
        finding: Finding,
        rule_frequency: Counter,
        category_frequency: Counter,
    ) -> float:
        """
        Calculate frequency-based score.

        More frequent issues get higher scores (systemic problems).

        Args:
            finding: Finding to score
            rule_frequency: Rule frequency counter
            category_frequency: Category frequency counter

        Returns:
            Frequency score (0-100)
        """
        # Get frequency counts
        rule_count = rule_frequency.get(finding.rule_id, 1) if finding.rule_id else 1
        category_count = category_frequency.get(finding.category, 1)

        # Calculate score based on frequency
        # Use logarithmic scale to avoid extreme values
        import math

        # Rule frequency (more weight)
        rule_score = min(100.0, 30.0 * math.log10(rule_count + 1))

        # Category frequency (less weight)
        category_score = min(50.0, 20.0 * math.log10(category_count + 1))

        return rule_score + category_score

    def _calculate_impact_score(self, finding: Finding) -> float:
        """
        Calculate business impact score based on file location.

        Args:
            finding: Finding to score

        Returns:
            Impact score (0-100)
        """
        score = 50.0  # Default medium impact

        # Check if file is in business-critical paths
        file_path = finding.file_path.lower()

        for critical_path in self.config.business_critical_paths:
            if critical_path.lower() in file_path:
                score = 100.0
                break

        # Heuristic-based impact assessment
        # Security issues in authentication/authorization code
        if finding.category in ["security", "vulnerability"]:
            if any(
                keyword in file_path
                for keyword in ["auth", "login", "password", "token", "session"]
            ):
                score = max(score, 95.0)

        # Issues in API/service layer
        if any(keyword in file_path for keyword in ["api", "service", "controller", "route"]):
            score = max(score, 80.0)

        # Issues in database layer
        if any(keyword in file_path for keyword in ["db", "database", "model", "migration"]):
            score = max(score, 75.0)

        # Issues in core/util code (high reuse)
        if any(keyword in file_path for keyword in ["core", "util", "lib", "shared"]):
            score = max(score, 70.0)

        # Issues in tests are lower priority
        if any(keyword in file_path for keyword in ["test", "spec", "mock"]):
            score = min(score, 30.0)

        # Issues in documentation are lowest priority
        if any(keyword in file_path for keyword in [".md", "readme", "doc"]):
            score = min(score, 20.0)

        return score

    def _calculate_age_score(self, finding: Finding) -> float:
        """
        Calculate age-based score.

        Newer issues get higher priority (easier to fix in context).
        Very old issues may indicate lower actual risk if not exploited.

        Args:
            finding: Finding to score

        Returns:
            Age score (0-100)
        """
        try:
            # Parse timestamp
            timestamp = datetime.fromisoformat(finding.timestamp.replace("Z", "+00:00"))
            now = datetime.now(timestamp.tzinfo)

            # Calculate age in days
            age_days = (now - timestamp).total_seconds() / (24 * 3600)

            # Scoring logic:
            # - 0-7 days: 100 (very fresh, fix immediately)
            # - 7-30 days: 80 (recent, high priority)
            # - 30-90 days: 60 (medium age, medium priority)
            # - 90+ days: 40 (old, may be accepted risk)

            if age_days <= 7:
                return 100.0
            elif age_days <= 30:
                return 80.0
            elif age_days <= 90:
                return 60.0
            else:
                return 40.0

        except (ValueError, AttributeError):
            # If timestamp is invalid or missing, assume medium priority
            return 70.0

    def _get_impact_level(self, priority_score: float) -> ImpactLevel:
        """
        Convert priority score to impact level.

        Args:
            priority_score: Priority score (0-100)

        Returns:
            ImpactLevel enum
        """
        for (min_score, max_score), level in self.IMPACT_LEVELS.items():
            if min_score <= priority_score < max_score:
                return level

        # Fallback
        return ImpactLevel.MEDIUM

    def _assess_business_impact(self, finding: Finding) -> str:
        """
        Generate business impact assessment text.

        Args:
            finding: Finding to assess

        Returns:
            Business impact description
        """
        file_path = finding.file_path.lower()

        # Critical business areas
        if any(
            keyword in file_path
            for keyword in ["payment", "billing", "checkout", "transaction"]
        ):
            return "Critical: Affects payment/transaction processing"

        if any(keyword in file_path for keyword in ["auth", "login", "security"]):
            return "High: Affects authentication/authorization"

        if any(keyword in file_path for keyword in ["api", "service"]):
            return "Medium: Affects API/service functionality"

        if any(keyword in file_path for keyword in ["ui", "view", "component"]):
            return "Medium: Affects user interface"

        if any(keyword in file_path for keyword in ["test", "spec"]):
            return "Low: Affects test code only"

        # Default
        return f"Medium: Affects {finding.category} in {os.path.basename(finding.file_path)}"

    def get_priority_distribution(
        self, scores: Dict[str, tuple[float, ImpactLevel, str]]
    ) -> Dict[str, any]:
        """
        Get distribution statistics for scored findings.

        Args:
            scores: Scored findings

        Returns:
            Distribution statistics
        """
        if not scores:
            return {
                "total": 0,
                "by_impact": {},
                "avg_score": 0.0,
                "score_ranges": {},
            }

        priority_scores = [score for score, _, _ in scores.values()]
        impact_counts = Counter(impact for _, impact, _ in scores.values())

        # Score ranges
        ranges = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for score in priority_scores:
            if score >= 90:
                ranges["critical"] += 1
            elif score >= 70:
                ranges["high"] += 1
            elif score >= 40:
                ranges["medium"] += 1
            else:
                ranges["low"] += 1

        return {
            "total": len(scores),
            "by_impact": dict(impact_counts),
            "avg_score": sum(priority_scores) / len(priority_scores),
            "min_score": min(priority_scores),
            "max_score": max(priority_scores),
            "score_ranges": ranges,
        }
