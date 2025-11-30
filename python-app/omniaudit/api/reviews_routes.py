"""
PR Reviews API Routes

Endpoints for managing PR review history and repository connections.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/api/v1", tags=["reviews"])


# In-memory storage (would be database in production)
REVIEWS_STORE: List[Dict[str, Any]] = []
REPOSITORIES_STORE: List[Dict[str, Any]] = []


class ConnectRepoRequest(BaseModel):
    owner: str
    repo: str


# Initialize with some realistic demo data
def init_demo_data():
    """Initialize demo data for demonstration purposes."""
    global REVIEWS_STORE, REPOSITORIES_STORE

    if not REVIEWS_STORE:
        now = datetime.utcnow()
        REVIEWS_STORE = [
            {
                "id": str(uuid.uuid4()),
                "repo": "acme/frontend",
                "owner": "acme",
                "repo_name": "frontend",
                "pr_number": 142,
                "title": "Add user authentication flow",
                "author": "johndoe",
                "status": "reviewed",
                "issues_found": 3,
                "security_issues": 1,
                "performance_issues": 1,
                "quality_issues": 0,
                "suggestions": 1,
                "reviewed_at": (now - timedelta(hours=2)).isoformat() + "Z",
                "action": "REQUEST_CHANGES",
                "comments": [
                    {"type": "security", "line": 45, "file": "auth.js", "message": "Potential XSS vulnerability"},
                    {"type": "performance", "line": 128, "file": "login.js", "message": "Consider memoizing this function"},
                    {"type": "suggestion", "line": 67, "file": "auth.js", "message": "Add error handling for network failures"}
                ]
            },
            {
                "id": str(uuid.uuid4()),
                "repo": "acme/api-server",
                "owner": "acme",
                "repo_name": "api-server",
                "pr_number": 89,
                "title": "Optimize database queries",
                "author": "janedoe",
                "status": "reviewed",
                "issues_found": 0,
                "security_issues": 0,
                "performance_issues": 0,
                "quality_issues": 0,
                "suggestions": 0,
                "reviewed_at": (now - timedelta(hours=5)).isoformat() + "Z",
                "action": "APPROVE",
                "comments": []
            },
            {
                "id": str(uuid.uuid4()),
                "repo": "acme/frontend",
                "owner": "acme",
                "repo_name": "frontend",
                "pr_number": 141,
                "title": "Update dependencies",
                "author": "bobsmith",
                "status": "reviewed",
                "issues_found": 5,
                "security_issues": 2,
                "performance_issues": 0,
                "quality_issues": 1,
                "suggestions": 2,
                "reviewed_at": (now - timedelta(hours=12)).isoformat() + "Z",
                "action": "REQUEST_CHANGES",
                "comments": [
                    {"type": "security", "line": 1, "file": "package.json", "message": "lodash 4.17.15 has known vulnerabilities"},
                    {"type": "security", "line": 12, "file": "package.json", "message": "axios 0.19.0 is vulnerable to SSRF"},
                ]
            },
            {
                "id": str(uuid.uuid4()),
                "repo": "acme/mobile-app",
                "owner": "acme",
                "repo_name": "mobile-app",
                "pr_number": 56,
                "title": "Implement push notifications",
                "author": "alicew",
                "status": "reviewed",
                "issues_found": 1,
                "security_issues": 0,
                "performance_issues": 1,
                "quality_issues": 0,
                "suggestions": 0,
                "reviewed_at": (now - timedelta(days=1)).isoformat() + "Z",
                "action": "COMMENT",
                "comments": [
                    {"type": "performance", "line": 89, "file": "notifications.ts", "message": "Large payload may cause delays on slow networks"}
                ]
            },
            {
                "id": str(uuid.uuid4()),
                "repo": "acme/backend",
                "owner": "acme",
                "repo_name": "backend",
                "pr_number": 234,
                "title": "Add rate limiting middleware",
                "author": "techops",
                "status": "reviewed",
                "issues_found": 0,
                "security_issues": 0,
                "performance_issues": 0,
                "quality_issues": 0,
                "suggestions": 0,
                "reviewed_at": (now - timedelta(days=1, hours=6)).isoformat() + "Z",
                "action": "APPROVE",
                "comments": []
            }
        ]

    if not REPOSITORIES_STORE:
        REPOSITORIES_STORE = [
            {"id": str(uuid.uuid4()), "owner": "acme", "name": "frontend", "full_name": "acme/frontend", "url": "https://github.com/acme/frontend", "connected_at": datetime.utcnow().isoformat() + "Z", "status": "active"},
            {"id": str(uuid.uuid4()), "owner": "acme", "name": "api-server", "full_name": "acme/api-server", "url": "https://github.com/acme/api-server", "connected_at": datetime.utcnow().isoformat() + "Z", "status": "active"},
            {"id": str(uuid.uuid4()), "owner": "acme", "name": "mobile-app", "full_name": "acme/mobile-app", "url": "https://github.com/acme/mobile-app", "connected_at": datetime.utcnow().isoformat() + "Z", "status": "active"},
            {"id": str(uuid.uuid4()), "owner": "acme", "name": "backend", "full_name": "acme/backend", "url": "https://github.com/acme/backend", "connected_at": datetime.utcnow().isoformat() + "Z", "status": "active"},
        ]


# Initialize demo data on module load
init_demo_data()


@router.get("/reviews")
async def get_reviews(
    repo: Optional[str] = Query(None, description="Filter by repository"),
    action: Optional[str] = Query(None, description="Filter by action (APPROVE, REQUEST_CHANGES, COMMENT)"),
    limit: int = Query(50, le=100),
    offset: int = Query(0)
) -> Dict[str, Any]:
    """Get PR review history."""
    reviews = REVIEWS_STORE.copy()

    # Apply filters
    if repo:
        reviews = [r for r in reviews if r["repo"] == repo]
    if action:
        reviews = [r for r in reviews if r["action"].lower() == action.lower()]

    # Sort by reviewed_at descending
    reviews.sort(key=lambda x: x["reviewed_at"], reverse=True)

    # Paginate
    total = len(reviews)
    reviews = reviews[offset:offset + limit]

    return {
        "reviews": reviews,
        "total": total,
        "limit": limit,
        "offset": offset
    }


# IMPORTANT: Static route must come BEFORE parameterized route
@router.get("/reviews/stats")
async def get_review_stats() -> Dict[str, Any]:
    """Get review statistics."""
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    total_reviews = len(REVIEWS_STORE)

    # Calculate stats
    total_issues = sum(r["issues_found"] for r in REVIEWS_STORE)
    security_issues = sum(r["security_issues"] for r in REVIEWS_STORE)
    performance_issues = sum(r["performance_issues"] for r in REVIEWS_STORE)

    # Reviews this week
    this_week = len([r for r in REVIEWS_STORE
                     if datetime.fromisoformat(r["reviewed_at"].replace("Z", "")) > week_ago])

    # Reviews this month
    this_month = len([r for r in REVIEWS_STORE
                      if datetime.fromisoformat(r["reviewed_at"].replace("Z", "")) > month_ago])

    # Approval rate
    approved = len([r for r in REVIEWS_STORE if r["action"] == "APPROVE"])
    approval_rate = (approved / total_reviews * 100) if total_reviews > 0 else 0

    # Security blocked (changes requested due to security)
    security_blocked = len([r for r in REVIEWS_STORE
                           if r["action"] == "REQUEST_CHANGES" and r["security_issues"] > 0])

    return {
        "total_reviews": total_reviews,
        "issues_found": total_issues,
        "security_issues": security_issues,
        "performance_issues": performance_issues,
        "security_blocked": security_blocked,
        "this_week": this_week,
        "this_month": this_month,
        "approval_rate": round(approval_rate, 1),
        "repos_connected": len(REPOSITORIES_STORE),
        "avg_issues_per_pr": round(total_issues / total_reviews, 1) if total_reviews > 0 else 0
    }


@router.get("/reviews/{review_id}")
async def get_review(review_id: str) -> Dict[str, Any]:
    """Get a specific PR review by ID."""
    for review in REVIEWS_STORE:
        if review["id"] == review_id:
            return {"review": review}
    raise HTTPException(status_code=404, detail="Review not found")


@router.get("/repositories")
async def get_repositories() -> Dict[str, Any]:
    """Get connected repositories."""
    return {
        "repositories": REPOSITORIES_STORE,
        "total": len(REPOSITORIES_STORE)
    }


@router.post("/repositories/connect")
async def connect_repository(request: ConnectRepoRequest) -> Dict[str, Any]:
    """Connect a new repository."""
    full_name = f"{request.owner}/{request.repo}"

    # Check if already connected
    for repo in REPOSITORIES_STORE:
        if repo["full_name"] == full_name:
            raise HTTPException(status_code=400, detail="Repository already connected")

    new_repo = {
        "id": str(uuid.uuid4()),
        "owner": request.owner,
        "name": request.repo,
        "full_name": full_name,
        "url": f"https://github.com/{full_name}",
        "connected_at": datetime.utcnow().isoformat() + "Z",
        "status": "active"
    }

    REPOSITORIES_STORE.append(new_repo)

    return {"repository": new_repo, "message": "Repository connected successfully"}


@router.delete("/repositories/{repo_id}")
async def disconnect_repository(repo_id: str) -> Dict[str, Any]:
    """Disconnect a repository."""
    for i, repo in enumerate(REPOSITORIES_STORE):
        if repo["id"] == repo_id:
            removed = REPOSITORIES_STORE.pop(i)
            return {"message": f"Disconnected {removed['full_name']}"}

    raise HTTPException(status_code=404, detail="Repository not found")


@router.get("/dashboard/stats")
async def get_dashboard_stats() -> Dict[str, Any]:
    """Get dashboard statistics and metrics."""
    review_stats = await get_review_stats()

    # Add activity data for charts
    now = datetime.utcnow()
    activity = []
    for i in range(7):
        day = now - timedelta(days=6-i)
        day_str = day.strftime("%a")
        day_reviews = len([r for r in REVIEWS_STORE
                          if datetime.fromisoformat(r["reviewed_at"].replace("Z", "")).date() == day.date()])
        activity.append({"day": day_str, "reviews": day_reviews})

    # Issues breakdown
    issues_breakdown = {
        "security": review_stats["security_issues"],
        "performance": review_stats["performance_issues"],
        "quality": sum(r.get("quality_issues", 0) for r in REVIEWS_STORE),
        "suggestions": sum(r.get("suggestions", 0) for r in REVIEWS_STORE)
    }

    # Top repositories
    repo_counts = {}
    for review in REVIEWS_STORE:
        repo = review["repo"]
        repo_counts[repo] = repo_counts.get(repo, 0) + 1

    top_repos = sorted(repo_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    # Sort reviews by date before slicing for recent_reviews
    sorted_reviews = sorted(REVIEWS_STORE, key=lambda x: x["reviewed_at"], reverse=True)

    return {
        "stats": review_stats,
        "activity": activity,
        "issues_breakdown": issues_breakdown,
        "top_repositories": [{"name": r[0], "reviews": r[1]} for r in top_repos],
        "recent_reviews": sorted_reviews[:5]
    }
