# OmniAudit MCP Server

Model Context Protocol (MCP) server implementation for OmniAudit with 15+ tools and resource providers.

## Overview

The OmniAudit MCP server exposes OmniAudit functionality as tools and resources that can be used by AI assistants like Claude. This enables AI-powered code auditing workflows directly within AI conversations.

## Features

- **15+ Tools**: Comprehensive set of audit, findings, fixes, reports, and configuration tools
- **8+ Resources**: Dynamic resource providers for rules, config, findings, stats, and more
- **Real-time Progress**: Streaming progress updates during audits
- **Type-safe**: Full type hints and validation
- **Async**: Built on asyncio for high performance

## Installation

```bash
pip install omniaudit
```

## Usage

### Starting the Server

```bash
# Start MCP server in stdio mode
python -m omniaudit.mcp.server

# Or use the convenience command
omniaudit-mcp
```

### Configuration

Configure the server using environment variables or a config file:

```bash
export OMNIAUDIT_API_URL=http://localhost:8000
export OMNIAUDIT_API_KEY=your-api-key
```

## Available Tools

### Audit Tools

1. **omniaudit_audit_run**
   - Run a comprehensive code audit
   - Args: `path`, `rules`, `severity`, `format`, `fix`
   - Returns: Audit results with findings

### Findings Tools

2. **omniaudit_findings_list**
   - List and filter audit findings
   - Args: `audit_id`, `severity`, `category`, `file`, `limit`
   - Returns: Filtered list of findings

3. **omniaudit_findings_get**
   - Get detailed information about a specific finding
   - Args: `id`
   - Returns: Finding details with code snippet and recommendations

### Fix Tools

4. **omniaudit_fix_apply**
   - Apply automatic fixes to findings
   - Args: `finding_ids`, `rule_id`, `severity`, `dry_run`
   - Returns: Fix results with diffs

### Report Tools

5. **omniaudit_report_generate**
   - Generate audit reports in various formats
   - Args: `audit_id`, `format`, `output_file`, `include_metadata`, `pretty`
   - Returns: Generated report or file path

### Rules Tools

6. **omniaudit_rules_list** - List all available audit rules
7. **omniaudit_rules_enable** - Enable a specific rule
8. **omniaudit_rules_disable** - Disable a specific rule

### Configuration Tools

9. **omniaudit_config_get** - Get configuration value
10. **omniaudit_config_set** - Set configuration value

### Statistics Tools

11. **omniaudit_stats_summary** - Get audit statistics summary
12. **omniaudit_stats_trends** - Get audit trends over time

### Analysis Tools

13. **omniaudit_compare** - Compare two audit results
14. **omniaudit_history** - Get audit history

### Watch Tools

15. **omniaudit_watch_start** - Start watching files for changes
16. **omniaudit_watch_stop** - Stop watching files

## Available Resources

Resources provide dynamic data that can be queried by AI assistants:

1. **omniaudit://rules** - List of all available audit rules
2. **omniaudit://config** - Current OmniAudit configuration
3. **omniaudit://findings/latest** - Most recent audit findings
4. **omniaudit://stats** - Audit statistics and metrics
5. **omniaudit://history** - Historical audit results
6. **omniaudit://integrations** - Available integrations and their status
7. **omniaudit://plugins** - Installed plugins and extensions
8. **omniaudit://reports/formats** - Supported report output formats

## Example Usage with Claude

### Example 1: Run an Audit

```
User: Can you audit my TypeScript project?

Claude: I'll use the OmniAudit tool to audit your project.
[Uses omniaudit_audit_run tool with path="./"]

Results: Found 15 issues - 2 critical, 5 high, 8 medium
```

### Example 2: Get Findings

```
User: Show me all critical security issues

Claude: I'll get the critical security findings.
[Uses omniaudit_findings_list with severity=["critical"], category=["security"]]

Results: 2 critical security issues found:
1. Dangerous use of eval() in src/utils.ts:42
2. SQL injection vulnerability in src/db.ts:78
```

### Example 3: Auto-fix Issues

```
User: Can you fix the medium severity issues?

Claude: I'll apply auto-fixes to the medium severity issues.
[Uses omniaudit_fix_apply with severity=["medium"], dry_run=false]

Results: Fixed 8 out of 8 medium severity issues
```

### Example 4: Generate Report

```
User: Generate an HTML report of the last audit

Claude: I'll generate an HTML report.
[Uses omniaudit_report_generate with format="html", output_file="report.html"]

Results: Report saved to report.html
```

## MCP Protocol

The server implements the Model Context Protocol specification:

### Request Format

```json
{
  "method": "tools/call",
  "params": {
    "name": "omniaudit_audit_run",
    "arguments": {
      "path": "./src",
      "severity": ["critical", "high"]
    }
  }
}
```

### Response Format

```json
{
  "success": true,
  "audit_id": "audit-12345",
  "total_findings": 7,
  "findings_by_severity": {
    "critical": 2,
    "high": 5
  },
  "findings": [...]
}
```

## Development

### Adding New Tools

```python
class MyCustomTool:
    name = "omniaudit_custom_tool"
    description = "My custom tool"
    input_schema = {
        "type": "object",
        "properties": {
            "param": {"type": "string"}
        }
    }

async def execute_custom_tool(arguments):
    # Implementation
    return {"success": True}

# Register in server.py
server.register_tool(MyCustomTool())
```

### Adding New Resources

```python
resource = MCPResource(
    uri="omniaudit://custom",
    name="Custom Resource",
    description="My custom resource",
    mime_type="application/json"
)

# Register in providers.py
provider.resources.append(resource)
```

## License

MIT
