# OmniAudit CI/CD Guide

This guide explains the Continuous Integration and Continuous Deployment (CI/CD) setup for OmniAudit.

## Overview

OmniAudit uses GitHub Actions for automated testing, linting, security scanning, and builds. The CI pipeline runs on every push to `main`, `develop`, and `claude/**` branches, as well as on all pull requests.

## CI Pipeline

The CI workflow (`.github/workflows/ci.yml`) consists of five parallel jobs:

### 1. Lint & Type Check

**Purpose:** Ensure code quality and type safety

**Steps:**
- Install Python dependencies with `pip install -e .[dev]`
- Run `ruff` linter on source and test files
- Run `ruff` formatter check
- Run `mypy` type checker

**Configuration:**
- Runs on: Ubuntu Latest
- Python: 3.11
- All steps have `continue-on-error: true` (non-blocking)

**Local execution:**
```bash
# Install dev dependencies
pip install -e .[dev]

# Run ruff linter
ruff check src/ tests/

# Check formatting
ruff format --check src/ tests/

# Run type checker
mypy src/
```

### 2. Test Suite

**Purpose:** Run unit and integration tests across multiple platforms and Python versions

**Matrix Strategy:**
- **Operating Systems:** Ubuntu, macOS, Windows
- **Python Versions:** 3.10, 3.11, 3.12

**Steps:**
- Checkout code with full Git history (`fetch-depth: 0`)
- Install Python dependencies with `pip install -e .[test]`
- Run unit tests with coverage reporting
- Run integration tests
- Upload coverage to Codecov (Ubuntu 3.11 only)

**Local execution:**
```bash
# Install test dependencies
pip install -e .[test]

# Run unit tests with coverage
pytest tests/unit/ -v --cov=src/omniaudit --cov-report=xml

# Run integration tests
pytest tests/integration/ -v

# Run all tests
pytest tests/ -v
```

### 3. Frontend Tests

**Purpose:** Build and validate the React frontend

**Steps:**
- Setup Node.js 20 with npm caching
- Install frontend dependencies with `npm ci`
- Build production frontend bundle

**Local execution:**
```bash
cd frontend

# Install dependencies
npm ci

# Build for production
npm run build

# Development server
npm run dev
```

### 4. Security Scan

**Purpose:** Detect security vulnerabilities and code issues

**Steps:**
- Install dependencies including `safety` and `bandit`
- Check for known vulnerabilities in dependencies using `safety`
- Run Bandit security linter for Python code
- Upload security reports as artifacts

**Local execution:**
```bash
# Install security tools
pip install safety bandit

# Check dependencies for vulnerabilities
pip freeze | safety check --stdin

# Run security linter
bandit -r src/ -f json -o bandit-report.json
```

### 5. Build Package

**Purpose:** Build distributable Python package

**Dependencies:** Requires `lint` and `test` jobs to pass

**Steps:**
- Install `build` package
- Build wheel and source distribution
- Upload build artifacts

**Local execution:**
```bash
# Install build tool
pip install build

# Build package
python -m build

# Check dist/ directory for artifacts
ls -la dist/
```

## Dependency Management

OmniAudit uses **setuptools** with `pyproject.toml` for dependency management (not Poetry).

### Installing Dependencies

```bash
# Production dependencies only
pip install -e .

# With development tools (linting, type checking)
pip install -e .[dev]

# With test dependencies only
pip install -e .[test]

# All optional dependencies
pip install -e .[dev,test]
```

### Dependency Groups

Defined in `pyproject.toml`:

**Main dependencies:**
- `gitpython` - Git repository interaction
- `requests` - HTTP client
- `fastapi` - REST API framework
- `pydantic` - Data validation
- `sqlalchemy` - Database ORM
- `anthropic` - AI features (Phase 4)
- And more (see `pyproject.toml`)

**Dev dependencies:**
- `pytest` + `pytest-cov` - Testing framework
- `ruff` - Fast Python linter/formatter
- `mypy` - Static type checker
- `black` - Code formatter
- `bandit` - Security linter
- `safety` - Dependency security scanner

**Test dependencies:**
- `pytest` + `pytest-cov`
- `httpx` - For testing FastAPI endpoints

## GitHub Actions Configuration

### Workflow Triggers

```yaml
on:
  push:
    branches: [ main, develop, claude/** ]
  pull_request:
    branches: [ main, develop ]
```

**Triggers on:**
- Pushes to `main`, `develop`, or any `claude/**` branch
- Pull requests targeting `main` or `develop`

### Artifacts

The CI workflow produces the following artifacts:

1. **`dist`** - Built Python package (wheel + source)
2. **`frontend-build`** - Compiled React application
3. **`security-reports`** - Bandit security scan results

