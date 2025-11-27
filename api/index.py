"""
FastAPI application entrypoint for Vercel deployment.
"""

import sys
import os
from pathlib import Path

# Get absolute paths
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
src_path = project_root / "src"

# Add to Python path (use absolute paths)
sys.path.insert(0, str(src_path.absolute()))
sys.path.insert(0, str(project_root.absolute()))

# Also try setting environment variable for good measure
os.environ["PYTHONPATH"] = f"{src_path.absolute()}:{project_root.absolute()}"

# Import the FastAPI application
try:
    from omniaudit.api.main import app

    # Successfully imported
    print(f"Successfully imported app from omniaudit.api.main", file=sys.stderr)

except ImportError as e:
    # Fallback: create a minimal FastAPI app to show the error
    import traceback
    from fastapi import FastAPI

    app = FastAPI(title="OmniAudit API - Import Error")

    error_details = {
        "error": "Failed to import main application",
        "details": str(e),
        "traceback": traceback.format_exc(),
        "python_path": sys.path,
        "cwd": os.getcwd(),
        "project_root": str(project_root),
        "src_path": str(src_path),
        "files_in_src": list(str(p) for p in src_path.glob("*")) if src_path.exists() else []
    }

    @app.get("/")
    async def root():
        return error_details

    @app.get("/health")
    async def health():
        return {"status": "error", "message": str(e)}

    @app.get("/debug")
    async def debug():
        return error_details

# Export the app
__all__ = ["app"]
