from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from typing import Annotated

from fastmcp import FastMCP, Context, Client
from pydantic import Field
from starlette.responses import JSONResponse

mcp = FastMCP(name="MCP Summarize Server")


@mcp.tool(description="Высчитывает саммари по прогнозу погоды и сохраняет в файл")
async def save_forecast_summary(
    forecast: Annotated[dict, Field(description="WeatherForecast dict")],
    ctx: Context,
):
    await ctx.info(f"save_forecast_summary for {forecast}")

    days = forecast.get("days", [])

    temp_max = max(d["temp_max_c"] for d in days)
    temp_min = min(d["temp_min_c"] for d in days)
    temp_avg = sum((d["temp_max_c"] + d["temp_min_c"]) / 2 for d in days) / len(days)
    total_precipitation = sum(d["precipitation_mm"] for d in days)
    most_common_condition = Counter(d["condition"] for d in days).most_common(1)[0][0]

    summary = {
        "days_count": len(days),
        "temp_max_c": round(temp_max, 1),
        "temp_min_c": round(temp_min, 1),
        "temp_avg_c": round(temp_avg, 1),
        "total_precipitation_mm": round(total_precipitation, 1),
        "most_common_condition": most_common_condition,
        "days": days,
    }

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    async with Client("http://mcp-saver:8005/mcp") as client:
        await client.call_tool("save_to_file", {
            "filename": f"forecast_summary_{timestamp}.json",
            "data": json.dumps(summary, ensure_ascii=False, indent=2),
        })


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "ok", "service": "mcp-server"})
