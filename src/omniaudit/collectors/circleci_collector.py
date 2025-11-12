"""
CircleCI Collector

Fetches pipeline data from CircleCI API.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None

from .base import BaseCollector, ConfigurationError, DataCollectionError


class CircleCICollector(BaseCollector):
    """
    Collects CI/CD data from CircleCI.

    Configuration:
        token: str - CircleCI API token (required)
        project_slug: str - Project slug (vcs/org/repo) (required)

    Example:
        >>> config = {
        ...     "token": os.getenv("CIRCLECI_TOKEN"),
        ...     "project_slug": "gh/myorg/myrepo"
        ... }
        >>> collector = CircleCICollector(config)
        >>> result = collector.collect()
    """

    @property
    def name(self) -> str:
        return "circleci_collector"

    @property
    def version(self) -> str:
        return "0.1.0"

    def _validate_config(self) -> None:
        """Validate CircleCI collector configuration."""
        if not REQUESTS_AVAILABLE:
            raise ConfigurationError("requests library required")

        if "token" not in self.config:
            raise ConfigurationError("token required")

        if "project_slug" not in self.config:
            raise ConfigurationError("project_slug required")

    def collect(self) -> Dict[str, Any]:
        """Collect data from CircleCI API."""
        token = self.config["token"]
        project_slug = self.config["project_slug"]

        try:
            pipelines = self._fetch_pipelines(token, project_slug)

            data = {
                "project_slug": project_slug,
                "pipelines_count": len(pipelines),
                "pipelines": pipelines,
                "statistics": self._calculate_statistics(pipelines)
            }

            return self._create_response(data)

        except requests.exceptions.RequestException as e:
            raise DataCollectionError(f"CircleCI API request failed: {e}")

    def _fetch_pipelines(self, token: str, project_slug: str) -> List[Dict[str, Any]]:
        """Fetch pipelines from CircleCI API."""
        url = f"https://circleci.com/api/v2/project/{project_slug}/pipeline"
        headers = {"Circle-Token": token}

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        pipelines = []
        for pipeline in response.json().get("items", [])[:50]:
            pipelines.append({
                "id": pipeline["id"],
                "number": pipeline["number"],
                "state": pipeline["state"],
                "created_at": pipeline["created_at"],
                "updated_at": pipeline.get("updated_at")
            })

        return pipelines

    def _calculate_statistics(self, pipelines: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate pipeline statistics."""
        if not pipelines:
            return {}

        states = {}
        for pipeline in pipelines:
            state = pipeline["state"]
            states[state] = states.get(state, 0) + 1

        return {
            "by_state": states,
            "success_rate": (states.get("success", 0) / len(pipelines)) * 100
        }
