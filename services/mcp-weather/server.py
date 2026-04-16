"""MCP Weather server with HTTP transport (tools/call endpoints)."""
from __future__ import annotations

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="MCP Weather Server")

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
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


async def _geocode(city: str) -> tuple[float, float, str]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            GEOCODING_URL,
            params={"name": city, "count": 1, "language": "ru", "format": "json"},
        )
        resp.raise_for_status()
        data = resp.json()
    results = data.get("results", [])
    if not results:
        raise ValueError(f"Город '{city}' не найден")
    r = results[0]
    return r["latitude"], r["longitude"], r.get("name", city)


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


# ---- Tool implementations ----

async def get_current_weather(city: str) -> str:
    try:
        lat, lon, name = await _geocode(city)
        data = await _fetch_weather(lat, lon, days=1)
        cur = data.get("current", {})
        temp = cur.get("temperature_2m", "?")
        wcode = cur.get("weathercode", 0)
        wind = cur.get("windspeed_10m", "?")
        humidity = cur.get("relativehumidity_2m", "?")
        desc = WMO_CODES.get(wcode, "Неизвестно")
        return (
            f"Погода в {name}:\n"
            f"  Состояние: {desc}\n"
            f"  Температура: {temp}°C\n"
            f"  Ветер: {wind} км/ч\n"
            f"  Влажность: {humidity}%"
        )
    except Exception as e:
        return f"Ошибка получения погоды: {type(e).__name__}: {e}"


async def get_forecast(city: str, days: int = 3) -> str:
    try:
        days = max(1, min(days, 7))
        lat, lon, name = await _geocode(city)
        data = await _fetch_weather(lat, lon, days=days)
        daily = data.get("daily", {})
        dates = daily.get("time", [])
        codes = daily.get("weathercode", [])
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        precip = daily.get("precipitation_sum", [])

        lines = [f"Прогноз погоды для {name} на {days} дн.:"]
        for i, date in enumerate(dates):
            desc = WMO_CODES.get(codes[i] if i < len(codes) else 0, "?")
            tmax = max_temps[i] if i < len(max_temps) else "?"
            tmin = min_temps[i] if i < len(min_temps) else "?"
            pr = precip[i] if i < len(precip) else "?"
            lines.append(f"  {date}: {desc}, {tmin}…{tmax}°C, осадки {pr} мм")
        return "\n".join(lines)
    except Exception as e:
        return f"Ошибка получения прогноза: {type(e).__name__}: {e}"


async def get_weather_by_coords(lat: float, lon: float, days: int = 1) -> str:
    try:
        days = max(1, min(days, 7))
        data = await _fetch_weather(lat, lon, days=days)
        cur = data.get("current", {})
        temp = cur.get("temperature_2m", "?")
        wcode = cur.get("weathercode", 0)
        wind = cur.get("windspeed_10m", "?")
        humidity = cur.get("relativehumidity_2m", "?")
        desc = WMO_CODES.get(wcode, "Неизвестно")
        result = (
            f"Погода по координатам ({lat}, {lon}):\n"
            f"  Состояние: {desc}\n"
            f"  Температура: {temp}°C\n"
            f"  Ветер: {wind} км/ч\n"
            f"  Влажность: {humidity}%"
        )
        if days > 1:
            daily = data.get("daily", {})
            dates = daily.get("time", [])
            codes = daily.get("weathercode", [])
            max_temps = daily.get("temperature_2m_max", [])
            min_temps = daily.get("temperature_2m_min", [])
            precip = daily.get("precipitation_sum", [])
            lines = [result, f"\nПрогноз на {days} дн.:"]
            for i, date in enumerate(dates):
                d = WMO_CODES.get(codes[i] if i < len(codes) else 0, "?")
                tmax = max_temps[i] if i < len(max_temps) else "?"
                tmin = min_temps[i] if i < len(min_temps) else "?"
                pr = precip[i] if i < len(precip) else "?"
                lines.append(f"  {date}: {d}, {tmin}…{tmax}°C, осадки {pr} мм")
            return "\n".join(lines)
        return result
    except Exception as e:
        return f"Ошибка получения погоды: {type(e).__name__}: {e}"


# ---- HTTP endpoints ----

TOOLS_LIST = [
    {
        "name": "get_weather_by_coords",
        "description": (
            "Возвращает погоду и прогноз по географическим координатам. "
            "ИСПОЛЬЗУЙ ЭТОТ ИНСТРУМЕНТ В ПЕРВУЮ ОЧЕРЕДЬ, если известны координаты (широта/долгота). "
            "Быстрее и точнее, чем поиск по названию города."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "lat": {"type": "number", "description": "Широта"},
                "lon": {"type": "number", "description": "Долгота"},
                "days": {"type": "integer", "description": "Количество дней прогноза (1–7), по умолчанию 1", "default": 1},
            },
            "required": ["lat", "lon"],
        },
    },
    {
        "name": "get_current_weather",
        "description": "Возвращает текущую погоду в указанном городе.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "Название города"},
            },
            "required": ["city"],
        },
    },
    {
        "name": "get_forecast",
        "description": "Возвращает прогноз погоды на несколько дней.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "Название города"},
                "days": {
                    "type": "integer",
                    "description": "Количество дней (1–7)",
                    "default": 3,
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
    if req.name == "get_current_weather":
        result = await get_current_weather(**req.arguments)
    elif req.name == "get_forecast":
        result = await get_forecast(**req.arguments)
    elif req.name == "get_weather_by_coords":
        result = await get_weather_by_coords(**req.arguments)
    else:
        result = f"Unknown tool: {req.name}"
    return {"content": [{"type": "text", "text": result}]}


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
