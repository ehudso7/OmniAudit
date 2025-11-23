"""
Git Collector - Repository Analysis

Collects commit history, branch information, and contributor statistics
from Git repositories (local or remote).
"""

import os
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path

try:
    from git import Repo, GitCommandError
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    Repo = None
    GitCommandError = Exception

from .base import BaseCollector, ConfigurationError, DataCollectionError


class GitCollector(BaseCollector):
    """
    Collects data from Git repositories.

    Supports both local repositories and remote cloning.
    Extracts commit history, branch information, and contributor stats.

    Configuration:
        repo_path: str - Path to local repository (required)
        branch: str - Branch to analyze (default: current branch)
        since: str - ISO date to collect commits from (optional)
        max_commits: int - Maximum commits to collect (default: 1000)

    Example:
        >>> config = {"repo_path": "/path/to/repo"}
        >>> collector = GitCollector(config)
        >>> result = collector.collect()
        >>> print(result["data"]["commits_count"])
    """

    @property
    def name(self) -> str:
        return "git_collector"

    @property
    def version(self) -> str:
        return "0.1.0"

    def _validate_config(self) -> None:
        """
        Validate Git collector configuration.

        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not GIT_AVAILABLE:
            raise ConfigurationError(
                "GitPython is not installed. "
                "Install with: pip install gitpython"
            )

        if "repo_path" not in self.config:
            raise ConfigurationError("repo_path is required in configuration")

        repo_path = Path(self.config["repo_path"])
        if not repo_path.exists():
            raise ConfigurationError(f"Repository path does not exist: {repo_path}")

        if not (repo_path / ".git").exists():
            raise ConfigurationError(f"Not a git repository: {repo_path}")

    def collect(self) -> Dict[str, Any]:
        """
        Collect data from Git repository.

        Returns:
            Dictionary with commit history, branches, and contributors

        Raises:
            DataCollectionError: If collection fails
        """
        try:
            repo = Repo(self.config["repo_path"])

            # Get configuration parameters
            branch = self.config.get("branch", None)
            since = self._parse_since_date(self.config.get("since"))
            max_commits = self.config.get("max_commits", 1000)

            # Collect data
            commits = self._collect_commits(repo, branch, since, max_commits)
            branches = self._collect_branches(repo)
            contributors = self._collect_contributors(commits)

            # Handle detached HEAD state
            current_branch = self._get_current_branch(repo)

            data = {
                "repository_path": str(self.config["repo_path"]),
                "current_branch": current_branch,
                "commits_count": len(commits),
                "commits": commits,
                "branches_count": len(branches),
                "branches": branches,
                "contributors_count": len(contributors),
                "contributors": contributors
            }

            metadata = {
                "collection_params": {
                    "branch": branch or "current",
                    "since": since.isoformat() if since else None,
                    "max_commits": max_commits
                }
            }

            return self._create_response(data, metadata)

        except GitCommandError as e:
            raise DataCollectionError(f"Git operation failed: {e}")
        except Exception as e:
            raise DataCollectionError(f"Unexpected error: {e}")

    def _get_current_branch(self, repo: "Repo") -> str:
        """
        Get current branch name, handling detached HEAD state.

        Args:
            repo: GitPython Repo object

        Returns:
            Branch name or "detached HEAD" with commit SHA
        """
        try:
            return str(repo.active_branch)
        except TypeError:
            # HEAD is detached
            return f"detached HEAD ({repo.head.commit.hexsha[:7]})"

    def _parse_since_date(self, since: Optional[str]) -> Optional[datetime]:
        """Parse since date string to datetime."""
        if not since:
            return None
        try:
            return datetime.fromisoformat(since.replace("Z", "+00:00"))
        except ValueError:
            raise ConfigurationError(f"Invalid date format for 'since': {since}")

    def _collect_commits(self, repo: "Repo", branch: Optional[str],
                        since: Optional[datetime], max_commits: int) -> List[Dict[str, Any]]:
        """
        Collect commit history.

        Args:
            repo: GitPython Repo object
            branch: Branch name or None for current
            since: Filter commits after this date
            max_commits: Maximum number of commits

        Returns:
            List of commit dictionaries
        """
        commits = []
        if branch:
            rev = branch
        else:
            # Handle detached HEAD state by using HEAD
            try:
                rev = repo.active_branch.name
            except TypeError:
                rev = "HEAD"

        for commit in repo.iter_commits(rev, max_count=max_commits):
            commit_date = datetime.fromtimestamp(commit.committed_date)

            # Filter by date if specified
            if since and commit_date < since:
                continue

            commits.append({
                "sha": commit.hexsha,
                "short_sha": commit.hexsha[:7],
                "author": commit.author.name,
                "author_email": commit.author.email,
                "date": commit_date.isoformat(),
                "message": commit.message.strip(),
                "files_changed": len(commit.stats.files),
                "insertions": commit.stats.total["insertions"],
                "deletions": commit.stats.total["deletions"],
                "lines_changed": commit.stats.total["lines"]
            })

        return commits

    def _collect_branches(self, repo: "Repo") -> List[Dict[str, Any]]:
        """
        Collect branch information.

        Args:
            repo: GitPython Repo object

        Returns:
            List of branch dictionaries
        """
        branches = []

        # Get current branch, handling detached HEAD
        try:
            active_branch = repo.active_branch
        except TypeError:
            active_branch = None

        for branch in repo.branches:
            branches.append({
                "name": branch.name,
                "commit_sha": branch.commit.hexsha,
                "is_current": branch == active_branch if active_branch else False
            })

        return branches

    def _collect_contributors(self, commits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Aggregate contributor statistics from commits.

        Args:
            commits: List of commit dictionaries

        Returns:
            List of contributor dictionaries with statistics
        """
        contributors_map: Dict[str, Dict[str, Any]] = {}

        for commit in commits:
            author = commit["author"]
            email = commit["author_email"]

            if author not in contributors_map:
                contributors_map[author] = {
                    "name": author,
                    "email": email,
                    "commits": 0,
                    "insertions": 0,
                    "deletions": 0,
                    "lines_changed": 0
                }

            contributors_map[author]["commits"] += 1
            contributors_map[author]["insertions"] += commit["insertions"]
            contributors_map[author]["deletions"] += commit["deletions"]
            contributors_map[author]["lines_changed"] += commit["lines_changed"]

        # Sort by commit count
        return sorted(
            contributors_map.values(),
            key=lambda x: x["commits"],
            reverse=True
        )
