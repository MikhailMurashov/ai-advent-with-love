"""MCP Dadata server — address/name/phone cleaning and party suggestions via Dadata API."""
from __future__ import annotations

import os

import httpx
from fastmcp import FastMCP, Context
from starlette.responses import JSONResponse

mcp = FastMCP(name="MCP Weather Server")

DADATA_SUGGEST_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/party"
DADATA_SUGGEST_ADDRESS_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/address"

DADATA_API_KEY = os.environ.get("DADATA_API_KEY", "")
DADATA_SECRET_KEY = os.environ.get("DADATA_SECRET_KEY", "")


@mcp.tool(
    name="Подсказка адреса",
    description="Ищет адреса по любой части адреса от региона до квартиры. Используй для любого запроса о городе или адресе"
)
async def suggest_address(query: str, ctx: Context, count: int = 1) -> str:
    await ctx.info(f"suggest_address for {query}")

    if not query:
        return "Ошибка: запрос не может быть пустым"
    if not 1 <= count <= 20:
        return "Ошибка: count должен быть от 1 до 20"
    if not DADATA_API_KEY:
        return "Ошибка: не задан DADATA_API_KEY"

    try:
        headers = {
            "Authorization": f"Token {DADATA_API_KEY}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                DADATA_SUGGEST_ADDRESS_URL,
                headers=headers,
                json={"query": query, "count": count},
            )
            resp.raise_for_status()
            data = resp.json()

        suggestions = data.get("suggestions", [])
        if not suggestions:
            return "Адреса не найдены"

        lines = []
        for i, s in enumerate(suggestions):
            d = s.get("data", {})
            fields = [
                ("address", s.get("value")),
                ("postal_code", d.get("postal_code")),
                ("region", d.get("region")),
                ("city", d.get("city") or d.get("settlement")),
                ("street", d.get("street")),
                ("house", d.get("house")),
                ("geo_lat", d.get("geo_lat")),
                ("geo_lon", d.get("geo_lon")),
                ("fias_id", d.get("fias_id")),
            ]
            parts = [f"{k}: {v}" for k, v in fields if v not in (None, "")]
            lines.append(f"[{i + 1}] " + "\n  ".join(parts))

        return "\n\n".join(lines)
    except httpx.HTTPStatusError as e:
        return f"Ошибка Dadata API: {e.response.status_code} {e.response.text}"
    except Exception as e:
        return f"Ошибка: {e}"


@mcp.tool(
    name="Подсказка организации",
    description="Ищет компании и индивидуальных предпринимателей: по ИНН, ИНН/КПП, ОГРН или названию"
)
async def suggest_party(query: str, count: int = 5) -> str:
    if not query:
        return "Ошибка: запрос не может быть пустым"
    if not 1 <= count <= 20:
        return "Ошибка: count должен быть от 1 до 20"
    if not DADATA_API_KEY:
        return "Ошибка: не задан DADATA_API_KEY"

    try:
        headers = {
            "Authorization": f"Token {DADATA_API_KEY}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                DADATA_SUGGEST_URL,
                headers=headers,
                json={"query": query, "count": count},
            )
            resp.raise_for_status()
            data = resp.json()

        suggestions = data.get("suggestions", [])
        if not suggestions:
            return "Организации не найдены"

        lines = []
        for i, s in enumerate(suggestions):
            d = s.get("data", {})
            opf = d.get("opf") or {}
            status = d.get("status") or {}
            address = d.get("address") or {}
            management = d.get("management") or {}

            fields = [
                ("name", s.get("value")),
                ("inn", d.get("inn")),
                ("ogrn", d.get("ogrn")),
                ("kpp", d.get("kpp")),
                ("opf", opf.get("short")),
                ("status", status.get("status")),
                ("address", address.get("value")),
                ("management", f"{management.get('name', '')} ({management.get('post', '')})" if management.get("name") else None),
            ]
            parts = [f"{k}: {v}" for k, v in fields if v not in (None, "")]
            lines.append(f"[{i + 1}] " + "\n  ".join(parts))

        return "\n\n".join(lines)
    except httpx.HTTPStatusError as e:
        return f"Ошибка Dadata API: {e.response.status_code} {e.response.text}"
    except Exception as e:
        return f"Ошибка: {e}"


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "ok", "service": "mcp-server"})
