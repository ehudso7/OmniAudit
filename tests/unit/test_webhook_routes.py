"""
Unit tests for webhook routes.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from omniaudit.api.main import app


@pytest.mark.asyncio
class TestWebhookRoutes:
    """Test webhook API routes."""

    async def test_webhook_status(self):
        """Test webhook status endpoint."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/webhooks/status")

        assert response.status_code == 200
        data = response.json()
        assert "github_webhook_configured" in data
        assert "supported_events" in data
        assert "endpoints" in data
        assert "push" in data["supported_events"]
        assert "pull_request" in data["supported_events"]

    async def test_github_webhook_without_secret(self):
        """Test GitHub webhook returns 503 when secret not configured."""
        payload = {
            "repository": {"full_name": "user/repo"},
            "commits": [{"id": "abc123"}]
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/webhooks/github",
                json=payload,
                headers={"X-GitHub-Event": "push"}
            )

        # Should return 503 when secret not configured (secure behavior)
        assert response.status_code == 503
        data = response.json()
        assert "GITHUB_WEBHOOK_SECRET" in data["detail"]

    async def test_slack_webhook_status_command(self):
        """Test Slack webhook returns 503 when signing secret not configured."""
        payload = {
            "command": "/omniaudit",
            "text": "status"
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/webhooks/slack",
                json=payload
            )

        # Should return 503 when signing secret not configured (secure behavior)
        assert response.status_code == 503
        data = response.json()
        assert "SLACK_SIGNING_SECRET" in data["detail"]

    async def test_slack_webhook_help_command(self):
        """Test Slack webhook returns 503 when signing secret not configured."""
        payload = {
            "command": "/omniaudit",
            "text": "help"
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/webhooks/slack",
                json=payload
            )

        # Should return 503 when signing secret not configured (secure behavior)
        assert response.status_code == 503
        data = response.json()
        assert "SLACK_SIGNING_SECRET" in data["detail"]

    async def test_slack_webhook_unknown_command(self):
        """Test Slack webhook returns 503 when signing secret not configured."""
        payload = {
            "command": "/omniaudit",
            "text": "unknown"
        }

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/webhooks/slack",
                json=payload
            )

        # Should return 503 when signing secret not configured (secure behavior)
        assert response.status_code == 503
        data = response.json()
        assert "SLACK_SIGNING_SECRET" in data["detail"]
