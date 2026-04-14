import asyncio
import concurrent.futures
import json

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

SERVER_PARAMS = StdioServerParameters(
    command="weather-server",
    args=[],
)


async def _get_tools_async() -> list[dict]:
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            return [_to_litellm_tool(t) for t in tools.tools]


async def _call_tool_async(name: str, arguments: dict) -> str:
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(name, arguments)
            return str(result.content[0].text if result.content else "")


def _run_in_thread(coro):
    """Run async coroutine in a fresh thread with its own event loop.

    This avoids conflicts with Streamlit's internal event loop.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(asyncio.run, coro)
        return future.result()


def get_tools() -> list[dict]:
    return _run_in_thread(_get_tools_async())


def call_tool(name: str, arguments: dict) -> str:
    return _run_in_thread(_call_tool_async(name, arguments))


def _to_litellm_tool(mcp_tool) -> dict:
    return {
        "type": "function",
        "function": {
            "name": mcp_tool.name,
            "description": mcp_tool.description or "",
            "parameters": mcp_tool.inputSchema,
        },
    }
