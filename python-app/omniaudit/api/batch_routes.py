"""
Batch Operations API Routes

Endpoints for batch processing multiple repositories or audits.
"""

import asyncio
import os
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime, timedelta

from ..utils.logger import get_logger
from ..analyzers import SecurityAnalyzer, DependencyAnalyzer
from ..analyzers.ai_insights import AIInsightsAnalyzer
from ..analyzers.code_quality import CodeQualityAnalyzer

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/batch",
    tags=["Batch Operations"]
)

# WARNING: In-memory storage for batch jobs
# This is NOT secure for production use as:
# - Data is lost on server restart
# - Not shared across multiple server instances
# - Vulnerable to memory exhaustion attacks
# For production, use Redis, PostgreSQL, or another persistent store
batch_jobs: Dict[str, Dict[str, Any]] = {}

# Maximum number of batch jobs to store
MAX_BATCH_JOBS = 100

# Maximum age for completed jobs (in hours)
MAX_JOB_AGE_HOURS = 24


def cleanup_old_jobs():
    """
    Remove completed jobs older than MAX_JOB_AGE_HOURS to prevent memory exhaustion.

    This is a basic cleanup mechanism. For production, use a proper
    job queue system with TTL support (Redis, Celery, etc.)
    """
    current_time = datetime.now()
    jobs_to_delete = []

    for job_id, job in batch_jobs.items():
        # Only cleanup completed or failed jobs
        if job["status"] in ("completed", "failed"):
            completed_at = job.get("completed_at")
            if completed_at:
                try:
                    completed_time = datetime.fromisoformat(completed_at)
                    age = current_time - completed_time

                    if age > timedelta(hours=MAX_JOB_AGE_HOURS):
                        jobs_to_delete.append(job_id)
                except (ValueError, TypeError):
                    # Invalid timestamp, mark for deletion
                    jobs_to_delete.append(job_id)

    # Delete old jobs
    for job_id in jobs_to_delete:
        logger.info(f"Cleaning up old batch job: {job_id}")
        del batch_jobs[job_id]

    if jobs_to_delete:
        logger.info(f"Cleaned up {len(jobs_to_delete)} old batch jobs")


class BatchAuditRequest(BaseModel):
    """Request model for batch audit."""
    repositories: List[Dict[str, Any]] = Field(
        ...,
        description="List of repository configurations to audit",
        max_length=50  # Limit to prevent DoS
    )
    collectors: List[str] = Field(
        default=["git_collector"],
        description="Collectors to run on each repository",
        max_length=10
    )
    analyzers: List[str] = Field(
        default=[],
        description="Analyzers to run on each repository",
        max_length=10
    )


class BatchJobStatus(BaseModel):
    """Response model for batch job status."""
    job_id: str
    status: str  # pending, running, completed, failed
    total_items: int
    completed_items: int
    failed_items: int
    started_at: str
    completed_at: str = None
    results: Dict[str, Any] = {}


def run_analyzer(analyzer_name: str, config: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
    """Run a specific analyzer and return results."""
    try:
        if analyzer_name == "security":
            analyzer = SecurityAnalyzer(config)
        elif analyzer_name == "dependency":
            analyzer = DependencyAnalyzer(config)
        elif analyzer_name == "code_quality":
            analyzer = CodeQualityAnalyzer(config)
        elif analyzer_name == "ai_insights":
            analyzer = AIInsightsAnalyzer(config)
        else:
            return {"error": f"Unknown analyzer: {analyzer_name}"}

        return analyzer.analyze(data)
    except Exception as e:
        logger.error(f"Analyzer {analyzer_name} failed: {e}")
        return {"error": str(e), "analyzer": analyzer_name}


def collect_files_from_path(project_path: Path) -> List[Dict[str, Any]]:
    """Collect file information from a project path."""
    files = []
    supported_extensions = {
        ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs",
        ".rb", ".php", ".c", ".cpp", ".h", ".hpp", ".cs", ".kt",
        ".yaml", ".yml", ".json", ".toml"
    }

    try:
        for file_path in project_path.rglob("*"):
            if file_path.is_file() and file_path.suffix in supported_extensions:
                # Skip common non-source directories
                if any(part.startswith(".") or part in {"node_modules", "venv", "__pycache__", "dist", "build"}
                       for part in file_path.parts):
                    continue

                try:
                    stat = file_path.stat()
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        lines = len(content.split("\n"))

                    files.append({
                        "path": str(file_path.relative_to(project_path)),
                        "absolute_path": str(file_path),
                        "lines": lines,
                        "size": stat.st_size,
                        "language": get_language_from_extension(file_path.suffix),
                        "content": content[:10000] if len(content) > 10000 else content,  # Limit content
                    })
                except Exception as e:
                    logger.warning(f"Failed to read file {file_path}: {e}")
    except Exception as e:
        logger.error(f"Failed to collect files from {project_path}: {e}")

    return files


def get_language_from_extension(ext: str) -> str:
    """Map file extension to language name."""
    mapping = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".jsx": "javascript",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".cs": "csharp",
        ".kt": "kotlin",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".json": "json",
        ".toml": "toml",
    }
    return mapping.get(ext.lower(), "unknown")


