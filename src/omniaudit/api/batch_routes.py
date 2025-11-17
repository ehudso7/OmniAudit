"""
Batch Operations API Routes

Endpoints for batch processing multiple repositories or audits.
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime, timedelta

from ..utils.logger import get_logger

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
        max_items=50  # Limit to prevent DoS
    )
    collectors: List[str] = Field(
        default=["git_collector"],
        description="Collectors to run on each repository",
        max_items=10
    )
    analyzers: List[str] = Field(
        default=[],
        description="Analyzers to run on each repository",
        max_items=10
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


async def process_batch_audit(job_id: str, request: BatchAuditRequest):
    """Process batch audit in background."""
    job = batch_jobs[job_id]
    job["status"] = "running"

    results = {}
    completed = 0
    failed = 0

    for idx, repo_config in enumerate(request.repositories):
        try:
            logger.info(f"Processing repository {idx + 1}/{len(request.repositories)}")

            # TODO: Actually run audit
            # For now, simulate
            repo_name = repo_config.get("name", f"repo_{idx}")
            results[repo_name] = {
                "status": "success",
                "collectors": {},
                "analyzers": {}
            }

            completed += 1

        except Exception as e:
            logger.error(f"Failed to process repository: {e}")
            failed += 1

        job["completed_items"] = completed
        job["failed_items"] = failed
        job["results"] = results

    job["status"] = "completed"
    job["completed_at"] = datetime.now().isoformat()


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
