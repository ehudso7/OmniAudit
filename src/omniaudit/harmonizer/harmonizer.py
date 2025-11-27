"""
Main Harmonization Engine.

This module orchestrates the harmonization process, coordinating deduplication,
correlation, false positive filtering, priority scoring, root cause analysis,
and fix generation.
"""

import time
import uuid
from collections import Counter
from datetime import datetime
from typing import Dict, List, Optional

from omniaudit.harmonizer.correlator import Correlator
from omniaudit.harmonizer.deduplicator import Deduplicator
from omniaudit.harmonizer.false_positive_filter import FalsePositiveFilter
from omniaudit.harmonizer.fix_generator import FixGenerator
from omniaudit.harmonizer.priority_scorer import PriorityScorer
from omniaudit.harmonizer.root_cause_analyzer import RootCauseAnalyzer
from omniaudit.harmonizer.types import (
    Finding,
    HarmonizationConfig,
    HarmonizationResult,
    HarmonizationStats,
    HarmonizedFinding,
)


class Harmonizer:
    """
    Main harmonization engine that processes findings through multiple stages.

    Processing stages:
    1. Deduplication - Remove duplicate findings
    2. False Positive Filtering - Filter out likely false positives
    3. Correlation - Identify related findings
    4. Priority Scoring - Assign priority scores
    5. Root Cause Analysis - Identify root causes
    6. Fix Generation - Generate automatic fixes
    """

    def __init__(self, config: Optional[HarmonizationConfig] = None):
        """
        Initialize harmonizer with configuration.

        Args:
            config: Harmonization configuration (uses defaults if not provided)
        """
        self.config = config or HarmonizationConfig()

        # Initialize components
        self.deduplicator = Deduplicator(self.config.deduplication)
        self.correlator = Correlator(self.config.correlation)
        self.false_positive_filter = FalsePositiveFilter(self.config.false_positive)
        self.priority_scorer = PriorityScorer(self.config.priority)
        self.root_cause_analyzer = RootCauseAnalyzer(
            self.config.root_cause, self.config.anthropic_api_key
        )
        self.fix_generator = FixGenerator(
            self.config.fix_generation, self.config.anthropic_api_key
        )

    def harmonize(self, findings: List[Finding]) -> HarmonizationResult:
        """
        Harmonize a list of findings.

        Args:
            findings: Raw findings from analyzers

        Returns:
            HarmonizationResult with harmonized findings and statistics
        """
        start_time = time.time()
        errors = []
        warnings = []

        # Track original count
        original_count = len(findings)

        # Stage 1: Deduplication
        try:
            unique_findings, duplicate_map = self.deduplicator.deduplicate(findings)
            duplicates_removed = original_count - len(unique_findings)
        except Exception as e:
            errors.append(f"Deduplication error: {str(e)}")
            unique_findings = findings
            duplicate_map = {}
            duplicates_removed = 0

        # Stage 2: False Positive Filtering
        try:
            valid_findings, false_positives = self.false_positive_filter.filter(unique_findings)
            false_positives_count = len(false_positives)
        except Exception as e:
            errors.append(f"False positive filtering error: {str(e)}")
            valid_findings = unique_findings
            false_positives_count = 0

        # Stage 3: Correlation
        try:
            correlations = self.correlator.correlate(valid_findings)
            findings_correlated = sum(1 for corr in correlations.values() if corr)
        except Exception as e:
            errors.append(f"Correlation error: {str(e)}")
            correlations = {}
            findings_correlated = 0

        # Stage 4: Priority Scoring
        try:
            priority_scores = self.priority_scorer.score_findings(valid_findings)
        except Exception as e:
            errors.append(f"Priority scoring error: {str(e)}")
            priority_scores = {}

        # Stage 5: Root Cause Analysis
        try:
            root_causes = self.root_cause_analyzer.analyze_batch(valid_findings, correlations)
            root_causes_count = sum(1 for rc in root_causes.values() if rc)
        except Exception as e:
            errors.append(f"Root cause analysis error: {str(e)}")
            root_causes = {}
            root_causes_count = 0

        # Stage 6: Fix Generation
        auto_fixes_count = 0
        all_fixes = {}
        try:
            for finding in valid_findings:
                root_cause = root_causes.get(finding.id)
                fixes = self.fix_generator.generate_fixes(finding, root_cause)
                if fixes:
                    all_fixes[finding.id] = fixes
                    auto_fixes_count += len(fixes)
        except Exception as e:
            errors.append(f"Fix generation error: {str(e)}")

        # Stage 7: Build harmonized findings
        harmonized = self._build_harmonized_findings(
            valid_findings,
            duplicate_map,
            correlations,
            priority_scores,
            root_causes,
            all_fixes,
        )

        # Calculate statistics
        processing_time = time.time() - start_time
        stats = self._build_stats(
            original_count,
            harmonized,
            duplicates_removed,
            false_positives_count,
            findings_correlated,
            auto_fixes_count,
            root_causes_count,
            processing_time,
        )

        return HarmonizationResult(
            findings=harmonized,
            stats=stats,
            config_used=self.config,
            errors=errors,
            warnings=warnings,
        )

    def _build_harmonized_findings(
        self,
        findings: List[Finding],
        duplicate_map: Dict[str, str],
        correlations: Dict[str, List[str]],
        priority_scores: Dict[str, tuple],
        root_causes: Dict[str, any],
        all_fixes: Dict[str, List],
    ) -> List[HarmonizedFinding]:
        """
        Build harmonized findings from processed data.

        Args:
            findings: Valid findings
            duplicate_map: Duplicate mapping
            correlations: Correlation mapping
            priority_scores: Priority scores
            root_causes: Root cause analysis
            all_fixes: Generated fixes

        Returns:
            List of HarmonizedFinding objects
        """
        harmonized = []

        # Build finding lookup
        finding_map = {f.id: f for f in findings}

        for finding in findings:
            # Get data for this finding
            correlated_ids = correlations.get(finding.id, [])
            score_data = priority_scores.get(finding.id)
            root_cause = root_causes.get(finding.id)
            fixes = all_fixes.get(finding.id, [])

            # Check if this finding is a duplicate
            is_duplicate = finding.id in duplicate_map.values()
            duplicate_of = None
            duplicate_count = 1

            if is_duplicate:
                # Find the primary finding
                for dup_id, primary_id in duplicate_map.items():
                    if primary_id == finding.id:
                        duplicate_count += 1
                        break

            # Extract priority data
            if score_data:
                priority_score, impact_level, business_impact = score_data
            else:
                priority_score = 50.0
                impact_level = None
                business_impact = None

            # Build affected files list
            affected_files = [finding.file_path]
            for corr_id in correlated_ids[:5]:  # Limit to 5
                if corr_id in finding_map:
                    corr_finding = finding_map[corr_id]
                    if corr_finding.file_path not in affected_files:
                        affected_files.append(corr_finding.file_path)

            # Create harmonized finding
            harmonized_finding = HarmonizedFinding(
                id=finding.id,
                original_finding_ids=[finding.id],
                file_path=finding.file_path,
                affected_files=affected_files,
                line_number=finding.line_number,
                severity=finding.severity,
                category=finding.category,
                message=finding.message,
                priority_score=priority_score,
                impact_level=impact_level,
                business_impact=business_impact,
                is_duplicate=is_duplicate,
                duplicate_of=duplicate_of,
                duplicate_count=duplicate_count,
                is_false_positive=False,  # Already filtered out
                false_positive_confidence=0.0,
                false_positive_reasons=[],
                correlated_findings=correlated_ids,
                correlation_reason=(
                    f"{len(correlated_ids)} related findings identified"
                    if correlated_ids
                    else None
                ),
                root_cause=root_cause,
                auto_fixes=fixes,
                analyzers=[finding.analyzer_name],
                first_seen=finding.timestamp,
                metadata=finding.metadata,
            )

            harmonized.append(harmonized_finding)

        # Sort by priority score (descending)
        harmonized.sort(key=lambda f: f.priority_score, reverse=True)

        return harmonized

    def _build_stats(
        self,
        original_count: int,
        harmonized: List[HarmonizedFinding],
        duplicates_removed: int,
        false_positives_count: int,
        findings_correlated: int,
        auto_fixes_count: int,
        root_causes_count: int,
        processing_time: float,
    ) -> HarmonizationStats:
        """
        Build harmonization statistics.

        Args:
            original_count: Original finding count
            harmonized: Harmonized findings
            duplicates_removed: Number of duplicates removed
            false_positives_count: Number of false positives filtered
            findings_correlated: Number of correlated findings
            auto_fixes_count: Number of auto-fixes generated
            root_causes_count: Number of root causes identified
            processing_time: Processing time in seconds

        Returns:
            HarmonizationStats
        """
        # Count by severity
        by_severity = Counter(f.severity.value for f in harmonized)

        # Count by category
        by_category = Counter(f.category for f in harmonized)

        # Count by impact
        by_impact = Counter(
            f.impact_level.value for f in harmonized if f.impact_level
        )

        return HarmonizationStats(
            total_findings=original_count,
            harmonized_findings=len(harmonized),
            duplicates_removed=duplicates_removed,
            false_positives_filtered=false_positives_count,
            findings_correlated=findings_correlated,
            auto_fixes_generated=auto_fixes_count,
            root_causes_identified=root_causes_count,
            processing_time_seconds=processing_time,
            by_severity=dict(by_severity),
            by_category=dict(by_category),
            by_impact=dict(by_impact),
        )

    def harmonize_incremental(
        self, new_findings: List[Finding], previous_result: HarmonizationResult
    ) -> HarmonizationResult:
        """
        Incrementally harmonize new findings with previous results.

        Args:
            new_findings: New findings to harmonize
            previous_result: Previous harmonization result

        Returns:
            Updated HarmonizationResult
        """
        # Convert previous harmonized findings back to Finding objects
        # (simplified - in production, maintain full history)
        all_findings = new_findings

        # Run full harmonization
        # In production, this could be optimized to only process new findings
        return self.harmonize(all_findings)

    def get_top_priority_findings(
        self, result: HarmonizationResult, limit: int = 10
    ) -> List[HarmonizedFinding]:
        """
        Get top priority findings from result.

        Args:
            result: Harmonization result
            limit: Maximum number of findings to return

        Returns:
            Top priority findings
        """
        # Already sorted by priority in harmonize()
        return result.findings[:limit]

    def get_findings_by_category(
        self, result: HarmonizationResult, category: str
    ) -> List[HarmonizedFinding]:
        """
        Get findings filtered by category.

        Args:
            result: Harmonization result
            category: Category to filter by

        Returns:
            Findings in the specified category
        """
        return [f for f in result.findings if f.category == category]

    def get_auto_fixable_findings(
        self, result: HarmonizationResult
    ) -> List[HarmonizedFinding]:
        """
        Get findings that have high-confidence auto-fixes.

        Args:
            result: Harmonization result

        Returns:
            Findings with auto-fixable issues
        """
        return [
            f
            for f in result.findings
            if f.auto_fixes
            and any(
                fix.confidence_score >= self.config.fix_generation.auto_apply_threshold
                for fix in f.auto_fixes
            )
        ]

    def export_summary(self, result: HarmonizationResult) -> Dict[str, any]:
        """
        Export a summary of harmonization results.

        Args:
            result: Harmonization result

        Returns:
            Summary dictionary
        """
        return {
            "timestamp": result.timestamp,
            "statistics": result.stats.model_dump(),
            "top_priorities": [
                {
                    "id": f.id,
                    "category": f.category,
                    "severity": f.severity.value,
                    "priority_score": f.priority_score,
                    "message": f.message[:100],
                    "file": f.file_path,
                    "has_fix": len(f.auto_fixes) > 0,
                }
                for f in result.findings[:10]
            ],
            "errors": result.errors,
            "warnings": result.warnings,
        }
