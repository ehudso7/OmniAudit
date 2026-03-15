"""
Notification API Routes

Endpoints for reading and managing user notifications.
"""

from fastapi import APIRouter, Depends, Query
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
            (Notification.user_id == user.id) | (Notification.user_id == None)
        )
    if unread_only:
        query = query.filter(Notification.read == False)

    total = query.count()
    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()

    return {
        "notifications": [
            {
                "id": n.id,
                "event_type": n.event_type,
                "title": n.title,
                "message": n.message,
                "severity": n.severity,
                "metadata": n.metadata,
                "read": n.read,
                "created_at": n.created_at.isoformat() + "Z" if n.created_at else None,
            }
            for n in notifications
        ],
        "total": total,
        "unread": query.filter(Notification.read == False).count() if not unread_only else total,
    }


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Mark a notification as read."""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if notification:
        notification.read = True
        db.commit()
    return {"status": "ok"}


@router.post("/notifications/read-all")
async def mark_all_read(
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Mark all notifications as read."""
    query = db.query(Notification).filter(Notification.read == False)
    if user:
        query = query.filter(
            (Notification.user_id == user.id) | (Notification.user_id == None)
        )
    count = query.update({"read": True})
    db.commit()
    return {"marked_read": count}
