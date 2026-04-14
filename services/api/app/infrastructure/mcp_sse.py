from __future__ import annotations

import logging

import httpx

from app.interfaces.mcp import ToolSchema

logger = logging.getLogger(__name__)


class SSETransport:
    """HTTP/SSE transport for MCP servers."""

    def __init__(self, url: str) -> None:
        # url points to the SSE endpoint, e.g. http://mcp-weather:8001/sse
        self._base_url = url.rstrip("/")

    async def list_tools(self) -> list[ToolSchema]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{self._base_url}/tools")
            resp.raise_for_status()
            data = resp.json()
        tools = []
        for item in data.get("tools", data if isinstance(data, list) else []):
            tools.append(
                ToolSchema(
                    name=item["name"],
                    description=item.get("description", ""),
                    parameters=item.get("inputSchema", item.get("parameters", {})),
                )
            )
        return tools

    async def call_tool(self, name: str, args: dict) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self._base_url}/call",
                json={"name": name, "arguments": args},
            )
            resp.raise_for_status()
            data = resp.json()
        # MCP response: {"content": [{"type": "text", "text": "..."}]}
        content = data.get("content", [])
        if content and isinstance(content, list):
            return content[0].get("text", str(data))
        return str(data)
