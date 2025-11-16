"""
OmniAudit data models.

This package contains Pydantic models for structured data throughout the application,
including AI-enhanced features.
"""

from omniaudit.models.ai_models import (
    AIInsightsResult,
    AnomalyReport,
    Anomaly,
    CodeSmell,
    CollectorRecommendation,
    ExecutiveSummary,
    ProjectSetupSuggestion,
    QueryResult,
)

__all__ = [
    "AIInsightsResult",
    "AnomalyReport",
    "Anomaly",
    "CodeSmell",
    "CollectorRecommendation",
    "ExecutiveSummary",
    "ProjectSetupSuggestion",
    "QueryResult",
]
