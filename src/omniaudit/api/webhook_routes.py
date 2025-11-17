"""
Webhook API Routes

Endpoints for receiving webhooks from external services like GitHub.
"""

import hmac
import hashlib
from fastapi import APIRouter, HTTPException, Header, Request, BackgroundTasks, status
from typing import Dict, Any, Optional
import os

from ..utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/webhooks",
    tags=["Webhooks"],
    responses={
        401: {"description": "Invalid webhook signature"},
        500: {"description": "Webhook processing failed"}
    }
)


def verify_github_signature(payload_body: bytes, signature_header: str, secret: str) -> bool:
    """
    Verify GitHub webhook signature using constant-time comparison.

    Prevents timing attacks by using hmac.compare_digest.
    """
    if not signature_header or not secret:
        return False

    try:
        hash_object = hmac.new(
            secret.encode('utf-8'),
            msg=payload_body,
            digestmod=hashlib.sha256
        )
        expected_signature = "sha256=" + hash_object.hexdigest()

        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_signature, signature_header)
    except Exception as e:
        logger.error(f"Signature verification failed: {e}")
        return False


async def process_github_webhook(event: str, payload: Dict[str, Any]):
    """Process GitHub webhook events in background."""
    try:
        logger.info(f"Processing GitHub webhook event: {event}")

        if event == "push":
            # Handle push events
            repo_name = payload.get("repository", {}).get("full_name")
            commits = payload.get("commits", [])
            logger.info(f"Push to {repo_name}: {len(commits)} commits")

            # TODO: Trigger audit on push
            # from ..collectors.git_collector import GitCollector
            # collector = GitCollector({"repo_path": clone_url})
            # result = collector.collect()

        elif event == "pull_request":
            # Handle PR events
            action = payload.get("action")
            pr_number = payload.get("pull_request", {}).get("number")
            logger.info(f"Pull request {pr_number}: {action}")

            # TODO: Run audit on PR

        logger.info(f"Successfully processed {event} webhook")

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")


@router.post("/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_github_event: Optional[str] = Header(None),
    x_hub_signature_256: Optional[str] = Header(None)
):
    """
    Receive GitHub webhooks.

    Configure this endpoint in your GitHub repository settings:
    - Payload URL: https://your-domain/api/v1/webhooks/github
    - Content type: application/json
    - Secret: Set GITHUB_WEBHOOK_SECRET environment variable
    - Events: Choose which events to receive
    """
    # Get webhook secret from environment
    secret = os.environ.get("GITHUB_WEBHOOK_SECRET", "")

    # Require secret in production
    if not secret:
        logger.error("GITHUB_WEBHOOK_SECRET not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook endpoint not properly configured. Set GITHUB_WEBHOOK_SECRET."
        )

    # Read request body
    payload_body = await request.body()

    # Verify signature (required for security)
    if not verify_github_signature(payload_body, x_hub_signature_256, secret):
        logger.warning("Invalid GitHub webhook signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )

    # Parse JSON payload
    payload = await request.json()

    # Process webhook in background
    background_tasks.add_task(process_github_webhook, x_github_event, payload)

    return {
        "status": "accepted",
        "event": x_github_event,
        "repository": payload.get("repository", {}).get("full_name")
    }


def verify_slack_token(token: str) -> bool:
    """Verify Slack request token."""
    expected_token = os.environ.get("SLACK_VERIFICATION_TOKEN", "")
    if not expected_token:
        return False
    return hmac.compare_digest(token, expected_token)


@router.post("/slack")
async def slack_webhook(payload: Dict[str, Any]):
    """
    Receive Slack slash commands or interactive messages.

    Example slash command: /omniaudit status

    Configure SLACK_VERIFICATION_TOKEN environment variable for security.
    """
    # Verify Slack token
    token = payload.get("token", "")
    if not verify_slack_token(token):
        logger.warning("Invalid Slack verification token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid verification token"
        )

    # Handle Slack slash commands
    command = payload.get("command")
    text = payload.get("text", "")

    if command == "/omniaudit":
        if text == "status":
            return {
                "response_type": "in_channel",
                "text": "✅ OmniAudit is operational",
                "attachments": [{
                    "text": "Use `/omniaudit help` for available commands"
                }]
            }
        elif text == "help":
            return {
                "response_type": "ephemeral",
                "text": "Available commands:",
                "attachments": [{
                    "text": "• `/omniaudit status` - Check service status\n"
                           "• `/omniaudit audit <repo>` - Run audit on repository"
                }]
            }

    return {"response_type": "ephemeral", "text": "Unknown command"}


@router.get("/status")
async def webhook_status():
    """Get webhook configuration status."""
    return {
        "github_webhook_configured": bool(os.environ.get("GITHUB_WEBHOOK_SECRET")),
        "supported_events": ["push", "pull_request", "release"],
        "endpoints": {
            "github": "/api/v1/webhooks/github",
            "slack": "/api/v1/webhooks/slack"
        }
    }
