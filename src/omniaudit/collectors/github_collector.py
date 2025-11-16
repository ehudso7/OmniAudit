"""
GitHub API Collector

Fetches data from GitHub API including pull requests, issues,
workflows, and repository metadata.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import os

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None

from .base import BaseCollector, ConfigurationError, DataCollectionError


class GitHubCollector(BaseCollector):
    """
    Collects data from GitHub API.

    Requires GitHub personal access token for authentication.
    Fetches PRs, issues, workflows, and repository stats.

    Configuration:
        owner: str - Repository owner/organization (required)
        repo: str - Repository name (required)
        token: str - GitHub personal access token (required)
        since_days: int - Collect data from last N days (default: 30)

    Example:
        >>> config = {
        ...     "owner": "python",
        ...     "repo": "cpython",
        ...     "token": os.getenv("GITHUB_TOKEN")
        ... }
        >>> collector = GitHubCollector(config)
        >>> result = collector.collect()
    """

    @property
    def name(self) -> str:
        return "github_collector"

    @property
    def version(self) -> str:
        return "0.1.0"

    def _validate_config(self) -> None:
        """Validate GitHub collector configuration."""
        if not REQUESTS_AVAILABLE:
            raise ConfigurationError(
                "requests library not installed. "
                "Install with: pip install requests"
            )

        required = ["owner", "repo", "token"]
        for field in required:
            if field not in self.config:
                raise ConfigurationError(f"{field} is required in configuration")

        if not self.config["token"]:
            raise ConfigurationError("GitHub token cannot be empty")

    def collect(self) -> Dict[str, Any]:
        """
        Collect data from GitHub API.

        Returns:
            Dictionary with PRs, issues, workflows, and stats

        Raises:
            DataCollectionError: If collection fails
        """
        owner = self.config["owner"]
        repo = self.config["repo"]
        token = self.config["token"]
        since_days = self.config.get("since_days", 30)

        since_date = datetime.utcnow() - timedelta(days=since_days)

        try:
            # Collect data from various endpoints
            pull_requests = self._fetch_pull_requests(owner, repo, token, since_date)
            issues = self._fetch_issues(owner, repo, token, since_date)
            workflows = self._fetch_workflows(owner, repo, token)
            repo_stats = self._fetch_repository_stats(owner, repo, token)

            data = {
                "owner": owner,
                "repository": repo,
                "pull_requests_count": len(pull_requests),
                "pull_requests": pull_requests,
                "issues_count": len(issues),
                "issues": issues,
                "workflows_count": len(workflows),
                "workflows": workflows,
                "repository_stats": repo_stats
            }

            metadata = {
                "collection_params": {
                    "since_days": since_days,
                    "since_date": since_date.isoformat()
                }
            }

            return self._create_response(data, metadata)

        except requests.exceptions.RequestException as e:
            raise DataCollectionError(f"GitHub API request failed: {e}")
        except Exception as e:
            raise DataCollectionError(f"Unexpected error: {e}")

    def _make_request(self, url: str, token: str,
                     params: Optional[Dict] = None) -> Any:
        """Make authenticated GitHub API request."""
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

        response = requests.get(url, headers=headers, params=params or {})
        response.raise_for_status()

        return response.json()

    def _fetch_pull_requests(self, owner: str, repo: str,
                            token: str, since: datetime) -> List[Dict[str, Any]]:
        """Fetch pull requests."""
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
        params = {
            "state": "all",
            "sort": "updated",
            "direction": "desc",
            "per_page": 100
        }

        data = self._make_request(url, token, params)

        prs = []
        for pr in data:
            updated_at = datetime.fromisoformat(
                pr["updated_at"].replace("Z", "+00:00")
            )

            if updated_at < since:
                continue

            prs.append({
                "number": pr["number"],
                "title": pr["title"],
                "state": pr["state"],
                "author": pr["user"]["login"],
                "created_at": pr["created_at"],
                "updated_at": pr["updated_at"],
                "merged_at": pr.get("merged_at"),
                "closed_at": pr.get("closed_at"),
                "additions": pr.get("additions", 0),
                "deletions": pr.get("deletions", 0),
                "changed_files": pr.get("changed_files", 0)
            })

        return prs

    def _fetch_issues(self, owner: str, repo: str,
                     token: str, since: datetime) -> List[Dict[str, Any]]:
        """Fetch issues (excluding PRs)."""
        url = f"https://api.github.com/repos/{owner}/{repo}/issues"
        params = {
            "state": "all",
            "sort": "updated",
            "direction": "desc",
            "per_page": 100
        }

        data = self._make_request(url, token, params)

        issues = []
        for issue in data:
            # Skip pull requests
            if "pull_request" in issue:
                continue

            updated_at = datetime.fromisoformat(
                issue["updated_at"].replace("Z", "+00:00")
            )

            if updated_at < since:
                continue

            issues.append({
                "number": issue["number"],
                "title": issue["title"],
                "state": issue["state"],
                "author": issue["user"]["login"],
                "created_at": issue["created_at"],
                "updated_at": issue["updated_at"],
                "closed_at": issue.get("closed_at"),
                "labels": [label["name"] for label in issue.get("labels", [])]
            })

        return issues

    def _fetch_workflows(self, owner: str, repo: str,
                        token: str) -> List[Dict[str, Any]]:
        """Fetch GitHub Actions workflows."""
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows"

        try:
            data = self._make_request(url, token)
            workflows = []

            for workflow in data.get("workflows", []):
                workflows.append({
                    "id": workflow["id"],
                    "name": workflow["name"],
                    "path": workflow["path"],
                    "state": workflow["state"],
                    "created_at": workflow["created_at"]
                })

            return workflows

        except requests.exceptions.HTTPError:
            # Workflows might not be available
            return []

    def _fetch_repository_stats(self, owner: str, repo: str,
                               token: str) -> Dict[str, Any]:
        """Fetch repository statistics."""
        url = f"https://api.github.com/repos/{owner}/{repo}"
        data = self._make_request(url, token)

        return {
            "stars": data.get("stargazers_count", 0),
            "forks": data.get("forks_count", 0),
            "watchers": data.get("watchers_count", 0),
            "open_issues": data.get("open_issues_count", 0),
            "default_branch": data.get("default_branch", "main"),
            "language": data.get("language"),
            "size_kb": data.get("size", 0),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "pushed_at": data.get("pushed_at")
        }
