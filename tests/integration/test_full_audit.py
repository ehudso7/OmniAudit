"""
Integration tests for full audit workflow.

Tests end-to-end functionality combining collectors, analyzers, and reporters.
"""

import os
import tempfile
from pathlib import Path
import pytest

from omniaudit.collectors.git_collector import GitCollector
from omniaudit.analyzers.code_quality import CodeQualityAnalyzer
from omniaudit.reporters import MarkdownReporter, JSONReporter


class TestFullAuditWorkflow:
    """Test complete audit workflow from collection to reporting."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_git_collection(self):
        """Test Git collection."""
        collector = GitCollector({
            'repo_path': '.',
            'max_commits': 10
        })

        result = collector.collect()

        # Check structure matches what collectors actually return
        assert 'collector' in result
        assert result['collector'] == 'git_collector'
        assert 'data' in result
        assert 'commits' in result['data']
        assert len(result['data']['commits']) > 0

    def test_code_quality_analysis(self):
        """Test code quality analysis."""
        analyzer = CodeQualityAnalyzer({
            'project_path': '.',
            'languages': ['python']
        })

        result = analyzer.analyze({})

        # Check structure matches what analyzers actually return
        assert 'analyzer' in result
        assert 'data' in result
        assert 'metrics' in result['data']
        assert 'python' in result['data']['metrics']

    def test_markdown_report_generation(self, temp_output_dir):
        """Test generating Markdown report."""
        # Collect data
        collector = GitCollector({
            'repo_path': '.',
            'max_commits': 10
        })
        git_result = collector.collect()

        # Prepare audit results (add status field for reporters)
        results = {
            'collectors': {
                'git_collector': {
                    'status': 'success',
                    **git_result
                }
            },
            'analyzers': {}
        }

        # Generate Markdown report
        reporter = MarkdownReporter()
        output_path = temp_output_dir / "audit_report.md"
        reporter.generate(results, str(output_path))

        # Verify report was created
        assert output_path.exists()
        content = output_path.read_text()

        # Verify report structure
        assert "# 🔍 OmniAudit Report" in content
        assert "## 📊 Summary" in content
        assert "## 📦 Git Repository Analysis" in content

    def test_json_report_generation(self, temp_output_dir):
        """Test generating JSON report."""
        import json

        # Collect data
        collector = GitCollector({
            'repo_path': '.',
            'max_commits': 10
        })
        git_result = collector.collect()

        # Prepare audit results
        results = {
            'collectors': {
                'git_collector': {
                    'status': 'success',
                    **git_result
                }
            },
            'analyzers': {}
        }

        # Generate JSON report
        reporter = JSONReporter()
        output_path = temp_output_dir / "audit_report.json"
        reporter.generate(results, str(output_path))

        # Verify report was created
        assert output_path.exists()

        # Parse and verify JSON structure
        with open(output_path, 'r') as f:
            report = json.load(f)

        assert "metadata" in report
        assert "summary" in report
        assert "collectors" in report
        assert "analyzers" in report

        # Verify metadata
        assert report["metadata"]["tool"] == "OmniAudit"
        assert "generated_at" in report["metadata"]

    def test_empty_results_reporting(self, temp_output_dir):
        """Test report generation with empty/minimal data."""
        empty_results = {
            'collectors': {},
            'analyzers': {}
        }

        # Test Markdown reporter with empty data
        md_reporter = MarkdownReporter()
        md_path = temp_output_dir / "empty.md"
        md_reporter.generate(empty_results, str(md_path))
        assert md_path.exists()

        # Test JSON reporter with empty data
        json_reporter = JSONReporter()
        json_path = temp_output_dir / "empty.json"
        json_reporter.generate(empty_results, str(json_path))
        assert json_path.exists()

    def test_report_file_permissions(self, temp_output_dir):
        """Test that generated reports have correct permissions."""
        collector = GitCollector({
            'repo_path': '.',
            'max_commits': 5
        })
        git_result = collector.collect()

        results = {
            'collectors': {
                'git_collector': {
                    'status': 'success',
                    **git_result
                }
            },
            'analyzers': {}
        }

        # Generate report
        reporter = MarkdownReporter()
        output_path = temp_output_dir / "report.md"
        reporter.generate(results, str(output_path))

        # Verify file is readable
        assert os.access(output_path, os.R_OK)
        # Verify file has content
        assert output_path.stat().st_size > 0
