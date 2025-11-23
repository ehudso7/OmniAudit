"""
Markdown Reporter

Generates human-readable Markdown reports from audit data.
"""

from datetime import datetime
from typing import Any, Dict, List
from .base import BaseReporter


class MarkdownReporter(BaseReporter):
    """Generates Markdown-formatted audit reports."""

    @property
    def name(self) -> str:
        """Return reporter name."""
        return "markdown_reporter"

    @property
    def format(self) -> str:
        """Return output format."""
        return "markdown"

    def generate(self, data: Dict[str, Any], output_path: str) -> None:
        """
        Generate Markdown report from audit data.

        Args:
            data: Audit results data
            output_path: Path to save the report
        """
        sections = []

        # Header
        sections.append(self._generate_header())
        sections.append("")

        # Summary
        sections.append(self._generate_summary(data))
        sections.append("")

        # Git Analysis
        if "git_collector" in data.get("collectors", {}):
            sections.append(self._generate_git_section(data["collectors"]["git_collector"]))
            sections.append("")

        # GitHub Analysis
        if "github_collector" in data.get("collectors", {}):
            sections.append(self._generate_github_section(data["collectors"]["github_collector"]))
            sections.append("")

        # Code Quality Analysis
        if "code_quality" in data.get("analyzers", {}):
            sections.append(self._generate_quality_section(data["analyzers"]["code_quality"]))
            sections.append("")

        # Footer
        sections.append(self._generate_footer())

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(sections))

    def _generate_header(self) -> str:
        """Generate report header."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"""# 🔍 OmniAudit Report

**Generated:** {timestamp}

