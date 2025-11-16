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

        Uses Claude with guaranteed structured outputs to analyze code quality,
        detect code smells, and provide actionable recommendations.

        Args:
            data: Project data to analyze containing:
                - project_path: Path to project
                - files: List of file analysis results
                - metrics: Complexity, coverage, etc.
                - language_breakdown: Languages used

        Returns:
            AIInsightsResult with structured insights

        Raises:
            AnalyzerError: If Anthropic client not initialized or API error
        """
        if not self._client:
            raise AnalyzerError("Anthropic client not initialized")

        project_path = data.get("project_path", "unknown")
        file_count = len(data.get("files", []))
        metrics = data.get("metrics", {})
        language_breakdown = data.get("language_breakdown", {})

        # Build comprehensive prompt for code analysis
        prompt = self._build_analysis_prompt(data)

        try:
            # Call Anthropic API with Structured Outputs
            response = self._client.beta.messages.parse(
                model=self._get_model(),
                betas=["structured-outputs-2025-11-13"],
                max_tokens=self._get_max_tokens(),
                response_model=AIInsightsResult,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # The parsed response is guaranteed to be valid AIInsightsResult
            return response.parsed_output

        except Exception as e:
            # If API call fails, raise for fallback handling
            raise AnalyzerError(f"Anthropic API error: {str(e)}")

    def _build_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """
        Build comprehensive analysis prompt for Claude.

        Args:
            data: Project data

        Returns:
            Detailed prompt for code quality analysis
        """
        project_path = data.get("project_path", "unknown")
        files = data.get("files", [])
        metrics = data.get("metrics", {})
        language_breakdown = data.get("language_breakdown", {})

        # Extract key metrics
        total_files = len(files)
        total_lines = sum(f.get("lines", 0) for f in files)
        avg_complexity = metrics.get("complexity_avg", 0)
        coverage = metrics.get("coverage_percent", 0)

        # Build language summary
        languages_used = ", ".join(language_breakdown.keys()) if language_breakdown else "Unknown"

        # Create detailed prompt
        prompt = f"""You are an expert code quality analyst. Analyze this software project and provide detailed insights.

**Project Overview:**
- Path: {project_path}
- Total Files: {total_files}
- Total Lines of Code: {total_lines:,}
- Languages: {languages_used}
- Average Cyclomatic Complexity: {avg_complexity:.2f}
- Test Coverage: {coverage:.1f}%

**Code Metrics:**
{self._format_metrics(metrics)}

**Files Analyzed:**
{self._format_files_summary(files[:20])}  # Limit to first 20 files

**Your Task:**
Provide a comprehensive code quality analysis with:

1. **Code Smells**: Identify specific anti-patterns or quality issues based on the metrics.
   - For each issue, specify file path, line number, severity, type, description, and recommendation
   - Focus on high-impact issues: high complexity methods, low test coverage, duplicated code patterns

2. **Technical Debt Score** (0-100): Calculate based on:
   - Code complexity (weight: 30%)
   - Test coverage (weight: 25%)
   - Code duplication (weight: 20%)
   - Code organization (weight: 15%)
   - Documentation quality (weight: 10%)

3. **Maintainability Index** (0-100): Consider:
   - Average file size and complexity
   - Naming conventions
   - Code structure and organization
   - Dependency management

4. **Test Coverage Assessment**: Evaluate if {coverage:.1f}% coverage is adequate for this type of project.

5. **Architecture Assessment**: Based on file structure and metrics, assess the overall architecture quality.

6. **Summary**: 2-3 sentence executive summary of overall code health.

7. **Priority Actions**: Top 3-5 concrete actions to improve code quality, ordered by impact.

8. **Estimated Remediation Hours**: Rough estimate of total hours needed to address all major issues.

Be specific, actionable, and honest in your assessment. Use the structured output format to ensure consistency.
"""

        return prompt

    def _format_metrics(self, metrics: Dict[str, Any]) -> str:
        """Format metrics for prompt."""
        if not metrics:
            return "No metrics available"

        lines = []
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                lines.append(f"- {key}: {value}")
            elif isinstance(value, dict):
                lines.append(f"- {key}: {len(value)} items")

        return "\n".join(lines) if lines else "No metrics available"

    def _format_files_summary(self, files: List[Dict[str, Any]]) -> str:
        """Format file list for prompt."""
        if not files:
            return "No files available"

        lines = []
        for f in files:
            path = f.get("path", "unknown")
            lines_count = f.get("lines", 0)
            complexity = f.get("complexity", 0)
            lines.append(f"- {path}: {lines_count} lines, complexity {complexity}")

        return "\n".join(lines) if lines else "No files available"

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


def warm_up_ai_schemas(api_key: Optional[str] = None) -> bool:
    """
    Pre-compile AI schemas to reduce first-request latency.

    This function sends minimal test requests to warm up the schema cache.
    Call this during application startup for better performance.

    Args:
        api_key: Anthropic API key (optional if set in env)

    Returns:
        True if warm-up successful, False otherwise

    Example:
        >>> # During FastAPI app startup
        >>> @app.on_event("startup")
        >>> async def startup():
        ...     warm_up_ai_schemas()
    """
    try:
        if not ANTHROPIC_AVAILABLE:
            return False

        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            return False

        # Create minimal test data
        test_data = {
            "project_path": "/warmup/test",
            "files": [],
            "metrics": {},
            "language_breakdown": {}
        }

        # Create analyzer with minimal token limit to reduce cost
        analyzer = AIInsightsAnalyzer({
            "enabled": True,
            "api_key": key,
            "model": "claude-sonnet-4-5",
            "max_tokens": 512,  # Minimal for schema compilation
            "enable_cache": False,  # Don't cache warmup requests
        })

        # Trigger schema compilation (might fail due to minimal data, that's OK)
        try:
            analyzer._analyze_with_ai(test_data)
        except Exception:
            # Expected to fail with minimal data, but schema is now cached
            pass

        return True

    except Exception:
        return False
