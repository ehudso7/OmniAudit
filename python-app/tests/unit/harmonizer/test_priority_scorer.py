"""
Tests for the Priority Scorer component.

Note: These tests are skipped because the harmonizer module
is not yet implemented.
"""

import pytest

pytestmark = pytest.mark.skip(
    reason="Harmonizer priority scorer module not yet implemented"
)


class TestPriorityScorer:
    """Test suite for PriorityScorer class."""

    def test_scorer_initialization(self):
        """Test that PriorityScorer initializes correctly."""
        pass

    def test_high_severity_gets_high_priority(self):
        """Test that high severity findings get high priority."""
        pass

    def test_priority_considers_category(self):
        """Test that category influences priority."""
        pass

    def test_priority_considers_file_importance(self):
        """Test that file importance influences priority."""
        pass
