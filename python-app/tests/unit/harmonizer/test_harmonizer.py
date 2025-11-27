"""
Tests for the main Harmonizer engine.
"""

import pytest
from datetime import datetime

from omniaudit.harmonizer import Harmonizer, Finding, HarmonizationConfig
from omniaudit.models.ai_models import Severity


class TestHarmonizer:
    """Test suite for Harmonizer class."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return HarmonizationConfig()

    @pytest.fixture
    def harmonizer(self, config):
        """Create Harmonizer instance."""
        return Harmonizer(config)

    @pytest.fixture
    def sample_findings(self):
        """Create sample findings for testing."""
        return [
            Finding(
                id="finding_1",
                analyzer_name="test_analyzer",
                file_path="/src/main.py",
                line_number=10,
                severity=Severity.HIGH,
                rule_id="S001",
                category="security",
                message="SQL injection vulnerability detected",
                timestamp=datetime.utcnow().isoformat() + "Z",
            ),
            Finding(
                id="finding_2",
                analyzer_name="test_analyzer",
                file_path="/src/main.py",
                line_number=12,
                severity=Severity.HIGH,
                rule_id="S001",
                category="security",
                message="SQL injection vulnerability detected",  # Duplicate
                timestamp=datetime.utcnow().isoformat() + "Z",
            ),
            Finding(
                id="finding_3",
                analyzer_name="quality_analyzer",
                file_path="/src/utils.py",
                line_number=5,
                severity=Severity.MEDIUM,
                rule_id="C001",
                category="code_quality",
                message="High cyclomatic complexity detected",
                timestamp=datetime.utcnow().isoformat() + "Z",
            ),
            Finding(
                id="finding_4",
                analyzer_name="test_analyzer",
                file_path="/tests/test_main.py",
                line_number=1,
                severity=Severity.LOW,
                rule_id="D001",
                category="style",
                message="Missing docstring in test file",
                timestamp=datetime.utcnow().isoformat() + "Z",
            ),
        ]

    def test_harmonizer_initialization(self, harmonizer):
        """Test that Harmonizer initializes correctly."""
        assert harmonizer is not None
        assert harmonizer.config is not None
        assert harmonizer.deduplicator is not None
        assert harmonizer.correlator is not None
        assert harmonizer.false_positive_filter is not None
        assert harmonizer.priority_scorer is not None

    def test_harmonize_empty_findings(self, harmonizer):
        """Test harmonization with empty findings list."""
        result = harmonizer.harmonize([])

        assert result is not None
        assert len(result.findings) == 0
        assert result.stats.total_findings == 0
        assert result.stats.harmonized_findings == 0

    def test_harmonize_basic(self, harmonizer, sample_findings):
        """Test basic harmonization process."""
        result = harmonizer.harmonize(sample_findings)

        assert result is not None
        assert result.findings is not None
        assert result.stats.total_findings == len(sample_findings)
        assert result.stats.processing_time_seconds > 0

    def test_harmonize_deduplication(self, harmonizer, sample_findings):
        """Test that deduplication works."""
        result = harmonizer.harmonize(sample_findings)

        # Should have removed duplicate findings
        assert result.stats.harmonized_findings < result.stats.total_findings
        assert result.stats.duplicates_removed > 0

    def test_harmonize_false_positive_filtering(self, harmonizer, sample_findings):
        """Test false positive filtering."""
        result = harmonizer.harmonize(sample_findings)

        # Test file finding should be filtered as false positive
        assert result.stats.false_positives_filtered > 0

    def test_harmonize_priority_scoring(self, harmonizer, sample_findings):
        """Test that priority scores are assigned."""
        result = harmonizer.harmonize(sample_findings)

        # All findings should have priority scores
        for finding in result.findings:
            assert finding.priority_score >= 0
            assert finding.priority_score <= 100
            assert finding.impact_level is not None

    def test_harmonize_sorting_by_priority(self, harmonizer, sample_findings):
        """Test that findings are sorted by priority."""
        result = harmonizer.harmonize(sample_findings)

        if len(result.findings) > 1:
            # Check that findings are sorted in descending priority order
            for i in range(len(result.findings) - 1):
                assert result.findings[i].priority_score >= result.findings[i + 1].priority_score

    def test_get_top_priority_findings(self, harmonizer, sample_findings):
        """Test getting top priority findings."""
        result = harmonizer.harmonize(sample_findings)
        top_findings = harmonizer.get_top_priority_findings(result, limit=2)

        assert len(top_findings) <= 2
        if len(top_findings) > 1:
            assert top_findings[0].priority_score >= top_findings[1].priority_score

    def test_get_findings_by_category(self, harmonizer, sample_findings):
        """Test filtering findings by category."""
        result = harmonizer.harmonize(sample_findings)
        security_findings = harmonizer.get_findings_by_category(result, "security")

        for finding in security_findings:
            assert finding.category == "security"

    def test_export_summary(self, harmonizer, sample_findings):
        """Test summary export."""
        result = harmonizer.harmonize(sample_findings)
        summary = harmonizer.export_summary(result)

        assert "timestamp" in summary
        assert "statistics" in summary
        assert "top_priorities" in summary
        assert isinstance(summary["statistics"], dict)
        assert isinstance(summary["top_priorities"], list)

    def test_harmonization_stats(self, harmonizer, sample_findings):
        """Test that statistics are computed correctly."""
        result = harmonizer.harmonize(sample_findings)
        stats = result.stats

        assert stats.total_findings > 0
        assert stats.harmonized_findings >= 0
        assert stats.processing_time_seconds > 0
        assert isinstance(stats.by_severity, dict)
        assert isinstance(stats.by_category, dict)

    def test_harmonizer_with_disabled_components(self):
        """Test harmonizer with some components disabled."""
        config = HarmonizationConfig()
        config.deduplication.enabled = False
        config.correlation.enabled = False

        harmonizer = Harmonizer(config)
        findings = [
            Finding(
                id="f1",
                analyzer_name="test",
                file_path="/test.py",
                severity=Severity.MEDIUM,
                category="quality",
                message="Test finding",
                timestamp=datetime.utcnow().isoformat() + "Z",
            )
        ]

        result = harmonizer.harmonize(findings)

        # Should still work with disabled components
        assert result is not None
        assert len(result.findings) > 0


class TestHarmonizerIntegration:
    """Integration tests for harmonizer."""

    def test_full_pipeline(self):
        """Test complete harmonization pipeline."""
        harmonizer = Harmonizer()

        findings = [
            Finding(
                id=f"finding_{i}",
                analyzer_name="scanner",
                file_path=f"/src/module{i % 3}.py",
                line_number=i * 10,
                severity=Severity.HIGH if i % 2 == 0 else Severity.MEDIUM,
                rule_id=f"R{i % 5:03d}",
                category="security" if i % 3 == 0 else "quality",
                message=f"Issue {i} detected in code",
                timestamp=datetime.utcnow().isoformat() + "Z",
            )
            for i in range(20)
        ]

        result = harmonizer.harmonize(findings)

        # Verify full pipeline execution
        assert result.stats.total_findings == 20
        assert result.stats.harmonized_findings <= 20
        assert len(result.findings) > 0
        assert result.stats.processing_time_seconds > 0

        # Verify findings have all required fields
        for finding in result.findings:
            assert finding.id is not None
            assert finding.priority_score >= 0
            assert finding.severity is not None
            assert finding.category is not None
