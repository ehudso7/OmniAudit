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
python_app_path = project_root / "python-app"

# Add to Python path (use absolute paths)
# Try python-app first (where the API is located), then src
sys.path.insert(0, str(python_app_path.absolute()))
sys.path.insert(0, str(src_path.absolute()))
sys.path.insert(0, str(project_root.absolute()))

# Also try setting environment variable for good measure
os.environ["PYTHONPATH"] = f"{python_app_path.absolute()}:{src_path.absolute()}:{project_root.absolute()}"

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

    # Only expose detailed debug info when explicitly enabled
    debug_enabled = os.environ.get("OMNIAUDIT_DEBUG", "false").lower() == "true"

    # Minimal error info for non-debug mode
    minimal_error = {
        "error": "Application initialization failed",
        "status": "error",
        "message": "Please check server logs or enable debug mode for details",
    }

    # Detailed error info only for debug mode
    if debug_enabled:
        detailed_error = {
            "error": "Failed to import main application",
            "details": str(e),
            "traceback": traceback.format_exc(),
            "python_path": sys.path,
            "cwd": os.getcwd(),
            "project_root": str(project_root),
            "src_path": str(src_path),
            "python_app_path": str(python_app_path),
            "files_in_src": list(str(p) for p in src_path.glob("*")) if src_path.exists() else [],
            "files_in_python_app": list(str(p) for p in python_app_path.glob("*")) if python_app_path.exists() else []
        }
    else:
        detailed_error = None

    @app.get("/")
    async def root():
        """Root endpoint - returns minimal error info."""
        return minimal_error

    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "error", "message": "Application failed to initialize"}

    # Only expose debug endpoint when debug mode is enabled
    if debug_enabled:
        @app.get("/debug")
        async def debug():
            """Debug endpoint - only available when OMNIAUDIT_DEBUG=true."""
            return detailed_error

# Export the app
__all__ = ["app"]
