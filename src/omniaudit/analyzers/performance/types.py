"""
Type definitions for Performance Analysis.

Pydantic models for performance metrics, issues, and results.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AlgorithmComplexity(str, Enum):
    """Big-O complexity classifications."""

    O_1 = "O(1)"  # Constant
    O_LOG_N = "O(log n)"  # Logarithmic
    O_N = "O(n)"  # Linear
    O_N_LOG_N = "O(n log n)"  # Linearithmic
    O_N2 = "O(n²)"  # Quadratic
    O_N3 = "O(n³)"  # Cubic
    O_2N = "O(2^n)"  # Exponential
    O_N_FACTORIAL = "O(n!)"  # Factorial
    UNKNOWN = "unknown"


class PerformanceImpact(str, Enum):
    """Performance impact levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NEGLIGIBLE = "negligible"


class QueryIssueType(str, Enum):
    """Types of database query issues."""

    N_PLUS_ONE = "n_plus_one"
    MISSING_INDEX = "missing_index"
    FULL_TABLE_SCAN = "full_table_scan"
    INEFFICIENT_JOIN = "inefficient_join"
    SUBOPTIMAL_QUERY = "suboptimal_query"


class MemoryIssueType(str, Enum):
    """Types of memory issues."""

    MEMORY_LEAK = "memory_leak"
    EXCESSIVE_ALLOCATION = "excessive_allocation"
    INEFFICIENT_STRUCTURE = "inefficient_data_structure"
    UNCLOSED_RESOURCE = "unclosed_resource"


class WebVitalMetric(str, Enum):
    """Core Web Vitals metrics."""

    LCP = "LCP"  # Largest Contentful Paint
    FID = "FID"  # First Input Delay
    CLS = "CLS"  # Cumulative Layout Shift
    TTFB = "TTFB"  # Time to First Byte
    FCP = "FCP"  # First Contentful Paint


class AlgorithmComplexityIssue(BaseModel):
    """An algorithm complexity issue."""

    file_path: str = Field(description="File containing the algorithm")
    function_name: str = Field(description="Function name")
    line_start: int = Field(ge=1, description="Starting line number")
    line_end: int = Field(ge=1, description="Ending line number")
    detected_complexity: AlgorithmComplexity = Field(
        description="Detected time complexity"
    )
    space_complexity: Optional[AlgorithmComplexity] = Field(
        None, description="Space complexity if available"
    )
    impact: PerformanceImpact = Field(description="Performance impact level")
    evidence: str = Field(description="Why this complexity was assigned")
    suggestion: str = Field(description="Optimization suggestion")
    confidence: float = Field(ge=0.0, le=1.0, description="Detection confidence")


class QueryPerformanceIssue(BaseModel):
    """A database query performance issue."""

    file_path: str = Field(description="File containing the query")
    line_start: int = Field(ge=1, description="Starting line number")
    line_end: int = Field(ge=1, description="Ending line number")
    issue_type: QueryIssueType = Field(description="Type of query issue")
    query_pattern: str = Field(description="Query pattern or ORM call")
    impact: PerformanceImpact = Field(description="Performance impact")
    description: str = Field(description="Issue description")
    suggestion: str = Field(description="Optimization suggestion")
    estimated_improvement: Optional[str] = Field(
        None, description="Estimated performance improvement"
    )


class MemoryIssue(BaseModel):
    """A memory-related performance issue."""

    file_path: str = Field(description="File containing the issue")
    line_start: int = Field(ge=1, description="Starting line number")
    line_end: int = Field(ge=1, description="Ending line number")
    issue_type: MemoryIssueType = Field(description="Type of memory issue")
    impact: PerformanceImpact = Field(description="Memory impact")
    description: str = Field(description="Issue description")
    evidence: str = Field(description="Evidence for the issue")
    suggestion: str = Field(description="How to fix it")
    potential_leak_size: Optional[str] = Field(
        None, description="Estimated leak size if applicable"
    )


class BundleOptimization(BaseModel):
    """Bundle optimization opportunity."""

    file_path: str = Field(description="File or module")
    optimization_type: str = Field(
        description="Type (tree-shaking, code-splitting, lazy-loading)"
    )
    current_size: Optional[int] = Field(None, description="Current size in bytes")
    potential_savings: Optional[int] = Field(
        None, description="Potential savings in bytes"
    )
    impact: PerformanceImpact = Field(description="Impact on bundle size")
    description: str = Field(description="Optimization description")
    suggestion: str = Field(description="How to implement")


class WebVitalImpact(BaseModel):
    """Web Vitals impact prediction."""

    metric: WebVitalMetric = Field(description="Affected Web Vital")
    file_path: str = Field(description="File causing impact")
    line_start: Optional[int] = Field(None, description="Starting line number")
    impact_level: PerformanceImpact = Field(description="Impact level")
    current_estimate: Optional[str] = Field(
        None, description="Current estimated value"
    )
    target_value: str = Field(description="Target value for good performance")
    description: str = Field(description="How this affects the metric")
    suggestions: List[str] = Field(
        description="Optimization suggestions", max_length=5
    )


class PerformanceAnalysisResult(BaseModel):
    """Complete performance analysis results."""

    project_path: str = Field(description="Analyzed project path")
    language: str = Field(description="Primary language")
    total_files: int = Field(ge=0, description="Total files analyzed")

    # Algorithm complexity
    algorithm_issues: List[AlgorithmComplexityIssue] = Field(
        default_factory=list, description="Algorithm complexity issues"
    )
    average_complexity: str = Field(description="Average algorithm complexity")

    # Query performance
    query_issues: List[QueryPerformanceIssue] = Field(
        default_factory=list, description="Database query issues"
    )
    n_plus_one_count: int = Field(ge=0, description="N+1 query instances")

    # Memory issues
    memory_issues: List[MemoryIssue] = Field(
        default_factory=list, description="Memory-related issues"
    )
    potential_leaks: int = Field(ge=0, description="Potential memory leaks")

    # Bundle optimization
    bundle_opportunities: List[BundleOptimization] = Field(
        default_factory=list, description="Bundle optimization opportunities"
    )
    potential_size_reduction: int = Field(
        ge=0, description="Potential bundle size reduction in bytes"
    )

    # Web Vitals
    web_vital_impacts: List[WebVitalImpact] = Field(
        default_factory=list, description="Web Vitals impact predictions"
    )

    # Overall scores
    performance_score: float = Field(
        ge=0.0, le=100.0, description="Overall performance score (0-100)"
    )
    optimization_potential: float = Field(
        ge=0.0, le=100.0, description="Optimization potential score (0-100)"
    )

    # Summary
    summary: str = Field(description="Analysis summary")
    critical_issues: List[str] = Field(
        default_factory=list, description="Critical performance issues"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="Top optimization recommendations"
    )
