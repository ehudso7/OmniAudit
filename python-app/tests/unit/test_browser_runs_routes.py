"""
Tests for Browser Verification Runs API routes.
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

# Set up SQLite before importing app
import os
os.environ["DATABASE_URL"] = "sqlite:///test_browser_runs.db"

from omniaudit.api.main import app
from omniaudit.db.base import init_db, engine, Base


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    # Clean up test db file
    try:
        os.remove("test_browser_runs.db")
    except OSError:
        pass


@pytest.fixture
def client():
    return TestClient(app)


class TestBrowserRunsRoutes:
    def test_list_browser_runs_empty(self, client):
        response = client.get("/api/v1/browser-runs")
        assert response.status_code == 200
        data = response.json()
        assert data["runs"] == []
        assert data["total"] == 0

    def test_create_browser_run(self, client):
        response = client.post("/api/v1/browser-runs", json={
            "target_url": "https://example.com",
            "environment": "preview",
            "viewport_width": 1280,
            "viewport_height": 720,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["run"]["target_url"] == "https://example.com"
        assert data["run"]["status"] == "pending"
        assert "id" in data["run"]

    def test_create_browser_run_with_journeys(self, client):
        response = client.post("/api/v1/browser-runs", json={
            "target_url": "https://example.com",
            "journeys": [
                {"name": "page_load", "steps": [{"action": "navigate", "url": "{target_url}"}]},
            ],
            "release_gate": True,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["run"]["release_gate"] is True

    def test_get_browser_run_not_found(self, client):
        response = client.get("/api/v1/browser-runs/nonexistent")
        assert response.status_code == 404

    def test_get_browser_run(self, client):
        # Create a run first
        create_resp = client.post("/api/v1/browser-runs", json={
            "target_url": "https://example.com",
        })
        run_id = create_resp.json()["run"]["id"]

        response = client.get(f"/api/v1/browser-runs/{run_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["run"]["id"] == run_id

    def test_get_browser_run_artifacts(self, client):
        create_resp = client.post("/api/v1/browser-runs", json={
            "target_url": "https://example.com",
        })
        run_id = create_resp.json()["run"]["id"]

        response = client.get(f"/api/v1/browser-runs/{run_id}/artifacts")
        assert response.status_code == 200
        data = response.json()
        assert data["run_id"] == run_id
        assert data["artifacts"] == []

    def test_rerun_browser_run(self, client):
        create_resp = client.post("/api/v1/browser-runs", json={
            "target_url": "https://example.com",
            "environment": "staging",
        })
        run_id = create_resp.json()["run"]["id"]

        response = client.post(f"/api/v1/browser-runs/{run_id}/rerun")
        assert response.status_code == 200
        data = response.json()
        assert data["run"]["target_url"] == "https://example.com"
        assert data["run"]["environment"] == "staging"
        assert data["original_run_id"] == run_id

    def test_rerun_not_found(self, client):
        response = client.post("/api/v1/browser-runs/nonexistent/rerun")
        assert response.status_code == 404

    def test_browser_run_stats(self, client):
        response = client.get("/api/v1/browser-runs/summary/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_runs" in data
        assert "avg_score" in data

    def test_list_with_filters(self, client):
        # Create runs
        client.post("/api/v1/browser-runs", json={"target_url": "https://a.com"})
        client.post("/api/v1/browser-runs", json={"target_url": "https://b.com"})

        response = client.get("/api/v1/browser-runs?limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data["runs"]) == 1
        assert data["total"] == 2


class TestReleasePolicies:
    def test_list_policies_empty(self, client):
        response = client.get("/api/v1/release-policies")
        assert response.status_code == 200
        assert response.json()["total"] == 0

    def test_create_policy_requires_repository(self, client):
        response = client.post("/api/v1/release-policies", json={
            "repository_id": "nonexistent",
            "name": "Test Policy",
        })
        assert response.status_code == 404