async def process_batch_audit(job_id: str, request: BatchAuditRequest):
    """Process batch audit in background."""
    job = batch_jobs[job_id]
    job["status"] = "running"

    results = {}
    completed = 0
    failed = 0

    for idx, repo_config in enumerate(request.repositories):
        repo_name = repo_config.get("name", f"repo_{idx}")
        start_time = datetime.now()

        try:
            logger.info(f"Processing repository {idx + 1}/{len(request.repositories)}: {repo_name}")

            # Get project path from config
            project_path = repo_config.get("path") or repo_config.get("url")

            if not project_path:
                raise ValueError("Repository must have 'path' or 'url' specified")

            # If it's a local path, verify it exists
            if os.path.isdir(project_path):
                path = Path(project_path)
            else:
                # For remote URLs, we would need to clone first
                # For now, we'll just note that cloning is needed
                results[repo_name] = {
                    "status": "skipped",
                    "message": "Remote repositories not supported in this version. Please provide a local path.",
                    "duration_seconds": 0,
                }
                failed += 1
                job["completed_items"] = completed
                job["failed_items"] = failed
                job["results"] = results
                continue

            # Collect files from the repository
            files = collect_files_from_path(path)

            if not files:
                results[repo_name] = {
                    "status": "warning",
                    "message": "No supported files found in repository",
                    "duration_seconds": 0,
                }
                completed += 1
                job["completed_items"] = completed
                job["failed_items"] = failed
                job["results"] = results
                continue

            # Build analysis data
            analysis_data = {
                "project_path": str(path),
                "project_name": repo_name,
                "files": files,
                "metrics": {
                    "total_files": len(files),
                    "total_lines": sum(f.get("lines", 0) for f in files),
                },
                "language_breakdown": {},
            }

            # Calculate language breakdown
            for file in files:
                lang = file.get("language", "unknown")
                if lang not in analysis_data["language_breakdown"]:
                    analysis_data["language_breakdown"][lang] = 0
                analysis_data["language_breakdown"][lang] += 1

            # Run requested analyzers
            analyzer_results = {}
            analyzers_to_run = request.analyzers if request.analyzers else ["security", "code_quality"]

            for analyzer_name in analyzers_to_run:
                analyzer_config = {
                    "project_path": str(path),
                    "project_name": repo_name,
                    **repo_config.get("analyzer_config", {}),
                }

                logger.info(f"Running {analyzer_name} analyzer on {repo_name}")
                result = run_analyzer(analyzer_name, analyzer_config, analysis_data)
                analyzer_results[analyzer_name] = result

            # Calculate summary
            total_issues = 0
            critical_issues = 0
            for analyzer_name, result in analyzer_results.items():
                if "data" in result:
                    data = result["data"]
                    if "findings" in data:
                        total_issues += len(data["findings"])
                        critical_issues += len([f for f in data["findings"]
                                                if f.get("severity") in ["critical", "high"]])
                    elif "vulnerabilities" in data:
                        total_issues += len(data["vulnerabilities"])
                        critical_issues += len([v for v in data["vulnerabilities"]
                                                if v.get("severity") in ["critical", "high"]])

            duration = (datetime.now() - start_time).total_seconds()

            results[repo_name] = {
                "status": "success",
                "duration_seconds": round(duration, 2),
                "files_analyzed": len(files),
                "total_lines": analysis_data["metrics"]["total_lines"],
                "languages": list(analysis_data["language_breakdown"].keys()),
                "analyzers": analyzer_results,
                "summary": {
                    "total_issues": total_issues,
                    "critical_issues": critical_issues,
                },
            }

            completed += 1
            logger.info(f"Completed {repo_name}: {total_issues} issues found in {duration:.2f}s")

        except Exception as e:
            logger.error(f"Failed to process repository {repo_name}: {e}")
            duration = (datetime.now() - start_time).total_seconds()
            results[repo_name] = {
                "status": "failed",
                "error": "An error occurred while processing this repository. Check server logs for details.",
                "duration_seconds": round(duration, 2),
            }
            failed += 1

        job["completed_items"] = completed
        job["failed_items"] = failed
        job["results"] = results

    job["status"] = "completed"
    job["completed_at"] = datetime.now().isoformat()

    # Log final summary
    logger.info(f"Batch audit {job_id} completed: {completed} succeeded, {failed} failed")


