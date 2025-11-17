"""
Export API Routes

Endpoints for exporting audit results in various formats.
"""

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any
import csv
import io
import json

from ..utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/export",
    tags=["Export"]
)


class ExportRequest(BaseModel):
    """Request model for export."""
    data: Dict[str, Any]
    format: str = "csv"  # csv, json, markdown


def generate_csv(data: Dict[str, Any]) -> str:
    """Generate CSV from audit data."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(["Category", "Metric", "Value"])

    # Write summary metrics
    collectors = data.get("collectors", {})
    analyzers = data.get("analyzers", {})

    writer.writerow(["Summary", "Total Collectors", len(collectors)])
    writer.writerow(["Summary", "Total Analyzers", len(analyzers)])

    # Write Git metrics
    if "git_collector" in collectors:
        git_data = collectors["git_collector"].get("data", {})
        writer.writerow(["Git", "Total Commits", git_data.get("commits_count", 0)])
        writer.writerow(["Git", "Contributors", git_data.get("contributors_count", 0)])
        writer.writerow(["Git", "Branches", len(git_data.get("branches", []))])

        # Top contributors
        for contributor in git_data.get("contributors", [])[:5]:
            writer.writerow([
                "Contributors",
                contributor.get("name"),
                f"{contributor.get('commits', 0)} commits"
            ])

    # Write code quality metrics
    if "code_quality" in analyzers:
        quality_data = analyzers["code_quality"].get("data", {})
        writer.writerow([
            "Quality",
            "Overall Score",
            f"{quality_data.get('overall_score', 0):.2f}"
        ])

        for lang, metrics in quality_data.get("metrics", {}).items():
            writer.writerow(["Language", lang, f"{metrics.get('loc', 0)} LOC"])

    return output.getvalue()


def generate_markdown_report(data: Dict[str, Any]) -> str:
    """Generate Markdown report from audit data."""
    lines = ["# Audit Report", ""]

    # Summary
    lines.append("## Summary")
    lines.append("")
    collectors = data.get("collectors", {})
    analyzers = data.get("analyzers", {})
    lines.append(f"- Collectors: {len(collectors)}")
    lines.append(f"- Analyzers: {len(analyzers)}")
    lines.append("")

    # Git data
    if "git_collector" in collectors:
        git_data = collectors["git_collector"].get("data", {})
        lines.append("## Git Repository")
        lines.append("")
        lines.append(f"- Commits: {git_data.get('commits_count', 0)}")
        lines.append(f"- Contributors: {git_data.get('contributors_count', 0)}")
        lines.append(f"- Branches: {len(git_data.get('branches', []))}")
        lines.append("")

        # Top contributors
        contributors = git_data.get("contributors", [])
        if contributors:
            lines.append("### Top Contributors")
            lines.append("")
            for c in contributors[:5]:
                lines.append(f"- **{c.get('name')}**: {c.get('commits', 0)} commits")
            lines.append("")

    # Code quality
    if "code_quality" in analyzers:
        quality_data = analyzers["code_quality"].get("data", {})
        lines.append("## Code Quality")
        lines.append("")
        lines.append(f"**Overall Score:** {quality_data.get('overall_score', 0):.2f}/100")
        lines.append("")

        metrics = quality_data.get("metrics", {})
        if metrics:
            lines.append("### Language Breakdown")
            lines.append("")
            for lang, lang_metrics in metrics.items():
                lines.append(f"- **{lang}**: {lang_metrics.get('loc', 0)} lines")
            lines.append("")

    return "\n".join(lines)


@router.post("/csv")
async def export_csv(request: ExportRequest):
    """
    Export audit results as CSV.

    Returns a downloadable CSV file.
    """
    try:
        csv_content = generate_csv(request.data)

        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=audit_report.csv"
            }
        )

    except Exception as e:
        logger.error(f"CSV export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/markdown")
async def export_markdown(request: ExportRequest):
    """
    Export audit results as Markdown.

    Returns a downloadable Markdown file.
    """
    try:
        md_content = generate_markdown_report(request.data)

        return Response(
            content=md_content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": "attachment; filename=audit_report.md"
            }
        )

    except Exception as e:
        logger.error(f"Markdown export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/json")
async def export_json(request: ExportRequest):
    """
    Export audit results as pretty-printed JSON.

    Returns a downloadable JSON file.
    """
    try:
        json_content = json.dumps(request.data, indent=2, ensure_ascii=False)

        return Response(
            content=json_content,
            media_type="application/json",
            headers={
                "Content-Disposition": "attachment; filename=audit_report.json"
            }
        )

    except Exception as e:
        logger.error(f"JSON export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/formats")
async def list_export_formats():
    """
    List available export formats.
    """
    return {
        "formats": [
            {
                "name": "CSV",
                "format": "csv",
                "endpoint": "/api/v1/export/csv",
                "media_type": "text/csv"
            },
            {
                "name": "Markdown",
                "format": "markdown",
                "endpoint": "/api/v1/export/markdown",
                "media_type": "text/markdown"
            },
            {
                "name": "JSON",
                "format": "json",
                "endpoint": "/api/v1/export/json",
                "media_type": "application/json"
            }
        ]
    }
