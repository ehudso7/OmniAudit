# Examples

Example usage of OmniAudit collectors, analyzers, and reporters.

## Basic Examples

- `basic/analyze_git_repo.py` - Analyze a Git repository

## Running Examples

```bash
# Install OmniAudit first
pip install -e .

# Run Git analysis on current repository
python examples/basic/analyze_git_repo.py .

# Run Git analysis on specific repository
python examples/basic/analyze_git_repo.py /path/to/repo
```

## Planned Examples (Phase 2+)

- GitHub integration
- CI/CD analysis
- Multi-collector pipeline
- Custom analyzer implementation
