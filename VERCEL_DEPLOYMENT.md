# Vercel Deployment Configuration

## Repository Structure for Vercel Deployment

This repository contains both Python and TypeScript code, but **only the TypeScript serverless functions are deployed to Vercel**.

### Python Code Relocated

All Python application code has been moved to the `python-app/` directory:

- `python-app/omniaudit/` - Python FastAPI application
- `python-app/tests/` - Python test files
- `python-app/scripts/` - Python utility scripts
- `python-app/migrations/` - Database migrations
- `python-app/examples/` - Python usage examples

Additionally, Python configuration files at the root have been renamed:
- `pyproject.toml` → `pyproject.toml.disabled`
- `requirements.txt` → `requirements.txt.disabled`

### Why This Structure?

**Vercel's framework detection runs BEFORE applying `.vercelignore`**. Even with Python files added to `.vercelignore`, Vercel's initial repository scan detects them and assumes this is a Python/FastAPI project, causing deployment failures with:

```
Error: No fastapi entrypoint found. Define a valid application entrypoint in one of the following locations: app.py, src/app.py, app/app.py, api/app.py...
```

By moving all Python code to a separate directory (`python-app/`) and excluding it from deployment, Vercel only sees:
- `package.json` (Node.js detection)
- `api/**/*.ts` (TypeScript serverless functions)
- `src/**` (TypeScript library code)

### Impact

- **Vercel deployment**: ✅ Works - Only detects Node.js/TypeScript serverless functions
- **Python application**: Located in `python-app/` for separate deployment (Docker, Cloud Run, etc.)
- **TypeScript library**: Compiled from `src/` for use in serverless functions and CLI

### For Local Development

The Python application is still fully functional in the `python-app/` directory:

```bash
# Work with Python application
cd python-app
python -m venv venv
source venv/bin/activate
pip install -e .

# Run Python application
cd ..
python -m omniaudit.cli

# Or use renamed config files
mv pyproject.toml.disabled pyproject.toml
mv requirements.txt.disabled requirements.txt
pip install -e .
```

### TypeScript Serverless Functions

The Vercel deployment ONLY deploys the serverless functions in `api/`:

- `/api/analyze` - Code analysis with Claude AI
- `/api/health` - Health check endpoint
- `/api/skills` - Skills management

These functions are compiled automatically by Vercel using `@vercel/node` runtime.
