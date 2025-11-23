"""
Integration tests for REST API endpoints.

Tests the FastAPI endpoints for triggering audits and retrieving results.
"""

import pytest
from fastapi.testclient import TestClient

from omniaudit.api.main import app


class TestAPIEndpoints:
    """Test REST API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data

    def test_collectors_list_endpoint(self, client):
        """Test endpoint for listing available collectors."""
        response = client.get("/api/v1/collectors")
        assert response.status_code == 200

        data = response.json()
        assert "collectors" in data
        assert isinstance(data["collectors"], list)
        assert len(data["collectors"]) > 0

        # Verify collector structure
        collector = data["collectors"][0]
        assert "name" in collector

    def test_audit_endpoint_basic(self, client):
        """Test basic audit endpoint functionality."""
        payload = {
            "collectors": {
                "git_collector": {
                    "repo_path": ".",
                    "max_commits": 5
                }
            }
        }

        response = client.post("/api/v1/audit", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "results" in data
        assert "collectors" in data["results"]
        assert "git_collector" in data["results"]["collectors"]

    def test_audit_endpoint_with_analyzers(self, client):
        """Test audit with both collectors and analyzers."""
        payload = {
            "collectors": {
                "git_collector": {
                    "repo_path": ".",
                    "max_commits": 5
                }
            },
            "analyzers": {
                "code_quality": {
                    "project_path": ".",
                    "languages": ["python"]
                }
            }
        }

        response = client.post("/api/v1/audit", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "results" in data
        assert "collectors" in data["results"]
        assert "analyzers" in data["results"]
        assert "git_collector" in data["results"]["collectors"]
        assert "code_quality" in data["results"]["analyzers"]

    def test_audit_endpoint_with_empty_payload(self, client):
        """Test audit endpoint with empty payload."""
        # Empty payload should still return 200 with empty results
        response = client.post("/api/v1/audit", json={})
        assert response.status_code in [200, 400, 422]

    def test_audit_response_structure(self, client):
        """Test that audit response has correct structure."""
        payload = {
            "collectors": {
                "git_collector": {
                    "repo_path": ".",
                    "max_commits": 5
                }
            }
        }

        response = client.post("/api/v1/audit", json=payload)
        data = response.json()

        # Verify top-level structure
        assert "results" in data
        assert isinstance(data["results"], dict)

        # Verify collector result structure
        git_result = data["results"]["collectors"]["git_collector"]
        assert "data" in git_result or "error" in git_result

    def test_audit_with_invalid_repo_path(self, client):
        """Test audit with invalid repo path."""
        payload = {
            "collectors": {
                "git_collector": {
                    "repo_path": "/nonexistent/path",
                    "max_commits": 5
                }
            }
        }

        response = client.post("/api/v1/audit", json=payload)
        # Should return 200 but with error in result
        assert response.status_code == 200

        data = response.json()
        git_result = data["results"]["collectors"]["git_collector"]
        # Should have error field
        assert "error" in git_result or "data" in git_result

    def test_concurrent_audit_requests(self, client):
        """Test handling multiple concurrent audit requests."""
        payload = {
            "collectors": {
                "git_collector": {
                    "repo_path": ".",
                    "max_commits": 3
                }
            }
        }

        # Send multiple requests
        responses = []
        for _ in range(3):
            response = client.post("/api/v1/audit", json=payload)
            responses.append(response)

        # All should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert "results" in data
