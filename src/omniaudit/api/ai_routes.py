"""
AI-Powered Features API Routes

Endpoints for AI-enhanced code analysis, insights, and recommendations
using Anthropic's Structured Outputs.
"""

import os
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any

from .models import AIInsightsRequest, AIInsightsResponse
from ..analyzers import create_ai_insights_analyzer
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Create AI router
router = APIRouter(
    prefix="/api/v1/ai",
    tags=["AI Features"],
    responses={
        503: {"description": "AI features not available or disabled"}
    }
)


def check_ai_enabled() -> bool:
    """Check if AI features are enabled."""
    return os.environ.get("AI_FEATURES_ENABLED", "false").lower() == "true"


def get_ai_analyzer():
    """Get configured AI insights analyzer."""
    if not check_ai_enabled():
        return None

    try:
        analyzer = create_ai_insights_analyzer(
            enabled=True,
            model=os.environ.get("AI_MODEL", "claude-sonnet-4-5"),
            max_tokens=int(os.environ.get("AI_MAX_TOKENS", "4096")),
            enable_cache=os.environ.get("AI_CACHE_ENABLED", "true").lower() == "true",
            cache_ttl_seconds=int(os.environ.get("AI_CACHE_TTL_SECONDS", "3600")),
            fallback_to_rules=os.environ.get("AI_FALLBACK_TO_RULES", "true").lower() == "true",
        )
        return analyzer
    except Exception as e:
        logger.error(f"Failed to create AI analyzer: {e}")
        return None


@router.get("/status")
async def ai_status() -> Dict[str, Any]:
    """
    Get AI features status.

    Returns information about AI service availability and configuration.
    """
    enabled = check_ai_enabled()
    api_key_set = bool(os.environ.get("ANTHROPIC_API_KEY"))

    return {
        "enabled": enabled,
        "api_key_configured": api_key_set,
        "model": os.environ.get("AI_MODEL", "claude-sonnet-4-5"),
        "cache_enabled": os.environ.get("AI_CACHE_ENABLED", "true").lower() == "true",
        "cache_ttl_seconds": int(os.environ.get("AI_CACHE_TTL_SECONDS", "3600")),
        "fallback_enabled": os.environ.get("AI_FALLBACK_TO_RULES", "true").lower() == "true",
        "features": {
            "insights": enabled and api_key_set,
            "anomaly_detection": False,  # Phase 4.2
            "natural_language_query": False,  # Phase 4.2
            "root_cause_analysis": False,  # Phase 4.3
        }
    }


@router.post("/insights", response_model=AIInsightsResponse)
async def analyze_with_ai(request: AIInsightsRequest) -> AIInsightsResponse:
    """
    Analyze code quality using AI-powered insights.

    This endpoint uses Anthropic's Structured Outputs to provide:
    - Code smell detection with specific recommendations
    - Technical debt score calculation
    - Maintainability index assessment
    - Architecture quality review
    - Priority actions for improvement

    **Requirements:**
    - `AI_FEATURES_ENABLED=true` environment variable
    - `ANTHROPIC_API_KEY` environment variable

    **Request Body:**
    ```json
    {
        "project_path": "/path/to/project",
        "files": [...],  # Optional: file analysis results
        "metrics": {...},  # Optional: code metrics
        "language_breakdown": {...},  # Optional: languages used
        "enable_cache": true  # Optional: use cached results
    }
    ```

    **Response:**
    Returns structured insights including:
    - Code smells with file paths and line numbers
    - Technical debt score (0-100)
    - Maintainability index (0-100)
    - Priority actions ordered by impact
    - Estimated remediation time

    **Error Handling:**
    - If AI features are disabled, returns 503
    - If API key is missing, returns 503
    - If analysis fails and fallback is enabled, returns rule-based analysis
    - If analysis fails and fallback is disabled, returns error details
    """
    # Check if AI features are enabled
    if not check_ai_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "AI features are disabled",
                "message": "Set AI_FEATURES_ENABLED=true environment variable to enable AI features",
                "fallback_available": False
            }
        )

    # Check if API key is configured
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Anthropic API key not configured",
                "message": "Set ANTHROPIC_API_KEY environment variable",
                "fallback_available": True
            }
        )

    # Get analyzer
    analyzer = get_ai_analyzer()
    if not analyzer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Failed to initialize AI analyzer",
                "message": "Check logs for details",
                "fallback_available": False
            }
        )

    # Prepare data for analysis
    data = {
        "project_path": request.project_path,
        "files": request.files,
        "metrics": request.metrics,
        "language_breakdown": request.language_breakdown,
    }

    # Run analysis
    try:
        result = analyzer.analyze(data)

        # Check if analysis was successful
        if "error" in result.get("data", {}):
            # Analysis failed but returned structured error
            return AIInsightsResponse(
                success=False,
                data=result["data"],
                metadata=result.get("metadata", {})
            )

        # Successful analysis
        return AIInsightsResponse(
            success=True,
            data=result["data"],
            metadata=result.get("metadata", {})
        )

    except Exception as e:
        logger.error(f"AI insights analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Analysis failed",
                "message": str(e),
                "fallback_available": True
            }
        )


@router.delete("/cache")
async def clear_ai_cache() -> Dict[str, Any]:
    """
    Clear AI analysis cache.

    Removes all cached AI responses. Useful after code changes or
    when you want to force fresh analysis.

    **Response:**
    ```json
    {
        "success": true,
        "message": "AI cache cleared",
        "items_cleared": 5
    }
    ```
    """
    if not check_ai_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI features are disabled"
        )

    analyzer = get_ai_analyzer()
    if not analyzer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to initialize AI analyzer"
        )

    # Get cache stats before clearing
    stats = analyzer.get_cache_stats()
    cache_size = stats["cache_size"]

    # Clear cache
    analyzer.clear_cache()

    return {
        "success": True,
        "message": "AI cache cleared",
        "items_cleared": cache_size
    }


@router.get("/cache/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """
    Get AI cache statistics.

    Returns information about cached AI responses.

    **Response:**
    ```json
    {
        "cache_enabled": true,
        "cache_size": 5,
        "cache_ttl_seconds": 3600,
        "cache_keys": ["project1", "project2"]
    }
    ```
    """
    if not check_ai_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI features are disabled"
        )

    analyzer = get_ai_analyzer()
    if not analyzer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to initialize AI analyzer"
        )

    stats = analyzer.get_cache_stats()

    return {
        **stats,
        "cache_ttl_seconds": int(os.environ.get("AI_CACHE_TTL_SECONDS", "3600"))
    }
