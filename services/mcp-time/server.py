"""MCP Time server with HTTP transport (tools/call endpoints)."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx
from fastmcp import FastMCP, Context
from starlette.responses import JSONResponse

mcp = FastMCP(name="MCP Weather Server")


@mcp.tool(
    name="Текущее время в часовом поясе",
    description="Возвращает текущее время по часовому поясу строго в формате IANA"
)
async def get_current_timezone_datetime(ctx: Context, timezone: str = "UTC") -> str:
    await ctx.info(f"get_current_timezone_datetime for {timezone}")

    try:
        tz = ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        return f"Часовой пояс '{timezone}' не найден. Используйте IANA-имена, например: Europe/Moscow, Asia/Tokyo"

    now = datetime.now(tz)
    utc_offset = now.strftime("%z")
    if len(utc_offset) == 5:
        utc_offset = utc_offset[:3] + ":" + utc_offset[3:]

    return (
        f"Текущая дата и время ({timezone}):\n"
        f"  Дата: {now.strftime('%Y-%m-%d')}\n"
        f"  Время: {now.strftime('%H:%M:%S')}\n"
        f"  День недели: {now.strftime('%A')}\n"
        f"  UTC смещение: {utc_offset}\n"
    )


@mcp.tool(
    name="Локальное время сервера",
    description="Возвращает текущее время на сервере"
)
def get_server_datetime() -> str:
    now = datetime.now().astimezone()

    tz_name = now.tzname() or "Unknown"
    utc_offset = now.strftime("%z")
    if len(utc_offset) == 5:
        utc_offset = utc_offset[:3] + ":" + utc_offset[3:]

    return (
        f"Локальное время сервера:\n"
        f"  Дата: {now.strftime('%Y-%m-%d')}\n"
        f"  Время: {now.strftime('%H:%M:%S')}\n"
        f"  День недели: {now.strftime('%A')}\n"
        f"  Часовой пояс: {tz_name}\n"
        f"  UTC смещение: {utc_offset}\n"
    )


@mcp.tool(
    name="Текущее время по координатам",
    description="Возвращает текущее время по координатам (широта, долгота)."
)
async def get_time_by_coords(lat: float, lon: float, ctx: Context) -> str:
    await ctx.info(f"get_time_by_coords for {lat} {lon}")

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://timeapi.io/api/time/current/coordinate",
                params={"latitude": lat, "longitude": lon},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        return f"Ошибка получения времени: {e}"

    iana_tz = data.get("timeZone", "Unknown")
    utc_offset_str = ""
    if iana_tz and iana_tz != "Unknown":
        try:
            tz = ZoneInfo(iana_tz)
            now = datetime.now(tz)
            utc_offset = now.strftime("%z")
            if len(utc_offset) == 5:
                utc_offset_str = utc_offset[:3] + ":" + utc_offset[3:]
        except ZoneInfoNotFoundError:
            pass

    return (
        f"Время по координатам ({lat}, {lon}) — {iana_tz}:\n"
        f"  Дата: {data.get('date', '?')}\n"
        f"  Время: {data.get('time', '?')}\n"
        f"  День недели: {data.get('dayOfWeek', '?')}\n"
        f"  UTC смещение: {utc_offset_str or '?'}\n"
    )


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "ok", "service": "mcp-server"})
