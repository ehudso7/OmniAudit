"""
JSON Reporter

Generates structured JSON reports from audit data.
"""

import json
from datetime import datetime
from typing import Any, Dict
from .base import BaseReporter


class JSONReporter(BaseReporter):
    """Generates JSON-formatted audit reports."""

    @property
    def name(self) -> str:
        """Return reporter name."""
        return "json_reporter"

    @property
    def format(self) -> str:
        """Return output format."""
        return "json"

    def generate(self, data: Dict[str, Any], output_path: str) -> None:
        """
        Generate JSON report from audit data.

        Args:
            data: Audit results data
            output_path: Path to save the report
        """
        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "tool": "OmniAudit",
                "version": "1.0.0",
                "format_version": "1.0"
            },
            "summary": self._generate_summary(data),
            "collectors": self._process_collectors(data.get("collectors", {})),
            "analyzers": self._process_analyzers(data.get("analyzers", {}))
        }

        # Write formatted JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    def _generate_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary metrics."""
        collectors = data.get("collectors", {})
        analyzers = data.get("analyzers", {})

        summary = {
            "total_collectors": len(collectors),
            "total_analyzers": len(analyzers),
            "collectors_success": sum(1 for c in collectors.values() if c.get("status") == "success"),
            "analyzers_success": sum(1 for a in analyzers.values() if a.get("status") == "success"),
        }

        # Git metrics
        if "git_collector" in collectors:
            git_data = collectors["git_collector"].get("data", {})
            summary["git"] = {
                "total_commits": git_data.get("commits_count", 0),
                "contributors": git_data.get("contributors_count", 0),
                "branches": len(git_data.get("branches", [])),
                "total_lines_changed": git_data.get("total_lines_changed", 0)
            }

        # GitHub metrics
        if "github_collector" in collectors:
            github_data = collectors["github_collector"].get("data", {})
            summary["github"] = {
                "stars": github_data.get("stars", 0),
                "forks": github_data.get("forks", 0),
                "open_issues": github_data.get("open_issues", 0),
                "watchers": github_data.get("watchers", 0)
            }

        # Code quality metrics
        if "code_quality" in analyzers:
            quality_data = analyzers["code_quality"].get("data", {})
            summary["quality"] = {
                "overall_score": quality_data.get("overall_score", 0.0),
                "languages_analyzed": list(quality_data.get("metrics", {}).keys()),
                "total_issues": len(quality_data.get("issues", []))
            }

        return summary

    def _process_collectors(self, collectors: Dict[str, Any]) -> Dict[str, Any]:
        """Process collector results."""
        processed = {}

        for collector_name, result in collectors.items():
            processed[collector_name] = {
                "status": result.get("status"),
                "duration": result.get("duration"),
                "data": result.get("data", {}),
                "error": result.get("error")
            }

        return processed

    def _process_analyzers(self, analyzers: Dict[str, Any]) -> Dict[str, Any]:
        """Process analyzer results."""
        processed = {}

        for analyzer_name, result in analyzers.items():
            processed[analyzer_name] = {
                "status": result.get("status"),
                "duration": result.get("duration"),
                "data": result.get("data", {}),
                "error": result.get("error")
            }

        return processed
