"""
FastAPI Application - Main Entry Point

REST API for OmniAudit platform.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Any
from datetime import datetime
import uuid

try:
    import uvicorn
    UVICORN_AVAILABLE = True
except ImportError:
    UVICORN_AVAILABLE = False
    uvicorn = None

from .models import (
    CollectorRequest,
    CollectorResponse,
    AnalyzerRequest,
    AnalyzerResponse,
    AuditRequest,
    AuditResponse
)
from .ai_routes import router as ai_router
from ..core.plugin_manager import PluginManager
from ..core.config_loader import ConfigLoader
from ..collectors.git_collector import GitCollector
from ..collectors.github_collector import GitHubCollector
from ..analyzers.code_quality import CodeQualityAnalyzer
from ..analyzers import warm_up_ai_schemas
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="OmniAudit API",
    description="Universal Project Auditing & Monitoring Platform",
    version="0.3.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include AI routes
app.include_router(ai_router)

# Initialize plugin manager
plugin_manager = PluginManager()

# Register collectors
plugin_manager.register_plugin(GitCollector)
plugin_manager.register_plugin(GitHubCollector)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("OmniAudit API starting up...")

    # Warm up AI schemas to reduce first-request latency
    logger.info("Warming up AI schemas...")
    warmed_up = warm_up_ai_schemas()
    if warmed_up:
        logger.info("AI schemas warmed up successfully")
    else:
        logger.info("AI schemas warm-up skipped (disabled or no API key)")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("OmniAudit API shutting down...")


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "OmniAudit API",
        "version": "0.3.0",
        "status": "operational",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "collectors": "/api/v1/collectors",
            "analyzers": "/api/v1/analyzers",
            "audit": "/api/v1/audit",
            "ai": {
                "status": "/api/v1/ai/status",
                "insights": "/api/v1/ai/insights",
                "cache": "/api/v1/ai/cache"
            }
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": get_timestamp()
    }


@app.get("/api/v1/collectors")
async def list_collectors() -> Dict[str, List[Dict[str, str]]]:
    """List all available collectors."""
    collectors = plugin_manager.list_plugins()
    return {"collectors": collectors}


@app.post("/api/v1/collectors/{collector_name}/collect")
async def run_collector(
    collector_name: str,
    request: CollectorRequest
) -> CollectorResponse:
    """
    Execute a specific collector.

    Args:
        collector_name: Name of collector to run
        request: Collector configuration

    Returns:
        Collector execution results
    """
    try:
        result = plugin_manager.execute_plugin(
            collector_name,
            request.config
        )

        return CollectorResponse(
            success=True,
            collector=collector_name,
            data=result
        )

    except Exception as e:
        logger.error(f"Collector execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/analyzers/code-quality")
async def analyze_code_quality(
    request: AnalyzerRequest
) -> AnalyzerResponse:
    """
    Run code quality analysis.

    Args:
        request: Analyzer configuration

    Returns:
        Analysis results
    """
    try:
        analyzer = CodeQualityAnalyzer(request.config)
        result = analyzer.analyze({})

        return AnalyzerResponse(
            success=True,
            analyzer="code_quality",
            data=result
        )

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/audit")
async def run_audit(request: AuditRequest) -> AuditResponse:
    """
    Run complete audit workflow.

    Executes collectors and analyzers in sequence.

    Args:
        request: Audit configuration

    Returns:
        Complete audit results
    """
    results = {
        "collectors": {},
        "analyzers": {}
    }

    # Run collectors
    for collector_name, config in request.collectors.items():
        try:
            result = plugin_manager.execute_plugin(collector_name, config)
            results["collectors"][collector_name] = result
        except Exception as e:
            logger.error(f"Collector {collector_name} failed: {e}")
            results["collectors"][collector_name] = {"error": str(e)}

    # Run analyzers
    if "code_quality" in request.analyzers:
        try:
            analyzer = CodeQualityAnalyzer(
                request.analyzers["code_quality"]
            )
            result = analyzer.analyze({})
            results["analyzers"]["code_quality"] = result
        except Exception as e:
            logger.error(f"Code quality analyzer failed: {e}")
            results["analyzers"]["code_quality"] = {"error": str(e)}

    return AuditResponse(
        success=True,
        audit_id=generate_audit_id(),
        results=results
    )


def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.utcnow().isoformat() + "Z"


def generate_audit_id() -> str:
    """Generate unique audit ID."""
    return str(uuid.uuid4())


def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the API server."""
    if not UVICORN_AVAILABLE:
        raise ImportError(
            "uvicorn is not installed. "
            "Install with: pip install uvicorn"
        )
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_server()
