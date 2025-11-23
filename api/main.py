"""
Vercel entrypoint for FastAPI application.

This file serves as the entry point for Vercel deployment.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))

# Import the FastAPI app from the main package
from omniaudit.api.main import app

# Explicitly export for Vercel
__all__ = ["app"]
