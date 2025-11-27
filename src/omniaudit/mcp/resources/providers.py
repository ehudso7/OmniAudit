"""Resource providers for MCP server"""

from typing import Any, Dict, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class MCPResource:
    """Represents an MCP resource"""
    uri: str
    name: str
    description: str
    mime_type: str


class ResourceProvider:
    """Provides resources for the MCP server"""

    def __init__(self):
        self.resources: List[MCPResource] = []
        self._initialize_resources()

    def _initialize_resources(self):
        """Initialize all available resources"""
        self.resources = [
            MCPResource(
                uri="omniaudit://rules",
                name="Audit Rules",
                description="List of all available audit rules",
                mime_type="application/json"
            ),
            MCPResource(
                uri="omniaudit://config",
                name="Configuration",
                description="Current OmniAudit configuration",
                mime_type="application/yaml"
            ),
            MCPResource(
                uri="omniaudit://findings/latest",
                name="Latest Findings",
                description="Most recent audit findings",
                mime_type="application/json"
            ),
            MCPResource(
                uri="omniaudit://stats",
                name="Statistics",
                description="Audit statistics and metrics",
                mime_type="application/json"
            ),
            MCPResource(
                uri="omniaudit://history",
                name="Audit History",
                description="Historical audit results",
                mime_type="application/json"
            ),
            MCPResource(
                uri="omniaudit://integrations",
                name="Integrations",
                description="Available integrations and their status",
                mime_type="application/json"
            ),
            MCPResource(
                uri="omniaudit://plugins",
                name="Plugins",
                description="Installed plugins and extensions",
                mime_type="application/json"
            ),
            MCPResource(
                uri="omniaudit://reports/formats",
                name="Report Formats",
                description="Supported report output formats",
                mime_type="application/json"
            ),
        ]

    def get_resources(self) -> List[MCPResource]:
        """Get all available resources"""
        return self.resources


async def get_resource_content(uri: str) -> Dict[str, Any]:
    """
    Get the content of a resource by URI

    Args:
        uri: Resource URI

    Returns:
        Resource content
    """
    logger.info("Getting resource content for %s", uri)

    # Mock resource content
    resource_map = {
        "omniaudit://rules": {
            "uri": uri,
            "mimeType": "application/json",
            "text": '''{
  "rules": [
    {
      "id": "security/no-eval",
      "name": "No eval()",
      "category": "security",
      "severity": "critical",
      "enabled": true
    },
    {
      "id": "performance/no-sync-fs",
      "name": "No synchronous file system",
      "category": "performance",
      "severity": "medium",
      "enabled": true
    }
  ],
  "total": 150
}'''
        },
        "omniaudit://config": {
            "uri": uri,
            "mimeType": "application/yaml",
            "text": '''version: 2.0.0
project:
  name: my-project
  paths:
    - src/
analysis:
  parallel: true
  max_workers: 4
'''
        },
        "omniaudit://findings/latest": {
            "uri": uri,
            "mimeType": "application/json",
            "text": '''{
  "audit_id": "audit-12345",
  "total_findings": 23,
  "findings": [
    {
      "id": "1",
      "rule_id": "security/no-eval",
      "severity": "critical",
      "file": "src/utils.ts",
      "line": 42
    }
  ]
}'''
        },
        "omniaudit://stats": {
            "uri": uri,
            "mimeType": "application/json",
            "text": '''{
  "period_days": 30,
  "total_audits": 127,
  "total_findings": 2543,
  "fixed_issues": 1892,
  "open_issues": 651,
  "fix_rate": 0.744
}'''
        },
        "omniaudit://history": {
            "uri": uri,
            "mimeType": "application/json",
            "text": '''{
  "audits": [
    {
      "id": "audit-12345",
      "timestamp": "2024-11-27T00:00:00Z",
      "total_findings": 23,
      "duration_ms": 5432
    },
    {
      "id": "audit-12344",
      "timestamp": "2024-11-26T00:00:00Z",
      "total_findings": 25,
      "duration_ms": 5123
    }
  ]
}'''
        },
        "omniaudit://integrations": {
            "uri": uri,
            "mimeType": "application/json",
            "text": '''{
  "integrations": [
    {"name": "GitHub", "enabled": true, "status": "connected"},
    {"name": "GitLab", "enabled": false, "status": "not_configured"},
    {"name": "Slack", "enabled": true, "status": "connected"},
    {"name": "JIRA", "enabled": false, "status": "not_configured"}
  ]
}'''
        },
        "omniaudit://plugins": {
            "uri": uri,
            "mimeType": "application/json",
            "text": '''{
  "plugins": [
    {"name": "eslint", "version": "8.0.0", "enabled": true},
    {"name": "typescript", "version": "5.0.0", "enabled": true},
    {"name": "security-scanner", "version": "2.0.0", "enabled": true}
  ]
}'''
        },
        "omniaudit://reports/formats": {
            "uri": uri,
            "mimeType": "application/json",
            "text": '''{
  "formats": [
    "json", "sarif", "markdown", "html", "pdf",
    "junit", "checkstyle", "gitlab", "github",
    "sonarqube", "codeclimate", "csv", "slack",
    "jira", "linear", "notion"
  ]
}'''
        }
    }

    if uri in resource_map:
        return resource_map[uri]

    raise ValueError(f"Unknown resource URI: {uri}")
