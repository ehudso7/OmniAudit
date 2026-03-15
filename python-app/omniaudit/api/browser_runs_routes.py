"""
Browser Verification Runs API Routes

Endpoints for creating, managing, and viewing browser verification runs.
"""

import asyncio
from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import uuid

from ..db.base import get_db
from ..db.models import BrowserRun, BrowserCheck, BrowserArtifact, Repository, ReleasePolicy, User
from ..services.browser_runner_service import BrowserRunnerService
from ..utils.logger import get_logger
from .auth_routes import get_current_user

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["browser-runs"])

# Shared service instance
_runner_service = BrowserRunnerService()


class BrowserRunCreateRequest(BaseModel):
    target_url: str = Field(..., description="URL to verify")
    repository_id: Optional[str] = Field(None, description="Associated repository ID")
    branch: Optional[str] = Field(None, description="Git branch name")
    commit_sha: Optional[str] = Field(None, description="Git commit SHA")
    pr_number: Optional[int] = Field(None, description="Associated PR number")
    environment: str = Field("preview", description="Environment type: preview, staging, production")
    viewport_width: int = Field(1280, description="Browser viewport width")
    viewport_height: int = Field(720, description="Browser viewport height")
    device: Optional[str] = Field(None, description="Device emulation name")
    journeys: Optional[List[Dict[str, Any]]] = Field(None, description="Custom journeys to run")
    auth_config: Optional[Dict[str, Any]] = Field(None, description="Authentication configuration")
    release_gate: bool = Field(False, description="Whether this run enforces release gate policy")


class BrowserRunResponse(BaseModel):
    id: str
    target_url: str
    status: str
    environment: Optional[str] = None
    score: Optional[int] = None
    summary: Optional[str] = None
    findings_count: int = 0
    security_findings: int = 0
    performance_findings: int = 0
    accessibility_findings: int = 0
    console_errors: int = 0
    network_failures: int = 0
    blocking_verdict: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None


def _run_to_dict(run: BrowserRun) -> Dict[str, Any]:
    return {
        "id": run.id,
        "target_url": run.target_url,
        "repository_id": run.repository_id,
        "environment": run.environment,
        "branch": run.branch,
        "commit_sha": run.commit_sha,
        "pr_number": run.pr_number,
        "status": run.status,
        "viewport_width": run.viewport_width,
        "viewport_height": run.viewport_height,
        "device": run.device,
        "journeys": run.journeys,
        "release_gate": run.release_gate,
        "score": run.score,
        "summary": run.summary,
        "findings_count": run.findings_count,
        "security_findings": run.security_findings,
        "performance_findings": run.performance_findings,
        "accessibility_findings": run.accessibility_findings,
        "console_errors": run.console_errors,
        "network_failures": run.network_failures,
        "blocking_verdict": run.blocking_verdict,
        "started_at": run.started_at.isoformat() + "Z" if run.started_at else None,
        "completed_at": run.completed_at.isoformat() + "Z" if run.completed_at else None,
        "created_at": run.created_at.isoformat() + "Z" if run.created_at else None,
        "duration_ms": run.duration_ms,
    }


def _check_to_dict(check: BrowserCheck) -> Dict[str, Any]:
    return {
        "id": check.id,
        "journey": check.journey,
        "check_type": check.check_type,
        "description": check.description,
        "status": check.status,
        "severity": check.severity,
        "category": check.category,
        "message": check.message,
        "details": check.details,
        "selector": check.selector,
        "url": check.url,
        "duration_ms": check.duration_ms,
    }


def _artifact_to_dict(artifact: BrowserArtifact) -> Dict[str, Any]:
    return {
        "id": artifact.id,
        "artifact_type": artifact.artifact_type,
        "name": artifact.name,
        "file_path": artifact.file_path,
        "content_type": artifact.content_type,
        "size_bytes": artifact.size_bytes,
        "metadata": artifact.extra_metadata,
        "created_at": artifact.created_at.isoformat() + "Z" if artifact.created_at else None,
    }


