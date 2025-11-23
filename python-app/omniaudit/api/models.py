"""
API Request/Response Models

Pydantic models for API validation.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List


class CollectorRequest(BaseModel):
    """Request model for collector execution."""
    config: Dict[str, Any] = Field(
        ...,
        description="Collector configuration"
    )


class CollectorResponse(BaseModel):
    """Response model for collector execution."""
    success: bool
    collector: str
    data: Dict[str, Any]


class AnalyzerRequest(BaseModel):
    """Request model for analyzer execution."""
    config: Dict[str, Any] = Field(
        ...,
        description="Analyzer configuration"
    )


class AnalyzerResponse(BaseModel):
    """Response model for analyzer execution."""
    success: bool
    analyzer: str
    data: Dict[str, Any]


class AuditRequest(BaseModel):
    """Request model for full audit."""
    collectors: Dict[str, Dict[str, Any]] = Field(
        default={},
        description="Collectors to run with their configs"
    )
    analyzers: Dict[str, Dict[str, Any]] = Field(
        default={},
        description="Analyzers to run with their configs"
    )


class AuditResponse(BaseModel):
    """Response model for full audit."""
    success: bool
    audit_id: str
    results: Dict[str, Any]


# AI Feature Models


class AIInsightsRequest(BaseModel):
    """Request model for AI insights analysis."""
    project_path: str = Field(description="Path to project")
    files: List[Dict[str, Any]] = Field(
        default=[],
        description="File analysis results"
    )
    metrics: Dict[str, Any] = Field(
        default={},
        description="Code metrics"
    )
    language_breakdown: Dict[str, Any] = Field(
        default={},
        description="Languages used in project"
    )
    enable_cache: bool = Field(
        default=True,
        description="Use cached results if available"
    )


class AIInsightsResponse(BaseModel):
    """Response model for AI insights."""
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]
