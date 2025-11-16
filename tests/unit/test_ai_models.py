"""
Unit tests for AI Pydantic models.

Tests validation, field constraints, and model behavior for all AI-powered
feature models used with Anthropic Structured Outputs.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from omniaudit.models.ai_models import (
    AIAnalysisError,
    AIAnalysisMetadata,
    AIInsightsResult,
    Anomaly,
    AnomalyReport,
    CodeSmell,
    CollectorRecommendation,
    ExecutiveSummary,
    HealthStatus,
    ProjectSetupSuggestion,
    ProjectType,
    QueryResult,
    ResultType,
    RootCause,
    RootCauseAnalysis,
    Severity,
    VisualizationType,
)


class TestEnums:
    """Test enum types."""

    def test_severity_enum_values(self):
        """Test Severity enum has correct values."""
        assert Severity.CRITICAL == "critical"
        assert Severity.HIGH == "high"
        assert Severity.MEDIUM == "medium"
        assert Severity.LOW == "low"
        assert Severity.INFO == "info"

    def test_health_status_enum_values(self):
        """Test HealthStatus enum values."""
        assert HealthStatus.HEALTHY == "healthy"
        assert HealthStatus.WARNING == "warning"
        assert HealthStatus.CRITICAL == "critical"
        assert HealthStatus.UNKNOWN == "unknown"

    def test_project_type_enum_values(self):
        """Test ProjectType enum values."""
        assert ProjectType.WEB_APP == "web_app"
        assert ProjectType.MICROSERVICE == "microservice"
        assert ProjectType.LIBRARY == "library"


class TestCodeSmell:
    """Test CodeSmell model."""

    def test_valid_code_smell(self):
        """Test creating valid CodeSmell."""
        smell = CodeSmell(
            file_path="src/app.py",
            line_number=42,
            severity=Severity.HIGH,
            smell_type="long_method",
            description="Method exceeds 50 lines",
            recommendation="Extract helper methods"
        )
        assert smell.file_path == "src/app.py"
        assert smell.line_number == 42
        assert smell.severity == Severity.HIGH

    def test_code_smell_with_line_end(self):
        """Test CodeSmell with line_end."""
        smell = CodeSmell(
            file_path="src/app.py",
            line_number=10,
            line_end=20,
            severity=Severity.MEDIUM,
            smell_type="duplicated_code",
            description="Duplicated logic",
            recommendation="Extract to function"
        )
        assert smell.line_end == 20

    def test_code_smell_line_end_validation(self):
        """Test that line_end must be >= line_number."""
        with pytest.raises(ValidationError) as exc_info:
            CodeSmell(
                file_path="src/app.py",
                line_number=20,
                line_end=10,  # Invalid: less than line_number
                severity=Severity.LOW,
                smell_type="test",
                description="test",
                recommendation="test"
            )
        assert "line_end must be >= line_number" in str(exc_info.value)

    def test_code_smell_invalid_line_number(self):
        """Test that line_number must be >= 1."""
        with pytest.raises(ValidationError):
            CodeSmell(
                file_path="src/app.py",
                line_number=0,  # Invalid
                severity=Severity.LOW,
                smell_type="test",
                description="test",
                recommendation="test"
            )

    def test_code_smell_with_optional_fields(self):
        """Test CodeSmell with all optional fields."""
        smell = CodeSmell(
            file_path="src/app.py",
            line_number=1,
            line_end=5,
            severity=Severity.LOW,
            smell_type="test",
            description="test",
            recommendation="test",
            estimated_effort_minutes=30,
            related_files=["src/helper.py", "src/utils.py"]
        )
        assert smell.estimated_effort_minutes == 30
        assert len(smell.related_files) == 2


class TestAIInsightsResult:
    """Test AIInsightsResult model."""

    def test_valid_insights_result(self):
        """Test creating valid AIInsightsResult."""
        result = AIInsightsResult(
            project_id="/path/to/project",
            analyzed_at="2025-11-16T12:00:00Z",
            code_smells=[],
            technical_debt_score=75.0,
            maintainability_index=80.0,
            test_coverage_assessment="Good coverage",
            architecture_assessment="Well structured",
            summary="Overall healthy codebase",
            priority_actions=["Increase test coverage", "Refactor module X"]
        )
        assert result.technical_debt_score == 75.0
        assert len(result.priority_actions) == 2

    def test_insights_score_bounds(self):
        """Test that scores must be 0-100."""
        # Valid scores
        result = AIInsightsResult(
            project_id="test",
            analyzed_at="2025-11-16T12:00:00Z",
            code_smells=[],
            technical_debt_score=0.0,
            maintainability_index=100.0,
            test_coverage_assessment="test",
            architecture_assessment="test",
            summary="test",
            priority_actions=["test"]
        )
        assert result.technical_debt_score == 0.0
        assert result.maintainability_index == 100.0

        # Invalid score > 100
        with pytest.raises(ValidationError):
            AIInsightsResult(
                project_id="test",
                analyzed_at="2025-11-16T12:00:00Z",
                code_smells=[],
                technical_debt_score=101.0,  # Invalid
                maintainability_index=80.0,
                test_coverage_assessment="test",
                architecture_assessment="test",
                summary="test",
                priority_actions=["test"]
            )

    def test_insights_priority_actions_max_length(self):
        """Test that priority_actions has max 5 items."""
        with pytest.raises(ValidationError):
            AIInsightsResult(
                project_id="test",
                analyzed_at="2025-11-16T12:00:00Z",
                code_smells=[],
                technical_debt_score=75.0,
                maintainability_index=80.0,
                test_coverage_assessment="test",
                architecture_assessment="test",
                summary="test",
                priority_actions=["a", "b", "c", "d", "e", "f"]  # 6 items, max is 5
            )

    def test_insights_timestamp_validation(self):
        """Test that analyzed_at must be valid ISO 8601."""
        # Valid timestamp
        result = AIInsightsResult(
            project_id="test",
            analyzed_at="2025-11-16T12:00:00Z",
            code_smells=[],
            technical_debt_score=75.0,
            maintainability_index=80.0,
            test_coverage_assessment="test",
            architecture_assessment="test",
            summary="test",
            priority_actions=["test"]
        )
        assert result.analyzed_at == "2025-11-16T12:00:00Z"

        # Invalid timestamp
        with pytest.raises(ValidationError):
            AIInsightsResult(
                project_id="test",
                analyzed_at="invalid-date",
                code_smells=[],
                technical_debt_score=75.0,
                maintainability_index=80.0,
                test_coverage_assessment="test",
                architecture_assessment="test",
                summary="test",
                priority_actions=["test"]
            )


class TestAnomaly:
    """Test Anomaly model."""

    def test_valid_anomaly(self):
        """Test creating valid Anomaly."""
        anomaly = Anomaly(
            metric_name="response_time",
            expected_range=(100.0, 200.0),
            actual_value=500.0,
            deviation_percentage=150.0,
            timestamp="2025-11-16T12:00:00Z",
            severity=Severity.HIGH,
            likely_cause="Database slow query",
            affected_components=["API", "Database"],
            recommended_actions=["Optimize query", "Add index"],
            confidence_score=0.85
        )
        assert anomaly.metric_name == "response_time"
        assert anomaly.actual_value == 500.0
        assert anomaly.confidence_score == 0.85

    def test_anomaly_range_validation(self):
        """Test that expected_range min must be <= max."""
        with pytest.raises(ValidationError) as exc_info:
            Anomaly(
                metric_name="test",
                expected_range=(200.0, 100.0),  # Invalid: min > max
                actual_value=150.0,
                deviation_percentage=50.0,
                timestamp="2025-11-16T12:00:00Z",
                severity=Severity.LOW,
                likely_cause="test",
                affected_components=["test"],
                recommended_actions=["test"],
                confidence_score=0.5
            )
        assert "expected_range min must be <= max" in str(exc_info.value)

    def test_anomaly_confidence_bounds(self):
        """Test that confidence_score must be 0-1."""
        # Valid
        anomaly = Anomaly(
            metric_name="test",
            expected_range=(0.0, 1.0),
            actual_value=0.5,
            deviation_percentage=0.0,
            timestamp="2025-11-16T12:00:00Z",
            severity=Severity.LOW,
            likely_cause="test",
            affected_components=["test"],
            recommended_actions=["test"],
            confidence_score=0.0
        )
        assert anomaly.confidence_score == 0.0

        # Invalid > 1
        with pytest.raises(ValidationError):
            Anomaly(
                metric_name="test",
                expected_range=(0.0, 1.0),
                actual_value=0.5,
                deviation_percentage=0.0,
                timestamp="2025-11-16T12:00:00Z",
                severity=Severity.LOW,
                likely_cause="test",
                affected_components=["test"],
                recommended_actions=["test"],
                confidence_score=1.5  # Invalid
            )


class TestAnomalyReport:
    """Test AnomalyReport model."""

    def test_valid_anomaly_report(self):
        """Test creating valid AnomalyReport."""
        anomaly = Anomaly(
            metric_name="cpu",
            expected_range=(0.0, 80.0),
            actual_value=95.0,
            deviation_percentage=18.75,
            timestamp="2025-11-16T12:00:00Z",
            severity=Severity.HIGH,
            likely_cause="High load",
            affected_components=["API"],
            recommended_actions=["Scale up"],
            confidence_score=0.9
        )

        report = AnomalyReport(
            scan_timestamp="2025-11-16T12:00:00Z",
            time_window_hours=24,
            anomalies_detected=1,
            anomalies=[anomaly],
            overall_health=HealthStatus.WARNING,
            health_trend="degrading",
            recommended_actions=["Monitor closely"],
            false_positive_likelihood=0.1
        )
        assert report.anomalies_detected == 1
        assert len(report.anomalies) == 1

    def test_anomaly_report_count_validation(self):
        """Test that anomalies count must match anomalies_detected."""
        anomaly = Anomaly(
            metric_name="test",
            expected_range=(0.0, 1.0),
            actual_value=0.5,
            deviation_percentage=0.0,
            timestamp="2025-11-16T12:00:00Z",
            severity=Severity.LOW,
            likely_cause="test",
            affected_components=["test"],
            recommended_actions=["test"],
            confidence_score=0.5
        )

        with pytest.raises(ValidationError) as exc_info:
            AnomalyReport(
                scan_timestamp="2025-11-16T12:00:00Z",
                time_window_hours=24,
                anomalies_detected=2,  # Says 2
                anomalies=[anomaly],  # But only 1 provided
                overall_health=HealthStatus.HEALTHY,
                health_trend="stable",
                recommended_actions=["test"],
                false_positive_likelihood=0.1
            )
        assert "anomalies list length must match anomalies_detected" in str(exc_info.value)


class TestQueryResult:
    """Test QueryResult model."""

    def test_valid_query_result(self):
        """Test creating valid QueryResult."""
        result = QueryResult(
            query_understood=True,
            original_query="Show me test coverage",
            interpreted_intent="Retrieve test coverage metrics",
            sql_equivalent="SELECT coverage FROM metrics",
            result_type=ResultType.METRIC,
            data={"coverage": 85.0},
            visualization_hint=VisualizationType.SINGLE_VALUE,
            explanation="Test coverage is 85%",
            confidence_score=0.95
        )
        assert result.query_understood is True
        assert result.confidence_score == 0.95

    def test_query_result_with_optional_fields(self):
        """Test QueryResult with optional fields omitted."""
        result = QueryResult(
            query_understood=False,
            original_query="Unknown query",
            interpreted_intent="Could not parse",
            result_type=ResultType.SUMMARY,
            data={},
            visualization_hint=VisualizationType.TABLE,
            explanation="Query not understood",
            confidence_score=0.1
        )
        assert result.sql_equivalent is None


class TestExecutiveSummary:
    """Test ExecutiveSummary model."""

    def test_valid_executive_summary(self):
        """Test creating valid ExecutiveSummary."""
        summary = ExecutiveSummary(
            headline="Project health is good",
            health_score=85,
            health_status=HealthStatus.HEALTHY,
            key_achievements=["Increased coverage", "Reduced complexity"],
            concerns=["Tech debt in module X"],
            strategic_recommendations=["Invest in refactoring"],
            risk_assessment="Low risk overall",
            next_review_date="2025-12-16"
        )
        assert summary.health_score == 85
        assert summary.health_status == HealthStatus.HEALTHY

    def test_executive_summary_date_validation(self):
        """Test that next_review_date must be valid ISO 8601 date."""
        # Valid date
        summary = ExecutiveSummary(
            headline="test",
            health_score=50,
            health_status=HealthStatus.WARNING,
            key_achievements=["test"],
            concerns=["test"],
            strategic_recommendations=["test"],
            risk_assessment="test",
            next_review_date="2025-12-31"
        )
        assert summary.next_review_date == "2025-12-31"

        # Invalid date format
        with pytest.raises(ValidationError):
            ExecutiveSummary(
                headline="test",
                health_score=50,
                health_status=HealthStatus.WARNING,
                key_achievements=["test"],
                concerns=["test"],
                strategic_recommendations=["test"],
                risk_assessment="test",
                next_review_date="12/31/2025"  # Invalid format
            )


class TestProjectSetupSuggestion:
    """Test ProjectSetupSuggestion model."""

    def test_valid_project_setup(self):
        """Test creating valid ProjectSetupSuggestion."""
        recommendation = CollectorRecommendation(
            collector_name="git_collector",
            enabled=True,
            priority=1,
            configuration={"repo_path": ".", "max_commits": 1000},
            rationale="Essential for version control analysis",
            estimated_scan_time_seconds=30
        )

        suggestion = ProjectSetupSuggestion(
            project_type=ProjectType.WEB_APP,
            detected_languages=["python", "javascript"],
            detected_frameworks=["Django", "React"],
            recommended_collectors=[recommendation],
            estimated_total_scan_time_seconds=120,
            warning_messages=["Large repository may take time"],
            optimization_suggestions=["Use max_commits limit"],
            confidence_score=0.9
        )
        assert suggestion.project_type == ProjectType.WEB_APP
        assert len(suggestion.detected_languages) == 2


class TestAIAnalysisMetadata:
    """Test AIAnalysisMetadata model."""

    def test_valid_metadata(self):
        """Test creating valid metadata."""
        metadata = AIAnalysisMetadata(
            model_version="claude-sonnet-4-5",
            analysis_duration_seconds=2.5,
            tokens_used=1500,
            cost_usd=0.05,
            cache_hit=False,
            structured_output_used=True
        )
        assert metadata.tokens_used == 1500
        assert metadata.cost_usd == 0.05

    def test_metadata_with_defaults(self):
        """Test metadata with default values."""
        metadata = AIAnalysisMetadata(
            model_version="claude-sonnet-4-5",
            analysis_duration_seconds=1.0,
            tokens_used=1000
        )
        assert metadata.cache_hit is False
        assert metadata.structured_output_used is True


class TestAIAnalysisError:
    """Test AIAnalysisError model."""

    def test_valid_error(self):
        """Test creating valid error."""
        error = AIAnalysisError(
            error_type="APIError",
            error_message="Rate limit exceeded",
            retry_recommended=True,
            fallback_available=True,
            timestamp="2025-11-16T12:00:00Z"
        )
        assert error.retry_recommended is True
        assert error.fallback_available is True


class TestModelDumps:
    """Test model serialization."""

    def test_code_smell_dump(self):
        """Test CodeSmell serialization."""
        smell = CodeSmell(
            file_path="src/app.py",
            line_number=42,
            severity=Severity.HIGH,
            smell_type="long_method",
            description="test",
            recommendation="test"
        )
        data = smell.model_dump()
        assert data["file_path"] == "src/app.py"
        assert data["severity"] == "high"

    def test_insights_result_dump(self):
        """Test AIInsightsResult serialization."""
        result = AIInsightsResult(
            project_id="test",
            analyzed_at="2025-11-16T12:00:00Z",
            code_smells=[],
            technical_debt_score=75.0,
            maintainability_index=80.0,
            test_coverage_assessment="test",
            architecture_assessment="test",
            summary="test",
            priority_actions=["test"]
        )
        data = result.model_dump()
        assert "technical_debt_score" in data
        assert data["code_smells"] == []
