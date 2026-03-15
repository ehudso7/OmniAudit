"""
PR Reviews & Repository API Routes

Endpoints for managing PR review history and repository connections.
Uses SQLAlchemy persistence instead of in-memory storage.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func
import uuid

from ..db.base import get_db, init_db
from ..db.models import Repository, Review, User
from .auth_routes import get_current_user

router = APIRouter(prefix="/api/v1", tags=["reviews"])


class ConnectRepoRequest(BaseModel):
    owner: str
    repo: str


def _seed_demo_data_if_empty(db: Session):
    """Seed demo data only if tables are empty (first run)."""
    if db.query(Repository).count() > 0:
        return

    now = datetime.utcnow()
    repos = [
        Repository(owner="acme", name="frontend", full_name="acme/frontend", url="https://github.com/acme/frontend", status="active"),
        Repository(owner="acme", name="api-server", full_name="acme/api-server", url="https://github.com/acme/api-server", status="active"),
        Repository(owner="acme", name="mobile-app", full_name="acme/mobile-app", url="https://github.com/acme/mobile-app", status="active"),
        Repository(owner="acme", name="backend", full_name="acme/backend", url="https://github.com/acme/backend", status="active"),
    ]
    db.add_all(repos)
    db.flush()

    reviews = [
        Review(
            repo="acme/frontend", owner="acme", repo_name="frontend",
            pr_number=142, title="Add user authentication flow", author="johndoe",
            status="reviewed", issues_found=3, security_issues=1, performance_issues=1,
            quality_issues=0, suggestions=1, action="REQUEST_CHANGES",
            reviewed_at=now - timedelta(hours=2),
            comments=[
                {"type": "security", "line": 45, "file": "auth.js", "message": "Potential XSS vulnerability"},
                {"type": "performance", "line": 128, "file": "login.js", "message": "Consider memoizing this function"},
                {"type": "suggestion", "line": 67, "file": "auth.js", "message": "Add error handling for network failures"}
            ]
        ),
        Review(
            repo="acme/api-server", owner="acme", repo_name="api-server",
            pr_number=89, title="Optimize database queries", author="janedoe",
            status="reviewed", issues_found=0, security_issues=0, performance_issues=0,
            quality_issues=0, suggestions=0, action="APPROVE",
            reviewed_at=now - timedelta(hours=5), comments=[]
        ),
        Review(
            repo="acme/frontend", owner="acme", repo_name="frontend",
            pr_number=141, title="Update dependencies", author="bobsmith",
            status="reviewed", issues_found=5, security_issues=2, performance_issues=0,
            quality_issues=1, suggestions=2, action="REQUEST_CHANGES",
            reviewed_at=now - timedelta(hours=12),
            comments=[
                {"type": "security", "line": 1, "file": "package.json", "message": "lodash 4.17.15 has known vulnerabilities"},
                {"type": "security", "line": 12, "file": "package.json", "message": "axios 0.19.0 is vulnerable to SSRF"},
            ]
        ),
        Review(
            repo="acme/mobile-app", owner="acme", repo_name="mobile-app",
            pr_number=56, title="Implement push notifications", author="alicew",
            status="reviewed", issues_found=1, security_issues=0, performance_issues=1,
            quality_issues=0, suggestions=0, action="COMMENT",
            reviewed_at=now - timedelta(days=1),
            comments=[
                {"type": "performance", "line": 89, "file": "notifications.ts", "message": "Large payload may cause delays on slow networks"}
            ]
        ),
        Review(
            repo="acme/backend", owner="acme", repo_name="backend",
            pr_number=234, title="Add rate limiting middleware", author="techops",
            status="reviewed", issues_found=0, security_issues=0, performance_issues=0,
            quality_issues=0, suggestions=0, action="APPROVE",
            reviewed_at=now - timedelta(days=1, hours=6), comments=[]
        ),
    ]
    db.add_all(reviews)
    db.commit()


def _review_to_dict(review: Review) -> Dict[str, Any]:
    return {
        "id": review.id,
        "repo": review.repo,
        "owner": review.owner,
        "repo_name": review.repo_name,
        "pr_number": review.pr_number,
        "title": review.title,
        "author": review.author,
        "status": review.status,
        "issues_found": review.issues_found,
        "security_issues": review.security_issues,
        "performance_issues": review.performance_issues,
        "quality_issues": review.quality_issues,
        "suggestions": review.suggestions,
        "reviewed_at": review.reviewed_at.isoformat() + "Z" if review.reviewed_at else None,
        "action": review.action,
        "comments": review.comments or [],
    }


def _repo_to_dict(repo: Repository) -> Dict[str, Any]:
    return {
        "id": repo.id,
        "owner": repo.owner,
        "name": repo.name,
        "full_name": repo.full_name,
        "url": repo.url,
        "connected_at": repo.connected_at.isoformat() + "Z" if repo.connected_at else None,
        "status": repo.status,
    }


@router.get("/reviews")
async def get_reviews(
    repo: Optional[str] = Query(None, description="Filter by repository"),
    action: Optional[str] = Query(None, description="Filter by action (APPROVE, REQUEST_CHANGES, COMMENT)"),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get PR review history."""
    _seed_demo_data_if_empty(db)

    query = db.query(Review)
    if repo:
        query = query.filter(Review.repo == repo)
    if action:
        query = query.filter(sql_func.lower(Review.action) == action.lower())

    total = query.count()
    reviews = query.order_by(Review.reviewed_at.desc()).offset(offset).limit(limit).all()

    return {
        "reviews": [_review_to_dict(r) for r in reviews],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/reviews/stats")
async def get_review_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get review statistics."""
    _seed_demo_data_if_empty(db)

    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    total_reviews = db.query(Review).count()
    total_issues = db.query(sql_func.coalesce(sql_func.sum(Review.issues_found), 0)).scalar()
    security_issues = db.query(sql_func.coalesce(sql_func.sum(Review.security_issues), 0)).scalar()
    performance_issues = db.query(sql_func.coalesce(sql_func.sum(Review.performance_issues), 0)).scalar()

    this_week = db.query(Review).filter(Review.reviewed_at > week_ago).count()
    this_month = db.query(Review).filter(Review.reviewed_at > now - timedelta(days=30)).count()

    approved = db.query(Review).filter(Review.action == "APPROVE").count()
    approval_rate = (approved / total_reviews * 100) if total_reviews > 0 else 0

    security_blocked = db.query(Review).filter(
        Review.action == "REQUEST_CHANGES",
        Review.security_issues > 0
    ).count()

    repos_connected = db.query(Repository).count()

    return {
        "total_reviews": total_reviews,
        "issues_found": int(total_issues),
        "security_issues": int(security_issues),
        "performance_issues": int(performance_issues),
        "security_blocked": security_blocked,
        "this_week": this_week,
        "this_month": this_month,
        "approval_rate": round(approval_rate, 1),
        "repos_connected": repos_connected,
        "avg_issues_per_pr": round(int(total_issues) / total_reviews, 1) if total_reviews > 0 else 0,
    }


@router.get("/reviews/{review_id}")
async def get_review(review_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get a specific PR review by ID."""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return {"review": _review_to_dict(review)}


@router.get("/repositories")
async def get_repositories(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get connected repositories."""
    _seed_demo_data_if_empty(db)
    repos = db.query(Repository).all()
    return {
        "repositories": [_repo_to_dict(r) for r in repos],
        "total": len(repos),
    }


@router.post("/repositories/connect")
async def connect_repository(
    request: ConnectRepoRequest,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Connect a new repository."""
    full_name = f"{request.owner}/{request.repo}"

    existing = db.query(Repository).filter(Repository.full_name == full_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Repository already connected")

    new_repo = Repository(
        owner=request.owner,
        name=request.repo,
        full_name=full_name,
        url=f"https://github.com/{full_name}",
        user_id=user.id if user else None,
        status="active",
    )
    db.add(new_repo)
    db.commit()
    db.refresh(new_repo)

    # Send notification
    try:
        from ..services.notification_service import NotificationService
        NotificationService.notify_repo_connected(db, full_name, user_id=user.id if user else None)
    except Exception:
        pass  # Don't fail the connect if notification fails

    return {"repository": _repo_to_dict(new_repo), "message": "Repository connected successfully"}


@router.delete("/repositories/{repo_id}")
async def disconnect_repository(repo_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Disconnect a repository."""
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    full_name = repo.full_name
    db.delete(repo)
    db.commit()
    return {"message": f"Disconnected {full_name}"}


@router.get("/dashboard/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get dashboard statistics and metrics."""
    _seed_demo_data_if_empty(db)

    review_stats = await get_review_stats(db)

    now = datetime.utcnow()
    activity = []
    for i in range(7):
        day = now - timedelta(days=6 - i)
        day_str = day.strftime("%a")
        day_reviews = db.query(Review).filter(
            sql_func.date(Review.reviewed_at) == day.date()
        ).count()
        activity.append({"day": day_str, "reviews": day_reviews})

    # Issues breakdown
    quality_sum = db.query(sql_func.coalesce(sql_func.sum(Review.quality_issues), 0)).scalar()
    suggestions_sum = db.query(sql_func.coalesce(sql_func.sum(Review.suggestions), 0)).scalar()
    issues_breakdown = {
        "security": review_stats["security_issues"],
        "performance": review_stats["performance_issues"],
        "quality": int(quality_sum),
        "suggestions": int(suggestions_sum),
    }

    # Top repositories
    from sqlalchemy import desc
    top_repos_query = (
        db.query(Review.repo, sql_func.count(Review.id).label("cnt"))
        .group_by(Review.repo)
        .order_by(desc("cnt"))
        .limit(5)
        .all()
    )
    top_repos = [{"name": r[0], "reviews": r[1]} for r in top_repos_query]

    # Recent reviews
    recent = db.query(Review).order_by(Review.reviewed_at.desc()).limit(5).all()

    # Browser run stats
    from ..db.models import BrowserRun
    total_browser_runs = db.query(BrowserRun).count()
    browser_passed = db.query(BrowserRun).filter(BrowserRun.status == "completed", BrowserRun.score >= 70).count()
    browser_failed = db.query(BrowserRun).filter(BrowserRun.status == "completed", BrowserRun.score < 70).count()
    browser_errors = db.query(BrowserRun).filter(BrowserRun.status == "failed").count()

    return {
        "stats": {
            **review_stats,
            "browser_runs": total_browser_runs,
            "browser_pass_rate": round(browser_passed / total_browser_runs * 100, 1) if total_browser_runs > 0 else 0,
        },
        "activity": activity,
        "issues_breakdown": issues_breakdown,
        "top_repositories": top_repos,
        "recent_reviews": [_review_to_dict(r) for r in recent],
        "browser_summary": {
            "total": total_browser_runs,
            "passed": browser_passed,
            "failed": browser_failed,
            "errors": browser_errors,
        },
    }
