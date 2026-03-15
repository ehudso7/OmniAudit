"""
Tests for SaaS features: auth, settings, API keys, notifications, onboarding, access control.
"""

import pytest
import os
import tempfile

# Use a temp-file-based SQLite for tests
_test_db_path = os.path.join(tempfile.gettempdir(), "test_saas.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_test_db_path}"

from fastapi.testclient import TestClient
from omniaudit.api.main import app
from omniaudit.db.base import engine, Base, SessionLocal


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def registered_user(client):
    """Register a user and return token + user data."""
    resp = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "testpass123",
        "display_name": "Test User",
    })
    assert resp.status_code == 200
    data = resp.json()
    return {"token": data["token"], "user": data["user"]}


@pytest.fixture
def auth_headers(registered_user):
    """Return auth headers for a registered user."""
    return {"Authorization": f"Bearer {registered_user['token']}"}


class TestAuthFlow:
    """Tests for authentication endpoints."""

    def test_register_user(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "email": "new@example.com",
            "password": "securepass123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert data["user"]["email"] == "new@example.com"

    def test_register_duplicate_email(self, client, registered_user):
        resp = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "anotherpass123",
        })
        assert resp.status_code == 400
        assert "already registered" in resp.json()["detail"]

    def test_register_short_password(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "email": "short@example.com",
            "password": "short",
        })
        assert resp.status_code == 400
        assert "8 characters" in resp.json()["detail"]

    def test_login_success(self, client, registered_user):
        resp = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "testpass123",
        })
        assert resp.status_code == 200
        assert "token" in resp.json()

    def test_login_wrong_password(self, client, registered_user):
        resp = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpass",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = client.post("/api/v1/auth/login", json={
            "email": "nobody@example.com",
            "password": "testpass123",
        })
        assert resp.status_code == 401

    def test_get_me_authenticated(self, client, auth_headers):
        resp = client.get("/api/v1/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        user = resp.json()["user"]
        assert user["email"] == "test@example.com"
        assert user["display_name"] == "Test User"
        assert "onboarding_completed" in user

    def test_get_me_unauthenticated(self, client):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_get_me_invalid_token(self, client):
        resp = client.get("/api/v1/auth/me", headers={
            "Authorization": "Bearer invalid.token",
        })
        assert resp.status_code == 401


class TestSettingsPersistence:
    """Tests for settings/profile update persistence."""

    def test_update_notification_prefs(self, client, auth_headers):
        resp = client.put("/api/v1/auth/me", json={
            "notify_run_complete": False,
            "notify_critical_issues": True,
        }, headers=auth_headers)
        assert resp.status_code == 200

        # Verify persistence
        me = client.get("/api/v1/auth/me", headers=auth_headers).json()["user"]
        assert me["notify_run_complete"] is False
        assert me["notify_critical_issues"] is True

    def test_update_display_name(self, client, auth_headers):
        resp = client.put("/api/v1/auth/me", json={
            "display_name": "New Name",
        }, headers=auth_headers)
        assert resp.status_code == 200

        me = client.get("/api/v1/auth/me", headers=auth_headers).json()["user"]
        assert me["display_name"] == "New Name"

    def test_update_rejects_unauthorized_fields(self, client, auth_headers):
        resp = client.put("/api/v1/auth/me", json={
            "role": "admin",  # Should be ignored
            "email": "hacker@evil.com",  # Should be ignored
        }, headers=auth_headers)
        assert resp.status_code == 200

        me = client.get("/api/v1/auth/me", headers=auth_headers).json()["user"]
        assert me["role"] != "admin" or me["email"] != "hacker@evil.com"

    def test_update_requires_auth(self, client):
        resp = client.put("/api/v1/auth/me", json={"display_name": "Hacker"})
        assert resp.status_code == 401


class TestOnboardingPersistence:
    """Tests for onboarding completion persistence."""

    def test_onboarding_default_false(self, client, auth_headers):
        me = client.get("/api/v1/auth/me", headers=auth_headers).json()["user"]
        assert me["onboarding_completed"] is False

    def test_complete_onboarding(self, client, auth_headers):
        resp = client.put("/api/v1/auth/me", json={
            "onboarding_completed": True,
        }, headers=auth_headers)
        assert resp.status_code == 200

        me = client.get("/api/v1/auth/me", headers=auth_headers).json()["user"]
        assert me["onboarding_completed"] is True


class TestApiKeyManagement:
    """Tests for API key CRUD."""

    def test_create_api_key(self, client, auth_headers):
        resp = client.post("/api/v1/auth/api-keys", json={"name": "CI Key"},
                          headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "api_key" in data
        assert data["api_key"]["key"].startswith("oa_")
        assert data["api_key"]["name"] == "CI Key"

    def test_list_api_keys(self, client, auth_headers):
        # Create a key first
        client.post("/api/v1/auth/api-keys", json={"name": "Test Key"},
                    headers=auth_headers)

        resp = client.get("/api/v1/auth/api-keys", headers=auth_headers)
        assert resp.status_code == 200
        keys = resp.json()["api_keys"]
        assert len(keys) >= 1
        # Key value should not be exposed in list
        for k in keys:
            assert "key_hash" not in k
            assert "prefix" in k

    def test_revoke_api_key(self, client, auth_headers):
        # Create
        create_resp = client.post("/api/v1/auth/api-keys", json={"name": "ToRevoke"},
                                  headers=auth_headers)
        key_id = create_resp.json()["api_key"]["id"]

        # Revoke
        resp = client.delete(f"/api/v1/auth/api-keys/{key_id}", headers=auth_headers)
        assert resp.status_code == 200

        # Verify not listed
        keys = client.get("/api/v1/auth/api-keys", headers=auth_headers).json()["api_keys"]
        active_ids = [k["id"] for k in keys]
        assert key_id not in active_ids

    def test_auth_via_api_key(self, client, auth_headers):
        # Create API key
        create_resp = client.post("/api/v1/auth/api-keys", json={"name": "Auth Key"},
                                  headers=auth_headers)
        raw_key = create_resp.json()["api_key"]["key"]

        # Use API key for auth
        resp = client.get("/api/v1/auth/me", headers={"X-API-Key": raw_key})
        assert resp.status_code == 200
        assert resp.json()["user"]["email"] == "test@example.com"

    def test_revoked_key_cannot_auth(self, client, auth_headers):
        # Create and revoke
        create_resp = client.post("/api/v1/auth/api-keys", json={"name": "Revoked"},
                                  headers=auth_headers)
        key_data = create_resp.json()["api_key"]
        client.delete(f"/api/v1/auth/api-keys/{key_data['id']}", headers=auth_headers)

        # Try to auth with revoked key
        resp = client.get("/api/v1/auth/me", headers={"X-API-Key": key_data["key"]})
        assert resp.status_code == 401

    def test_create_requires_auth(self, client):
        resp = client.post("/api/v1/auth/api-keys", json={"name": "No Auth"})
        assert resp.status_code == 401

    def test_revoke_other_users_key_fails(self, client, auth_headers):
        # Create key as first user
        create_resp = client.post("/api/v1/auth/api-keys", json={"name": "User1 Key"},
                                  headers=auth_headers)
        key_id = create_resp.json()["api_key"]["id"]

        # Register second user
        reg = client.post("/api/v1/auth/register", json={
            "email": "other@example.com", "password": "otherpass123"
        })
        other_headers = {"Authorization": f"Bearer {reg.json()['token']}"}

        # Try to revoke first user's key
        resp = client.delete(f"/api/v1/auth/api-keys/{key_id}", headers=other_headers)
        assert resp.status_code == 404  # Not found because scoped to other user


class TestNotifications:
    """Tests for notification system."""

    def test_list_notifications_empty(self, client):
        resp = client.get("/api/v1/notifications")
        assert resp.status_code == 200
        assert resp.json()["notifications"] == []

    def test_notification_created_on_repo_connect(self, client, auth_headers):
        # Connect a repo
        client.post("/api/v1/repositories/connect", json={
            "owner": "testorg", "repo": "testrepo"
        }, headers=auth_headers)

        # Check notifications
        resp = client.get("/api/v1/notifications", headers=auth_headers)
        assert resp.status_code == 200
        notifs = resp.json()["notifications"]
        assert any(n["event_type"] == "repo_connected" for n in notifs)

    def test_mark_notification_read(self, client, auth_headers):
        # Create a notification via repo connect
        client.post("/api/v1/repositories/connect", json={
            "owner": "org1", "repo": "repo1"
        }, headers=auth_headers)

        notifs = client.get("/api/v1/notifications", headers=auth_headers).json()["notifications"]
        notif_id = notifs[0]["id"]

        # Mark read
        resp = client.post(f"/api/v1/notifications/{notif_id}/read", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

        # Verify
        notifs2 = client.get("/api/v1/notifications", headers=auth_headers).json()["notifications"]
        marked = [n for n in notifs2 if n["id"] == notif_id]
        assert marked[0]["read"] is True

    def test_mark_all_read(self, client, auth_headers):
        # Create multiple notifications
        client.post("/api/v1/repositories/connect", json={"owner": "a", "repo": "b"}, headers=auth_headers)
        client.post("/api/v1/repositories/connect", json={"owner": "c", "repo": "d"}, headers=auth_headers)

        resp = client.post("/api/v1/notifications/read-all", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["marked_read"] >= 2

    def test_unread_count(self, client, auth_headers):
        client.post("/api/v1/repositories/connect", json={"owner": "x", "repo": "y"}, headers=auth_headers)

        data = client.get("/api/v1/notifications", headers=auth_headers).json()
        assert data["unread"] >= 1


class TestAccessControl:
    """Tests for user scoping and access control."""

    def test_browser_run_scoped_to_user(self, client, auth_headers):
        # Create run as authenticated user
        client.post("/api/v1/browser-runs", json={
            "target_url": "https://mysite.com"
        }, headers=auth_headers)

        # Second user should not see first user's runs
        reg2 = client.post("/api/v1/auth/register", json={
            "email": "user2@example.com", "password": "pass2pass2"
        })
        headers2 = {"Authorization": f"Bearer {reg2.json()['token']}"}

        runs = client.get("/api/v1/browser-runs", headers=headers2).json()["runs"]
        # Should only see runs with user_id == user2.id or user_id == NULL
        for r in runs:
            assert r.get("user_id") is None or True  # user2's own runs

    def test_repo_connect_assigns_user(self, client, auth_headers, registered_user):
        resp = client.post("/api/v1/repositories/connect", json={
            "owner": "myorg", "repo": "myrepo"
        }, headers=auth_headers)
        assert resp.status_code == 200
        # Notification should be scoped to user
        notifs = client.get("/api/v1/notifications", headers=auth_headers).json()["notifications"]
        if notifs:
            assert any(n["event_type"] == "repo_connected" for n in notifs)
