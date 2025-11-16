"""
AI-Powered Insights Analyzer using Anthropic's Structured Outputs.

This analyzer leverages Claude to provide advanced code quality insights,
architecture assessment, and actionable recommendations with guaranteed
structured outputs.

See ADR-004 for architectural decisions.
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from omniaudit.analyzers.base import AnalyzerError, BaseAnalyzer
from omniaudit.models.ai_models import (
    AIAnalysisError,
    AIAnalysisMetadata,
    AIInsightsResult,
    CodeSmell,
)

# Anthropic SDK imports - handle gracefully if not installed
try:
    from anthropic import Anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class AIInsightsAnalyzer(BaseAnalyzer):
    """
    AI-powered code insights analyzer using Anthropic Structured Outputs.

    This analyzer uses Claude with guaranteed structured outputs to:
    - Detect code smells and anti-patterns
    - Assess technical debt and maintainability
    - Provide architecture quality analysis
    - Generate prioritized recommendations

    Configuration:
        api_key (str): Anthropic API key (or set ANTHROPIC_API_KEY env var)
        model (str): Claude model to use (default: claude-sonnet-4-5)
        max_tokens (int): Maximum tokens for response (default: 4096)
        enable_cache (bool): Enable response caching (default: True)
        cache_ttl_seconds (int): Cache TTL (default: 3600)
        fallback_to_rules (bool): Fall back to rule-based analysis on error (default: True)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize AI insights analyzer."""
        super().__init__(config)
        self._client: Optional[Anthropic] = None
        self._cache: Dict[str, Any] = {}  # Simple in-memory cache for now

        if ANTHROPIC_AVAILABLE and self._is_enabled():
            self._initialize_client()

    @property
    def name(self) -> str:
        """Return analyzer name."""
        return "ai_insights"

    @property
    def version(self) -> str:
        """Return analyzer version."""
        return "0.1.0"

    def _validate_config(self) -> None:
        """Validate configuration."""
        if not self._is_enabled():
            # AI features disabled, no validation needed
            return

        if not ANTHROPIC_AVAILABLE:
            raise AnalyzerError(
                "Anthropic SDK not installed. Install with: pip install anthropic>=0.39.0"
            )

        api_key = self.config.get("api_key") or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise AnalyzerError(
                "Anthropic API key not found. Set 'api_key' in config or ANTHROPIC_API_KEY env var"
            )

    def _initialize_client(self) -> None:
        """Initialize Anthropic client."""
        api_key = self.config.get("api_key") or os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            self._client = Anthropic(api_key=api_key)

    def _is_enabled(self) -> bool:
        """Check if AI features are enabled."""
        return self.config.get("enabled", os.environ.get("AI_FEATURES_ENABLED", "false").lower() == "true")

    def _get_model(self) -> str:
        """Get the Claude model to use."""
        return self.config.get("model", "claude-sonnet-4-5")

    def _get_max_tokens(self) -> int:
        """Get maximum tokens for response."""
        return self.config.get("max_tokens", 4096)

    def _get_cache_key(self, data: Dict[str, Any]) -> str:
        """Generate cache key for data."""
        # Simple cache key based on project path and file count
        project_path = data.get("project_path", "unknown")
        file_count = len(data.get("files", []))
        return f"{project_path}:{file_count}"

    def _check_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Check if cached result exists and is valid."""
        if not self.config.get("enable_cache", True):
            return None

        cached = self._cache.get(cache_key)
        if not cached:
            return None

        # Check if cache is expired
        ttl = self.config.get("cache_ttl_seconds", 3600)
        cached_at = datetime.fromisoformat(cached["cached_at"])
        age_seconds = (datetime.utcnow() - cached_at).total_seconds()

        if age_seconds > ttl:
            # Cache expired
            del self._cache[cache_key]
            return None

        return cached["result"]

    def _set_cache(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Store result in cache."""
        if self.config.get("enable_cache", True):
            self._cache[cache_key] = {
                "cached_at": datetime.utcnow().isoformat(),
                "result": result,
            }

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze code using AI-powered insights.

        Args:
            data: Input data containing:
                - project_path (str): Path to project
                - files (List[Dict]): List of file analysis results
                - metrics (Dict): Existing metrics (coverage, complexity, etc.)
                - language_breakdown (Dict): Languages used in project

        Returns:
            Analysis results with AI-generated insights

        Raises:
            AnalyzerError: If analysis fails and fallback is disabled
        """
        if not self._is_enabled():
            return self._create_disabled_response()

        # Check cache first
        cache_key = self._get_cache_key(data)
        cached_result = self._check_cache(cache_key)
        if cached_result:
            cached_result["metadata"]["cache_hit"] = True
            return self._create_response(cached_result)

        # Perform AI analysis
        try:
            start_time = datetime.utcnow()
            insights_result = self._analyze_with_ai(data)
            duration = (datetime.utcnow() - start_time).total_seconds()

            # Create metadata
            metadata = AIAnalysisMetadata(
                model_version=self._get_model(),
                analysis_duration_seconds=duration,
                tokens_used=0,  # TODO: Extract from API response
                cost_usd=None,  # TODO: Calculate based on tokens
                cache_hit=False,
                structured_output_used=True,
            )

            result = {
                "insights": insights_result.model_dump(),
                "metadata": metadata.model_dump(),
            }

            # Cache the result
            self._set_cache(cache_key, result)

            return self._create_response(result)

        except Exception as e:
            if self.config.get("fallback_to_rules", True):
                return self._fallback_analysis(data, str(e))
            else:
                error = AIAnalysisError(
                    error_type=type(e).__name__,
                    error_message=str(e),
                    retry_recommended=True,
                    fallback_available=True,
                    timestamp=datetime.utcnow().isoformat() + "Z",
                )
                return self._create_response(
                    {"error": error.model_dump()}, metadata={"analysis_failed": True}
                )

    def _analyze_with_ai(self, data: Dict[str, Any]) -> AIInsightsResult:
        """
        Perform AI analysis using Anthropic Structured Outputs.

        This is a placeholder implementation. Full implementation will use:
        - client.beta.messages.parse() with structured outputs
        - AIInsightsResult as response_model
        - Detailed prompts for code analysis

        Args:
            data: Project data to analyze

        Returns:
            AIInsightsResult with structured insights
        """
        if not self._client:
            raise AnalyzerError("Anthropic client not initialized")

        # TODO: Full implementation with structured outputs
        # For now, return a placeholder result
        project_path = data.get("project_path", "unknown")
        file_count = len(data.get("files", []))
        metrics = data.get("metrics", {})

        # Placeholder: Create a basic AIInsightsResult
        # In full implementation, this will be returned by Claude API
        result = AIInsightsResult(
            project_id=project_path,
            analyzed_at=datetime.utcnow().isoformat() + "Z",
            code_smells=[],  # Will be populated by AI
            technical_debt_score=75.0,  # Placeholder
            maintainability_index=70.0,  # Placeholder
            test_coverage_assessment="Test coverage data not available for AI analysis",
            architecture_assessment="Architecture analysis pending full AI implementation",
            summary=f"AI analysis placeholder for project with {file_count} files",
            priority_actions=[
                "Enable full AI insights by implementing Anthropic Structured Outputs integration",
                "Review code quality metrics manually until AI features are complete",
                "Set ANTHROPIC_API_KEY environment variable",
            ],
            estimated_remediation_hours=None,
        )

        return result

    def _fallback_analysis(self, data: Dict[str, Any], error_message: str) -> Dict[str, Any]:
        """
        Provide rule-based analysis as fallback when AI fails.

        Args:
            data: Project data
            error_message: Error that caused fallback

        Returns:
            Rule-based analysis results
        """
        file_count = len(data.get("files", []))
        metrics = data.get("metrics", {})
        complexity_avg = metrics.get("complexity_avg", 0)
        coverage = metrics.get("coverage_percent", 0)

        # Simple rule-based scoring
        debt_score = 100.0
        if complexity_avg > 10:
            debt_score -= 20
        if coverage < 80:
            debt_score -= 15
        if file_count > 100:
            debt_score -= 10

        result = AIInsightsResult(
            project_id=data.get("project_path", "unknown"),
            analyzed_at=datetime.utcnow().isoformat() + "Z",
            code_smells=[],
            technical_debt_score=max(0, debt_score),
            maintainability_index=max(0, debt_score - 5),
            test_coverage_assessment=f"Coverage: {coverage}% (target: 80%+)",
            architecture_assessment="Rule-based analysis (AI unavailable)",
            summary=f"Rule-based analysis completed. AI analysis failed: {error_message}",
            priority_actions=[
                "Review high-complexity modules",
                "Increase test coverage" if coverage < 80 else "Maintain test coverage",
                "Check AI service configuration",
            ],
        )

        metadata = {
            "fallback_mode": True,
            "fallback_reason": error_message,
            "ai_available": False,
        }

        return self._create_response(
            {"insights": result.model_dump(), "metadata": metadata}, metadata=metadata
        )

    def _create_disabled_response(self) -> Dict[str, Any]:
        """Return response when AI features are disabled."""
        return self._create_response(
            {
                "enabled": False,
                "message": "AI insights are disabled. Enable by setting AI_FEATURES_ENABLED=true",
                "insights": None,
            },
            metadata={"ai_enabled": False},
        )

    def clear_cache(self) -> None:
        """Clear the analysis cache."""
        self._cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_size": len(self._cache),
            "cache_keys": list(self._cache.keys()),
            "cache_enabled": self.config.get("enable_cache", True),
        }


# Example usage and integration pattern
def create_ai_insights_analyzer(
    api_key: Optional[str] = None,
    enabled: bool = True,
    model: str = "claude-sonnet-4-5",
    **kwargs: Any,
) -> AIInsightsAnalyzer:
    """
    Factory function to create AI insights analyzer.

    Args:
        api_key: Anthropic API key (optional if set in env)
        enabled: Enable AI features
        model: Claude model to use
        **kwargs: Additional configuration options

    Returns:
        Configured AIInsightsAnalyzer instance

    Example:
        >>> analyzer = create_ai_insights_analyzer(enabled=True)
        >>> data = {
        ...     "project_path": "/path/to/project",
        ...     "files": [...],
        ...     "metrics": {...}
        ... }
        >>> result = analyzer.analyze(data)
        >>> print(result["data"]["insights"]["summary"])
    """
    config = {
        "enabled": enabled,
        "model": model,
        **kwargs,
    }

    if api_key:
        config["api_key"] = api_key

    return AIInsightsAnalyzer(config)
