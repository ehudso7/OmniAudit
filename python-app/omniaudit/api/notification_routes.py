"""
Notification API Routes

Endpoints for reading and managing user notifications.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from ..db.base import get_db
from ..db.models import Notification, User
from .auth_routes import get_current_user

router = APIRouter(prefix="/api/v1", tags=["notifications"])


@router.get("/notifications")
async def list_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
) -> Dict[str, Any]:
    """List notifications for the current user."""
    query = db.query(Notification)
    if user:
        query = query.filter(
            (Notification.user_id == user.id) | (Notification.user_id.is_(None))
        )
    else:
        # Unauthenticated users only see broadcast notifications
        query = query.filter(Notification.user_id.is_(None))

    if unread_only:
        query = query.filter(Notification.read == False)

    total = query.count()
    unread_query = db.query(Notification).filter(Notification.read == False)
    if user:
        unread_query = unread_query.filter(
            (Notification.user_id == user.id) | (Notification.user_id.is_(None))
        )
    else:
        unread_query = unread_query.filter(Notification.user_id.is_(None))

    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()

    return {
        "notifications": [
            {
                "id": n.id,
                "event_type": n.event_type,
                "title": n.title,
                "message": n.message,
                "severity": n.severity,
                "metadata": n.extra_metadata,
                "read": n.read,
                "created_at": n.created_at.isoformat() + "Z" if n.created_at else None,
            }
            for n in notifications
        ],
        "total": total,
        "unread": unread_query.count(),
    }


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Mark a notification as read. Validates ownership."""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    # Ownership check: only allow marking your own or broadcast notifications
    if notification.user_id and user and notification.user_id != user.id:
        raise HTTPException(status_code=403, detail="Cannot mark another user's notification as read")
    notification.read = True
    db.commit()
    return {"status": "ok"}


@router.post("/notifications/read-all")
async def mark_all_read(
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Mark all notifications as read for the current user."""
    query = db.query(Notification).filter(Notification.read == False)
    if user:
        query = query.filter(
            (Notification.user_id == user.id) | (Notification.user_id.is_(None))
        )
    else:
        # Unauthenticated: only broadcast
        query = query.filter(Notification.user_id.is_(None))
    count = query.update({"read": True})
    db.commit()
    return {"marked_read": count}
