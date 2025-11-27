"""
Type definitions for the Harmonization Engine.

This module defines all Pydantic models used throughout the harmonization process.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from omniaudit.models.ai_models import Severity


# ============================================================================
# Enums
# ============================================================================


class ConfidenceLevel(str, Enum):
    """Confidence levels for fixes and analysis."""

    VERY_HIGH = "very_high"  # 90-100%
    HIGH = "high"  # 75-89%
    MEDIUM = "medium"  # 50-74%
    LOW = "low"  # 25-49%
    VERY_LOW = "very_low"  # 0-24%


class ImpactLevel(str, Enum):
    """Impact levels for findings."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NEGLIGIBLE = "negligible"


class FixStrategy(str, Enum):
    """Auto-fix strategies."""

    AUTOMATED = "automated"  # Can be auto-applied
    SUGGESTED = "suggested"  # Needs review before applying
    MANUAL = "manual"  # Requires manual intervention
    INFEASIBLE = "infeasible"  # Cannot be automatically fixed


# ============================================================================
# Finding Models
# ============================================================================


class Finding(BaseModel):
    """Represents a single finding from an analyzer."""

    id: str = Field(description="Unique identifier for this finding")
    analyzer_name: str = Field(description="Name of the analyzer that produced this finding")
    file_path: str = Field(description="Path to the file containing the issue")
    line_number: Optional[int] = Field(None, description="Line number where issue occurs", ge=1)
    line_end: Optional[int] = Field(None, description="End line number for multi-line issues", ge=1)
    severity: Severity = Field(description="Severity level of the finding")
    rule_id: Optional[str] = Field(None, description="Rule or pattern ID")
    category: str = Field(description="Category of the finding (e.g., 'security', 'quality', 'performance')")
    message: str = Field(description="Description of the finding")
    code_snippet: Optional[str] = Field(None, description="Relevant code snippet")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class AutoFix(BaseModel):
    """Represents an automatically generated fix."""

    fix_id: str = Field(description="Unique identifier for this fix")
    finding_id: str = Field(description="ID of the finding this fix addresses")
    strategy: FixStrategy = Field(description="Fix strategy")
    description: str = Field(description="Human-readable description of the fix")
    code_change: Optional[str] = Field(None, description="Suggested code change (diff format)")
    confidence_score: float = Field(description="Confidence in this fix (0.0 to 1.0)", ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel = Field(description="Categorical confidence level")
    estimated_effort_minutes: int = Field(description="Estimated effort to apply fix", ge=0)
    risks: List[str] = Field(default_factory=list, description="Potential risks of applying this fix")
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisites before applying fix")
    validation_steps: List[str] = Field(default_factory=list, description="Steps to validate the fix")


class RootCauseInfo(BaseModel):
    """Root cause information for a finding."""

    primary_cause: str = Field(description="Primary root cause")
    contributing_factors: List[str] = Field(default_factory=list, description="Contributing factors")
    evidence: List[str] = Field(default_factory=list, description="Evidence supporting root cause")
    confidence: float = Field(description="Confidence in root cause analysis (0.0 to 1.0)", ge=0.0, le=1.0)
    related_patterns: List[str] = Field(default_factory=list, description="Related patterns in codebase")


class HarmonizedFinding(BaseModel):
    """A harmonized finding that may combine multiple raw findings."""

    id: str = Field(description="Unique ID for harmonized finding")
    original_finding_ids: List[str] = Field(description="IDs of original findings that were merged")
    file_path: str = Field(description="Primary file path")
    affected_files: List[str] = Field(default_factory=list, description="All affected files")
    line_number: Optional[int] = Field(None, description="Primary line number", ge=1)
    severity: Severity = Field(description="Harmonized severity")
    category: str = Field(description="Finding category")
    message: str = Field(description="Harmonized message")

    # Priority and impact
    priority_score: float = Field(description="Priority score (0-100)", ge=0, le=100)
    impact_level: ImpactLevel = Field(description="Overall impact level")
    business_impact: Optional[str] = Field(None, description="Business impact assessment")

    # Deduplication info
    is_duplicate: bool = Field(default=False, description="Whether this is a duplicate")
    duplicate_of: Optional[str] = Field(None, description="ID of the primary finding if duplicate")
    duplicate_count: int = Field(default=1, description="Number of duplicates merged", ge=1)

    # False positive detection
    is_false_positive: bool = Field(default=False, description="Whether likely a false positive")
    false_positive_confidence: float = Field(default=0.0, description="Confidence it's a false positive (0-1)", ge=0.0, le=1.0)
    false_positive_reasons: List[str] = Field(default_factory=list, description="Reasons for false positive classification")

    # Correlation info
    correlated_findings: List[str] = Field(default_factory=list, description="IDs of correlated findings")
    correlation_reason: Optional[str] = Field(None, description="Why findings are correlated")

    # Root cause and fixes
    root_cause: Optional[RootCauseInfo] = Field(None, description="Root cause analysis")
    auto_fixes: List[AutoFix] = Field(default_factory=list, description="Available auto-fixes")

    # Metadata
    analyzers: List[str] = Field(description="Names of analyzers that contributed")
    first_seen: str = Field(description="First occurrence timestamp")
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


# ============================================================================
# Configuration Models
# ============================================================================


class DeduplicationConfig(BaseModel):
    """Configuration for deduplication."""

    enabled: bool = Field(default=True, description="Enable deduplication")
    similarity_threshold: float = Field(default=0.85, description="Threshold for considering findings similar", ge=0.0, le=1.0)
    use_semantic: bool = Field(default=True, description="Use semantic similarity (vs exact matching)")
    consider_location: bool = Field(default=True, description="Consider file location in similarity")
    max_distance_lines: int = Field(default=10, description="Max line distance to consider duplicates", ge=0)


class CorrelationConfig(BaseModel):
    """Configuration for correlation."""

    enabled: bool = Field(default=True, description="Enable correlation")
    file_proximity_threshold: int = Field(default=3, description="Max directory depth for file proximity", ge=0)
    rule_similarity_threshold: float = Field(default=0.7, description="Threshold for rule similarity", ge=0.0, le=1.0)
    max_correlated_findings: int = Field(default=10, description="Max findings to correlate together", ge=1)


class FalsePositiveConfig(BaseModel):
    """Configuration for false positive filtering."""

    enabled: bool = Field(default=True, description="Enable false positive filtering")
    confidence_threshold: float = Field(default=0.7, description="Min confidence to mark as false positive", ge=0.0, le=1.0)
    use_ml_heuristics: bool = Field(default=True, description="Use ML-based heuristics")
    whitelist_patterns: List[str] = Field(default_factory=list, description="Patterns to whitelist")


class PriorityConfig(BaseModel):
    """Configuration for priority scoring."""

    severity_weight: float = Field(default=0.4, description="Weight for severity (0-1)", ge=0.0, le=1.0)
    frequency_weight: float = Field(default=0.2, description="Weight for frequency (0-1)", ge=0.0, le=1.0)
    impact_weight: float = Field(default=0.3, description="Weight for business impact (0-1)", ge=0.0, le=1.0)
    age_weight: float = Field(default=0.1, description="Weight for issue age (0-1)", ge=0.0, le=1.0)
    business_critical_paths: List[str] = Field(default_factory=list, description="Business-critical file paths")


class RootCauseConfig(BaseModel):
    """Configuration for root cause analysis."""

    enabled: bool = Field(default=True, description="Enable root cause analysis")
    use_ai: bool = Field(default=True, description="Use AI for root cause analysis")
    max_depth: int = Field(default=3, description="Max depth for cause chain analysis", ge=1)
    min_confidence: float = Field(default=0.5, description="Min confidence for root cause", ge=0.0, le=1.0)


class FixGenerationConfig(BaseModel):
    """Configuration for fix generation."""

    enabled: bool = Field(default=True, description="Enable fix generation")
    use_ai: bool = Field(default=True, description="Use AI for fix generation")
    max_fixes_per_finding: int = Field(default=3, description="Max fixes to generate per finding", ge=1)
    min_confidence: float = Field(default=0.6, description="Min confidence to suggest fix", ge=0.0, le=1.0)
    auto_apply_threshold: float = Field(default=0.95, description="Confidence threshold for auto-apply", ge=0.0, le=1.0)


class HarmonizationConfig(BaseModel):
    """Complete harmonization configuration."""

    deduplication: DeduplicationConfig = Field(default_factory=DeduplicationConfig)
    correlation: CorrelationConfig = Field(default_factory=CorrelationConfig)
    false_positive: FalsePositiveConfig = Field(default_factory=FalsePositiveConfig)
    priority: PriorityConfig = Field(default_factory=PriorityConfig)
    root_cause: RootCauseConfig = Field(default_factory=RootCauseConfig)
    fix_generation: FixGenerationConfig = Field(default_factory=FixGenerationConfig)

    # Caching
    enable_cache: bool = Field(default=True, description="Enable caching")
    cache_ttl_seconds: int = Field(default=3600, description="Cache TTL in seconds", ge=0)

    # AI settings
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic API key for AI features")
    ai_model: str = Field(default="claude-sonnet-4-5", description="AI model to use")


# ============================================================================
# Result Models
# ============================================================================


class HarmonizationStats(BaseModel):
    """Statistics from harmonization process."""

    total_findings: int = Field(description="Total raw findings processed", ge=0)
    harmonized_findings: int = Field(description="Number of harmonized findings", ge=0)
    duplicates_removed: int = Field(description="Number of duplicates removed", ge=0)
    false_positives_filtered: int = Field(description="Number of false positives filtered", ge=0)
    findings_correlated: int = Field(description="Number of findings correlated", ge=0)
    auto_fixes_generated: int = Field(description="Number of auto-fixes generated", ge=0)
    root_causes_identified: int = Field(description="Number of root causes identified", ge=0)
    processing_time_seconds: float = Field(description="Total processing time", ge=0.0)

    # Breakdown by severity
    by_severity: Dict[str, int] = Field(default_factory=dict, description="Count by severity level")
    by_category: Dict[str, int] = Field(default_factory=dict, description="Count by category")
    by_impact: Dict[str, int] = Field(default_factory=dict, description="Count by impact level")


class HarmonizationResult(BaseModel):
    """Result of harmonization process."""

    findings: List[HarmonizedFinding] = Field(description="Harmonized findings")
    stats: HarmonizationStats = Field(description="Processing statistics")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    config_used: HarmonizationConfig = Field(description="Configuration used for harmonization")
    errors: List[str] = Field(default_factory=list, description="Errors encountered during processing")
    warnings: List[str] = Field(default_factory=list, description="Warnings during processing")
