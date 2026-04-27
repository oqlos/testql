"""MCP (Model Context Protocol) server for TestQL.

This module provides MCP server integration for TestQL, enabling:
- IDE integration (Windsurf, VS Code, JetBrains)
- AI agent tool calling
- Real-time test discovery and execution

Usage:
    # Start MCP server
    python -m testql.mcp.server

    # Or use programmatically
    from testql.mcp import create_server
    server = create_server()
    server.run()
"""

from __future__ import annotations

try:
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

from testql.mcp.server import TestQLMCPServer, create_server, run_server

__all__ = [
    "TestQLMCPServer",
    "create_server",
    "run_server",
    "MCP_AVAILABLE",
]