**Accessing artifacts:**
- Go to the Actions tab in GitHub
- Click on a workflow run
- Scroll to "Artifacts" section at the bottom
- Download desired artifacts

## Environment Variables

No environment variables are required for basic CI runs.

**Optional for advanced features:**
- `ANTHROPIC_API_KEY` - Enable AI features (Phase 4)
- `CODECOV_TOKEN` - Upload coverage to Codecov

## CI Best Practices

### Before Pushing

Always run tests locally before pushing:

```bash
# Quick check (unit tests only)
pytest tests/unit/ -v

# Full check (unit + integration)
pytest tests/ -v

# With linting
ruff check src/ tests/
mypy src/
```

### Debugging CI Failures

1. **Check the workflow run logs:**
   - Go to GitHub Actions tab
   - Click on the failed run
   - Expand failed steps to see error details

2. **Reproduce locally:**
   ```bash
   # Use the same Python version as CI
   python --version  # Should match matrix version

   # Install exact dependencies
   pip install -e .[dev,test]

   # Run failing command
   pytest tests/unit/ -v
   ```

3. **Common issues:**
   - **Import errors:** Ensure package is installed with `pip install -e .`
   - **Missing dependencies:** Install with correct extras `.[dev]` or `.[test]`
   - **Path issues:** Tests expect to run from project root
   - **Platform-specific:** Test on the specific OS if needed (use Docker for Linux)

### Platform-Specific Testing

**Test on Windows:**
```powershell
# In PowerShell
python -m venv venv
.\venv\Scripts\activate
pip install -e .[test]
pytest tests/ -v
```

**Test on macOS:**
```bash
# In Terminal
python3 -m venv venv
source venv/bin/activate
pip install -e .[test]
pytest tests/ -v
```

**Test on Linux (via Docker):**
```bash
docker run -it --rm -v $(pwd):/app -w /app python:3.11 bash
pip install -e .[test]
pytest tests/ -v
```

## Coverage Requirements

**Current targets:**
- **Unit tests:** >80% coverage
- **Overall:** >70% coverage

**Checking coverage locally:**
```bash
pytest tests/unit/ -v --cov=src/omniaudit --cov-report=html

# Open htmlcov/index.html in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Release Workflow

There's a separate release workflow (`.github/workflows/release.yml`) for creating GitHub releases and publishing to PyPI.

**Triggering a release:**
1. Create and push a version tag:
   ```bash
   git tag v0.3.0
   git push origin v0.3.0
   ```

2. The release workflow will:
   - Build the package
   - Create a GitHub release
   - Publish to PyPI (if configured)

## Status Badges

Add these badges to your README:

```markdown
[![CI](https://github.com/yourusername/omniaudit/workflows/CI/badge.svg)](https://github.com/yourusername/omniaudit/actions)
[![codecov](https://codecov.io/gh/yourusername/omniaudit/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/omniaudit)
```

## Maintenance

### Updating Dependencies

```bash
# Update all dependencies to latest compatible versions
pip install --upgrade pip
pip install -e .[dev,test] --upgrade

# Test that everything still works
pytest tests/ -v

# Update pyproject.toml with new minimum versions if needed
```

### Updating CI Configuration

When modifying `.github/workflows/ci.yml`:

1. Test changes in a feature branch first
2. Push to a `claude/**` branch to trigger CI
3. Verify all jobs pass
4. Merge to main via PR

## Troubleshooting

### Issue: "ModuleNotFoundError" in CI

**Solution:**
Ensure the module is installed:
```bash
pip install -e .
```

Or add to `pyproject.toml` dependencies.

### Issue: Tests pass locally but fail in CI

**Common causes:**
1. **Platform differences:** Path separators, line endings
2. **Missing dependencies:** Check CI logs for import errors
3. **Environment variables:** Set in workflow if needed
4. **Git history:** Some tests need `fetch-depth: 0`

**Solution:**
Add debug output to CI:
```yaml
- name: Debug info
  run: |
    python --version
    pip list
    pwd
    ls -la
```

### Issue: Frontend build fails

**Common causes:**
1. **Missing package-lock.json:** Run `npm install` to generate
2. **Node version mismatch:** Check `node-version` in workflow
3. **TypeScript errors:** Fix type issues in `*.tsx` files

**Solution:**
Test build locally:
```bash
cd frontend
npm ci
npm run build
```

## Contact

For CI/CD issues or questions:
- Open an issue on GitHub
- Check GitHub Actions logs for details
- Review this guide for common solutions

---

**Last Updated:** 2025-11-16
**Maintainer:** OmniAudit Team
