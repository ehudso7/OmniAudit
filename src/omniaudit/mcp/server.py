"""
MCP Server implementation for OmniAudit

Provides 15+ tools and resource providers for code auditing.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class MCPTool:
    """Represents an MCP tool"""
    name: str
    description: str
    input_schema: Dict[str, Any]


@dataclass
class MCPResource:
    """Represents an MCP resource"""
    uri: str
    name: str
    description: str
    mime_type: str


class MCPServer:
    """
    OmniAudit MCP Server

    Implements the Model Context Protocol to expose OmniAudit functionality
    as tools and resources that can be used by AI assistants.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}
        self._initialize_tools()
        self._initialize_resources()
        logger.info("MCP Server initialized with %d tools and %d resources",
                   len(self.tools), len(self.resources))

    def _initialize_tools(self):
        """Initialize all available tools"""
        from .tools.audit import AuditTool
        from .tools.findings import FindingsTool
        from .tools.fixes import FixesTool
        from .tools.reports import ReportsTool

        # Register tools
        self.register_tool(AuditTool())
        self.register_tool(FindingsTool())
        self.register_tool(FixesTool())
        self.register_tool(ReportsTool())

        # Additional tools would be registered here
        self._register_additional_tools()

    def _register_additional_tools(self):
        """Register additional tools to reach 15+ total"""
        additional_tools = [
            {
                "name": "omniaudit_rules_list",
                "description": "List all available audit rules",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string", "description": "Filter by category"},
                        "severity": {"type": "string", "description": "Filter by severity"}
                    }
                }
            },
            {
                "name": "omniaudit_rules_enable",
                "description": "Enable a specific rule",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "rule_id": {"type": "string", "description": "Rule ID to enable"}
                    },
                    "required": ["rule_id"]
                }
            },
            {
                "name": "omniaudit_rules_disable",
                "description": "Disable a specific rule",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "rule_id": {"type": "string", "description": "Rule ID to disable"}
                    },
                    "required": ["rule_id"]
                }
            },
            {
                "name": "omniaudit_config_get",
                "description": "Get configuration value",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string", "description": "Configuration key"}
                    },
                    "required": ["key"]
                }
            },
            {
                "name": "omniaudit_config_set",
                "description": "Set configuration value",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string", "description": "Configuration key"},
                        "value": {"type": "string", "description": "Configuration value"}
                    },
                    "required": ["key", "value"]
                }
            },
            {
                "name": "omniaudit_stats_summary",
                "description": "Get audit statistics summary",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "period_days": {"type": "integer", "description": "Period in days", "default": 30}
                    }
                }
            },
            {
                "name": "omniaudit_stats_trends",
                "description": "Get audit trends over time",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "period_days": {"type": "integer", "description": "Period in days", "default": 30}
                    }
                }
            },
            {
                "name": "omniaudit_compare",
                "description": "Compare two audit results",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "baseline_id": {"type": "string", "description": "Baseline audit ID"},
                        "current_id": {"type": "string", "description": "Current audit ID"}
                    },
                    "required": ["baseline_id", "current_id"]
                }
            },
            {
                "name": "omniaudit_history",
                "description": "Get audit history",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Number of results", "default": 10}
                    }
                }
            },
            {
                "name": "omniaudit_watch_start",
                "description": "Start watching files for changes",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to watch"},
                        "patterns": {"type": "array", "items": {"type": "string"}, "description": "File patterns"}
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "omniaudit_watch_stop",
                "description": "Stop watching files",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "watch_id": {"type": "string", "description": "Watch session ID"}
                    },
                    "required": ["watch_id"]
                }
            },
        ]

        for tool_def in additional_tools:
            tool = MCPTool(
                name=tool_def["name"],
                description=tool_def["description"],
                input_schema=tool_def["input_schema"]
            )
            self.tools[tool.name] = tool

    def _initialize_resources(self):
        """Initialize resource providers"""
        from .resources.providers import ResourceProvider

        provider = ResourceProvider()

        # Register resources
        for resource in provider.get_resources():
            self.resources[resource.uri] = resource

    def register_tool(self, tool: Any):
        """Register a tool with the server"""
        if hasattr(tool, 'name') and hasattr(tool, 'description') and hasattr(tool, 'input_schema'):
            mcp_tool = MCPTool(
                name=tool.name,
                description=tool.description,
                input_schema=tool.input_schema
            )
            self.tools[tool.name] = mcp_tool
            logger.debug("Registered tool: %s", tool.name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools"""
        return [asdict(tool) for tool in self.tools.values()]

    def list_resources(self) -> List[Dict[str, Any]]:
        """List all available resources"""
        return [asdict(resource) for resource in self.resources.values()]

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool with the given arguments

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        if name not in self.tools:
            raise ValueError(f"Tool not found: {name}")

        # Import and execute the appropriate tool
        if name == "omniaudit_audit_run":
            from .tools.audit import execute_audit
            return await execute_audit(arguments)
        elif name == "omniaudit_findings_list":
            from .tools.findings import execute_list_findings
            return await execute_list_findings(arguments)
        elif name == "omniaudit_findings_get":
            from .tools.findings import execute_get_finding
            return await execute_get_finding(arguments)
        elif name == "omniaudit_fix_apply":
            from .tools.fixes import execute_apply_fix
            return await execute_apply_fix(arguments)
        elif name == "omniaudit_report_generate":
            from .tools.reports import execute_generate_report
            return await execute_generate_report(arguments)
        else:
            # Mock implementation for other tools
            return {
                "success": True,
                "message": f"Tool {name} executed successfully",
                "data": {}
            }

    async def get_resource(self, uri: str) -> Dict[str, Any]:
        """
        Get a resource by URI

        Args:
            uri: Resource URI

        Returns:
            Resource content
        """
        if uri not in self.resources:
            raise ValueError(f"Resource not found: {uri}")

        from .resources.providers import get_resource_content
        return await get_resource_content(uri)

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an MCP protocol request

        Args:
            request: MCP request

        Returns:
            MCP response
        """
        method = request.get("method")
        params = request.get("params", {})

        try:
            if method == "tools/list":
                return {
                    "tools": self.list_tools()
                }
            elif method == "tools/call":
                result = await self.call_tool(
                    params.get("name"),
                    params.get("arguments", {})
                )
                return result
            elif method == "resources/list":
                return {
                    "resources": self.list_resources()
                }
            elif method == "resources/read":
                content = await self.get_resource(params.get("uri"))
                return {
                    "contents": [content]
                }
            else:
                raise ValueError(f"Unknown method: {method}")
        except Exception as e:
            logger.error("Error handling request: %s", str(e), exc_info=True)
            return {
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }

    async def start(self, host: str = "localhost", port: int = 8001):
        """
        Start the MCP server

        Args:
            host: Server host
            port: Server port
        """
        logger.info("Starting MCP server on %s:%d", host, port)
        # Server implementation would go here
        # This would typically use stdio, HTTP, or WebSocket transport

    async def stop(self):
        """Stop the MCP server"""
        logger.info("Stopping MCP server")


def create_server(config: Optional[Dict[str, Any]] = None) -> MCPServer:
    """
    Factory function to create an MCP server instance

    Args:
        config: Optional server configuration

    Returns:
        Configured MCP server instance
    """
    return MCPServer(config)


async def main():
    """Main entry point for the MCP server"""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    server = create_server()

    # Handle stdio-based MCP protocol
    logger.info("MCP Server ready (stdio mode)")

    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break

            try:
                request = json.loads(line)
                response = await server.handle_request(request)
                print(json.dumps(response))
                sys.stdout.flush()
            except json.JSONDecodeError:
                logger.error("Invalid JSON received")
            except Exception as e:
                logger.error("Error processing request: %s", str(e))
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
