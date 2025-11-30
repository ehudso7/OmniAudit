"""
GitHub Service - PR Review and Comment Posting

Handles all GitHub API interactions for automated PR reviews.
"""

import os
import hmac
import hashlib
import httpx
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ReviewAction(Enum):
    """GitHub PR review actions."""
    APPROVE = "APPROVE"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    COMMENT = "COMMENT"


@dataclass
class ReviewComment:
    """A single review comment on a specific line."""
    path: str
    line: int
    body: str
    side: str = "RIGHT"  # LEFT for deletions, RIGHT for additions


@dataclass
class PRReviewResult:
    """Result of analyzing a PR."""
    summary: str
    action: ReviewAction
    comments: List[ReviewComment]
    issues_found: int
    security_issues: int
    performance_issues: int
    suggestions: int


class GitHubService:
    """
    GitHub API service for PR reviews.

    Handles:
    - Fetching PR diffs
    - Posting review comments
    - Creating check runs
    - Managing installations
    """

    BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None, app_id: Optional[str] = None,
                 private_key: Optional[str] = None):
        """
        Initialize GitHub service.

        Args:
            token: Personal access token or installation token
            app_id: GitHub App ID (for app authentication)
            private_key: GitHub App private key (for app authentication)
        """
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.app_id = app_id or os.environ.get("GITHUB_APP_ID")
        self.private_key = private_key or os.environ.get("GITHUB_APP_PRIVATE_KEY")

        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=self._get_headers(),
            timeout=30.0
        )

    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def get_pr(self, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        """Fetch PR details."""
        response = await self._client.get(f"/repos/{owner}/{repo}/pulls/{pr_number}")
        response.raise_for_status()
        return response.json()

    async def get_pr_files(self, owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        """Fetch files changed in a PR."""
        response = await self._client.get(
            f"/repos/{owner}/{repo}/pulls/{pr_number}/files",
            params={"per_page": 100}
        )
        response.raise_for_status()
        return response.json()

    async def get_file_content(self, owner: str, repo: str, path: str, ref: str) -> str:
        """Fetch file content at a specific ref."""
        response = await self._client.get(
            f"/repos/{owner}/{repo}/contents/{path}",
            params={"ref": ref},
            headers={**self._get_headers(), "Accept": "application/vnd.github.v3.raw"}
        )
        response.raise_for_status()
        return response.text

    async def create_review(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        result: PRReviewResult
    ) -> Dict[str, Any]:
        """
        Create a PR review with comments.

        This is the main method for posting OmniAudit reviews.
        """
        # Build the review body
        body = self._build_review_body(result)

        # Build review comments
        comments = [
            {
                "path": c.path,
                "line": c.line,
                "body": c.body,
                "side": c.side
            }
            for c in result.comments
        ]

        # Create the review
        review_data = {
            "body": body,
            "event": result.action.value,
            "comments": comments[:50]  # GitHub limits to 50 comments per review
        }

        response = await self._client.post(
            f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews",
            json=review_data
        )
        response.raise_for_status()

        logger.info(f"Posted review on {owner}/{repo}#{pr_number} with {len(comments)} comments")
        return response.json()

    async def create_check_run(
        self,
        owner: str,
        repo: str,
        head_sha: str,
        result: PRReviewResult
    ) -> Dict[str, Any]:
        """Create a check run for the PR."""
        status = "completed"
        conclusion = "success" if result.security_issues == 0 else "failure"

        if result.issues_found > 10:
            conclusion = "failure"
        elif result.issues_found > 0:
            conclusion = "neutral"

        check_data = {
            "name": "OmniAudit",
            "head_sha": head_sha,
            "status": status,
            "conclusion": conclusion,
            "output": {
                "title": f"OmniAudit found {result.issues_found} issues",
                "summary": result.summary,
                "text": self._build_check_details(result)
            }
        }

        response = await self._client.post(
            f"/repos/{owner}/{repo}/check-runs",
            json=check_data
        )
        response.raise_for_status()
        return response.json()

    async def post_comment(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        body: str
    ) -> Dict[str, Any]:
        """Post a general comment on the PR."""
        response = await self._client.post(
            f"/repos/{owner}/{repo}/issues/{pr_number}/comments",
            json={"body": body}
        )
        response.raise_for_status()
        return response.json()

    def _build_review_body(self, result: PRReviewResult) -> str:
        """Build the review summary body."""
        emoji = "✅" if result.issues_found == 0 else "⚠️" if result.security_issues == 0 else "🚨"

        body = f"""## {emoji} OmniAudit Review

{result.summary}

### Summary
| Category | Count |
|----------|-------|
| 🔴 Security Issues | {result.security_issues} |
| ⚡ Performance Issues | {result.performance_issues} |
| 💡 Suggestions | {result.suggestions} |
| **Total Issues** | **{result.issues_found}** |

---
<details>
<summary>🤖 Powered by OmniAudit</summary>

[OmniAudit](https://github.com/ehudso7/OmniAudit) - Universal AI Code Analysis & Optimization

**AI Skills Used:**
- Performance Optimizer Pro
- Security Auditor
- Architecture Advisor

</details>
"""
        return body

    def _build_check_details(self, result: PRReviewResult) -> str:
        """Build detailed check run output."""
        return f"""
## Detailed Analysis

### Security ({result.security_issues} issues)
Security issues require immediate attention before merging.

### Performance ({result.performance_issues} issues)
Performance issues may impact application speed and resource usage.

### Code Quality ({result.suggestions} suggestions)
Suggestions to improve code maintainability and readability.

---
Generated by OmniAudit v0.3.0
"""

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()


class GitHubAppAuth:
    """
    GitHub App authentication handler.

    Generates installation tokens for GitHub App authentication.
    """

    def __init__(self, app_id: str, private_key: str):
        self.app_id = app_id
        self.private_key = private_key

    def generate_jwt(self) -> str:
        """Generate a JWT for GitHub App authentication."""
        import jwt
        import time

        now = int(time.time())
        payload = {
            "iat": now - 60,  # Issued 60 seconds ago
            "exp": now + (10 * 60),  # Expires in 10 minutes
            "iss": self.app_id
        }

        return jwt.encode(payload, self.private_key, algorithm="RS256")

    async def get_installation_token(self, installation_id: int) -> str:
        """Get an installation access token."""
        jwt_token = self.generate_jwt()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.github.com/app/installations/{installation_id}/access_tokens",
                headers={
                    "Authorization": f"Bearer {jwt_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            response.raise_for_status()
            return response.json()["token"]
