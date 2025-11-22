# Vercel Deployment Configuration

## Python Files Renamed

The following files have been renamed to prevent Vercel from detecting this as a Python/FastAPI project:

- `pyproject.toml` → `pyproject.toml.disabled`
- `requirements.txt` → `requirements.txt.disabled`

### Why?

Vercel's framework detection scans for project files BEFORE applying `.vercelignore`. When it finds `pyproject.toml` at the root, it assumes this is a Python project and tries to find a FastAPI entrypoint, which causes deployment failures.

### Impact

- **Vercel deployment**: ✅ Works - Only detects Node.js/TypeScript
- **Local Python development**: ❌ Requires renaming files back
- **Main repo Python app**: Not affected (uses different deployment method)

### For Local Development

To work with the Python application locally:

```bash
# Rename back to enable Python tools
mv pyproject.toml.disabled pyproject.toml
mv requirements.txt.disabled requirements.txt

# When done, rename again before committing
mv pyproject.toml pyproject.toml.disabled  
mv requirements.txt requirements.txt.disabled
```

### TypeScript Serverless Functions

The Vercel deployment ONLY deploys the serverless functions in `api/`:

- `/api/analyze` - Code analysis with Claude AI
- `/api/health` - Health check endpoint
- `/api/skills` - Skills management

These functions are compiled automatically by Vercel using `@vercel/node` runtime.
