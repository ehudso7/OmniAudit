"""
Type definitions for Architecture Analysis.

Pydantic models for architecture metrics and results.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ArchitecturePattern(str, Enum):
    """Architecture pattern types."""

    CLEAN = "clean_architecture"
    HEXAGONAL = "hexagonal"
    ONION = "onion"
    LAYERED = "layered"
    MVC = "mvc"
    MICROSERVICES = "microservices"
    MONOLITH = "monolith"
    UNKNOWN = "unknown"


class LayerType(str, Enum):
    """Architecture layer types."""

    PRESENTATION = "presentation"
    APPLICATION = "application"
    DOMAIN = "domain"
    INFRASTRUCTURE = "infrastructure"
    DATABASE = "database"


class DependencyNode(BaseModel):
    """A node in the dependency graph."""

    module_path: str = Field(description="Module path")
    module_type: str = Field(description="Type (file, package)")
    imports_count: int = Field(ge=0, description="Number of imports")
    imported_by_count: int = Field(ge=0, description="Number of importers")
    dependencies: List[str] = Field(
        default_factory=list, description="Direct dependencies"
    )


class CircularDependency(BaseModel):
    """A circular dependency chain."""

    cycle: List[str] = Field(description="Modules in the cycle")
    severity: str = Field(description="Severity level")
    impact: str = Field(description="Impact description")
    suggestion: str = Field(description="How to break the cycle")


class LayerViolation(BaseModel):
    """An architecture layer violation."""

    from_layer: LayerType = Field(description="Source layer")
    to_layer: LayerType = Field(description="Target layer")
    from_module: str = Field(description="Source module")
    to_module: str = Field(description="Target module")
    line_number: int = Field(ge=1, description="Line number of violation")
    description: str = Field(description="Violation description")
    severity: str = Field(description="Severity level")
    suggestion: str = Field(description="How to fix")


class CouplingMetrics(BaseModel):
    """Coupling and cohesion metrics."""

    afferent_coupling: int = Field(ge=0, description="Incoming dependencies")
    efferent_coupling: int = Field(ge=0, description="Outgoing dependencies")
    instability: float = Field(ge=0.0, le=1.0, description="Instability metric")
    abstractness: float = Field(ge=0.0, le=1.0, description="Abstractness metric")


class ModuleMetrics(BaseModel):
    """Metrics for a module."""

    module_path: str = Field(description="Module path")
    coupling: CouplingMetrics = Field(description="Coupling metrics")
    cohesion_score: float = Field(
        ge=0.0, le=100.0, description="Cohesion score (0-100)"
    )
    lines_of_code: int = Field(ge=0, description="Lines of code")
    complexity: float = Field(ge=0.0, description="Average complexity")


class ArchitectureValidation(BaseModel):
    """Architecture pattern validation result."""

    detected_pattern: ArchitecturePattern = Field(description="Detected pattern")
    confidence: float = Field(ge=0.0, le=1.0, description="Detection confidence")
    compliance_score: float = Field(
        ge=0.0, le=100.0, description="Pattern compliance (0-100)"
    )
    violations: List[str] = Field(
        default_factory=list, description="Pattern violations"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="Recommendations"
    )


class ArchitectureAnalysisResult(BaseModel):
    """Complete architecture analysis results."""

    project_path: str = Field(description="Analyzed project path")
    total_modules: int = Field(ge=0, description="Total modules analyzed")

    # Dependency graph
    dependency_nodes: List[DependencyNode] = Field(
        default_factory=list, description="Dependency graph nodes"
    )
    total_dependencies: int = Field(ge=0, description="Total dependencies")

    # Circular dependencies
    circular_dependencies: List[CircularDependency] = Field(
        default_factory=list, description="Circular dependency cycles"
    )
    circular_count: int = Field(ge=0, description="Number of circular dependencies")

    # Layer violations
    layer_violations: List[LayerViolation] = Field(
        default_factory=list, description="Architecture layer violations"
    )

    # Module metrics
    module_metrics: List[ModuleMetrics] = Field(
        default_factory=list, description="Module-level metrics"
    )
    average_coupling: float = Field(ge=0.0, description="Average coupling")
    average_cohesion: float = Field(ge=0.0, description="Average cohesion")

    # Architecture validation
    architecture_validation: Optional[ArchitectureValidation] = Field(
        None, description="Architecture pattern validation"
    )

    # Overall scores
    architecture_score: float = Field(
        ge=0.0, le=100.0, description="Overall architecture score (0-100)"
    )
    maintainability_score: float = Field(
        ge=0.0, le=100.0, description="Maintainability score (0-100)"
    )

    # Summary
    summary: str = Field(description="Analysis summary")
    critical_issues: List[str] = Field(
        default_factory=list, description="Critical architecture issues"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="Top recommendations"
    )
