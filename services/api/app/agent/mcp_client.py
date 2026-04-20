from __future__ import annotations

import logging

from app.interfaces.mcp import IMCPTransport, ToolSchema  # noqa: F401

logger = logging.getLogger(__name__)

# GigaChat-specific metadata for tools. MCP protocol doesn't support these fields,
# so they are maintained here in the API layer and merged at schema-build time.
_GIGACHAT_TOOL_META: dict[str, dict] = {
    "create_one_shoot_notification": {
        "few_shot_examples": [
            {
                "request": "напомни мне через 5 минут проверить почту",
                "params": {
                    "text": "Проверить почту",
                    "scheduled_at": "2026-04-20T10:05:00+03:00",
                    "channel": "webhook",
                },
            },
            {
                "request": "создай уведомление 'позвонить клиенту' на 15:30",
                "params": {
                    "text": "Позвонить клиенту",
                    "scheduled_at": "2026-04-20T15:30:00+03:00",
                    "channel": "webhook",
                },
            },
        ],
        "return_parameters": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Результат: 'ok' при успехе",
                },
            },
        },
    },
}


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

        def _build_function(t: ToolSchema) -> dict:
            fn: dict = {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            }
            # Prefer fields from MCP schema; fall back to hardcoded metadata
            meta = _GIGACHAT_TOOL_META.get(t.name, {})
            few_shot = t.few_shot_examples if t.few_shot_examples is not None else meta.get("few_shot_examples")
            return_params = t.return_parameters if t.return_parameters is not None else meta.get("return_parameters")
            if few_shot is not None:
                fn["few_shot_examples"] = few_shot
            if return_params is not None:
                fn["return_parameters"] = return_params
            return fn

        self._tools_schema = [
            {"type": "function", "function": _build_function(t)}
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
