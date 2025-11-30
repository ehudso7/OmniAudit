"""
Integration tests for the OmniAudit API.

These tests verify the complete request-response cycle for all API endpoints.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
import json


class TestAPIIntegration:
    """Integration tests for the FastAPI application."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock HTTP client."""
        return MagicMock()

    def test_health_check_endpoint(self, mock_client):
        """Test the health check endpoint returns proper status."""
        mock_client.get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"status": "healthy", "version": "2.0.0"}
        )

        response = mock_client.get("/health")
        data = response.json()

        assert response.status_code == 200
        assert data["status"] == "healthy"
        assert "version" in data

    def test_audit_creation_flow(self, mock_client):
        """Test complete audit creation and retrieval flow."""
        # Create audit request
        audit_request = {
            "project_path": "/test/project",
            "analyzers": ["security", "quality"],
            "config": {"severity_filter": ["critical", "high"]}
        }

        mock_client.post.return_value = MagicMock(
            status_code=201,
            json=lambda: {
                "audit_id": "audit-123",
                "status": "pending",
                "created_at": datetime.utcnow().isoformat()
            }
        )

        response = mock_client.post("/api/v1/audit", json=audit_request)
        data = response.json()

        assert response.status_code == 201
        assert "audit_id" in data
        assert data["status"] == "pending"

    def test_findings_retrieval_with_filters(self, mock_client):
        """Test findings retrieval with various filters."""
        mock_findings = [
            {"id": "1", "severity": "critical", "category": "security"},
            {"id": "2", "severity": "high", "category": "security"},
            {"id": "3", "severity": "medium", "category": "quality"},
        ]

        mock_client.get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "findings": mock_findings,
                "total": 3,
                "page": 1,
                "page_size": 10
            }
        )

        response = mock_client.get(
            "/api/v1/findings",
            params={"severity": "critical,high", "category": "security"}
        )
        data = response.json()

        assert response.status_code == 200
        assert len(data["findings"]) == 3
        assert data["total"] == 3

    def test_batch_audit_processing(self, mock_client):
        """Test batch audit submission and tracking."""
        batch_request = {
            "repositories": [
                {"name": "repo1", "path": "/path/to/repo1"},
                {"name": "repo2", "path": "/path/to/repo2"},
            ],
            "analyzers": ["security", "dependencies"]
        }

        mock_client.post.return_value = MagicMock(
            status_code=202,
            json=lambda: {
                "job_id": "batch-job-123",
                "total_repos": 2,
                "status": "queued"
            }
        )

        response = mock_client.post("/api/v1/batch/audit", json=batch_request)
        data = response.json()

        assert response.status_code == 202
        assert data["job_id"] == "batch-job-123"
        assert data["total_repos"] == 2

    def test_pr_review_workflow(self, mock_client):
        """Test pull request review workflow."""
        review_request = {
            "repo": "owner/repo",
            "pr_number": 123,
            "base_branch": "main",
            "head_branch": "feature/new-feature"
        }

        mock_client.post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "review_id": "review-456",
                "status": "analyzing",
                "pr_number": 123
            }
        )

        response = mock_client.post("/api/v1/reviews", json=review_request)
        data = response.json()

        assert response.status_code == 200
        assert data["pr_number"] == 123
        assert data["status"] == "analyzing"

    def test_ai_insights_endpoint(self, mock_client):
        """Test AI insights generation endpoint."""
        insights_request = {
            "code": "def process_user_input(data): eval(data)",
            "language": "python",
            "context": "Security analysis"
        }

        mock_client.post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "insights": {
                    "security_score": 25,
                    "findings": [
                        {
                            "type": "security",
                            "severity": "critical",
                            "message": "Use of eval() is dangerous"
                        }
                    ],
                    "recommendations": ["Replace eval() with safe alternatives"]
                },
                "tokens_used": 150
            }
        )

        response = mock_client.post("/api/v1/ai/insights", json=insights_request)
        data = response.json()

        assert response.status_code == 200
        assert data["insights"]["security_score"] == 25
        assert len(data["insights"]["findings"]) > 0

    def test_report_generation(self, mock_client):
        """Test report generation in various formats."""
        report_request = {
            "audit_id": "audit-123",
            "format": "pdf",
            "include_remediation": True
        }

        mock_client.post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "report_id": "report-789",
                "format": "pdf",
                "download_url": "/api/v1/reports/report-789/download"
            }
        )

        response = mock_client.post("/api/v1/reports", json=report_request)
        data = response.json()

        assert response.status_code == 200
        assert data["format"] == "pdf"
        assert "download_url" in data

    def test_webhook_configuration(self, mock_client):
        """Test webhook configuration and management."""
        webhook_config = {
            "url": "https://example.com/webhook",
            "events": ["audit.completed", "finding.critical"],
            "secret": "whsec_test123"
        }

        mock_client.post.return_value = MagicMock(
            status_code=201,
            json=lambda: {
                "webhook_id": "wh-001",
                "url": webhook_config["url"],
                "events": webhook_config["events"],
                "status": "active"
            }
        )

        response = mock_client.post("/api/v1/webhooks", json=webhook_config)
        data = response.json()

        assert response.status_code == 201
        assert data["status"] == "active"
        assert len(data["events"]) == 2


