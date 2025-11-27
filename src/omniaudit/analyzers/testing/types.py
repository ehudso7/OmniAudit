"""
Type definitions for Testing Analysis.

Pydantic models for test metrics and results.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CoverageType(str, Enum):
    """Coverage metric types."""

    LINE = "line"
    BRANCH = "branch"
    FUNCTION = "function"
    STATEMENT = "statement"


class TestQualityIssue(str, Enum):
    """Test quality issue types."""

    NO_ASSERTIONS = "no_assertions"
    SINGLE_ASSERTION_PRINCIPLE_VIOLATION = "multiple_assertions"
    POOR_NAMING = "poor_naming"
    NO_CLEANUP = "no_cleanup"
    HARD_CODED_VALUES = "hard_coded_values"
    SLOW_TEST = "slow_test"


class CoverageMetrics(BaseModel):
    """Coverage metrics."""

    line_coverage: float = Field(ge=0.0, le=100.0, description="Line coverage %")
    branch_coverage: float = Field(ge=0.0, le=100.0, description="Branch coverage %")
    function_coverage: float = Field(
        ge=0.0, le=100.0, description="Function coverage %"
    )
    total_lines: int = Field(ge=0, description="Total lines")
    covered_lines: int = Field(ge=0, description="Covered lines")
    missed_lines: int = Field(ge=0, description="Missed lines")


class UncoveredCode(BaseModel):
    """Uncovered code region."""

    file_path: str = Field(description="File path")
    line_start: int = Field(ge=1, description="Starting line")
    line_end: int = Field(ge=1, description="Ending line")
    function_name: Optional[str] = Field(None, description="Function name if applicable")
    complexity: Optional[int] = Field(None, description="Complexity of uncovered code")
    priority: str = Field(description="Priority level (high, medium, low)")
    reason: str = Field(description="Why this should be covered")


class MissingEdgeCase(BaseModel):
    """A missing edge case in tests."""

    file_path: str = Field(description="Source file path")
    function_name: str = Field(description="Function name")
    edge_case_type: str = Field(
        description="Type (null_input, empty_input, boundary, error_condition)"
    )
    description: str = Field(description="Edge case description")
    test_suggestion: str = Field(description="Suggested test case")


class TestQualityIssueInstance(BaseModel):
    """A test quality issue."""

    test_file: str = Field(description="Test file path")
    test_function: str = Field(description="Test function name")
    line_number: int = Field(ge=1, description="Line number")
    issue_type: TestQualityIssue = Field(description="Issue type")
    description: str = Field(description="Issue description")
    severity: str = Field(description="Severity level")
    suggestion: str = Field(description="How to improve")
    quality_impact: float = Field(
        ge=0.0, le=10.0, description="Impact on quality (0-10)"
    )


class FlakyTestPattern(BaseModel):
    """A pattern suggesting flaky test."""

    test_file: str = Field(description="Test file")
    test_function: str = Field(description="Test function")
    pattern_type: str = Field(
        description="Pattern (timing, randomness, external_dependency, ordering)"
    )
    description: str = Field(description="Why it might be flaky")
    evidence: str = Field(description="Evidence found in code")
    suggestion: str = Field(description="How to make it more reliable")
    flakiness_score: float = Field(
        ge=0.0, le=10.0, description="Flakiness likelihood (0-10)"
    )


class TestingAnalysisResult(BaseModel):
    """Complete testing analysis results."""

    project_path: str = Field(description="Analyzed project path")
    total_test_files: int = Field(ge=0, description="Total test files")
    total_tests: int = Field(ge=0, description="Total test functions")

    # Coverage
    coverage_metrics: Optional[CoverageMetrics] = Field(
        None, description="Coverage metrics"
    )
    uncovered_code: List[UncoveredCode] = Field(
        default_factory=list, description="Uncovered code regions"
    )
    coverage_score: float = Field(
        ge=0.0, le=100.0, description="Overall coverage score"
    )

    # Edge cases
    missing_edge_cases: List[MissingEdgeCase] = Field(
        default_factory=list, description="Missing edge cases"
    )

    # Test quality
    test_quality_issues: List[TestQualityIssueInstance] = Field(
        default_factory=list, description="Test quality issues"
    )
    average_test_quality: float = Field(
        ge=0.0, le=100.0, description="Average test quality score"
    )

    # Flaky tests
    flaky_test_patterns: List[FlakyTestPattern] = Field(
        default_factory=list, description="Potential flaky test patterns"
    )
    potential_flaky_count: int = Field(ge=0, description="Potential flaky tests")

    # Overall scores
    testing_score: float = Field(
        ge=0.0, le=100.0, description="Overall testing score (0-100)"
    )
    test_maturity: str = Field(description="Test maturity level")

    # Summary
    summary: str = Field(description="Analysis summary")
    critical_gaps: List[str] = Field(
        default_factory=list, description="Critical testing gaps"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="Top recommendations"
    )
