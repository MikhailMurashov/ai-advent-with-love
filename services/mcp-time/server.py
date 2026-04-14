"""MCP Time server with HTTP transport (tools/call endpoints)."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="MCP Time Server")


# ---- Tool implementations ----


def get_current_datetime(timezone: str = "UTC") -> str:
    try:
        tz = ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        return f"Часовой пояс '{timezone}' не найден. Используйте IANA-имена, например: Europe/Moscow, America/New_York, Asia/Tokyo"
    now = datetime.now(tz)
    utc_offset = now.strftime("%z")
    if len(utc_offset) == 5:
        utc_offset = utc_offset[:3] + ":" + utc_offset[3:]
    return (
        f"Текущая дата и время ({timezone}):\n"
        f"  Дата: {now.strftime('%Y-%m-%d')}\n"
        f"  Время: {now.strftime('%H:%M:%S')}\n"
        f"  День недели: {now.strftime('%A')}\n"
        f"  Часовой пояс: {now.tzname()}\n"
        f"  UTC смещение: {utc_offset}\n"
        f"  ISO 8601: {now.isoformat()}"
    )


def get_local_datetime() -> str:
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
        f"  ISO 8601: {now.isoformat()}"
    )


async def get_city_time(city: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city, "count": 1, "language": "en", "format": "json"},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        return f"Ошибка геокодирования: {e}"

    results = data.get("results")
    if not results:
        return f"Город '{city}' не найден."

    location = results[0]
    iana_tz = location.get("timezone")
    if not iana_tz:
        return f"Для города '{city}' не удалось определить часовой пояс."

    city_name = location.get("name", city)
    country = location.get("country", "")

    try:
        tz = ZoneInfo(iana_tz)
    except ZoneInfoNotFoundError:
        return f"Неизвестный часовой пояс: {iana_tz}"

    now = datetime.now(tz)
    utc_offset = now.strftime("%z")
    if len(utc_offset) == 5:
        utc_offset = utc_offset[:3] + ":" + utc_offset[3:]

    return (
        f"Время в городе {city_name}, {country} ({iana_tz}):\n"
        f"  Дата: {now.strftime('%Y-%m-%d')}\n"
        f"  Время: {now.strftime('%H:%M:%S')}\n"
        f"  День недели: {now.strftime('%A')}\n"
        f"  UTC смещение: {utc_offset}\n"
        f"  ISO 8601: {now.isoformat()}"
    )


# ---- HTTP endpoints ----

TOOLS_LIST = [
    {
        "name": "get_current_datetime",
        "description": "Возвращает реальную текущую дату и время в указанном часовом поясе (IANA-имя или UTC по умолчанию).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "IANA-имя часового пояса (например, Europe/Moscow, America/New_York) или смещение +HH:MM. По умолчанию UTC.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_local_datetime",
        "description": "Возвращает локальное время сервера (системный часовой пояс контейнера).",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_city_time",
        "description": "Возвращает реальное текущее время в указанном городе. Геокодирует город через Open-Meteo и определяет его часовой пояс.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "Название города, например Tokyo, London, Москва",
                },
            },
            "required": ["city"],
        },
    },
]


@app.get("/tools")
async def list_tools() -> dict:
    return {"tools": TOOLS_LIST}


class CallRequest(BaseModel):
    name: str
    arguments: dict = {}


@app.post("/call")
async def call_tool(req: CallRequest) -> dict:
    if req.name == "get_current_datetime":
        result = get_current_datetime(**req.arguments)
    elif req.name == "get_local_datetime":
        result = get_local_datetime()
    elif req.name == "get_city_time":
        result = await get_city_time(**req.arguments)
    else:
        result = f"Unknown tool: {req.name}"
    return {"content": [{"type": "text", "text": result}]}


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
