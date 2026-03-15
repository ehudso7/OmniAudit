"""
Notification Service

Creates in-app notifications for high-value events.
Extensible to email/webhook delivery.
"""

from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from ..db.models import Notification
from ..utils.logger import get_logger

logger = get_logger(__name__)


class NotificationService:
    """Creates and manages notifications."""

    @staticmethod
    def notify(
        db: Session,
        event_type: str,
        title: str,
        message: str = "",
        severity: str = "info",
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        """Create a notification."""
        notification = Notification(
            user_id=user_id,
            event_type=event_type,
            title=title,
            message=message,
            severity=severity,
            metadata=metadata or {},
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        logger.info(f"Notification created: [{event_type}] {title}")
        return notification

    @staticmethod
    def notify_run_complete(db: Session, run_id: str, target_url: str, score: int, user_id: Optional[str] = None):
        """Notify when a browser run completes."""
        severity = "info" if score >= 70 else "warning" if score >= 40 else "critical"
        return NotificationService.notify(
            db,
            event_type="run_complete",
            title=f"Browser verification completed (score: {score})",
            message=f"Verification of {target_url} finished with score {score}/100.",
            severity=severity,
            user_id=user_id,
            metadata={"run_id": run_id, "score": score, "target_url": target_url},
        )

    @staticmethod
    def notify_release_blocked(db: Session, run_id: str, target_url: str, reasons: list, user_id: Optional[str] = None):
        """Notify when a release is blocked."""
        return NotificationService.notify(
            db,
            event_type="release_blocked",
            title="Release blocked by verification policy",
            message=f"Verification of {target_url} blocked release. Reasons: {', '.join(reasons)}",
            severity="critical",
            user_id=user_id,
            metadata={"run_id": run_id, "target_url": target_url, "reasons": reasons},
        )

    @staticmethod
    def notify_critical_issue(db: Session, source: str, issue: str, user_id: Optional[str] = None):
        """Notify about a critical issue found."""
        return NotificationService.notify(
            db,
            event_type="critical_issue",
            title=f"Critical issue found in {source}",
            message=issue,
            severity="critical",
            user_id=user_id,
            metadata={"source": source},
        )

    @staticmethod
    def notify_repo_connected(db: Session, repo_name: str, user_id: Optional[str] = None):
        """Notify when a repository is connected."""
        return NotificationService.notify(
            db,
            event_type="repo_connected",
            title=f"Repository connected: {repo_name}",
            message=f"{repo_name} is now connected to OmniAudit.",
            severity="info",
            user_id=user_id,
            metadata={"repo": repo_name},
        )

    @staticmethod
    def notify_pr_reviewed(db: Session, repo: str, pr_number: int, action: str, user_id: Optional[str] = None):
        """Notify when a PR review is completed."""
        return NotificationService.notify(
            db,
            event_type="pr_reviewed",
            title=f"PR #{pr_number} reviewed ({action})",
            message=f"Review posted on {repo}#{pr_number}.",
            severity="info" if action == "APPROVE" else "warning",
            user_id=user_id,
            metadata={"repo": repo, "pr_number": pr_number, "action": action},
        )
