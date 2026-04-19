from __future__ import annotations

import logging

from app.interfaces.mcp import IMCPTransport, ToolSchema

logger = logging.getLogger(__name__)


class MCPClient:
    """Facade over one or more MCP transports loaded from config."""

    def __init__(self) -> None:
        self._transports: dict[str, IMCPTransport] = {}
        self._tool_index: dict[str, IMCPTransport] = {}  # tool_name -> transport
        self._tools_schema: list[dict] = []

    def register(self, name: str, transport: IMCPTransport) -> None:
        self._transports[name] = transport

    async def _refresh_tools(self) -> None:
        self._tool_index = {}
        schemas: list[ToolSchema] = []
        for transport in self._transports.values():
            try:
                tools = await transport.list_tools()
                for t in tools:
                    self._tool_index[t.name] = transport
                    schemas.append(t)
            except Exception as e:
                logger.warning("mcp_client: failed to list tools: %s", e)

        self._tools_schema = [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in schemas
        ]
        logger.info("mcp_client: loaded %d tools", len(self._tools_schema))

    async def call_tool(self, name: str, args: dict) -> str:
        transport = self._tool_index.get(name)
        if transport is None:
            return f"[error] unknown tool: {name}"
        try:
            return await transport.call_tool(name, args)
        except Exception as e:
            logger.error("mcp_client: tool %r failed: %s", name, e)
            return f"[error] {e}"

    def get_tools_schema(self) -> list[dict]:
        return list(self._tools_schema)

    async def load_servers_from_db(self, servers: list) -> None:
        """Загружает серверы из списка MCPServerInfo (вызывается при старте)."""
        from app.infrastructure.mcp_sse import FastMCPTransport

        for s in servers:
            self.register(s.name, FastMCPTransport(url=s.url))
            logger.info("mcp_client: registered server %r at %s", s.name, s.url)
        await self._refresh_tools()

    async def register_server(self, name: str, url: str) -> None:
        """Добавляет сервер и обновляет tool index."""
        from app.infrastructure.mcp_sse import FastMCPTransport

        self.register(name, FastMCPTransport(url=url))
        await self._refresh_tools()

    async def unregister_server(self, name: str) -> None:
        """Удаляет сервер и обновляет tool index."""
        self._transports.pop(name, None)
        await self._refresh_tools()
