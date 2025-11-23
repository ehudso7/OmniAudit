"""
Unit tests for reporters.
"""

import json
import tempfile
from pathlib import Path

import pytest

from omniaudit.reporters.markdown_reporter import MarkdownReporter
from omniaudit.reporters.json_reporter import JSONReporter


class TestMarkdownReporter:
    """Test Markdown reporter."""

    @pytest.fixture
    def sample_data(self):
        """Sample audit data."""
        return {
            "collectors": {
                "git_collector": {
                    "status": "success",
                    "data": {
                        "commits_count": 100,
                        "contributors_count": 5,
                        "branches": [
                            {"name": "main", "commit_sha": "abc123"},
                            {"name": "develop", "commit_sha": "def456"}
                        ],
                        "contributors": [
                            {
                                "name": "Alice",
                                "commits": 50,
                                "insertions": 1000,
                                "deletions": 500,
                                "lines_changed": 1500
                            },
                            {
                                "name": "Bob",
                                "commits": 30,
                                "insertions": 600,
                                "deletions": 300,
                                "lines_changed": 900
                            }
                        ]
                    }
                }
            },
            "analyzers": {
                "code_quality": {
                    "status": "success",
                    "data": {
                        "overall_score": 85.5,
                        "metrics": {
                            "python": {
                                "files": 50,
                                "loc": 5000,
                                "complexity": 10.5,
                                "maintainability": 75.0
                            }
                        },
                        "issues": [
                            {
                                "severity": "WARNING",
                                "file": "main.py",
                                "line": 42,
                                "message": "Function too complex"
                            }
                        ]
                    }
                }
            }
        }

    def test_reporter_initialization(self):
        """Test reporter can be initialized."""
        reporter = MarkdownReporter()
        assert reporter.name == "markdown_reporter"
        assert reporter.format == "markdown"

    def test_generate_report(self, sample_data):
        """Test report generation."""
        reporter = MarkdownReporter()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.md"
            reporter.generate(sample_data, str(output_path))

            assert output_path.exists()
            content = output_path.read_text(encoding='utf-8')

            # Check header
            assert "# 🔍 OmniAudit Report" in content

            # Check summary section
            assert "## 📊 Summary" in content
            assert "Total Commits" in content
            assert "100" in content

            # Check git section
            assert "## 📦 Git Repository Analysis" in content
            assert "Alice" in content
            assert "Bob" in content

            # Check quality section
            assert "## ⭐ Code Quality Analysis" in content
            assert "85.5" in content
            assert "python" in content.lower()

    def test_generate_empty_report(self):
        """Test report generation with empty data."""
        reporter = MarkdownReporter()
        empty_data = {"collectors": {}, "analyzers": {}}

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "empty.md"
            reporter.generate(empty_data, str(output_path))

            assert output_path.exists()
            content = output_path.read_text(encoding='utf-8')
            assert "# 🔍 OmniAudit Report" in content

    def test_utf8_encoding(self, sample_data):
        """Test that report is written with UTF-8 encoding."""
        reporter = MarkdownReporter()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.md"
            reporter.generate(sample_data, str(output_path))

            # Should be able to read emojis
            content = output_path.read_text(encoding='utf-8')
            assert "🔍" in content
            assert "📊" in content
            assert "📦" in content


class TestJSONReporter:
    """Test JSON reporter."""

    @pytest.fixture
    def sample_data(self):
        """Sample audit data."""
        return {
            "collectors": {
                "git_collector": {
                    "status": "success",
                    "data": {
                        "commits_count": 100,
                        "contributors_count": 5
                    }
                }
            },
            "analyzers": {
                "code_quality": {
                    "status": "success",
                    "data": {
                        "overall_score": 85.5
                    }
                }
            }
        }

    def test_reporter_initialization(self):
        """Test reporter can be initialized."""
        reporter = JSONReporter()
        assert reporter.name == "json_reporter"
        assert reporter.format == "json"

    def test_generate_report(self, sample_data):
        """Test JSON report generation."""
        reporter = JSONReporter()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.json"
            reporter.generate(sample_data, str(output_path))

            assert output_path.exists()

            # Parse JSON
            with open(output_path, 'r', encoding='utf-8') as f:
                report = json.load(f)

            # Check structure
            assert "metadata" in report
            assert "summary" in report
            assert "collectors" in report
            assert "analyzers" in report

            # Check metadata
            assert report["metadata"]["tool"] == "OmniAudit"
            assert "generated_at" in report["metadata"]

            # Check summary
            assert report["summary"]["total_collectors"] == 1
            assert report["summary"]["total_analyzers"] == 1

    def test_generate_empty_report(self):
        """Test JSON report with empty data."""
        reporter = JSONReporter()
        empty_data = {"collectors": {}, "analyzers": {}}

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "empty.json"
            reporter.generate(empty_data, str(output_path))

            assert output_path.exists()

            with open(output_path, 'r', encoding='utf-8') as f:
                report = json.load(f)

            assert report["summary"]["total_collectors"] == 0
            assert report["summary"]["total_analyzers"] == 0

    def test_utf8_encoding(self, sample_data):
        """Test that JSON is written with UTF-8 encoding."""
        # Add Unicode characters to data
        sample_data["collectors"]["git_collector"]["data"]["contributors"] = [
            {"name": "François", "commits": 10},
            {"name": "José", "commits": 5}
        ]

        reporter = JSONReporter()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.json"
            reporter.generate(sample_data, str(output_path))

            # Read with UTF-8
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()

            assert "François" in content
            assert "José" in content

    def test_json_formatting(self, sample_data):
        """Test that JSON is properly formatted."""
        reporter = JSONReporter()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.json"
            reporter.generate(sample_data, str(output_path))

            content = output_path.read_text(encoding='utf-8')

            # Should be indented (pretty-printed)
            assert "  " in content  # Has indentation
            assert "\n" in content  # Has newlines