async def _execute_browser_run(run_id: str, request: BrowserRunCreateRequest):
    """Background task to execute the browser run."""
    from ..db.base import SessionLocal

    db = SessionLocal()
    try:
        run = db.query(BrowserRun).filter(BrowserRun.id == run_id).first()
        if not run:
            logger.error(f"Browser run {run_id} not found for execution")
            return

        run.status = "running"
        run.started_at = datetime.utcnow()
        db.commit()

        # Execute via Playwright service
        results = await _runner_service.execute_run(
            run_id=run_id,
            target_url=request.target_url,
            journeys=request.journeys,
            viewport_width=request.viewport_width,
            viewport_height=request.viewport_height,
            device=request.device,
            auth_config=request.auth_config,
        )

        # Update run with results
        run.status = results.get("status", "completed")
        run.score = results.get("score", 0)
        run.summary = results.get("summary", "")
        run.duration_ms = results.get("duration_ms")
        run.completed_at = datetime.utcnow()

        findings = results.get("findings", [])
        run.findings_count = len(findings)
        run.security_findings = len([f for f in findings if f.get("category") == "security" and f.get("status") == "failed"])
        run.performance_findings = len([f for f in findings if f.get("category") == "performance" and f.get("status") == "failed"])
        run.accessibility_findings = len(results.get("a11y_findings", []))
        run.console_errors = len([m for m in results.get("console_errors", []) if m.get("type") == "error"])
        run.network_failures = len(results.get("network_failures", []))

        # Evaluate release gate
        if run.release_gate:
            run.blocking_verdict = _evaluate_release_gate(db, run)

        # Persist checks
        for finding in findings:
            check = BrowserCheck(
                browser_run_id=run_id,
                journey=finding.get("journey", "unknown"),
                check_type=finding.get("check_type", "unknown"),
                status=finding.get("status", "unknown"),
                severity=finding.get("severity"),
                category=finding.get("category"),
                message=finding.get("message"),
                selector=finding.get("selector"),
                url=finding.get("url"),
            )
            db.add(check)

        # Persist artifacts
        for artifact_data in results.get("artifacts", []):
            import os
            file_path = artifact_data.get("path", "")
            size = 0
            if file_path and os.path.exists(file_path):
                size = os.path.getsize(file_path)

            artifact = BrowserArtifact(
                browser_run_id=run_id,
                artifact_type=artifact_data.get("type", "unknown"),
                name=artifact_data.get("name", "unnamed"),
                file_path=file_path,
                content_type=artifact_data.get("content_type"),
                size_bytes=size,
            )
            db.add(artifact)

        db.commit()
        logger.info(f"Browser run {run_id} completed with score {run.score}")

        # Send notifications
        try:
            from ..services.notification_service import NotificationService
            NotificationService.notify_run_complete(
                db, run_id, request.target_url, run.score or 0, user_id=run.user_id
            )
            if run.blocking_verdict == "blocked":
                reasons = run.blocking_reasons or ["Policy threshold not met"]
                NotificationService.notify_release_blocked(
                    db, run_id, request.target_url, reasons, user_id=run.user_id
                )
            if (run.security_findings or 0) > 0:
                NotificationService.notify_critical_issue(
                    db, request.target_url,
                    f"{run.security_findings} security findings detected",
                    user_id=run.user_id,
                )
        except Exception as notif_err:
            logger.warning(f"Notification failed: {notif_err}")

    except Exception as e:
        logger.error(f"Browser run {run_id} execution failed: {e}")
        try:
            run = db.query(BrowserRun).filter(BrowserRun.id == run_id).first()
            if run:
                run.status = "failed"
                run.summary = f"Execution error: {str(e)}"
                run.completed_at = datetime.utcnow()
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


