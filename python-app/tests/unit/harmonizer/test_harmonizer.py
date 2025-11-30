"""
Tests for the main Harmonizer engine.

Note: These tests are skipped because the harmonizer module
is not yet implemented.
"""

import pytest

pytestmark = pytest.mark.skip(
    reason="Harmonizer module not yet implemented"
)


class TestHarmonizer:
    """Test suite for Harmonizer class."""

    def test_harmonizer_initialization(self):
        """Test that Harmonizer initializes correctly."""
        pass

    def test_harmonize_empty_findings(self):
        """Test harmonization with empty findings list."""
        pass

    def test_harmonize_basic(self):
        """Test basic harmonization process."""
        pass

    def test_harmonize_deduplication(self):
        """Test that deduplication works."""
        pass

    def test_harmonize_false_positive_filtering(self):
        """Test false positive filtering."""
        pass

    def test_harmonize_priority_scoring(self):
        """Test that priority scores are assigned."""
        pass


class TestHarmonizerIntegration:
    """Integration tests for harmonizer."""

    def test_full_pipeline(self):
        """Test complete harmonization pipeline."""
        pass
