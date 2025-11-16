# Quickstart Guide

Get started with OmniAudit in 5 minutes.

## Prerequisites

- Python 3.10 or higher
- Git
- pip

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/omniaudit.git
cd omniaudit
```

### 2. Install OmniAudit

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
```

### 3. Verify Installation

```bash
omniaudit
```

You should see the OmniAudit welcome message.

## Your First Analysis

### Analyze a Git Repository

Let's analyze the OmniAudit repository itself:

```bash
cd examples/basic
python analyze_git_repo.py ../..
```

This will:

1. Collect commit history from the repository
2. Analyze contributor statistics
3. Display top contributors
4. Save results to `git_analysis.json`

### Output Example

```
============================================================
GIT REPOSITORY ANALYSIS
============================================================
Repository: /path/to/omniaudit
Current Branch: main

Commits Analyzed: 100
Total Branches: 2
Contributors: 3

============================================================
TOP CONTRIBUTORS
============================================================
1. John Doe
   Commits: 45
   Lines Changed: 2150

2. Jane Smith
   Commits: 35
   Lines Changed: 1820

3. Bob Johnson
   Commits: 20
   Lines Changed: 980

Full results saved to: git_analysis.json
```

## Using the Git Collector Programmatically

```python
from omniaudit.collectors.git_collector import GitCollector

# Configure the collector
config = {
    "repo_path": "/path/to/your/repository",
    "max_commits": 1000,
    "branch": "main"  # optional
}

# Create and run collector
collector = GitCollector(config)
result = collector.collect()

# Access the data
print(f"Found {result['data']['commits_count']} commits")
print(f"Contributors: {result['data']['contributors_count']}")

# Process contributors
for contributor in result['data']['contributors']:
    print(f"{contributor['name']}: {contributor['commits']} commits")
```

## Configuration

### Using Configuration Files

Create a configuration file for the Git collector:

```bash
cp config/collectors/git.yaml.example config/collectors/git.yaml
```

Edit `config/collectors/git.yaml`:

```yaml
collector: git_collector
version: 0.1.0

repo_path: /path/to/your/repository
max_commits: 1000
```

## Next Steps

- Read the [Configuration Guide](configuration.md) for advanced options
- Explore [Architecture Decision Records](../adr/README.md)
- Check out more [Examples](../../examples/README.md)
- Learn about [creating custom collectors](../../src/omniaudit/collectors/README.md)

## Troubleshooting

### ImportError: No module named 'git'

The GitPython library is not installed:

```bash
pip install gitpython
```

### ConfigurationError: Not a git repository

Make sure you're pointing to a valid Git repository with a `.git` directory.

### Permission Denied

Make sure you have read access to the repository directory.

## Getting Help

- Check the [documentation](../README.md)
- Report issues on [GitHub](https://github.com/yourusername/omniaudit/issues)
- Read the [Contributing Guide](../../CONTRIBUTING.md)
