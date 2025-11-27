"""
FastAPI application entrypoint for Vercel deployment.
"""

import sys
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# Import the FastAPI application
from omniaudit.api.main import app

__all__ = ["app"]