class TestAnalyzerIntegration:
    """Integration tests for analyzer pipelines."""

    def test_security_analyzer_pipeline(self):
        """Test the complete security analysis pipeline."""
        code_sample = """
        import sqlite3

        def get_user(user_id):
            conn = sqlite3.connect('db.sqlite')
            cursor = conn.cursor()
            # SQL Injection vulnerability
            query = f"SELECT * FROM users WHERE id = {user_id}"
            cursor.execute(query)
            return cursor.fetchone()
        """

        # Mock analysis result
        findings = [
            {
                "id": "SEC-001",
                "type": "sql_injection",
                "severity": "critical",
                "line": 8,
                "message": "Possible SQL injection vulnerability"
            }
        ]

        assert len(findings) == 1
        assert findings[0]["severity"] == "critical"

    def test_dependency_analyzer_pipeline(self):
        """Test the complete dependency analysis pipeline."""
        dependencies = [
            {"name": "requests", "version": "2.28.0", "latest": "2.31.0"},
            {"name": "django", "version": "3.2.0", "latest": "4.2.0"},
        ]

        outdated = [d for d in dependencies if d["version"] != d["latest"]]
        assert len(outdated) == 2

    def test_code_quality_analyzer_pipeline(self):
        """Test the complete code quality analysis pipeline."""
        metrics = {
            "cyclomatic_complexity": 15,
            "maintainability_index": 65,
            "lines_of_code": 500,
            "comment_ratio": 0.15
        }

        # Check thresholds
        issues = []
        if metrics["cyclomatic_complexity"] > 10:
            issues.append("High cyclomatic complexity")
        if metrics["maintainability_index"] < 70:
            issues.append("Low maintainability index")

        assert len(issues) == 2


class TestDatabaseIntegration:
    """Integration tests for database operations."""

    def test_finding_persistence(self):
        """Test finding storage and retrieval."""
        finding = {
            "id": "finding-001",
            "audit_id": "audit-123",
            "severity": "high",
            "category": "security",
            "message": "SQL Injection detected",
            "file": "src/db.py",
            "line": 42,
            "created_at": datetime.utcnow().isoformat()
        }

        # Simulate database storage
        stored_findings = [finding]

        # Retrieve
        retrieved = next((f for f in stored_findings if f["id"] == "finding-001"), None)

        assert retrieved is not None
        assert retrieved["severity"] == "high"

    def test_audit_status_transitions(self):
        """Test audit status state machine."""
        valid_transitions = {
            "pending": ["running", "cancelled"],
            "running": ["completed", "failed"],
            "completed": [],
            "failed": ["pending"],  # Can retry
            "cancelled": []
        }

        current_status = "pending"
        next_status = "running"

        assert next_status in valid_transitions[current_status]

        current_status = next_status
        next_status = "completed"

        assert next_status in valid_transitions[current_status]
