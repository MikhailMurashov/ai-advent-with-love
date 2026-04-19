"""MCP Weather server with HTTP transport (tools/call endpoints)."""
from __future__ import annotations

import httpx
from fastmcp import FastMCP, Context
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
    name="Текущая погода по координатам",
    description="Возвращает текущую погоду по географическим координатам"
)
async def get_current_weather(lat: float, lon: float, ctx: Context) -> str:
    await ctx.info(f"get_current_weather for {lat} {lon}")

    try:
        data = await _fetch_weather(lat, lon, days=1)
        await ctx.info(f"_fetch_weather: {data}")

        cur = data.get("current", {})
        temp = cur.get("temperature_2m", "?")
        wcode = cur.get("weathercode", 0)
        wind = cur.get("windspeed_10m", "?")
        humidity = cur.get("relativehumidity_2m", "?")
        desc = WMO_CODES.get(wcode, "Неизвестно")

        return (
            f"Состояние: {desc}\n"
            f"Температура: {temp}°C\n"
            f"Ветер: {wind} км/ч\n"
            f"Влажность: {humidity}%"
        )
    except Exception as e:
        return f"Ошибка получения погоды: {type(e).__name__}: {e}"


@mcp.tool(
    name="Прогноз погоды",
    description="Возвращает прогноз погоды по географическим координатам. По умолчанию на 2 дня"
)
async def get_forecast(lat: float, lon: float, ctx: Context, days: int = 2) -> str:
    await ctx.info(f"get_forecast for {lat} {lon} by {days} days")

    try:
        data = await _fetch_weather(lat, lon, days=days)
        await ctx.info(f"_fetch_weather: {data}")

        daily = data.get("daily", {})
        dates = daily.get("time", [])
        codes = daily.get("weathercode", [])
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        precip = daily.get("precipitation_sum", [])

        lines = [f"Прогноз на {days} дн.:"]

        for i, date in enumerate(dates):
            d = WMO_CODES.get(codes[i] if i < len(codes) else 0, "?")
            tmax = max_temps[i] if i < len(max_temps) else "?"
            tmin = min_temps[i] if i < len(min_temps) else "?"
            pr = precip[i] if i < len(precip) else "?"
            lines.append(f"  {date}: {d}, {tmin}…{tmax}°C, осадки {pr} мм")

        return "\n".join(lines)
    except Exception as e:
        return f"Ошибка получения погоды: {type(e).__name__}: {e}"


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "ok", "service": "mcp-server"})