def _evaluate_release_gate(db: Session, run: BrowserRun) -> str:
    """Evaluate release gate policy for a browser run. Sets blocking_reasons on the run."""
    reasons = []

    if not run.repository_id:
        if (run.security_findings or 0) > 0:
            reasons.append(f"Security findings: {run.security_findings}")
        if (run.score or 0) < 70:
            reasons.append(f"Score {run.score} below threshold 70")
        run.blocking_reasons = reasons if reasons else None
        return "blocked" if reasons else "passed"

    policies = db.query(ReleasePolicy).filter(
        ReleasePolicy.repository_id == run.repository_id,
        ReleasePolicy.enabled == True,
    ).all()

    if not policies:
        if (run.security_findings or 0) > 0:
            reasons.append(f"Security findings: {run.security_findings}")
        if (run.score or 0) < 70:
            reasons.append(f"Score {run.score} below default threshold 70")
        run.blocking_reasons = reasons if reasons else None
        return "blocked" if reasons else "passed"

    for policy in policies:
        if policy.min_score and (run.score or 0) < policy.min_score:
            reasons.append(f"Score {run.score} below policy minimum {policy.min_score}")
        if policy.block_on_security and (run.security_findings or 0) > 0:
            reasons.append(f"Security findings: {run.security_findings} (policy: {policy.name})")
        if policy.block_on_accessibility and (run.accessibility_findings or 0) > 0:
            reasons.append(f"Accessibility findings: {run.accessibility_findings} (policy: {policy.name})")
        if policy.block_on_performance and (run.performance_findings or 0) > 0:
            reasons.append(f"Performance findings: {run.performance_findings} (policy: {policy.name})")
        if policy.max_console_errors is not None and (run.console_errors or 0) > policy.max_console_errors:
            reasons.append(f"Console errors: {run.console_errors} exceeds max {policy.max_console_errors}")
        if policy.max_network_failures is not None and (run.network_failures or 0) > policy.max_network_failures:
            reasons.append(f"Network failures: {run.network_failures} exceeds max {policy.max_network_failures}")

    run.blocking_reasons = reasons if reasons else None
    return "blocked" if reasons else "passed"


