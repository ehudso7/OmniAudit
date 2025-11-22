"""
Unit tests for webhook routes.
"""

import pytest
import hmac
import hashlib
import time
import os
import json
from unittest.mock import patch
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

    async def test_github_webhook_with_valid_signature(self):
        """Test GitHub webhook accepts valid signature."""
        secret = "test_secret_key_12345"
        payload = {
            "repository": {"full_name": "user/repo"},
            "commits": [{"id": "abc123"}]
        }

        # Compute valid signature
        payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        signature = "sha256=" + hmac.new(
            secret.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()

        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": secret}):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/webhooks/github",
                    content=payload_bytes,
                    headers={
                        "X-GitHub-Event": "push",
                        "X-Hub-Signature-256": signature,
                        "Content-Type": "application/json"
                    }
                )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert data["event"] == "push"

    async def test_github_webhook_with_invalid_signature(self):
        """Test GitHub webhook rejects invalid signature."""
        secret = "test_secret_key_12345"
        payload = {
            "repository": {"full_name": "user/repo"},
            "commits": [{"id": "abc123"}]
        }

        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": secret}):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/webhooks/github",
                    json=payload,
                    headers={
                        "X-GitHub-Event": "push",
                        "X-Hub-Signature-256": "sha256=invalid_signature"
                    }
                )

        assert response.status_code == 401
        data = response.json()
        assert "Invalid signature" in data["detail"]

    async def test_github_webhook_missing_headers(self):
        """Test GitHub webhook returns 400 when headers missing."""
        secret = "test_secret_key_12345"
        payload = {"repository": {"full_name": "user/repo"}}

        with patch.dict(os.environ, {"GITHUB_WEBHOOK_SECRET": secret}):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                # Missing X-GitHub-Event header
                response = await client.post(
                    "/api/v1/webhooks/github",
                    json=payload
                )

        assert response.status_code == 400
        data = response.json()
        assert "Missing required headers" in data["detail"]

    @pytest.mark.parametrize("command,expected_text", [
        ("status", "OmniAudit is operational"),
        ("help", "Available commands"),
        ("unknown", "Unknown command")
    ])
    async def test_slack_webhook_without_secret(self, command, expected_text):
        """Test Slack webhook returns 503 when signing secret not configured."""
        payload = {
            "command": "/omniaudit",
            "text": command
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

    async def test_slack_webhook_with_valid_signature(self):
        """Test Slack webhook accepts valid signature."""
        signing_secret = "test_slack_secret_12345"
        timestamp = str(int(time.time()))
        payload_str = "command=%2Fomniaudit&text=status"

        # Compute valid signature
        sig_basestring = f"v0:{timestamp}:{payload_str}"
        signature = "v0=" + hmac.new(
            signing_secret.encode('utf-8'),
            sig_basestring.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        with patch.dict(os.environ, {"SLACK_SIGNING_SECRET": signing_secret}):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/webhooks/slack",
                    content=payload_str,
                    headers={
                        "X-Slack-Request-Timestamp": timestamp,
                        "X-Slack-Signature": signature,
                        "Content-Type": "application/x-www-form-urlencoded"
                    }
                )

        assert response.status_code == 200
        data = response.json()
        assert "OmniAudit is operational" in data["text"]

    async def test_slack_webhook_with_invalid_signature(self):
        """Test Slack webhook rejects invalid signature."""
        signing_secret = "test_slack_secret_12345"
        timestamp = str(int(time.time()))

        with patch.dict(os.environ, {"SLACK_SIGNING_SECRET": signing_secret}):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/webhooks/slack",
                    data={"command": "/omniaudit", "text": "status"},
                    headers={
                        "X-Slack-Request-Timestamp": timestamp,
                        "X-Slack-Signature": "v0=invalid_signature"
                    }
                )

        assert response.status_code == 401
        data = response.json()
        assert "Invalid signature" in data["detail"]

    async def test_slack_webhook_replay_attack_prevention(self):
        """Test Slack webhook rejects old timestamps (replay attack prevention)."""
        signing_secret = "test_slack_secret_12345"
        # Timestamp from 10 minutes ago (outside 5-minute window)
        old_timestamp = str(int(time.time()) - 600)
        payload_str = "command=%2Fomniaudit&text=status"

        # Compute valid signature for old timestamp
        sig_basestring = f"v0:{old_timestamp}:{payload_str}"
        signature = "v0=" + hmac.new(
            signing_secret.encode('utf-8'),
            sig_basestring.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        with patch.dict(os.environ, {"SLACK_SIGNING_SECRET": signing_secret}):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/webhooks/slack",
                    content=payload_str,
                    headers={
                        "X-Slack-Request-Timestamp": old_timestamp,
                        "X-Slack-Signature": signature,
                        "Content-Type": "application/x-www-form-urlencoded"
                    }
                )

        assert response.status_code == 401
        data = response.json()
        assert "Invalid signature" in data["detail"]

    async def test_slack_webhook_missing_headers(self):
        """Test Slack webhook returns 400 when headers missing."""
        signing_secret = "test_slack_secret_12345"

        with patch.dict(os.environ, {"SLACK_SIGNING_SECRET": signing_secret}):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                # Missing signature headers
                response = await client.post(
                    "/api/v1/webhooks/slack",
                    data={"command": "/omniaudit", "text": "status"}
                )

        assert response.status_code == 400
        data = response.json()
        assert "Missing required headers" in data["detail"]
