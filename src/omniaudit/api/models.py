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
