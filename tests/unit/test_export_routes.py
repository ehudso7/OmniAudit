"""
Unit tests for export routes.
"""

import pytest
from httpx import AsyncClient

from omniaudit.api.main import app


@pytest.mark.asyncio
class TestExportRoutes:
    """Test export API routes."""

    @pytest.fixture
    def sample_audit_data(self):
        """Sample audit data for export."""
        return {
            "collectors": {
                "git_collector": {
                    "status": "success",
                    "data": {
                        "commits_count": 50,
                        "contributors_count": 3,
                        "branches": [],
                        "contributors": [
                            {"name": "Alice", "commits": 30},
                            {"name": "Bob", "commits": 20}
                        ]
                    }
                }
            },
            "analyzers": {
                "code_quality": {
                    "status": "success",
                    "data": {
                        "overall_score": 85.5,
                        "metrics": {
                            "python": {"loc": 1000, "files": 10}
                        }
                    }
                }
            }
        }

    async def test_export_formats_list(self):
        """Test listing export formats."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/export/formats")

        assert response.status_code == 200
        data = response.json()
        assert "formats" in data
        assert len(data["formats"]) >= 3

        format_names = [f["format"] for f in data["formats"]]
        assert "csv" in format_names
        assert "markdown" in format_names
        assert "json" in format_names

    async def test_export_csv(self, sample_audit_data):
        """Test CSV export."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/export/csv",
                json={"data": sample_audit_data}
            )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]

        content = response.text
        assert "Category,Metric,Value" in content
        assert "Git" in content
        assert "50" in content  # commits_count

    async def test_export_markdown(self, sample_audit_data):
        """Test Markdown export."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/export/markdown",
                json={"data": sample_audit_data}
            )

        assert response.status_code == 200
        assert "markdown" in response.headers["content-type"]
        assert "attachment" in response.headers["content-disposition"]

        content = response.text
        assert "# Audit Report" in content
        assert "## Summary" in content
        assert "Alice" in content

    async def test_export_json(self, sample_audit_data):
        """Test JSON export."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/export/json",
                json={"data": sample_audit_data}
            )

        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
        assert "attachment" in response.headers["content-disposition"]

        # Should be valid JSON
        data = response.json()
        assert "collectors" in data
        assert "analyzers" in data

    async def test_export_empty_data(self):
        """Test export with empty data."""
        empty_data = {"collectors": {}, "analyzers": {}}

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/export/csv",
                json={"data": empty_data}
            )

        assert response.status_code == 200
        content = response.text
        assert "Category,Metric,Value" in content
