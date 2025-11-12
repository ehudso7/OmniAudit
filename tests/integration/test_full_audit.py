"""
Integration tests for full audit workflow.

Tests end-to-end functionality combining collectors, analyzers, and reporters.
"""

import os
import tempfile
from pathlib import Path
import pytest

from omniaudit.core.engine import AuditEngine
from omniaudit.collectors.git_collector import GitCollector
from omniaudit.analyzers.code_analyzer import CodeQualityAnalyzer
from omniaudit.reporters import MarkdownReporter, JSONReporter


class TestFullAuditWorkflow:
    """Test complete audit workflow from collection to reporting."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def audit_engine(self):
        """Create audit engine instance."""
        return AuditEngine()

    def test_git_collection_and_analysis(self, audit_engine, temp_output_dir):
        """Test Git collection with code analysis."""
        # Configure collectors
        audit_engine.add_collector(
            GitCollector({
                'repo_path': '.',
                'max_commits': 50
            })
        )

        # Configure analyzers
        audit_engine.add_analyzer(
            CodeQualityAnalyzer({
                'project_path': '.',
                'languages': ['python']
            })
        )

        # Run audit
        results = audit_engine.run()

        # Verify results structure
        assert 'collectors' in results
        assert 'analyzers' in results
        assert 'git_collector' in results['collectors']
        assert 'code_quality' in results['analyzers']

        # Verify Git collector results
        git_result = results['collectors']['git_collector']
        assert git_result['status'] == 'success'
        assert 'data' in git_result
        assert 'commits' in git_result['data']
        assert 'contributors' in git_result['data']
        assert len(git_result['data']['commits']) > 0

        # Verify code quality results
        quality_result = results['analyzers']['code_quality']
        assert quality_result['status'] == 'success'
        assert 'data' in quality_result
        assert 'metrics' in quality_result['data']
        assert 'overall_score' in quality_result['data']

    def test_markdown_report_generation(self, audit_engine, temp_output_dir):
        """Test generating Markdown report."""
        # Setup and run audit
        audit_engine.add_collector(
            GitCollector({
                'repo_path': '.',
                'max_commits': 50
            })
        )

        results = audit_engine.run()

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
        assert "Total Commits" in content
        assert "Contributors" in content

    def test_json_report_generation(self, audit_engine, temp_output_dir):
        """Test generating JSON report."""
        import json

        # Setup and run audit
        audit_engine.add_collector(
            GitCollector({
                'repo_path': '.',
                'max_commits': 50
            })
        )

        results = audit_engine.run()

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

        # Verify summary
        assert report["summary"]["total_collectors"] > 0

    def test_multi_collector_workflow(self, audit_engine, temp_output_dir):
        """Test workflow with multiple collectors."""
        # Add multiple collectors
        audit_engine.add_collector(
            GitCollector({
                'repo_path': '.',
                'max_commits': 50
            })
        )

        # Add analyzer
        audit_engine.add_analyzer(
            CodeQualityAnalyzer({
                'project_path': '.',
                'languages': ['python']
            })
        )

        # Run audit
        results = audit_engine.run()

        # Verify all components ran
        assert len(results['collectors']) >= 1
        assert len(results['analyzers']) >= 1

        # Generate both report formats
        md_reporter = MarkdownReporter()
        json_reporter = JSONReporter()

        md_path = temp_output_dir / "report.md"
        json_path = temp_output_dir / "report.json"

        md_reporter.generate(results, str(md_path))
        json_reporter.generate(results, str(json_path))

        assert md_path.exists()
        assert json_path.exists()

    def test_error_handling_in_workflow(self, audit_engine):
        """Test that workflow handles errors gracefully."""
        # Add collector with invalid configuration
        audit_engine.add_collector(
            GitCollector({
                'repo_path': '/nonexistent/path',
                'max_commits': 10
            })
        )

        # Run should not crash, but return error status
        results = audit_engine.run()

        git_result = results['collectors']['git_collector']
        assert git_result['status'] == 'error'
        assert 'error' in git_result

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

    def test_report_file_permissions(self, audit_engine, temp_output_dir):
        """Test that generated reports have correct permissions."""
        # Run basic audit
        audit_engine.add_collector(
            GitCollector({
                'repo_path': '.',
                'max_commits': 10
            })
        )

        results = audit_engine.run()

        # Generate report
        reporter = MarkdownReporter()
        output_path = temp_output_dir / "report.md"
        reporter.generate(results, str(output_path))

        # Verify file is readable
        assert os.access(output_path, os.R_OK)
        # Verify file has content
        assert output_path.stat().st_size > 0
