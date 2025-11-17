"""
Export API Routes

Endpoints for exporting audit results in various formats.
"""

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, Any
import csv
import io
import json

from ..utils.logger import get_logger
import re

logger = get_logger(__name__)


def sanitize_csv_value(value: Any) -> str:
    """
    Sanitize CSV values to prevent formula injection.

    CSV injection occurs when cells start with =, +, -, @, or tab
    which can be interpreted as formulas by spreadsheet applications.
    """
    if value is None:
        return ""

    str_value = str(value)

    # Check if value starts with dangerous characters
    if str_value and str_value[0] in ('=', '+', '-', '@', '\t', '\r'):
        # Prefix with single quote to treat as literal text
        return "'" + str_value

    return str_value


def sanitize_markdown_text(text: Any) -> str:
    """
    Sanitize text for Markdown to prevent injection.

    Escapes special Markdown characters that could be used for injection.
    """
    if text is None:
        return ""

    str_text = str(text)

    # Escape special markdown characters
    # Escape: \ ` * _ { } [ ] ( ) # + - . !
    special_chars = ['\\', '`', '*', '_', '{', '}', '[', ']', '(', ')', '#', '+', '-', '.', '!', '<', '>']
    for char in special_chars:
        str_text = str_text.replace(char, '\\' + char)

    return str_text

router = APIRouter(
    prefix="/api/v1/export",
    tags=["Export"]
)


class ExportRequest(BaseModel):
    """Request model for export."""
    data: Dict[str, Any] = Field(
        ...,
        description="Audit data to export"
    )
    format: str = Field(
        default="csv",
        description="Export format",
        pattern="^(csv|json|markdown)$"  # Only allow these formats
    )


def generate_csv(data: Dict[str, Any]) -> str:
    """
    Generate CSV from audit data with formula injection protection.

    All user-controlled values are sanitized to prevent CSV injection.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header (static values, safe)
    writer.writerow(["Category", "Metric", "Value"])

    # Write summary metrics
    collectors = data.get("collectors", {})
    analyzers = data.get("analyzers", {})

    writer.writerow(["Summary", "Total Collectors", str(len(collectors))])
    writer.writerow(["Summary", "Total Analyzers", str(len(analyzers))])

    # Write Git metrics
    if "git_collector" in collectors:
        git_data = collectors["git_collector"].get("data", {})
        writer.writerow(["Git", "Total Commits", str(git_data.get("commits_count", 0))])
        writer.writerow(["Git", "Contributors", str(git_data.get("contributors_count", 0))])
        writer.writerow(["Git", "Branches", str(len(git_data.get("branches", [])))])

        # Top contributors (sanitize user-controlled names)
        for contributor in git_data.get("contributors", [])[:5]:
            writer.writerow([
                "Contributors",
                sanitize_csv_value(contributor.get("name", "Unknown")),
                sanitize_csv_value(f"{contributor.get('commits', 0)} commits")
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
            # Sanitize language name (user-controlled)
            writer.writerow([
                "Language",
                sanitize_csv_value(lang),
                f"{metrics.get('loc', 0)} LOC"
            ])

    return output.getvalue()


def generate_markdown_report(data: Dict[str, Any]) -> str:
    """
    Generate Markdown report from audit data with injection protection.

    All user-controlled values are sanitized to prevent Markdown injection.
    """
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

        # Top contributors (sanitize user-controlled names)
        contributors = git_data.get("contributors", [])
        if contributors:
            lines.append("### Top Contributors")
            lines.append("")
            for c in contributors[:5]:
                safe_name = sanitize_markdown_text(c.get('name', 'Unknown'))
                lines.append(f"- **{safe_name}**: {c.get('commits', 0)} commits")
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
                # Sanitize language name (user-controlled)
                safe_lang = sanitize_markdown_text(lang)
                lines.append(f"- **{safe_lang}**: {lang_metrics.get('loc', 0)} lines")
            lines.append("")

    return "\n".join(lines)


@router.post("/csv")
async def export_csv(request: ExportRequest):
    """
    Export audit results as CSV.

    Returns a downloadable CSV file.
    """
    try:
        # Validate data exists
        if not request.data:
            raise HTTPException(
                status_code=400,
                detail="No data provided for export"
            )

        csv_content = generate_csv(request.data)

        # Check size limit (prevent DoS)
        if len(csv_content) > 10_000_000:  # 10MB limit
            raise HTTPException(
                status_code=413,
                detail="Export data too large. Please reduce the amount of data."
            )

        return Response(
            content=csv_content,
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": "attachment; filename=audit_report.csv",
                "Content-Length": str(len(csv_content))
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CSV export failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Export generation failed. Please check your data format."
        )


@router.post("/markdown")
async def export_markdown(request: ExportRequest):
    """
    Export audit results as Markdown.

    Returns a downloadable Markdown file.
    """
    try:
        if not request.data:
            raise HTTPException(
                status_code=400,
                detail="No data provided for export"
            )

        md_content = generate_markdown_report(request.data)

        if len(md_content) > 10_000_000:  # 10MB limit
            raise HTTPException(
                status_code=413,
                detail="Export data too large"
            )

        return Response(
            content=md_content,
            media_type="text/markdown; charset=utf-8",
            headers={
                "Content-Disposition": "attachment; filename=audit_report.md",
                "Content-Length": str(len(md_content))
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Markdown export failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Export generation failed"
        )


@router.post("/json")
async def export_json(request: ExportRequest):
    """
    Export audit results as pretty-printed JSON.

    Returns a downloadable JSON file.
    """
    try:
        if not request.data:
            raise HTTPException(
                status_code=400,
                detail="No data provided for export"
            )

        json_content = json.dumps(request.data, indent=2, ensure_ascii=False)

        if len(json_content) > 10_000_000:  # 10MB limit
            raise HTTPException(
                status_code=413,
                detail="Export data too large"
            )

        return Response(
            content=json_content,
            media_type="application/json; charset=utf-8",
            headers={
                "Content-Disposition": "attachment; filename=audit_report.json",
                "Content-Length": str(len(json_content))
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"JSON export failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Export generation failed"
        )


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
