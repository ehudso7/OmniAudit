"""
PR Analyzer Service

Analyzes pull request diffs using AI and multiple analyzers.
"""

import os
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .github_service import GitHubService, PRReviewResult, ReviewComment, ReviewAction
from ..analyzers.code_quality import CodeQualityAnalyzer
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class FileAnalysis:
    """Analysis result for a single file."""
    path: str
    language: str
    issues: List[Dict[str, Any]]
    suggestions: List[Dict[str, Any]]


class PRAnalyzer:
    """
    Analyzes pull requests for issues and improvements.

    Uses multiple analyzers:
    - Security scanning
    - Performance analysis
    - Code quality checks
    - Best practices validation
    """

    SUPPORTED_LANGUAGES = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".rb": "ruby",
        ".php": "php",
        ".cs": "csharp",
        ".cpp": "cpp",
        ".c": "c",
        ".swift": "swift",
        ".kt": "kotlin",
    }

    def __init__(self, github_service: GitHubService):
        self.github = github_service
        self.anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

    async def analyze_pr(
        self,
        owner: str,
        repo: str,
        pr_number: int
    ) -> PRReviewResult:
        """
        Analyze a pull request and generate review.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number

        Returns:
            PRReviewResult with summary and comments
        """
        logger.info(f"Analyzing PR {owner}/{repo}#{pr_number}")

        # Fetch PR details
        pr = await self.github.get_pr(owner, repo, pr_number)
        files = await self.github.get_pr_files(owner, repo, pr_number)

        # Filter to supported files
        analyzable_files = [
            f for f in files
            if self._get_language(f["filename"]) is not None
        ]

        if not analyzable_files:
            return PRReviewResult(
                summary="No analyzable files found in this PR.",
                action=ReviewAction.COMMENT,
                comments=[],
                issues_found=0,
                security_issues=0,
                performance_issues=0,
                suggestions=0
            )

        # Analyze each file
        all_comments: List[ReviewComment] = []
        total_security = 0
        total_performance = 0
        total_suggestions = 0

        for file in analyzable_files[:20]:  # Limit to 20 files
            file_comments = await self._analyze_file(
                owner, repo, pr["head"]["sha"], file
            )
            all_comments.extend(file_comments)

            # Categorize issues
            for comment in file_comments:
                if "security" in comment.body.lower() or "vulnerability" in comment.body.lower():
                    total_security += 1
                elif "performance" in comment.body.lower() or "optimize" in comment.body.lower():
                    total_performance += 1
                else:
                    total_suggestions += 1

        total_issues = len(all_comments)

        # Determine review action
        if total_security > 0:
            action = ReviewAction.REQUEST_CHANGES
        elif total_issues > 5:
            action = ReviewAction.COMMENT
        else:
            action = ReviewAction.APPROVE if total_issues == 0 else ReviewAction.COMMENT

        # Generate summary
        summary = self._generate_summary(
            pr, analyzable_files, total_issues, total_security, total_performance
        )

        return PRReviewResult(
            summary=summary,
            action=action,
            comments=all_comments[:50],  # GitHub limit
            issues_found=total_issues,
            security_issues=total_security,
            performance_issues=total_performance,
            suggestions=total_suggestions
        )

    async def _analyze_file(
        self,
        owner: str,
        repo: str,
        ref: str,
        file: Dict[str, Any]
    ) -> List[ReviewComment]:
        """Analyze a single file and return comments."""
        filename = file["filename"]
        language = self._get_language(filename)

        if not language:
            return []

        # Skip deleted files
        if file.get("status") == "removed":
            return []

        try:
            # Get file content
            content = await self.github.get_file_content(owner, repo, filename, ref)
        except Exception as e:
            logger.warning(f"Could not fetch {filename}: {e}")
            return []

        # Parse the patch to get changed lines
        patch = file.get("patch", "")
        changed_lines = self._parse_patch(patch)

        # Analyze the content
        comments = await self._run_analysis(filename, content, language, changed_lines)

        return comments

    async def _run_analysis(
        self,
        filename: str,
        content: str,
        language: str,
        changed_lines: List[int]
    ) -> List[ReviewComment]:
        """Run AI analysis on file content."""
        if not self.anthropic_key:
            logger.warning("ANTHROPIC_API_KEY not set, skipping AI analysis")
            return self._run_static_analysis(filename, content, language, changed_lines)

        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.anthropic_key)

            # Build prompt
            prompt = self._build_analysis_prompt(filename, content, language, changed_lines)

            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse response into comments
            return self._parse_ai_response(filename, response.content[0].text, changed_lines)

        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return self._run_static_analysis(filename, content, language, changed_lines)

    def _build_analysis_prompt(
        self,
        filename: str,
        content: str,
        language: str,
        changed_lines: List[int]
    ) -> str:
        """Build the AI analysis prompt."""
        return f"""Analyze this {language} code file for issues. Focus ONLY on the changed lines.

File: {filename}
Changed lines: {changed_lines[:20]}

```{language}
{content[:8000]}
```

Find issues in these categories:
1. 🔴 SECURITY: SQL injection, XSS, hardcoded secrets, auth issues
2. ⚡ PERFORMANCE: N+1 queries, unnecessary loops, memory leaks
3. 🐛 BUGS: Null references, race conditions, logic errors
4. 💡 SUGGESTIONS: Better patterns, cleaner code, maintainability

For each issue, respond in this exact format:
LINE: <line_number>
CATEGORY: <SECURITY|PERFORMANCE|BUG|SUGGESTION>
ISSUE: <brief description>
FIX: <suggested fix>
---

Only report issues on the changed lines. Be concise. Maximum 10 issues."""

    def _parse_ai_response(
        self,
        filename: str,
        response: str,
        changed_lines: List[int]
    ) -> List[ReviewComment]:
        """Parse AI response into review comments."""
        comments = []
        issues = response.split("---")

        for issue in issues:
            if not issue.strip():
                continue

            try:
                lines = issue.strip().split("\n")
                line_match = re.search(r"LINE:\s*(\d+)", issue)
                category_match = re.search(r"CATEGORY:\s*(\w+)", issue)
                issue_match = re.search(r"ISSUE:\s*(.+?)(?=FIX:|$)", issue, re.DOTALL)
                fix_match = re.search(r"FIX:\s*(.+)", issue, re.DOTALL)

                if not line_match:
                    continue

                line_num = int(line_match.group(1))

                # Only comment on changed lines
                if changed_lines and line_num not in changed_lines:
                    continue

                category = category_match.group(1) if category_match else "SUGGESTION"
                issue_text = issue_match.group(1).strip() if issue_match else "Issue found"
                fix_text = fix_match.group(1).strip() if fix_match else ""

                # Format comment
                emoji = {
                    "SECURITY": "🔴",
                    "PERFORMANCE": "⚡",
                    "BUG": "🐛",
                    "SUGGESTION": "💡"
                }.get(category, "💡")

                body = f"{emoji} **{category}**: {issue_text}"
                if fix_text:
                    body += f"\n\n**Suggested fix:**\n```\n{fix_text}\n```"

                comments.append(ReviewComment(
                    path=filename,
                    line=line_num,
                    body=body
                ))

            except Exception as e:
                logger.debug(f"Failed to parse issue: {e}")
                continue

        return comments[:10]  # Limit per file

    def _run_static_analysis(
        self,
        filename: str,
        content: str,
        language: str,
        changed_lines: List[int]
    ) -> List[ReviewComment]:
        """Run basic static analysis without AI."""
        comments = []

        # Security patterns
        security_patterns = [
            (r"eval\s*\(", "Avoid using eval() - security risk"),
            (r"exec\s*\(", "Avoid using exec() - security risk"),
            (r"password\s*=\s*['\"][^'\"]+['\"]", "Possible hardcoded password"),
            (r"api_key\s*=\s*['\"][^'\"]+['\"]", "Possible hardcoded API key"),
            (r"secret\s*=\s*['\"][^'\"]+['\"]", "Possible hardcoded secret"),
            (r"innerHTML\s*=", "Using innerHTML can lead to XSS vulnerabilities"),
            (r"dangerouslySetInnerHTML", "dangerouslySetInnerHTML can lead to XSS"),
        ]

        # Performance patterns
        performance_patterns = [
            (r"\.forEach\(.*\.forEach\(", "Nested forEach loops - consider refactoring"),
            (r"SELECT\s+\*\s+FROM", "SELECT * can be inefficient - specify columns"),
            (r"console\.log\(", "Remove console.log in production"),
        ]

        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            if changed_lines and i not in changed_lines:
                continue

            for pattern, message in security_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    comments.append(ReviewComment(
                        path=filename,
                        line=i,
                        body=f"🔴 **SECURITY**: {message}"
                    ))
                    break

            for pattern, message in performance_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    comments.append(ReviewComment(
                        path=filename,
                        line=i,
                        body=f"⚡ **PERFORMANCE**: {message}"
                    ))
                    break

        return comments[:10]

    def _parse_patch(self, patch: str) -> List[int]:
        """Parse git patch to extract changed line numbers."""
        if not patch:
            return []

        changed_lines = []
        current_line = 0

        for line in patch.split("\n"):
            # Parse hunk header: @@ -start,count +start,count @@
            hunk_match = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
            if hunk_match:
                current_line = int(hunk_match.group(1))
                continue

            if line.startswith("+") and not line.startswith("+++"):
                changed_lines.append(current_line)
                current_line += 1
            elif line.startswith("-") and not line.startswith("---"):
                # Deleted line, don't increment
                pass
            else:
                current_line += 1

        return changed_lines

    def _get_language(self, filename: str) -> Optional[str]:
        """Get language from file extension."""
        for ext, lang in self.SUPPORTED_LANGUAGES.items():
            if filename.endswith(ext):
                return lang
        return None

    def _generate_summary(
        self,
        pr: Dict[str, Any],
        files: List[Dict[str, Any]],
        total_issues: int,
        security_issues: int,
        performance_issues: int
    ) -> str:
        """Generate PR summary."""
        if total_issues == 0:
            return f"""Great work! 🎉 This PR looks good.

**Files analyzed:** {len(files)}
**Issues found:** 0

The code changes in this PR pass all OmniAudit checks."""

        severity = "requires attention" if security_issues > 0 else "has some suggestions"

        return f"""This PR {severity}.

**Files analyzed:** {len(files)}
**Total issues:** {total_issues}

Please review the inline comments below for specific improvements."""
