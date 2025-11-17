"""
Vercel entrypoint for FastAPI application.

This file serves as the entry point for Vercel deployment.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

try:
    from omniaudit.api.main import app

    # Export the app for Vercel
    __all__ = ["app"]

except Exception as e:
    # If import fails, create a minimal FastAPI app to show the error
    from fastapi import FastAPI

    app = FastAPI()

    @app.get("/")
    async def root():
        return {
            "error": "Failed to import main application",
            "details": str(e),
            "type": type(e).__name__,
            "python_path": sys.path,
            "cwd": os.getcwd(),
            "project_root": str(project_root)
        }

    @app.get("/health")
    async def health():
        return {"status": "error", "message": str(e)}
