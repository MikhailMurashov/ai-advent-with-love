"""MCP Time server with HTTP transport (tools/call endpoints)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx
from fastmcp import FastMCP, Context
from pydantic import Field
from starlette.responses import JSONResponse

mcp = FastMCP(name="MCP Time Server")


@dataclass
class DateTimeInfo:
    date: str
    time: str
    weekday: str
    timezone: str
    utc_offset: str
    iso_format: str


def _format_utc_offset(dt: datetime) -> str:
    utc_offset = dt.strftime("%z")
    if len(utc_offset) == 5:
        return utc_offset[:3] + ":" + utc_offset[3:]
    return utc_offset


@mcp.tool(
    description="Текущее время по IANA-часовому поясу",
    annotations={"readOnlyHint": True, "openWorldHint": False},
)
async def get_current_timezone_datetime(
    ctx: Context,
    timezone: Annotated[str, Field(description='IANA timezone, например "Europe/Moscow"')] = "UTC",
) -> DateTimeInfo:
    await ctx.info(f"get_current_timezone_datetime for {timezone}")

    try:
        tz = ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        raise ValueError(f"Часовой пояс '{timezone}' не найден. Используйте IANA-имена, например: Europe/Moscow, Asia/Tokyo")

    now = datetime.now(tz)
    return DateTimeInfo(
        date=now.strftime("%Y-%m-%d"),
        time=now.strftime("%H:%M:%S"),
        weekday=now.strftime("%A"),
        timezone=timezone,
        utc_offset=_format_utc_offset(now),
        iso_format=now.isoformat(),
    )


@mcp.tool(
    description="Текущее время на сервере",
    annotations={"readOnlyHint": True, "openWorldHint": False},
)
def get_server_datetime() -> DateTimeInfo:
    now = datetime.now().astimezone()
    return DateTimeInfo(
        date=now.strftime("%Y-%m-%d"),
        time=now.strftime("%H:%M:%S"),
        weekday=now.strftime("%A"),
        timezone=now.tzname() or "Unknown",
        utc_offset=_format_utc_offset(now),
        iso_format=now.isoformat(),
    )


@mcp.tool(
    description="Текущее время по координатам (широта, долгота)",
    annotations={"readOnlyHint": True, "openWorldHint": True},
)
async def get_time_by_coords(
    lat: Annotated[float, Field(description="Широта", ge=-90, le=90)],
    lon: Annotated[float, Field(description="Долгота", ge=-180, le=180)],
    ctx: Context,
) -> DateTimeInfo:
    await ctx.info(f"get_time_by_coords for {lat} {lon}")

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            "https://timeapi.io/api/time/current/coordinate",
            params={"latitude": lat, "longitude": lon},
        )
        resp.raise_for_status()
        data = resp.json()

    iana_tz = data.get("timeZone", "Unknown")
    utc_offset_str = "?"
    if iana_tz and iana_tz != "Unknown":
        try:
            tz = ZoneInfo(iana_tz)
            now = datetime.now(tz)
            utc_offset_str = _format_utc_offset(now)
        except ZoneInfoNotFoundError:
            pass

    return DateTimeInfo(
        date=data.get("date", "?"),
        time=data.get("time", "?"),
        weekday=data.get("dayOfWeek", "?"),
        timezone=iana_tz,
        utc_offset=utc_offset_str,
        iso_format='?',
    )


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "ok", "service": "mcp-server"})
