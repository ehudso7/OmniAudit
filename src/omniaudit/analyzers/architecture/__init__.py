"""Architecture Analysis Package."""

from .architecture_analyzer import ArchitectureAnalyzer
from .types import (
    ArchitectureAnalysisResult,
    ArchitecturePattern,
    ArchitectureValidation,
    CircularDependency,
    CouplingMetrics,
    DependencyNode,
    LayerType,
    LayerViolation,
    ModuleMetrics,
)

__all__ = [
    "ArchitectureAnalyzer",
    "ArchitectureAnalysisResult",
    "ArchitecturePattern",
    "ArchitectureValidation",
    "CircularDependency",
    "CouplingMetrics",
    "DependencyNode",
    "LayerType",
    "LayerViolation",
    "ModuleMetrics",
]
