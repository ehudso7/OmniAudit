"""
Vercel entrypoint for FastAPI application.

This file serves as the entry point for Vercel deployment.
"""

from src.omniaudit.api.main import app

# Export the app for Vercel
__all__ = ["app"]
