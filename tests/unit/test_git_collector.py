"""Unit tests for GitCollector."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.omniaudit.collectors.git_collector import GitCollector
from src.omniaudit.collectors.base import ConfigurationError, DataCollectionError


@patch('src.omniaudit.collectors.git_collector.GIT_AVAILABLE', True)
def test_git_collector_properties():
    """Test collector properties."""
    # Mock valid repo path
    with patch('src.omniaudit.collectors.git_collector.Path.exists', return_value=True):
        with patch('pathlib.Path.exists', return_value=True):
            config = {"repo_path": "/fake/repo"}
            collector = GitCollector(config)

            assert collector.name == "git_collector"
            assert collector.version == "0.1.0"


@patch('src.omniaudit.collectors.git_collector.GIT_AVAILABLE', True)
def test_git_collector_missing_repo_path():
    """Test error when repo_path is missing."""
    with pytest.raises(ConfigurationError, match="repo_path is required"):
        GitCollector({})


@patch('src.omniaudit.collectors.git_collector.GIT_AVAILABLE', True)
def test_git_collector_nonexistent_path():
    """Test error when repo path doesn't exist."""
    with pytest.raises(ConfigurationError, match="does not exist"):
        GitCollector({"repo_path": "/nonexistent/path"})


@patch('src.omniaudit.collectors.git_collector.GIT_AVAILABLE', True)
def test_git_collector_not_a_repo():
    """Test error when path is not a git repository."""
    # Create a mock Path class
    with patch('src.omniaudit.collectors.git_collector.Path') as mock_path_cls:
        mock_path_instance = MagicMock()
        mock_path_cls.return_value = mock_path_instance

        # Mock the path to exist
        mock_path_instance.exists.return_value = True

        # Mock .git subdirectory to not exist
        mock_git_path = MagicMock()
        mock_git_path.exists.return_value = False
        mock_path_instance.__truediv__.return_value = mock_git_path

        with pytest.raises(ConfigurationError, match="Not a git repository"):
            GitCollector({"repo_path": "/not/a/repo"})


@patch('src.omniaudit.collectors.git_collector.GIT_AVAILABLE', True)
@patch('src.omniaudit.collectors.git_collector.Repo')
@patch('pathlib.Path.exists', return_value=True)
def test_git_collector_collect_success(mock_path, mock_repo):
    """Test successful data collection."""
    # Mock repository
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance
    mock_repo_instance.active_branch.name = "main"

    # Mock commit
    mock_commit = Mock()
    mock_commit.hexsha = "abc123def456"
    mock_commit.author.name = "Test Author"
    mock_commit.author.email = "test@example.com"
    mock_commit.committed_date = 1609459200  # 2021-01-01
    mock_commit.message = "Test commit"
    mock_commit.stats.files = {"file1.py": {}, "file2.py": {}}
    mock_commit.stats.total = {"insertions": 10, "deletions": 5, "lines": 15}

    mock_repo_instance.iter_commits.return_value = [mock_commit]

    # Mock branches
    mock_branch = Mock()
    mock_branch.name = "main"
    mock_branch.commit.hexsha = "abc123def456"
    mock_repo_instance.branches = [mock_branch]
    mock_repo_instance.active_branch = mock_branch

    # Collect data
    config = {"repo_path": "/fake/repo"}
    collector = GitCollector(config)
    result = collector.collect()

    # Verify response structure
    assert result["collector"] == "git_collector"
    assert "timestamp" in result
    assert "data" in result

    # Verify data content
    data = result["data"]
    assert data["commits_count"] == 1
    assert len(data["commits"]) == 1
    assert data["commits"][0]["author"] == "Test Author"
    assert data["branches_count"] == 1
    assert data["contributors_count"] == 1
