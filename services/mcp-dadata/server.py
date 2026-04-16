"""MCP Dadata server — address/name/phone cleaning and party suggestions via Dadata API."""
from __future__ import annotations

import os

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="MCP Dadata Server")

DADATA_SUGGEST_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/party"
DADATA_SUGGEST_ADDRESS_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/address"

DADATA_API_KEY = os.environ.get("DADATA_API_KEY", "")
DADATA_SECRET_KEY = os.environ.get("DADATA_SECRET_KEY", "")


async def suggest_address(query: str, count: int = 5) -> str:
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


# ---- HTTP endpoints ----

TOOLS_LIST = [
    {
        "name": "suggest_address",
        "description": (
            "Поиск российских адресов, городов и населённых пунктов по любому запросу через Dadata Suggestions API. "
            "Возвращает полный адрес, регион, город, почтовый индекс и координаты. "
            "Используй для любого запроса о городе или адресе."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Адрес, название города или населённого пункта для поиска",
                },
                "count": {
                    "type": "integer",
                    "description": "Количество результатов (1–20, по умолчанию 1)",
                    "minimum": 1,
                    "maximum": 20,
                    "default": 1,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "suggest_party",
        "description": (
            "Поиск российских организаций и ИП по названию или ИНН через Dadata Suggestions API. "
            "Возвращает ИНН, ОГРН, КПП, форму собственности, статус, адрес и руководителя."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Название организации, ИНН или ОГРН для поиска",
                },
                "count": {
                    "type": "integer",
                    "description": "Количество результатов (1–20, по умолчанию 1)",
                    "minimum": 1,
                    "maximum": 20,
                    "default": 1,
                },
            },
            "required": ["query"],
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
    if req.name == "suggest_address":
        result = await suggest_address(**req.arguments)
    elif req.name == "suggest_party":
        result = await suggest_party(**req.arguments)
    else:
        result = f"Unknown tool: {req.name}"
    return {"content": [{"type": "text", "text": result}]}


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
