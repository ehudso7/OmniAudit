"""
Type definitions for Code Quality Analysis.

Pydantic models for code quality metrics, issues, and results.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ComplexityLevel(str, Enum):
    """Complexity classification levels."""

    LOW = "low"  # 1-5
    MODERATE = "moderate"  # 6-10
    HIGH = "high"  # 11-20
    VERY_HIGH = "very_high"  # 21+


class DuplicationType(str, Enum):
    """Types of code duplication."""

    EXACT = "exact"  # Exact copy-paste
    STRUCTURAL = "structural"  # Same structure, different names
    SEMANTIC = "semantic"  # Same logic, different implementation


class AntiPatternType(str, Enum):
    """Common anti-patterns."""

    GOD_CLASS = "god_class"
    LONG_METHOD = "long_method"
    FEATURE_ENVY = "feature_envy"
    DATA_CLUMPS = "data_clumps"
    SHOTGUN_SURGERY = "shotgun_surgery"
    PRIMITIVE_OBSESSION = "primitive_obsession"
    SWITCH_STATEMENTS = "switch_statements"
    SPECULATIVE_GENERALITY = "speculative_generality"
    LAZY_CLASS = "lazy_class"
    DEAD_CODE = "dead_code"


class SOLIDPrinciple(str, Enum):
    """SOLID principles."""

    SINGLE_RESPONSIBILITY = "single_responsibility"
    OPEN_CLOSED = "open_closed"
    LISKOV_SUBSTITUTION = "liskov_substitution"
    INTERFACE_SEGREGATION = "interface_segregation"
    DEPENDENCY_INVERSION = "dependency_inversion"


class DesignPattern(str, Enum):
    """Common design patterns."""

    SINGLETON = "singleton"
    FACTORY = "factory"
    BUILDER = "builder"
    PROTOTYPE = "prototype"
    ADAPTER = "adapter"
    BRIDGE = "bridge"
    COMPOSITE = "composite"
    DECORATOR = "decorator"
    FACADE = "facade"
    FLYWEIGHT = "flyweight"
    PROXY = "proxy"
    CHAIN_OF_RESPONSIBILITY = "chain_of_responsibility"
    COMMAND = "command"
    ITERATOR = "iterator"
    MEDIATOR = "mediator"
    MEMENTO = "memento"
    OBSERVER = "observer"
    STATE = "state"
    STRATEGY = "strategy"
    TEMPLATE_METHOD = "template_method"
    VISITOR = "visitor"


class ComplexityMetrics(BaseModel):
    """Complexity metrics for a code entity."""

    cyclomatic_complexity: int = Field(ge=1, description="Cyclomatic complexity")
    cognitive_complexity: int = Field(ge=0, description="Cognitive complexity")
    complexity_level: ComplexityLevel = Field(description="Complexity classification")
    lines_of_code: int = Field(ge=0, description="Lines of code")
    parameters_count: int = Field(ge=0, description="Number of parameters")
    nesting_depth: int = Field(ge=0, description="Maximum nesting depth")


class FunctionComplexity(BaseModel):
    """Complexity analysis for a function."""

    name: str = Field(description="Function name")
    file_path: str = Field(description="File containing the function")
    line_start: int = Field(ge=1, description="Starting line number")
    line_end: int = Field(ge=1, description="Ending line number")
    metrics: ComplexityMetrics = Field(description="Complexity metrics")
    suggestions: List[str] = Field(
        default_factory=list, description="Refactoring suggestions"
    )


class DuplicationCluster(BaseModel):
    """A cluster of duplicated code."""

    duplication_type: DuplicationType = Field(description="Type of duplication")
    total_lines: int = Field(ge=1, description="Total duplicated lines")
    instance_count: int = Field(ge=2, description="Number of instances")
    instances: List[Dict[str, Any]] = Field(description="File and line information")
    code_snippet: str = Field(description="Sample of duplicated code")
    confidence: float = Field(ge=0.0, le=1.0, description="Detection confidence")
    suggestions: List[str] = Field(
        default_factory=list, description="Refactoring suggestions"
    )


class DeadCodeItem(BaseModel):
    """A piece of dead/unused code."""

    file_path: str = Field(description="File containing dead code")
    line_start: int = Field(ge=1, description="Starting line number")
    line_end: int = Field(ge=1, description="Ending line number")
    entity_type: str = Field(description="Type (function, class, variable, import)")
    entity_name: str = Field(description="Name of the entity")
    reason: str = Field(description="Why it's considered dead code")
    confidence: float = Field(ge=0.0, le=1.0, description="Detection confidence")


class AntiPatternInstance(BaseModel):
    """An instance of an anti-pattern."""

    pattern_type: AntiPatternType = Field(description="Type of anti-pattern")
    file_path: str = Field(description="File containing the anti-pattern")
    line_start: int = Field(ge=1, description="Starting line number")
    line_end: int = Field(ge=1, description="Ending line number")
    entity_name: str = Field(description="Name of affected entity")
    description: str = Field(description="Detailed description")
    severity: str = Field(description="Impact severity (low, medium, high)")
    evidence: Dict[str, Any] = Field(description="Supporting evidence")
    refactoring_suggestion: str = Field(description="How to fix it")


class SOLIDViolation(BaseModel):
    """A violation of SOLID principles."""

    principle: SOLIDPrinciple = Field(description="Violated principle")
    file_path: str = Field(description="File containing the violation")
    line_start: int = Field(ge=1, description="Starting line number")
    entity_name: str = Field(description="Name of affected entity")
    description: str = Field(description="Violation description")
    severity: str = Field(description="Impact severity")
    suggestion: str = Field(description="How to fix it")


class DesignPatternInstance(BaseModel):
    """A detected design pattern."""

    pattern: DesignPattern = Field(description="Detected pattern")
    file_paths: List[str] = Field(description="Files implementing the pattern")
    confidence: float = Field(ge=0.0, le=1.0, description="Detection confidence")
    components: Dict[str, Any] = Field(description="Pattern components")
    quality_score: float = Field(
        ge=0.0, le=100.0, description="Implementation quality (0-100)"
    )
    notes: str = Field(description="Implementation notes")


class QualityAnalysisResult(BaseModel):
    """Complete quality analysis results."""

    project_path: str = Field(description="Analyzed project path")
    language: str = Field(description="Primary language analyzed")
    total_files: int = Field(ge=0, description="Total files analyzed")
    total_lines: int = Field(ge=0, description="Total lines of code")

    # Complexity
    complexity_results: List[FunctionComplexity] = Field(
        default_factory=list, description="Complexity analysis results"
    )
    average_complexity: float = Field(ge=0.0, description="Average complexity")
    high_complexity_count: int = Field(ge=0, description="High complexity items")

    # Duplication
    duplication_clusters: List[DuplicationCluster] = Field(
        default_factory=list, description="Code duplication clusters"
    )
    duplication_percentage: float = Field(
        ge=0.0, le=100.0, description="Percentage of duplicated code"
    )

    # Dead code
    dead_code_items: List[DeadCodeItem] = Field(
        default_factory=list, description="Dead code items"
    )
    dead_code_lines: int = Field(ge=0, description="Total dead code lines")

    # Anti-patterns
    anti_patterns: List[AntiPatternInstance] = Field(
        default_factory=list, description="Detected anti-patterns"
    )

    # SOLID violations
    solid_violations: List[SOLIDViolation] = Field(
        default_factory=list, description="SOLID violations"
    )

    # Design patterns
    design_patterns: List[DesignPatternInstance] = Field(
        default_factory=list, description="Detected design patterns"
    )

    # Overall scores
    quality_score: float = Field(
        ge=0.0, le=100.0, description="Overall quality score (0-100)"
    )
    maintainability_index: float = Field(
        ge=0.0, le=100.0, description="Maintainability index (0-100)"
    )

    # Summary
    summary: str = Field(description="Analysis summary")
    top_issues: List[str] = Field(
        default_factory=list, description="Top priority issues"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="Top recommendations"
    )
