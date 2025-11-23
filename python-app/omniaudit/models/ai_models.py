"""
Pydantic models for AI-enhanced features using Anthropic Structured Outputs.

These models define the structured output schemas for all AI-powered features
in OmniAudit. They guarantee type-safe, schema-compliant responses from Claude API.

See ADR-004 for architectural decision details.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Enums for structured categories
# ============================================================================


class Severity(str, Enum):
    """Severity levels for issues and anomalies."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class HealthStatus(str, Enum):
    """Overall health status categories."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class ProjectType(str, Enum):
    """Detected project types for intelligent configuration."""

    WEB_APP = "web_app"
    MICROSERVICE = "microservice"
    LIBRARY = "library"
    MONOLITH = "monolith"
    CLI_TOOL = "cli_tool"
    MOBILE_APP = "mobile_app"
    UNKNOWN = "unknown"


class VisualizationType(str, Enum):
    """Suggested visualization types for query results."""

    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    TABLE = "table"
    SINGLE_VALUE = "single_value"
    HEATMAP = "heatmap"
    SCATTER_PLOT = "scatter_plot"


class ResultType(str, Enum):
    """Types of natural language query results."""

    METRIC = "metric"
    TREND = "trend"
    COMPARISON = "comparison"
    RECOMMENDATION = "recommendation"
    SUMMARY = "summary"


# ============================================================================
# Code Quality & Analysis Models
# ============================================================================


class CodeSmell(BaseModel):
    """Represents a detected code smell or anti-pattern."""

    file_path: str = Field(description="Path to the file containing the issue")
    line_number: int = Field(description="Line number where issue starts", ge=1)
    line_end: Optional[int] = Field(
        None, description="Line number where issue ends (for multi-line issues)", ge=1
    )
    severity: Severity = Field(description="Impact level of this code smell")
    smell_type: str = Field(
        description="Type of code smell (e.g., 'long_method', 'duplicated_code', 'large_class')"
    )
    description: str = Field(description="Human-readable explanation of the issue")
    recommendation: str = Field(description="Suggested fix or refactoring approach")
    estimated_effort_minutes: Optional[int] = Field(
        None, description="Estimated time to fix in minutes", ge=0
    )
    related_files: List[str] = Field(
        default_factory=list, description="Other files affected by this issue"
    )

    @field_validator("line_end")
    @classmethod
    def validate_line_end(cls, v: Optional[int], info) -> Optional[int]:
        """Ensure line_end is greater than or equal to line_number."""
        if v is not None and "line_number" in info.data:
            if v < info.data["line_number"]:
                raise ValueError("line_end must be >= line_number")
        return v


class AIInsightsResult(BaseModel):
    """Structured output from AI-powered code analysis."""

    project_id: str = Field(description="Unique identifier for the analyzed project")
    analyzed_at: str = Field(description="ISO 8601 timestamp of analysis")
    code_smells: List[CodeSmell] = Field(
        default_factory=list, description="List of detected code quality issues"
    )
    technical_debt_score: float = Field(
        description="Overall technical debt score from 0 (worst) to 100 (perfect)", ge=0, le=100
    )
    maintainability_index: float = Field(
        description="Code maintainability index from 0 to 100", ge=0, le=100
    )
    test_coverage_assessment: str = Field(
        description="Qualitative assessment of test coverage adequacy"
    )
    architecture_assessment: str = Field(
        description="High-level assessment of architectural quality"
    )
    summary: str = Field(description="Executive summary of code quality state")
    priority_actions: List[str] = Field(
        description="Top 3-5 recommended actions, ordered by priority", max_length=5
    )
    estimated_remediation_hours: Optional[float] = Field(
        None, description="Total estimated hours to address all issues", ge=0
    )

    @field_validator("analyzed_at")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        """Validate that analyzed_at is a valid ISO 8601 timestamp."""
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError as e:
            raise ValueError(f"Invalid ISO 8601 timestamp: {v}") from e
        return v


# ============================================================================
# Anomaly Detection Models
# ============================================================================


class Anomaly(BaseModel):
    """Represents a detected anomaly in metrics."""

    metric_name: str = Field(description="Name of the metric showing anomalous behavior")
    expected_range: Tuple[float, float] = Field(
        description="Expected (min, max) range for this metric"
    )
    actual_value: float = Field(description="The actual observed value")
    deviation_percentage: float = Field(
        description="Percentage deviation from expected range", ge=0
    )
    timestamp: str = Field(description="ISO 8601 timestamp when anomaly was detected")
    severity: Severity = Field(description="Severity level of this anomaly")
    likely_cause: str = Field(description="AI-generated hypothesis for the root cause")
    affected_components: List[str] = Field(
        description="System components likely affected by this anomaly"
    )
    recommended_actions: List[str] = Field(
        description="Suggested remediation steps", max_length=3
    )
    confidence_score: float = Field(
        description="Confidence in the analysis from 0 to 1", ge=0, le=1
    )

    @field_validator("expected_range")
    @classmethod
    def validate_range(cls, v: Tuple[float, float]) -> Tuple[float, float]:
        """Ensure expected_range has min <= max."""
        if v[0] > v[1]:
            raise ValueError("expected_range min must be <= max")
        return v


class AnomalyReport(BaseModel):
    """Complete anomaly detection report."""

    scan_timestamp: str = Field(description="ISO 8601 timestamp of the scan")
    time_window_hours: int = Field(description="Time window analyzed in hours", ge=1)
    anomalies_detected: int = Field(description="Total number of anomalies found", ge=0)
    anomalies: List[Anomaly] = Field(description="Detailed list of anomalies")
    overall_health: HealthStatus = Field(description="Overall system health assessment")
    health_trend: str = Field(
        description="Trend assessment: 'improving', 'stable', 'degrading'"
    )
    recommended_actions: List[str] = Field(
        description="Top recommended actions across all anomalies", max_length=5
    )
    false_positive_likelihood: float = Field(
        description="Estimated likelihood of false positives from 0 to 1", ge=0, le=1
    )

    @field_validator("anomalies")
    @classmethod
    def validate_anomaly_count(cls, v: List[Anomaly], info) -> List[Anomaly]:
        """Ensure anomalies list length matches anomalies_detected."""
        if "anomalies_detected" in info.data and len(v) != info.data["anomalies_detected"]:
            raise ValueError("anomalies list length must match anomalies_detected")
        return v


# ============================================================================
# Natural Language Query Models
# ============================================================================


class QueryResult(BaseModel):
    """Structured response for natural language queries about audit data."""

    query_understood: bool = Field(description="Whether the query was successfully parsed")
    original_query: str = Field(description="The original user query")
    interpreted_intent: str = Field(description="AI's interpretation of user intent")
    sql_equivalent: Optional[str] = Field(
        None, description="SQL query equivalent (if applicable)"
    )
    result_type: ResultType = Field(description="Type of result returned")
    data: Dict[str, Any] = Field(description="The actual query results")
    visualization_hint: VisualizationType = Field(
        description="Suggested visualization type for the data"
    )
    explanation: str = Field(description="Natural language explanation of results")
    related_queries: List[str] = Field(
        default_factory=list, description="Suggested follow-up queries", max_length=3
    )
    confidence_score: float = Field(
        description="Confidence in query understanding from 0 to 1", ge=0, le=1
    )


# ============================================================================
# Intelligent Configuration Models
# ============================================================================


class CollectorRecommendation(BaseModel):
    """AI recommendation for enabling/configuring a collector."""

    collector_name: str = Field(description="Name of the collector (e.g., 'git_collector')")
    enabled: bool = Field(description="Whether to enable this collector")
    priority: int = Field(description="Priority level from 1 (highest) to 10 (lowest)", ge=1, le=10)
    configuration: Dict[str, Any] = Field(
        description="Recommended configuration parameters for this collector"
    )
    rationale: str = Field(description="Explanation for this recommendation")
    estimated_scan_time_seconds: int = Field(
        description="Estimated time this collector will take", ge=0
    )
    estimated_cost: Optional[float] = Field(
        None, description="Estimated cost in USD (if applicable)", ge=0
    )


class ProjectSetupSuggestion(BaseModel):
    """AI-generated project setup recommendations."""

    project_type: ProjectType = Field(description="Detected project type")
    detected_languages: List[str] = Field(
        description="Programming languages detected in the project"
    )
    detected_frameworks: List[str] = Field(
        default_factory=list, description="Frameworks detected (e.g., 'Django', 'React')"
    )
    recommended_collectors: List[CollectorRecommendation] = Field(
        description="Recommended collectors for this project"
    )
    estimated_total_scan_time_seconds: int = Field(
        description="Estimated total scan time across all collectors", ge=0
    )
    warning_messages: List[str] = Field(
        default_factory=list,
        description="Warnings about potential issues or missing dependencies",
        max_length=5,
    )
    optimization_suggestions: List[str] = Field(
        default_factory=list, description="Suggestions to optimize audit performance", max_length=5
    )
    confidence_score: float = Field(
        description="Confidence in project type detection from 0 to 1", ge=0, le=1
    )


# ============================================================================
# Executive Summary Models
# ============================================================================


class ExecutiveSummary(BaseModel):
    """AI-generated executive summary of audit results."""

    headline: str = Field(description="One-line summary of overall project health")
    health_score: int = Field(
        description="Overall health score from 0 (worst) to 100 (perfect)", ge=0, le=100
    )
    health_status: HealthStatus = Field(description="Categorical health status")
    key_achievements: List[str] = Field(
        description="Positive highlights from the audit", max_length=5
    )
    concerns: List[str] = Field(
        description="Issues requiring attention", max_length=5
    )
    strategic_recommendations: List[str] = Field(
        description="High-level recommendations for leadership", max_length=5
    )
    risk_assessment: str = Field(description="Assessment of technical and business risks")
    next_review_date: str = Field(
        description="Suggested date for next audit (ISO 8601 date: YYYY-MM-DD)"
    )
    comparison_to_previous: Optional[str] = Field(
        None, description="Comparison to previous audit if available"
    )
    estimated_investment_needed: Optional[str] = Field(
        None, description="Estimated time/money investment to address issues"
    )

    @field_validator("next_review_date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        """Validate that next_review_date is a valid ISO 8601 date."""
        try:
            datetime.fromisoformat(v)
        except ValueError as e:
            raise ValueError(f"Invalid ISO 8601 date: {v}") from e
        return v


# ============================================================================
# Root Cause Analysis Models
# ============================================================================


class RootCause(BaseModel):
    """Identified root cause of an issue."""

    cause_id: str = Field(description="Unique identifier for this root cause")
    description: str = Field(description="Description of the root cause")
    evidence: List[str] = Field(description="Evidence supporting this root cause", max_length=5)
    confidence: float = Field(description="Confidence level from 0 to 1", ge=0, le=1)
    category: str = Field(
        description="Category of root cause (e.g., 'code_quality', 'architecture', 'process')"
    )


class RootCauseAnalysis(BaseModel):
    """AI-powered root cause analysis for failures or issues."""

    issue_id: str = Field(description="Identifier for the issue being analyzed")
    issue_description: str = Field(description="Description of the issue")
    analyzed_at: str = Field(description="ISO 8601 timestamp of analysis")
    root_causes: List[RootCause] = Field(
        description="Identified root causes ordered by confidence", max_length=5
    )
    recommended_fixes: List[str] = Field(
        description="Concrete steps to resolve the issue", max_length=5
    )
    prevention_strategies: List[str] = Field(
        description="Strategies to prevent recurrence", max_length=3
    )
    severity: Severity = Field(description="Severity of the underlying issue")
    estimated_resolution_time_hours: Optional[float] = Field(
        None, description="Estimated time to fully resolve", ge=0
    )
    related_issues: List[str] = Field(
        default_factory=list, description="IDs of related issues", max_length=5
    )


# ============================================================================
# Utility Models
# ============================================================================


class AIAnalysisMetadata(BaseModel):
    """Metadata for any AI analysis operation."""

    model_version: str = Field(description="Claude model version used")
    analysis_duration_seconds: float = Field(description="Time taken for analysis", ge=0)
    tokens_used: int = Field(description="Total tokens consumed", ge=0)
    cost_usd: Optional[float] = Field(None, description="Cost in USD", ge=0)
    cache_hit: bool = Field(
        default=False, description="Whether results were served from cache"
    )
    structured_output_used: bool = Field(
        default=True, description="Whether structured outputs feature was used"
    )


class AIAnalysisError(BaseModel):
    """Error information when AI analysis fails."""

    error_type: str = Field(description="Type of error that occurred")
    error_message: str = Field(description="Human-readable error message")
    retry_recommended: bool = Field(description="Whether retrying might succeed")
    fallback_available: bool = Field(description="Whether fallback analysis is available")
    timestamp: str = Field(description="ISO 8601 timestamp of error")
