# Configuration Guide

Comprehensive guide to configuring OmniAudit collectors, analyzers, and reporters.

## Configuration File Format

OmniAudit supports YAML and JSON configuration files.

### YAML Example

```yaml
collector: git_collector
version: 0.1.0

repo_path: /path/to/repository
branch: main
max_commits: 1000
since: 2024-01-01

output:
  format: json
  file: results.json
```

### JSON Example

```json
{
  "collector": "git_collector",
  "version": "0.1.0",
  "repo_path": "/path/to/repository",
  "branch": "main",
  "max_commits": 1000,
  "since": "2024-01-01",
  "output": {
    "format": "json",
    "file": "results.json"
  }
}
```

## Git Collector Configuration

### Required Parameters

#### repo_path

- **Type:** string
- **Description:** Path to the Git repository (local)
- **Example:** `/home/user/projects/myapp`

### Optional Parameters

#### branch

- **Type:** string
- **Default:** Current active branch
- **Description:** Branch to analyze
- **Example:** `main`, `develop`, `feature/new-feature`

#### max_commits

- **Type:** integer
- **Default:** 1000
- **Description:** Maximum number of commits to collect
- **Example:** `500`, `5000`

#### since

- **Type:** string (ISO 8601 date)
- **Default:** None (collect all commits up to max_commits)
- **Description:** Only collect commits after this date
- **Examples:**
  - `2024-01-01`
  - `2024-01-01T00:00:00`
  - `2024-01-01T00:00:00Z`

### Configuration Examples

#### Analyze Last 100 Commits

```yaml
collector: git_collector
repo_path: /path/to/repo
max_commits: 100
```

#### Analyze Specific Branch Since Date

```yaml
collector: git_collector
repo_path: /path/to/repo
branch: develop
since: 2024-01-01
max_commits: 1000
```

#### Analyze Current Repository

```yaml
collector: git_collector
repo_path: .
```

## Programmatic Configuration

### Python Dictionary

```python
from omniaudit.collectors.git_collector import GitCollector

config = {
    "repo_path": "/path/to/repo",
    "branch": "main",
    "max_commits": 500,
    "since": "2024-01-01"
}

collector = GitCollector(config)
result = collector.collect()
```

### Loading from YAML File

```python
import yaml
from omniaudit.collectors.git_collector import GitCollector

# Load configuration
with open("config/collectors/git.yaml") as f:
    config = yaml.safe_load(f)

# Create collector
collector = GitCollector(config)
result = collector.collect()
```

### Loading from JSON File

```python
import json
from omniaudit.collectors.git_collector import GitCollector

# Load configuration
with open("config/collectors/git.json") as f:
    config = json.load(f)

# Create collector
collector = GitCollector(config)
result = collector.collect()
```

## Output Format

All collectors produce a standardized output format:

```json
{
  "collector": "git_collector",
  "version": "0.1.0",
  "timestamp": "2025-10-05T14:30:00Z",
  "data": {
    "repository_path": "/path/to/repo",
    "current_branch": "main",
    "commits_count": 100,
    "commits": [...],
    "branches_count": 5,
    "branches": [...],
    "contributors_count": 3,
    "contributors": [...]
  },
  "metadata": {
    "collection_params": {
      "branch": "main",
      "since": "2024-01-01",
      "max_commits": 100
    }
  }
}
```

### Data Structure

#### Commit Object

```json
{
  "sha": "abc123def456...",
  "short_sha": "abc123d",
  "author": "John Doe",
  "author_email": "john@example.com",
  "date": "2024-10-01T10:30:00",
  "message": "Add new feature",
  "files_changed": 3,
  "insertions": 45,
  "deletions": 12,
  "lines_changed": 57
}
```

#### Branch Object

```json
{
  "name": "main",
  "commit_sha": "abc123def456...",
  "is_current": true
}
```

#### Contributor Object

```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "commits": 45,
  "insertions": 1200,
  "deletions": 450,
  "lines_changed": 1650
}
```

## Environment Variables

OmniAudit supports configuration via environment variables:

```bash
export OMNIAUDIT_REPO_PATH=/path/to/repo
export OMNIAUDIT_MAX_COMMITS=1000
export OMNIAUDIT_BRANCH=main
```

## Configuration Precedence

Configuration values are resolved in this order (highest to lowest):

1. Programmatic configuration (Python dictionary)
2. Configuration file
3. Environment variables
4. Default values

## Validation

All collectors validate their configuration on initialization:

```python
from omniaudit.collectors.git_collector import GitCollector
from omniaudit.collectors.base import ConfigurationError

try:
    collector = GitCollector({"repo_path": "/invalid/path"})
except ConfigurationError as e:
    print(f"Configuration error: {e}")
```

### Common Validation Errors

- **Missing repo_path**: `repo_path is required in configuration`
- **Path doesn't exist**: `Repository path does not exist: /path`
- **Not a Git repository**: `Not a git repository: /path`
- **Invalid date format**: `Invalid date format for 'since': bad-date`
- **Missing GitPython**: `GitPython is not installed`

## Best Practices

### 1. Use Configuration Files

Store configurations in version control:

```
config/
  collectors/
    git.yaml
    github.yaml
```

### 2. Use Environment Variables for Secrets

```yaml
repo_path: /path/to/repo
github_token: ${GITHUB_TOKEN}  # From environment
```

### 3. Use Relative Paths

```yaml
repo_path: .  # Current directory
```

### 4. Set Reasonable Limits

```yaml
max_commits: 1000  # Avoid memory issues
```

### 5. Filter by Date for Large Repos

```yaml
since: 2024-01-01  # Focus on recent activity
```

## Next Steps

- Explore [examples](../../examples/README.md)
- Learn about [creating custom collectors](../../src/omniaudit/collectors/README.md)
- Read [ADR-001: Plugin Architecture](../adr/001-plugin-architecture.md)
