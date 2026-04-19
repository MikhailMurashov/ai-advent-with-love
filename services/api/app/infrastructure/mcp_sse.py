from __future__ import annotations

import logging

from fastmcp import Client

from app.interfaces.mcp import ToolSchema

logger = logging.getLogger(__name__)


class FastMCPTransport:
    """FastMCP HTTP transport (MCP Streamable HTTP at /mcp/)."""

    def __init__(self, url: str) -> None:
        base = url.rstrip("/")
        self._mcp_url = base if base.endswith("/mcp") else f"{base}/mcp"

    async def list_tools(self) -> list[ToolSchema]:
        logger.info(f"Fetching tools from {self._mcp_url}")
        async with Client(self._mcp_url) as client:
            tools = await client.list_tools()
        return [
            ToolSchema(
                name=t.name,
                description=t.description or "",
                parameters=t.inputSchema or {},
            )
            for t in tools
        ]

    async def call_tool(self, name: str, args: dict) -> str:
        async with Client(self._mcp_url) as client:
            result = await client.call_tool_mcp(name, args)
        parts = [
            item.text
            for item in (result.content or [])
            if hasattr(item, "text") and item.text
        ]
        return "\n".join(parts) if parts else str(result)
