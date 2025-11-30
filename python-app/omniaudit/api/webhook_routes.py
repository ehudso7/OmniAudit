"""
Webhook API Routes

Endpoints for receiving webhooks from external services like GitHub.
"""

import hmac
import hashlib
import time
from fastapi import APIRouter, HTTPException, Header, Request, BackgroundTasks, status
from typing import Dict, Any, Optional
import os

from ..utils.logger import get_logger
from ..services.github_service import GitHubService
from ..services.pr_analyzer import PRAnalyzer

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


async def process_pull_request(payload: Dict[str, Any]):
    """Process pull request events - run OmniAudit analysis."""
    action = payload.get("action")

    # Only analyze on open, synchronize (new commits), or reopened
    if action not in ["opened", "synchronize", "reopened"]:
        logger.info(f"Skipping PR action: {action}")
        return

    pr = payload.get("pull_request", {})
    repo = payload.get("repository", {})

    owner = repo.get("owner", {}).get("login")
    repo_name = repo.get("name")
    pr_number = pr.get("number")
    head_sha = pr.get("head", {}).get("sha")

    if not all([owner, repo_name, pr_number]):
        logger.error("Missing required PR information")
        return

    logger.info(f"🔍 Analyzing PR {owner}/{repo_name}#{pr_number}")

    try:
        # Initialize services
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            logger.error("GITHUB_TOKEN not configured")
            return

        github = GitHubService(token=token)
        analyzer = PRAnalyzer(github)

        # Run analysis
        result = await analyzer.analyze_pr(owner, repo_name, pr_number)

        # Post review
        await github.create_review(owner, repo_name, pr_number, result)

        # Create check run if we have the SHA
        if head_sha:
            try:
                await github.create_check_run(owner, repo_name, head_sha, result)
            except Exception as e:
                logger.warning(f"Could not create check run: {e}")

        logger.info(f"✅ Posted review on {owner}/{repo_name}#{pr_number}: {result.issues_found} issues")

        await github.close()

    except Exception as e:
        logger.error(f"Failed to analyze PR: {e}")


async def process_github_webhook(event: str, payload: Dict[str, Any]):
    """Process GitHub webhook events in background."""
    try:
        logger.info(f"Processing GitHub webhook event: {event}")

        if event == "pull_request":
            await process_pull_request(payload)

        elif event == "push":
            # Handle push events
            repo_name = payload.get("repository", {}).get("full_name")
            commits = payload.get("commits", [])
            logger.info(f"Push to {repo_name}: {len(commits)} commits")
            # Future: Trigger scheduled full-repo audits

        elif event == "installation":
            # Handle GitHub App installation
            action = payload.get("action")
            installation_id = payload.get("installation", {}).get("id")
            account = payload.get("installation", {}).get("account", {}).get("login")
            logger.info(f"GitHub App {action} for {account} (installation: {installation_id})")
            # Future: Store installation, send welcome message

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

    # Verify required headers
    if not x_hub_signature_256 or not x_github_event:
        logger.warning("Missing required GitHub webhook headers")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required headers (X-Hub-Signature-256 and X-GitHub-Event)"
        )

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


def verify_slack_signature(payload_body: bytes, timestamp: str, signature: str, signing_secret: str) -> bool:
    """
    Verify Slack request signature using HMAC-SHA256.

    Follows Slack's recommended security practices:
    - Uses signing secret (not deprecated verification token)
    - Includes timestamp to prevent replay attacks
    - Uses constant-time comparison

    https://api.slack.com/authentication/verifying-requests-from-slack
    """
    if not timestamp or not signature or not signing_secret:
        return False

    try:
        # Check timestamp is recent (within 5 minutes) to prevent replay attacks
        current_time = int(time.time())
        request_time = int(timestamp)
        if abs(current_time - request_time) > 60 * 5:
            logger.warning(f"Slack request timestamp too old: {abs(current_time - request_time)}s")
            return False

        # Create signature base string: v0:timestamp:body
        sig_basestring = f"v0:{timestamp}:{payload_body.decode('utf-8')}"

        # Compute HMAC-SHA256
        hash_object = hmac.new(
            signing_secret.encode('utf-8'),
            msg=sig_basestring.encode('utf-8'),
            digestmod=hashlib.sha256
        )
        expected_signature = "v0=" + hash_object.hexdigest()

        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_signature, signature)
    except (ValueError, AttributeError) as e:
        logger.error(f"Slack signature verification failed: {e}")
        return False


@router.post("/slack")
async def slack_webhook(
    request: Request,
    x_slack_request_timestamp: Optional[str] = Header(None),
    x_slack_signature: Optional[str] = Header(None)
):
    """
    Receive Slack slash commands or interactive messages.

    Example slash command: /omniaudit status

    Configure SLACK_SIGNING_SECRET environment variable for security.
    Uses Slack's recommended signature verification (not deprecated tokens).

    https://api.slack.com/authentication/verifying-requests-from-slack
    """
    # Get signing secret from environment
    signing_secret = os.environ.get("SLACK_SIGNING_SECRET", "")

    # Require signing secret in production
    if not signing_secret:
        logger.error("SLACK_SIGNING_SECRET not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Slack webhook endpoint not properly configured. Set SLACK_SIGNING_SECRET."
        )

    # Read request body
    payload_body = await request.body()

    # Verify required headers
    if not x_slack_request_timestamp or not x_slack_signature:
        logger.warning("Missing required Slack webhook headers")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required headers (X-Slack-Request-Timestamp and X-Slack-Signature)"
        )

    # Verify signature (required for security)
    if not verify_slack_signature(payload_body, x_slack_request_timestamp, x_slack_signature, signing_secret):
        logger.warning("Invalid Slack request signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )

    # Parse payload (Slack sends form-encoded data, not JSON)
    # For slash commands, parse the form data
    form_data = await request.form()
    payload = dict(form_data)

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
        "slack_webhook_configured": bool(os.environ.get("SLACK_SIGNING_SECRET")),
        "supported_events": ["push", "pull_request", "release"],
        "endpoints": {
            "github": "/api/v1/webhooks/github",
            "slack": "/api/v1/webhooks/slack"
        }
    }
