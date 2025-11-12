"""
Jenkins CI Collector

Fetches build data from Jenkins API.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import base64

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None

from .base import BaseCollector, ConfigurationError, DataCollectionError


class JenkinsCollector(BaseCollector):
    """
    Collects CI/CD data from Jenkins.

    Configuration:
        url: str - Jenkins URL (required)
        username: str - Jenkins username (required)
        api_token: str - Jenkins API token (required)
        jobs: List[str] - Job names to collect (required)

    Example:
        >>> config = {
        ...     "url": "https://jenkins.example.com",
        ...     "username": "user",
        ...     "api_token": "token",
        ...     "jobs": ["my-app-build", "my-app-deploy"]
        ... }
        >>> collector = JenkinsCollector(config)
        >>> result = collector.collect()
    """

    @property
    def name(self) -> str:
        return "jenkins_collector"

    @property
    def version(self) -> str:
        return "0.1.0"

    def _validate_config(self) -> None:
        """Validate Jenkins collector configuration."""
        if not REQUESTS_AVAILABLE:
            raise ConfigurationError("requests library required")

        required = ["url", "username", "api_token", "jobs"]
        for field in required:
            if field not in self.config:
                raise ConfigurationError(f"{field} required")

    def collect(self) -> Dict[str, Any]:
        """Collect data from Jenkins API."""
        url = self.config["url"].rstrip('/')
        username = self.config["username"]
        api_token = self.config["api_token"]
        jobs = self.config["jobs"]

        try:
            all_builds = []

            for job_name in jobs:
                builds = self._fetch_job_builds(url, username, api_token, job_name)
                all_builds.extend(builds)

            data = {
                "jenkins_url": url,
                "jobs_count": len(jobs),
                "builds_count": len(all_builds),
                "builds": all_builds,
                "statistics": self._calculate_statistics(all_builds)
            }

            return self._create_response(data)

        except requests.exceptions.RequestException as e:
            raise DataCollectionError(f"Jenkins API request failed: {e}")

    def _fetch_job_builds(self, jenkins_url: str, username: str,
                          api_token: str, job_name: str) -> List[Dict[str, Any]]:
        """Fetch builds for a specific job."""
        url = f"{jenkins_url}/job/{job_name}/api/json"
        auth = (username, api_token)

        response = requests.get(url, auth=auth)
        response.raise_for_status()

        job_data = response.json()

        builds = []
        for build in job_data.get("builds", [])[:20]:  # Last 20 builds
            build_url = f"{build['url']}api/json"
            build_response = requests.get(build_url, auth=auth)
            build_response.raise_for_status()
            build_data = build_response.json()

            builds.append({
                "job_name": job_name,
                "number": build_data["number"],
                "result": build_data.get("result"),
                "duration": build_data.get("duration"),
                "timestamp": build_data.get("timestamp"),
                "url": build_data["url"]
            })

        return builds

    def _calculate_statistics(self, builds: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate build statistics."""
        if not builds:
            return {}

        results = {}
        total_duration = 0
        duration_count = 0

        for build in builds:
            result = build.get("result", "UNKNOWN")
            results[result] = results.get(result, 0) + 1

            if build.get("duration"):
                total_duration += build["duration"]
                duration_count += 1

        return {
            "by_result": results,
            "success_rate": (results.get("SUCCESS", 0) / len(builds)) * 100,
            "average_duration_ms": total_duration / duration_count if duration_count > 0 else 0
        }
