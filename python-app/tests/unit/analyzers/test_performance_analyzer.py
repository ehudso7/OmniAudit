"""
Unit tests for Performance Analyzer.

Tests algorithm complexity, query patterns, memory issues, and Web Vitals.
"""

from pathlib import Path

import pytest

from omniaudit.analyzers.performance.detectors import (
    AlgorithmAnalyzer,
    MemoryAnalyzer,
    QueryAnalyzer,
    WebVitalsAnalyzer,
)
from omniaudit.analyzers.performance.types import AlgorithmComplexity


class TestAlgorithmAnalyzer:
    """Test algorithm complexity analysis."""

    def test_nested_loops_detected_as_quadratic(self, tmp_path):
        """Test that nested loops are detected as O(n²)."""
        analyzer = AlgorithmAnalyzer()

        code = """
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
"""
        test_file = tmp_path / "test.py"
        test_file.write_text(code)

        issues = analyzer.analyze_files([test_file])

        # Should detect O(n²) complexity
        assert len(issues) > 0
        assert issues[0].detected_complexity == AlgorithmComplexity.O_N2

    def test_single_loop_is_linear(self, tmp_path):
        """Test that single loop is O(n)."""
        analyzer = AlgorithmAnalyzer()

        code = """
def sum_array(arr):
    total = 0
    for item in arr:
        total += item
    return total
"""
        test_file = tmp_path / "test.py"
        test_file.write_text(code)

        issues = analyzer.analyze_files([test_file])

        # Should not report O(n) as issue
        assert len(issues) == 0  # Only reports concerning complexity


class TestQueryAnalyzer:
    """Test database query analysis."""

    def test_n_plus_one_query_detected(self, tmp_path):
        """Test that N+1 query pattern is detected."""
        analyzer = QueryAnalyzer()

        code = """
def get_user_posts(users):
    results = []
    for user in User.objects.all():
        posts = user.posts.all()  # N+1 query!
        results.append(posts)
    return results
"""
        test_file = tmp_path / "test.py"
        test_file.write_text(code)

        issues = analyzer.analyze_files([test_file])

        # Should detect N+1 pattern
        assert len(issues) > 0


class TestMemoryAnalyzer:
    """Test memory issue analysis."""

    def test_unclosed_file_detected(self, tmp_path):
        """Test that unclosed files are detected."""
        analyzer = MemoryAnalyzer()

        code = """
def read_data():
    f = open('data.txt')  # Not using context manager!
    data = f.read()
    return data
"""
        test_file = tmp_path / "test.py"
        test_file.write_text(code)

        issues = analyzer.analyze_files([test_file])

        # Should detect unclosed resource
        unclosed = [i for i in issues if "UNCLOSED" in str(i.issue_type)]
        assert len(unclosed) > 0


class TestWebVitalsAnalyzer:
    """Test Web Vitals analysis."""

    def test_large_library_import_detected(self, tmp_path):
        """Test that large library imports are detected."""
        analyzer = WebVitalsAnalyzer()

        code = """
import moment from 'moment';

function formatDate(date) {
    return moment(date).format('YYYY-MM-DD');
}
"""
        test_file = tmp_path / "test.js"
        test_file.write_text(code)

        impacts, optimizations = analyzer.analyze_files([test_file])

        # Should detect moment.js as large library
        assert len(impacts) > 0 or len(optimizations) > 0


@pytest.fixture
def tmp_path(tmp_path_factory):
    """Create temporary path for tests."""
    return tmp_path_factory.mktemp("performance_tests")