@router.post("/audit", response_model=Dict[str, str])
async def create_batch_audit(
    request: BatchAuditRequest,
    background_tasks: BackgroundTasks
):
    """
    Create a batch audit job for multiple repositories.

    Returns a job ID that can be used to check status.

    Limits:
    - Maximum 50 repositories per batch
    - Maximum 10 collectors
    - Maximum 10 analyzers
    """
    # Cleanup old jobs before checking limit
    cleanup_old_jobs()

    # Check if we've hit the job limit
    if len(batch_jobs) >= MAX_BATCH_JOBS:
        raise HTTPException(
            status_code=429,
            detail=f"Maximum batch job limit reached ({MAX_BATCH_JOBS}). Please try again later."
        )

    # Validate input
    if not request.repositories:
        raise HTTPException(
            status_code=400,
            detail="At least one repository is required"
        )

    job_id = str(uuid.uuid4())

    # Create job record
    batch_jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "total_items": len(request.repositories),
        "completed_items": 0,
        "failed_items": 0,
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "results": {}
    }

    # Start background processing
    background_tasks.add_task(process_batch_audit, job_id, request)

    return {
        "job_id": job_id,
        "status": "pending",
        "message": f"Batch audit started for {len(request.repositories)} repositories"
    }


@router.get("/audit/{job_id}", response_model=BatchJobStatus)
async def get_batch_audit_status(job_id: str):
    """
    Get the status of a batch audit job.
    """
    if job_id not in batch_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return batch_jobs[job_id]


@router.get("/audit")
async def list_batch_audits(
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of jobs to return"),
    offset: int = Query(default=0, ge=0, description="Number of jobs to skip"),
    status: Optional[str] = Query(default=None, description="Filter by status (pending, running, completed, failed)")
):
    """
    List batch audit jobs with pagination.

    Supports filtering by status and pagination to prevent DoS via large responses.

    Query Parameters:
    - limit: Maximum number of jobs to return (1-100, default: 20)
    - offset: Number of jobs to skip for pagination (default: 0)
    - status: Optional filter by job status
    """
    # Get all jobs
    all_jobs = list(batch_jobs.values())

    # Filter by status if provided
    if status:
        all_jobs = [job for job in all_jobs if job.get("status") == status]

    # Sort by started_at descending (most recent first)
    all_jobs.sort(key=lambda x: x.get("started_at", ""), reverse=True)

    # Apply pagination
    total_count = len(all_jobs)
    paginated_jobs = all_jobs[offset:offset + limit]

    return {
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "jobs": paginated_jobs
    }


@router.delete("/audit/{job_id}")
async def delete_batch_audit(job_id: str):
    """
    Delete a batch audit job and its results.
    """
    if job_id not in batch_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    del batch_jobs[job_id]

    return {"message": "Batch audit deleted", "job_id": job_id}