---"""

    def _generate_summary(self, data: Dict[str, Any]) -> str:
        """Generate summary section."""
        lines = ["## 📊 Summary", ""]

        collectors = data.get("collectors", {})
        analyzers = data.get("analyzers", {})

        # Calculate summary metrics
        total_commits = 0
        total_contributors = 0
        quality_score = 0.0

        if "git_collector" in collectors:
            git_data = collectors["git_collector"].get("data", {})
            total_commits = git_data.get("commits_count", 0)
            total_contributors = git_data.get("contributors_count", 0)

        if "code_quality" in analyzers:
            quality_data = analyzers["code_quality"].get("data", {})
            quality_score = quality_data.get("overall_score", 0.0)

        # Create summary table
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Total Commits | {total_commits} |")
        lines.append(f"| Contributors | {total_contributors} |")
        lines.append(f"| Quality Score | {quality_score:.2f}/100 |")
        lines.append(f"| Collectors Run | {len(collectors)} |")
        lines.append(f"| Analyzers Run | {len(analyzers)} |")

        return '\n'.join(lines)

    def _generate_git_section(self, git_result: Dict[str, Any]) -> str:
        """Generate Git analysis section."""
        lines = ["## 📦 Git Repository Analysis", ""]

        if git_result.get("status") != "success":
            lines.append(f"**Status:** Failed - {git_result.get('error', 'Unknown error')}")
            return '\n'.join(lines)

        data = git_result.get("data", {})

        # Repository Info
        lines.append("### Repository Information")
        lines.append("")
        lines.append(f"- **Total Commits:** {data.get('commits_count', 0)}")
        lines.append(f"- **Contributors:** {data.get('contributors_count', 0)}")
        lines.append(f"- **Branches:** {len(data.get('branches', []))}")
        lines.append(f"- **Total Lines Changed:** {data.get('total_lines_changed', 0)}")
        lines.append("")

        # Top Contributors
        contributors = data.get("contributors", [])
        if contributors:
            lines.append("### Top Contributors")
            lines.append("")
            lines.append("| Name | Commits | Insertions | Deletions | Lines Changed |")
            lines.append("|------|---------|------------|-----------|---------------|")

            for contributor in contributors[:10]:
                name = contributor.get("name", "Unknown")
                commits = contributor.get("commits", 0)
                insertions = contributor.get("insertions", 0)
                deletions = contributor.get("deletions", 0)
                lines_changed = contributor.get("lines_changed", 0)
                lines.append(f"| {name} | {commits} | +{insertions} | -{deletions} | {lines_changed} |")

        return '\n'.join(lines)

    def _generate_github_section(self, github_result: Dict[str, Any]) -> str:
        """Generate GitHub analysis section."""
        lines = ["## 🐙 GitHub Analysis", ""]

        if github_result.get("status") != "success":
            lines.append(f"**Status:** Failed - {github_result.get('error', 'Unknown error')}")
            return '\n'.join(lines)

        data = github_result.get("data", {})

        # Repository Stats
        lines.append("### Repository Stats")
        lines.append("")
        lines.append(f"- **Stars:** {data.get('stars', 0)}")
        lines.append(f"- **Forks:** {data.get('forks', 0)}")
        lines.append(f"- **Open Issues:** {data.get('open_issues', 0)}")
        lines.append(f"- **Watchers:** {data.get('watchers', 0)}")
        lines.append("")

        # Pull Requests
        prs = data.get("pull_requests", [])
        if prs:
            lines.append("### Recent Pull Requests")
            lines.append("")
            lines.append("| Title | State | Author | Created |")
            lines.append("|-------|-------|--------|---------|")

            for pr in prs[:10]:
                title = pr.get("title", "")[:50]
                state = pr.get("state", "")
                author = pr.get("author", "")
                created = pr.get("created_at", "")[:10]
                lines.append(f"| {title} | {state} | {author} | {created} |")
            lines.append("")

        # Issues
        issues = data.get("issues", [])
        if issues:
            lines.append("### Recent Issues")
            lines.append("")
            lines.append("| Title | State | Author | Created |")
            lines.append("|-------|-------|--------|---------|")

            for issue in issues[:10]:
                title = issue.get("title", "")[:50]
                state = issue.get("state", "")
                author = issue.get("author", "")
                created = issue.get("created_at", "")[:10]
                lines.append(f"| {title} | {state} | {author} | {created} |")

        return '\n'.join(lines)

    def _generate_quality_section(self, quality_result: Dict[str, Any]) -> str:
        """Generate code quality analysis section."""
        lines = ["## ⭐ Code Quality Analysis", ""]

        if quality_result.get("status") != "success":
            lines.append(f"**Status:** Failed - {quality_result.get('error', 'Unknown error')}")
            return '\n'.join(lines)

        data = quality_result.get("data", {})

        # Overall Score
        overall_score = data.get("overall_score", 0.0)
        lines.append(f"### Overall Quality Score: {overall_score:.2f}/100")
        lines.append("")

        # Language Metrics
        metrics = data.get("metrics", {})
        if metrics:
            lines.append("### Language Metrics")
            lines.append("")

            for language, lang_data in metrics.items():
                lines.append(f"#### {language.title()}")
                lines.append("")
                lines.append("| Metric | Value |")
                lines.append("|--------|-------|")
                lines.append(f"| Files | {lang_data.get('files', 0)} |")
                lines.append(f"| Lines of Code | {lang_data.get('loc', 0)} |")
                lines.append(f"| Complexity | {lang_data.get('complexity', 0.0):.2f} |")
                lines.append(f"| Maintainability | {lang_data.get('maintainability', 0.0):.2f} |")

                if 'coverage' in lang_data and lang_data['coverage'] > 0:
                    lines.append(f"| Test Coverage | {lang_data['coverage']:.1f}% |")

                lines.append("")

        # Issues
        issues = data.get("issues", [])
        if issues:
            lines.append("### Quality Issues")
            lines.append("")
            lines.append("| Severity | File | Line | Message |")
            lines.append("|----------|------|------|---------|")

            for issue in issues[:20]:
                severity = issue.get("severity", "INFO")
                file_path = issue.get("file", "")[:40]
                line = issue.get("line", "")
                message = issue.get("message", "")[:60]
                lines.append(f"| {severity} | {file_path} | {line} | {message} |")

        return '\n'.join(lines)

    def _generate_footer(self) -> str:
        """Generate report footer."""
        return """---

*Report generated by OmniAudit - Universal Project Auditing & Monitoring*"""
