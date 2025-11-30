"""
FastAPI Application - Main Entry Point

REST API for OmniAudit platform.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Any
from datetime import datetime
import uuid
import os

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
from .webhook_routes import router as webhook_router
from .batch_routes import router as batch_router
from .export_routes import router as export_router
from .reviews_routes import router as reviews_router
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

# CORS middleware - Secure configuration
# In production, ALWAYS set CORS_ORIGINS environment variable with allowed origins
allowed_origins_str = os.environ.get("CORS_ORIGINS", "")
if allowed_origins_str:
    # Use explicit origins from environment (recommended for production)
    allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]
else:
    # Default for local development only
    # IMPORTANT: Do not use wildcards - CORS doesn't support pattern matching
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:5173",  # Vite default port
        "http://localhost:8000"
    ]
    # Log warning if not configured
    logger.warning(
        "CORS_ORIGINS not configured. Using localhost defaults. "
        "Set CORS_ORIGINS environment variable for production."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Include routers
app.include_router(ai_router)
app.include_router(webhook_router)
app.include_router(batch_router)
app.include_router(export_router)
app.include_router(reviews_router)

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
            },
            "webhooks": {
                "github": "/api/v1/webhooks/github",
                "slack": "/api/v1/webhooks/slack",
                "status": "/api/v1/webhooks/status"
            },
            "batch": {
                "audit": "/api/v1/batch/audit",
                "list": "/api/v1/batch/audit"
            },
            "export": {
                "csv": "/api/v1/export/csv",
                "markdown": "/api/v1/export/markdown",
                "json": "/api/v1/export/json",
                "formats": "/api/v1/export/formats"
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


@app.get("/api/health")
async def api_health_check():
    """API health check endpoint (alias for frontend)."""
    return {
        "status": "healthy",
        "timestamp": get_timestamp(),
        "version": "0.3.0"
    }


@app.get("/api/skills")
async def get_skills():
    """Get available analysis skills."""
    return {
        "skills": [
            {"name": "Security Auditor", "category": "Security", "description": "Detects vulnerabilities, SQL injection, XSS, and security misconfigurations"},
            {"name": "Performance Optimizer", "category": "Performance", "description": "Identifies performance bottlenecks and optimization opportunities"},
            {"name": "Code Quality", "category": "Quality", "description": "Checks for code smells, complexity issues, and maintainability"},
            {"name": "Dependency Analyzer", "category": "Dependencies", "description": "Scans for vulnerable dependencies and outdated packages"},
            {"name": "Architecture Advisor", "category": "Architecture", "description": "Reviews code structure and suggests improvements"},
            {"name": "React Best Practices", "category": "React", "description": "Checks React patterns, hooks usage, and component structure"},
            {"name": "TypeScript Expert", "category": "TypeScript", "description": "Validates types, generics, and TypeScript patterns"},
            {"name": "API Design", "category": "API", "description": "Reviews REST/GraphQL endpoints and data contracts"},
            {"name": "Test Coverage", "category": "Testing", "description": "Analyzes test coverage and suggests missing tests"},
            {"name": "Documentation", "category": "Docs", "description": "Checks for missing documentation and JSDoc comments"},
            {"name": "Accessibility", "category": "A11y", "description": "Validates WCAG compliance and accessibility patterns"},
            {"name": "Error Handling", "category": "Reliability", "description": "Checks for proper error handling and edge cases"}
        ]
    }


from pydantic import BaseModel
from typing import Optional, List


class AnalyzeRequest(BaseModel):
    code: str
    skills: List[str] = []
    language: str = "javascript"


@app.post("/api/analyze")
async def analyze_code(request: AnalyzeRequest):
    """
    Analyze code with selected skills.

    This provides instant code analysis without requiring full audit setup.
    """
    from ..analyzers.security import SecurityAnalyzer
    from ..analyzers.code_quality import CodeQualityAnalyzer

    results = {
        "success": True,
        "language": request.language,
        "skills_applied": request.skills,
        "findings": [],
        "summary": {
            "total_issues": 0,
            "security": 0,
            "performance": 0,
            "quality": 0,
            "suggestions": 0
        },
        "score": 100,
        "timestamp": get_timestamp()
    }

    # Run security analysis
    if any(s in request.skills for s in ["security-auditor", "Security Auditor", "security"]):
        security = SecurityAnalyzer()
        report = await security.analyze(request.code, "input.js")
        for finding in report.findings:
            results["findings"].append({
                "type": "security",
                "severity": finding.severity.value,
                "title": finding.title,
                "description": finding.description,
                "line": finding.line_number,
                "code": finding.code_snippet,
                "fix": finding.remediation
            })
            results["summary"]["security"] += 1
            results["summary"]["total_issues"] += 1

    # Run code quality analysis
    try:
        quality = CodeQualityAnalyzer({})
        quality_result = quality.analyze({"code": request.code})
        if isinstance(quality_result, dict) and "issues" in quality_result:
            for issue in quality_result.get("issues", []):
                results["findings"].append({
                    "type": "quality",
                    "severity": issue.get("severity", "medium"),
                    "title": issue.get("rule", "Code Quality Issue"),
                    "description": issue.get("message", ""),
                    "line": issue.get("line", 0),
                    "code": "",
                    "fix": issue.get("suggestion", "")
                })
                results["summary"]["quality"] += 1
                results["summary"]["total_issues"] += 1
    except Exception as e:
        logger.warning(f"Quality analysis failed: {e}")  # Log but continue

    # Calculate score
    total = results["summary"]["total_issues"]
    if total > 0:
        # Deduct points based on severity
        security_penalty = results["summary"]["security"] * 10
        quality_penalty = results["summary"]["quality"] * 3
        results["score"] = max(0, 100 - security_penalty - quality_penalty)

    # Add performance suggestions based on patterns
    if "performance" in str(request.skills).lower():
        code_lower = request.code.lower()
        if "for" in code_lower and "length" in code_lower:
            results["findings"].append({
                "type": "performance",
                "severity": "low",
                "title": "Loop Optimization",
                "description": "Consider caching array.length outside the loop for better performance",
                "line": 0,
                "code": "",
                "fix": "Store array.length in a variable before the loop"
            })
            results["summary"]["performance"] += 1
            results["summary"]["total_issues"] += 1

    return results


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
