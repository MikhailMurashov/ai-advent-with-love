"""MCP Weather server with HTTP transport (tools/call endpoints)."""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Annotated

import httpx
from fastmcp import FastMCP, Context, Client
from pydantic import Field
from starlette.responses import JSONResponse

mcp = FastMCP(name="MCP Weather Server")

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WMO_CODES = {
    0: "Ясно", 1: "Преимущественно ясно", 2: "Переменная облачность",
    3: "Пасмурно", 45: "Туман", 48: "Иней",
    51: "Лёгкая морось", 53: "Умеренная морось", 55: "Сильная морось",
    61: "Небольшой дождь", 63: "Умеренный дождь", 65: "Сильный дождь",
    71: "Небольшой снег", 73: "Умеренный снег", 75: "Сильный снег",
    80: "Ливень", 81: "Умеренный ливень", 82: "Сильный ливень",
    95: "Гроза", 96: "Гроза с градом", 99: "Сильная гроза с градом",
}


@dataclass
class CurrentWeather:
    condition: str
    temperature_c: float
    wind_kmh: float
    humidity_pct: float


@dataclass
class ForecastDay:
    date: str
    condition: str
    temp_min_c: float
    temp_max_c: float
    precipitation_mm: float


@dataclass
class WeatherForecast:
    days: list[ForecastDay]


async def _fetch_weather(lat: float, lon: float, days: int = 1) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,weathercode,windspeed_10m,relativehumidity_2m",
        "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum",
        "forecast_days": days,
        "timezone": "auto",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(FORECAST_URL, params=params)
        resp.raise_for_status()
        return resp.json()


@mcp.tool(
    description="Возвращает текущую погоду по координатам",
    annotations={"readOnlyHint": True, "openWorldHint": True},
)
async def get_current_weather(
    lat: Annotated[float, Field(description="Широта", ge=-90, le=90)],
    lon: Annotated[float, Field(description="Долгота", ge=-180, le=180)],
    ctx: Context,
) -> CurrentWeather:
    await ctx.info(f"get_current_weather for {lat} {lon}")

    data = await _fetch_weather(lat, lon, days=1)
    await ctx.info(f"_fetch_weather: {data}")

    cur = data.get("current", {})
    wcode = cur.get("weathercode", 0)

    return CurrentWeather(
        condition=WMO_CODES.get(wcode, "Неизвестно"),
        temperature_c=cur.get("temperature_2m", 0.0),
        wind_kmh=cur.get("windspeed_10m", 0.0),
        humidity_pct=cur.get("relativehumidity_2m", 0.0),
    )


@mcp.tool(
    description="Прогноз по координатам. По умолчанию на 2 дня",
    annotations={"readOnlyHint": True, "openWorldHint": True},
)
async def get_forecast(
    lat: Annotated[float, Field(description="Широта", ge=-90, le=90)],
    lon: Annotated[float, Field(description="Долгота", ge=-180, le=180)],
    ctx: Context,
    days: Annotated[int, Field(description="Дней прогноза", ge=1, le=16)] = 2,
) -> WeatherForecast:
    await ctx.info(f"get_forecast for {lat} {lon} by {days} days")

    data = await _fetch_weather(lat, lon, days=days)
    await ctx.info(f"_fetch_weather: {data}")

    daily = data.get("daily", {})
    dates = daily.get("time", [])
    codes = daily.get("weathercode", [])
    max_temps = daily.get("temperature_2m_max", [])
    min_temps = daily.get("temperature_2m_min", [])
    precip = daily.get("precipitation_sum", [])

    forecast_days = [
        ForecastDay(
            date=date,
            condition=WMO_CODES.get(codes[i] if i < len(codes) else 0, "?"),
            temp_min_c=min_temps[i] if i < len(min_temps) else 0.0,
            temp_max_c=max_temps[i] if i < len(max_temps) else 0.0,
            precipitation_mm=precip[i] if i < len(precip) else 0.0,
        )
        for i, date in enumerate(dates)
    ]

    return WeatherForecast(days=forecast_days)


@mcp.tool(
    description="Сохраняет в файл саммари прогноза по координатам на 7 дней",
    annotations={"readOnlyHint": False, "openWorldHint": True},
)
async def save_forecast_summary(
    lat: Annotated[float, Field(description="Широта", ge=-90, le=90)],
    lon: Annotated[float, Field(description="Долгота", ge=-180, le=180)],
    ctx: Context,
) -> bool:
    await ctx.info(f"save_forecast_summary for {lat} {lon}")

    data = await _fetch_weather(lat, lon, days=7)

    daily = data.get("daily", {})
    dates = daily.get("time", [])
    codes = daily.get("weathercode", [])
    max_temps = daily.get("temperature_2m_max", [])
    min_temps = daily.get("temperature_2m_min", [])
    precip = daily.get("precipitation_sum", [])

    forecast_days = [
        ForecastDay(
            date=date,
            condition=WMO_CODES.get(codes[i] if i < len(codes) else 0, "?"),
            temp_min_c=min_temps[i] if i < len(min_temps) else 0.0,
            temp_max_c=max_temps[i] if i < len(max_temps) else 0.0,
            precipitation_mm=precip[i] if i < len(precip) else 0.0,
        )
        for i, date in enumerate(dates)
    ]

    async with Client("http://mcp-summarize:8006/mcp") as client:
        await client.call_tool("save_forecast_summary", {
            "forecast": {"days": [dataclasses.asdict(d) for d in forecast_days]},
        })

    return True


mcp.disable(names=[
    "save_forecast_summary",
    "get_current_weather",
])


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "ok", "service": "mcp-server"})