@router.post("/browser-runs")
async def create_browser_run(
    request: BrowserRunCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Create and start a new browser verification run."""
    # Validate repository if provided
    if request.repository_id:
        repo = db.query(Repository).filter(Repository.id == request.repository_id).first()
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")

    run = BrowserRun(
        target_url=request.target_url,
        repository_id=request.repository_id,
        user_id=user.id if user else None,
        environment=request.environment,
        branch=request.branch,
        commit_sha=request.commit_sha,
        pr_number=request.pr_number,
        viewport_width=request.viewport_width,
        viewport_height=request.viewport_height,
        device=request.device,
        journeys=request.journeys,
        auth_config=request.auth_config,
        release_gate=request.release_gate,
        status="pending",
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # Run browser verification in background
    background_tasks.add_task(_execute_browser_run, run.id, request)

    return {
        "run": _run_to_dict(run),
        "message": "Browser verification run started",
    }


@router.get("/browser-runs")
async def list_browser_runs(
    repository_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
) -> Dict[str, Any]:
    """List browser verification runs. Scoped to current user if authenticated."""
    query = db.query(BrowserRun)
    if user:
        query = query.filter(
            (BrowserRun.user_id == user.id) | (BrowserRun.user_id.is_(None))
        )
    if repository_id:
        query = query.filter(BrowserRun.repository_id == repository_id)
    if status:
        query = query.filter(BrowserRun.status == status)

    total = query.count()
    runs = query.order_by(BrowserRun.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "runs": [_run_to_dict(r) for r in runs],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/browser-runs/{run_id}")
async def get_browser_run(run_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get a specific browser verification run with checks."""
    run = db.query(BrowserRun).filter(BrowserRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Browser run not found")

    checks = db.query(BrowserCheck).filter(BrowserCheck.browser_run_id == run_id).all()

    return {
        "run": _run_to_dict(run),
        "checks": [_check_to_dict(c) for c in checks],
    }


@router.post("/browser-runs/{run_id}/rerun")
async def rerun_browser_run(
    run_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Re-run a browser verification run with the same configuration."""
    original = db.query(BrowserRun).filter(BrowserRun.id == run_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="Browser run not found")

    # Create new run with same config
    new_run = BrowserRun(
        target_url=original.target_url,
        repository_id=original.repository_id,
        environment=original.environment,
        branch=original.branch,
        commit_sha=original.commit_sha,
        pr_number=original.pr_number,
        viewport_width=original.viewport_width,
        viewport_height=original.viewport_height,
        device=original.device,
        journeys=original.journeys,
        auth_config=original.auth_config,
        release_gate=original.release_gate,
        status="pending",
    )
    db.add(new_run)
    db.commit()
    db.refresh(new_run)

    # Build request for background task
    request = BrowserRunCreateRequest(
        target_url=original.target_url,
        repository_id=original.repository_id,
        environment=original.environment,
        branch=original.branch,
        commit_sha=original.commit_sha,
        pr_number=original.pr_number,
        viewport_width=original.viewport_width,
        viewport_height=original.viewport_height,
        device=original.device,
        journeys=original.journeys,
        auth_config=original.auth_config,
        release_gate=original.release_gate,
    )
    background_tasks.add_task(_execute_browser_run, new_run.id, request)

    return {
        "run": _run_to_dict(new_run),
        "message": "Browser verification re-run started",
        "original_run_id": run_id,
    }


@router.get("/browser-runs/{run_id}/artifacts")
async def get_browser_run_artifacts(run_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get artifacts for a browser verification run."""
    run = db.query(BrowserRun).filter(BrowserRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Browser run not found")

    artifacts = db.query(BrowserArtifact).filter(BrowserArtifact.browser_run_id == run_id).all()

    return {
        "run_id": run_id,
        "artifacts": [_artifact_to_dict(a) for a in artifacts],
        "total": len(artifacts),
    }


@router.get("/release-policies")
async def list_release_policies(
    repository_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """List release gate policies."""
    query = db.query(ReleasePolicy)
    if repository_id:
        query = query.filter(ReleasePolicy.repository_id == repository_id)
    policies = query.all()
    return {
        "policies": [
            {
                "id": p.id,
                "repository_id": p.repository_id,
                "name": p.name,
                "enabled": p.enabled,
                "min_score": p.min_score,
                "block_on_security": p.block_on_security,
                "block_on_accessibility": p.block_on_accessibility,
                "block_on_performance": p.block_on_performance,
                "max_critical_findings": p.max_critical_findings,
                "max_high_findings": p.max_high_findings,
                "require_browser_run": p.require_browser_run,
            }
            for p in policies
        ],
        "total": len(policies),
    }


class ReleasePolicyCreateRequest(BaseModel):
    repository_id: str
    name: str = "Default Policy"
    min_score: int = 70
    block_on_security: bool = True
    block_on_accessibility: bool = False
    block_on_performance: bool = False
    max_critical_findings: int = 0
    max_high_findings: int = 3
    require_browser_run: bool = False


@router.post("/release-policies")
async def create_release_policy(
    request: ReleasePolicyCreateRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Create a release gate policy."""
    repo = db.query(Repository).filter(Repository.id == request.repository_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    policy = ReleasePolicy(
        repository_id=request.repository_id,
        name=request.name,
        min_score=request.min_score,
        block_on_security=request.block_on_security,
        block_on_accessibility=request.block_on_accessibility,
        block_on_performance=request.block_on_performance,
        max_critical_findings=request.max_critical_findings,
        max_high_findings=request.max_high_findings,
        require_browser_run=request.require_browser_run,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)

    return {
        "policy": {
            "id": policy.id,
            "repository_id": policy.repository_id,
            "name": policy.name,
            "enabled": policy.enabled,
            "min_score": policy.min_score,
            "block_on_security": policy.block_on_security,
        },
        "message": "Release policy created",
    }


@router.get("/browser-runs/summary/stats")
async def get_browser_run_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get aggregate browser run statistics."""
    from sqlalchemy import func as sql_func

    total = db.query(BrowserRun).count()
    completed = db.query(BrowserRun).filter(BrowserRun.status == "completed").count()
    failed = db.query(BrowserRun).filter(BrowserRun.status == "failed").count()
    running = db.query(BrowserRun).filter(BrowserRun.status == "running").count()

    avg_score = db.query(sql_func.avg(BrowserRun.score)).filter(
        BrowserRun.status == "completed"
    ).scalar()

    total_security = db.query(sql_func.coalesce(sql_func.sum(BrowserRun.security_findings), 0)).scalar()
    total_a11y = db.query(sql_func.coalesce(sql_func.sum(BrowserRun.accessibility_findings), 0)).scalar()
    total_perf = db.query(sql_func.coalesce(sql_func.sum(BrowserRun.performance_findings), 0)).scalar()

    blocked = db.query(BrowserRun).filter(BrowserRun.blocking_verdict == "blocked").count()

    return {
        "total_runs": total,
        "completed": completed,
        "failed": failed,
        "running": running,
        "avg_score": round(avg_score, 1) if avg_score else 0,
        "total_security_findings": int(total_security),
        "total_accessibility_findings": int(total_a11y),
        "total_performance_findings": int(total_perf),
        "release_blocked": blocked,
    }
