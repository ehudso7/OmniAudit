# Collectors

Data collectors fetch information from various sources and normalize it for analysis.

## Available Collectors

- **GitCollector** - Extracts commit history, branches, and contributor statistics from Git repositories

## Planned Collectors (Phase 2+)

- **GitHubCollector** - GitHub API integration (issues, PRs, actions)
- **GitLabCollector** - GitLab API integration
- **JenkinsCollector** - Jenkins CI/CD data
- **SonarQubeCollector** - Code quality metrics
- **DockerCollector** - Container and image analysis

## Creating a Collector

All collectors must inherit from `BaseCollector` and implement:

```python
from omniaudit.collectors.base import BaseCollector

class MyCollector(BaseCollector):
    @property
    def name(self) -> str:
        return "my_collector"

    @property
    def version(self) -> str:
        return "1.0.0"

    def _validate_config(self) -> None:
        # Validate configuration
        pass

    def collect(self) -> Dict[str, Any]:
        # Collect and return data
        return self._create_response(data)
```
