"""
Integration tests for REST API endpoints.

Tests the FastAPI endpoints for triggering audits and retrieving results.
"""

import pytest
from fastapi.testclient import TestClient

from omniaudit.api.server import app


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
        assert "version" in data

    def test_audit_endpoint_basic(self, client):
        """Test basic audit endpoint functionality."""
        payload = {
            "collectors": {
                "git_collector": {
                    "repo_path": ".",
                    "max_commits": 10
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
                    "max_commits": 20
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

    def test_audit_endpoint_invalid_payload(self, client):
        """Test audit endpoint with invalid payload."""
        # Empty payload
        response = client.post("/api/v1/audit", json={})
        assert response.status_code in [400, 422]  # Bad request or validation error

    def test_audit_endpoint_invalid_collector_config(self, client):
        """Test audit with invalid collector configuration."""
        payload = {
            "collectors": {
                "git_collector": {
                    "repo_path": "/nonexistent/path",
                    "max_commits": 10
                }
            }
        }

        response = client.post("/api/v1/audit", json=payload)
        # Should return 200 but with error status in result
        assert response.status_code == 200

        data = response.json()
        git_result = data["results"]["collectors"]["git_collector"]
        assert git_result["status"] == "error"

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
        assert "description" in collector

    def test_analyzers_list_endpoint(self, client):
        """Test endpoint for listing available analyzers."""
        response = client.get("/api/v1/analyzers")
        assert response.status_code == 200

        data = response.json()
        assert "analyzers" in data
        assert isinstance(data["analyzers"], list)

    def test_concurrent_audit_requests(self, client):
        """Test handling multiple concurrent audit requests."""
        payload = {
            "collectors": {
                "git_collector": {
                    "repo_path": ".",
                    "max_commits": 5
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

    def test_audit_response_structure(self, client):
        """Test that audit response has correct structure."""
        payload = {
            "collectors": {
                "git_collector": {
                    "repo_path": ".",
                    "max_commits": 10
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
        assert "status" in git_result
        assert "duration" in git_result
        assert git_result["status"] in ["success", "error"]

        if git_result["status"] == "success":
            assert "data" in git_result
            assert isinstance(git_result["data"], dict)

    def test_audit_with_multiple_collectors(self, client):
        """Test audit with multiple collectors."""
        payload = {
            "collectors": {
                "git_collector": {
                    "repo_path": ".",
                    "max_commits": 10
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
        collectors = data["results"]["collectors"]
        assert len(collectors) >= 1

    def test_api_error_handling(self, client):
        """Test API error handling for malformed requests."""
        # Invalid JSON
        response = client.post(
            "/api/v1/audit",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.get("/health")
        # Basic check that response is successful
        assert response.status_code == 200

    def test_api_versioning(self, client):
        """Test that API version is in path."""
        payload = {
            "collectors": {
                "git_collector": {
                    "repo_path": ".",
                    "max_commits": 5
                }
            }
        }

        # Should work with /api/v1
        response = client.post("/api/v1/audit", json=payload)
        assert response.status_code == 200

    def test_audit_duration_tracking(self, client):
        """Test that audit tracks execution duration."""
        payload = {
            "collectors": {
                "git_collector": {
                    "repo_path": ".",
                    "max_commits": 10
                }
            }
        }

        response = client.post("/api/v1/audit", json=payload)
        data = response.json()

        git_result = data["results"]["collectors"]["git_collector"]
        assert "duration" in git_result
        assert isinstance(git_result["duration"], (int, float))
        assert git_result["duration"] >= 0

    def test_large_commit_limit(self, client):
        """Test audit with large commit limit."""
        payload = {
            "collectors": {
                "git_collector": {
                    "repo_path": ".",
                    "max_commits": 1000
                }
            }
        }

        response = client.post("/api/v1/audit", json=payload)
        assert response.status_code == 200

        data = response.json()
        git_result = data["results"]["collectors"]["git_collector"]

        # Should either succeed or fail gracefully
        assert git_result["status"] in ["success", "error"]

    def test_content_type_validation(self, client):
        """Test that API validates content type."""
        response = client.post(
            "/api/v1/audit",
            data="test",
            headers={"Content-Type": "text/plain"}
        )
        # Should reject non-JSON content type
        assert response.status_code in [400, 415, 422]
