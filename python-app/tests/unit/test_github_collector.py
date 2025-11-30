"""Unit tests for GitHubCollector."""

import pytest
from unittest.mock import Mock, patch
from omniaudit.collectors.github_collector import GitHubCollector
from omniaudit.collectors.base import ConfigurationError


@patch('omniaudit.collectors.github_collector.REQUESTS_AVAILABLE', True)
def test_github_collector_properties():
    """Test collector properties."""
    config = {
        "owner": "python",
        "repo": "cpython",
        "token": "test_token"
    }
    collector = GitHubCollector(config)

    assert collector.name == "github_collector"
    assert collector.version == "0.1.0"


@patch('omniaudit.collectors.github_collector.REQUESTS_AVAILABLE', True)
def test_github_collector_missing_fields():
    """Test error when required fields missing."""
    with pytest.raises(ConfigurationError, match="owner is required"):
        GitHubCollector({})


@patch('omniaudit.collectors.github_collector.REQUESTS_AVAILABLE', True)
def test_github_collector_missing_repo():
    """Test error when repo is missing."""
    config = {
        "owner": "python",
        "token": "test_token"
    }

    with pytest.raises(ConfigurationError, match="repo is required"):
        GitHubCollector(config)


@patch('omniaudit.collectors.github_collector.REQUESTS_AVAILABLE', True)
def test_github_collector_empty_token():
    """Test error when token is empty."""
    config = {
        "owner": "python",
        "repo": "cpython",
        "token": ""
    }

    with pytest.raises(ConfigurationError, match="token cannot be empty"):
        GitHubCollector(config)


@patch('omniaudit.collectors.github_collector.REQUESTS_AVAILABLE', True)
def test_github_collector_collect_success():
    """Test successful data collection."""
    import requests as real_requests

    with patch('omniaudit.collectors.github_collector.requests.get') as mock_get:
        # Mock API responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = [
            [],  # PRs
            [],  # Issues
            {"workflows": []},  # Workflows
            {    # Repo stats
                "stargazers_count": 100,
                "forks_count": 50,
                "watchers_count": 25,
                "open_issues_count": 10,
                "default_branch": "main",
                "language": "Python",
                "size": 1000,
                "created_at": "2020-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
                "pushed_at": "2025-01-01T00:00:00Z"
            }
        ]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        config = {
            "owner": "test",
            "repo": "repo",
            "token": "token",
            "since_days": 7
        }

        collector = GitHubCollector(config)
        result = collector.collect()

        assert result["collector"] == "github_collector"
        assert "data" in result
        assert result["data"]["owner"] == "test"
        assert result["data"]["repository"] == "repo"
