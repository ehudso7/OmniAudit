"""
GitLab CI Collector

Fetches pipeline data from GitLab API.
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


class GitLabCollector(BaseCollector):
    """
    Collects CI/CD data from GitLab.

    Configuration:
        project_id: str - GitLab project ID (required)
        token: str - GitLab access token (required)
        gitlab_url: str - GitLab instance URL (default: https://gitlab.com)
        since_days: int - Days of history to collect (default: 30)

    Example:
        >>> config = {
        ...     "project_id": "12345",
        ...     "token": os.getenv("GITLAB_TOKEN"),
        ...     "gitlab_url": "https://gitlab.com"
        ... }
        >>> collector = GitLabCollector(config)
        >>> result = collector.collect()
    """

    @property
    def name(self) -> str:
        return "gitlab_collector"

    @property
    def version(self) -> str:
        return "0.1.0"

    def _validate_config(self) -> None:
        """Validate GitLab collector configuration."""
        if not REQUESTS_AVAILABLE:
            raise ConfigurationError("requests library required")

        if "project_id" not in self.config:
            raise ConfigurationError("project_id required")

        if "token" not in self.config:
            raise ConfigurationError("token required")

    def collect(self) -> Dict[str, Any]:
        """Collect data from GitLab API."""
        project_id = self.config["project_id"]
        token = self.config["token"]
        gitlab_url = self.config.get("gitlab_url", "https://gitlab.com")
        since_days = self.config.get("since_days", 30)

        since_date = datetime.utcnow() - timedelta(days=since_days)

        try:
            # Collect pipelines
            pipelines = self._fetch_pipelines(gitlab_url, project_id, token, since_date)

            # Collect jobs from recent pipelines
            jobs = []
            for pipeline in pipelines[:10]:  # Limit to recent 10 pipelines
                pipeline_jobs = self._fetch_pipeline_jobs(
                    gitlab_url, project_id, token, pipeline['id']
                )
                jobs.extend(pipeline_jobs)

            data = {
                "project_id": project_id,
                "gitlab_url": gitlab_url,
                "pipelines_count": len(pipelines),
                "pipelines": pipelines,
                "jobs_count": len(jobs),
                "jobs": jobs,
                "statistics": self._calculate_statistics(pipelines)
            }

            return self._create_response(data)

        except requests.exceptions.RequestException as e:
            raise DataCollectionError(f"GitLab API request failed: {e}")

    def _fetch_pipelines(self, gitlab_url: str, project_id: str,
                         token: str, since: datetime) -> List[Dict[str, Any]]:
        """Fetch pipelines from GitLab API."""
        url = f"{gitlab_url}/api/v4/projects/{project_id}/pipelines"
        headers = {"PRIVATE-TOKEN": token}
        params = {
            "updated_after": since.isoformat(),
            "per_page": 100
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        pipelines = []
        for pipeline in response.json():
            pipelines.append({
                "id": pipeline["id"],
                "status": pipeline["status"],
                "ref": pipeline["ref"],
                "created_at": pipeline["created_at"],
                "updated_at": pipeline["updated_at"],
                "duration": pipeline.get("duration"),
                "web_url": pipeline["web_url"]
            })

        return pipelines

    def _fetch_pipeline_jobs(self, gitlab_url: str, project_id: str,
                             token: str, pipeline_id: int) -> List[Dict[str, Any]]:
        """Fetch jobs for a specific pipeline."""
        url = f"{gitlab_url}/api/v4/projects/{project_id}/pipelines/{pipeline_id}/jobs"
        headers = {"PRIVATE-TOKEN": token}

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        jobs = []
        for job in response.json():
            jobs.append({
                "id": job["id"],
                "name": job["name"],
                "stage": job["stage"],
                "status": job["status"],
                "created_at": job["created_at"],
                "started_at": job.get("started_at"),
                "finished_at": job.get("finished_at"),
                "duration": job.get("duration")
            })

        return jobs

    def _calculate_statistics(self, pipelines: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate pipeline statistics."""
        if not pipelines:
            return {}

        statuses = {}
        total_duration = 0
        duration_count = 0

        for pipeline in pipelines:
            status = pipeline["status"]
            statuses[status] = statuses.get(status, 0) + 1

            if pipeline.get("duration"):
                total_duration += pipeline["duration"]
                duration_count += 1

        return {
            "by_status": statuses,
            "success_rate": (statuses.get("success", 0) / len(pipelines)) * 100,
            "average_duration": total_duration / duration_count if duration_count > 0 else 0
        }
