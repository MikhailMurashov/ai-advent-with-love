from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastmcp import FastMCP, Context
from pydantic import Field
from starlette.responses import JSONResponse

mcp = FastMCP(name="MCP Saver Server")


@mcp.tool(description="Сохраняет данные в файл")
async def save_to_file(
    filename: Annotated[str, Field(description="Имя файла с расширением")],
    data: Annotated[str, Field(description="Данные для записи")],
    ctx: Context,
):
    await ctx.info(f"save_to_file to {filename}")
    path = Path("/app/data") / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding="utf-8")


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "ok", "service": "mcp-saver"})
