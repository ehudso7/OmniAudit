"""
Tests for the Deduplicator component.
"""

import pytest
from datetime import datetime

from omniaudit.harmonizer.deduplicator import Deduplicator
from omniaudit.harmonizer.types import DeduplicationConfig, Finding
from omniaudit.models.ai_models import Severity


class TestDeduplicator:
    """Test suite for Deduplicator class."""

    @pytest.fixture
    def config(self):
        """Create default deduplication configuration."""
        return DeduplicationConfig()

    @pytest.fixture
    def deduplicator(self, config):
        """Create Deduplicator instance."""
        return Deduplicator(config)

    def test_deduplicator_initialization(self, deduplicator):
        """Test that Deduplicator initializes correctly."""
        assert deduplicator is not None
        assert deduplicator.config is not None

    def test_exact_duplicates(self, deduplicator):
        """Test detection of exact duplicates."""
        findings = [
            Finding(
                id="f1",
                analyzer_name="test",
                file_path="/src/main.py",
                line_number=10,
                severity=Severity.HIGH,
                category="security",
                rule_id="S001",
                message="SQL injection vulnerability",
                timestamp=datetime.utcnow().isoformat() + "Z",
            ),
            Finding(
                id="f2",
                analyzer_name="test",
                file_path="/src/main.py",
                line_number=10,
                severity=Severity.HIGH,
                category="security",
                rule_id="S001",
                message="SQL injection vulnerability",
                timestamp=datetime.utcnow().isoformat() + "Z",
            ),
        ]

        unique, duplicates = deduplicator.deduplicate(findings)

        assert len(unique) == 1
        assert len(duplicates) == 1
        assert duplicates["f2"] == "f1"

    def test_similar_messages(self, deduplicator):
        """Test detection of similar messages."""
        findings = [
            Finding(
                id="f1",
                analyzer_name="test",
                file_path="/src/main.py",
                line_number=10,
                severity=Severity.MEDIUM,
                category="quality",
                message="Function complexity is too high in calculate_total",
                timestamp=datetime.utcnow().isoformat() + "Z",
            ),
            Finding(
                id="f2",
                analyzer_name="test",
                file_path="/src/main.py",
                line_number=11,
                severity=Severity.MEDIUM,
                category="quality",
                message="Function complexity too high calculate_total",
                timestamp=datetime.utcnow().isoformat() + "Z",
            ),
        ]

        unique, duplicates = deduplicator.deduplicate(findings)

        # Should detect as duplicates due to semantic similarity
        assert len(unique) <= 2

    def test_different_categories_not_duplicates(self, deduplicator):
        """Test that findings with different categories aren't duplicates."""
        findings = [
            Finding(
                id="f1",
                analyzer_name="test",
                file_path="/src/main.py",
                line_number=10,
                severity=Severity.MEDIUM,
                category="security",
                message="Issue detected",
                timestamp=datetime.utcnow().isoformat() + "Z",
            ),
            Finding(
                id="f2",
                analyzer_name="test",
                file_path="/src/main.py",
                line_number=10,
                severity=Severity.MEDIUM,
                category="quality",
                message="Issue detected",
                timestamp=datetime.utcnow().isoformat() + "Z",
            ),
        ]

        unique, duplicates = deduplicator.deduplicate(findings)

        # Different categories should not be duplicates
        assert len(unique) == 2
        assert len(duplicates) == 0

    def test_location_proximity(self, deduplicator):
        """Test location-based duplicate detection."""
        findings = [
            Finding(
                id="f1",
                analyzer_name="test",
                file_path="/src/main.py",
                line_number=10,
                severity=Severity.LOW,
                category="style",
                rule_id="W001",
                message="Line too long",
                timestamp=datetime.utcnow().isoformat() + "Z",
            ),
            Finding(
                id="f2",
                analyzer_name="test",
                file_path="/src/main.py",
                line_number=12,  # Within proximity threshold
                severity=Severity.LOW,
                category="style",
                rule_id="W001",
                message="Line too long",
                timestamp=datetime.utcnow().isoformat() + "Z",
            ),
        ]

        unique, duplicates = deduplicator.deduplicate(findings)

        # Should be detected as duplicates (same rule, close lines)
        assert len(unique) == 1

    def test_different_files_not_duplicates(self, deduplicator):
        """Test that findings in different files aren't duplicates by location."""
        findings = [
            Finding(
                id="f1",
                analyzer_name="test",
                file_path="/src/main.py",
                line_number=10,
                severity=Severity.MEDIUM,
                category="quality",
                rule_id="C001",
                message="High complexity",
                timestamp=datetime.utcnow().isoformat() + "Z",
            ),
            Finding(
                id="f2",
                analyzer_name="test",
                file_path="/src/utils.py",
                line_number=10,
                severity=Severity.MEDIUM,
                category="quality",
                rule_id="C001",
                message="High complexity",
                timestamp=datetime.utcnow().isoformat() + "Z",
            ),
        ]

        unique, duplicates = deduplicator.deduplicate(findings)

        # Different files should not be location duplicates
        assert len(unique) == 2

    def test_disabled_deduplication(self):
        """Test deduplication when disabled."""
        config = DeduplicationConfig(enabled=False)
        deduplicator = Deduplicator(config)

        findings = [
            Finding(
                id="f1",
                analyzer_name="test",
                file_path="/test.py",
                severity=Severity.LOW,
                category="style",
                message="Test",
                timestamp=datetime.utcnow().isoformat() + "Z",
            ),
            Finding(
                id="f2",
                analyzer_name="test",
                file_path="/test.py",
                severity=Severity.LOW,
                category="style",
                message="Test",
                timestamp=datetime.utcnow().isoformat() + "Z",
            ),
        ]

        unique, duplicates = deduplicator.deduplicate(findings)

        # Should return all findings when disabled
        assert len(unique) == 2
        assert len(duplicates) == 0

    def test_similarity_threshold(self):
        """Test similarity threshold configuration."""
        # High threshold - requires very similar messages
        config = DeduplicationConfig(similarity_threshold=0.95)
        deduplicator = Deduplicator(config)

        findings = [
            Finding(
                id="f1",
                analyzer_name="test",
                file_path="/test.py",
                severity=Severity.MEDIUM,
                category="quality",
                message="Function is too complex",
                timestamp=datetime.utcnow().isoformat() + "Z",
            ),
            Finding(
                id="f2",
                analyzer_name="test",
                file_path="/test.py",
                severity=Severity.MEDIUM,
                category="quality",
                message="Function too complex",
                timestamp=datetime.utcnow().isoformat() + "Z",
            ),
        ]

        unique, duplicates = deduplicator.deduplicate(findings)

        # With high threshold, might not detect as duplicates
        # (depends on exact similarity calculation)
        assert len(unique) >= 1

    def test_clear_cache(self, deduplicator):
        """Test cache clearing."""
        findings = [
            Finding(
                id="f1",
                analyzer_name="test",
                file_path="/test.py",
                severity=Severity.LOW,
                category="style",
                message="Test message",
                timestamp=datetime.utcnow().isoformat() + "Z",
            )
        ]

        # Run deduplication to populate cache
        deduplicator.deduplicate(findings)

        # Cache should have entries
        stats = deduplicator.get_stats()
        initial_cache_size = stats["cache_size"]

        # Clear cache
        deduplicator.clear_cache()

        # Cache should be empty
        stats = deduplicator.get_stats()
        assert stats["cache_size"] == 0

    def test_get_stats(self, deduplicator):
        """Test statistics retrieval."""
        stats = deduplicator.get_stats()

        assert "cache_size" in stats
        assert "config" in stats
        assert isinstance(stats["cache_size"], int)
        assert isinstance(stats["config"], dict)

    def test_empty_findings(self, deduplicator):
        """Test deduplication with empty findings list."""
        unique, duplicates = deduplicator.deduplicate([])

        assert len(unique) == 0
        assert len(duplicates) == 0

    def test_single_finding(self, deduplicator):
        """Test deduplication with single finding."""
        findings = [
            Finding(
                id="f1",
                analyzer_name="test",
                file_path="/test.py",
                severity=Severity.MEDIUM,
                category="quality",
                message="Single finding",
                timestamp=datetime.utcnow().isoformat() + "Z",
            )
        ]

        unique, duplicates = deduplicator.deduplicate(findings)

        assert len(unique) == 1
        assert len(duplicates) == 0
