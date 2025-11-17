"""
Batch Operations API Routes

Endpoints for batch processing multiple repositories or audits.
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List
import uuid
from datetime import datetime

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


@router.get("/audit", response_model=List[Dict[str, Any]])
async def list_batch_audits():
    """
    List all batch audit jobs.
    """
    return list(batch_jobs.values())


@router.delete("/audit/{job_id}")
async def delete_batch_audit(job_id: str):
    """
    Delete a batch audit job and its results.
    """
    if job_id not in batch_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    del batch_jobs[job_id]

    return {"message": "Batch audit deleted", "job_id": job_id}
