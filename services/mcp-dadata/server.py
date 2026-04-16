"""MCP Dadata server — address/name/phone cleaning and party suggestions via Dadata API."""
from __future__ import annotations

import os

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="MCP Dadata Server")

DADATA_CLEAN_BASE = "https://cleaner.dadata.ru/api/v1/clean/{schema}"
DADATA_SUGGEST_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/party"

DADATA_API_KEY = os.environ.get("DADATA_API_KEY", "")
DADATA_SECRET_KEY = os.environ.get("DADATA_SECRET_KEY", "")


async def _call_cleaner(schema: str, items: list[str]) -> list[dict]:
    headers = {
        "Authorization": f"Token {DADATA_API_KEY}",
        "X-Secret": DADATA_SECRET_KEY,
        "Content-Type": "application/json",
    }
    url = DADATA_CLEAN_BASE.format(schema=schema)
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, headers=headers, json=items)
        resp.raise_for_status()
        return resp.json()


async def clean_address(addresses: list[str]) -> str:
    if not addresses:
        return "Ошибка: список адресов пуст"
    if len(addresses) > 50:
        return "Ошибка: максимум 50 адресов за один запрос"
    if not DADATA_API_KEY or not DADATA_SECRET_KEY:
        return "Ошибка: не заданы DADATA_API_KEY или DADATA_SECRET_KEY"

    try:
        results = await _call_cleaner("ADDRESS", addresses)

        lines = []
        for i, item in enumerate(results):
            fields = [
                ("result", item.get("result")),
                ("postal_code", item.get("postal_code")),
                ("region", item.get("region")),
                ("city", item.get("city")),
                ("street", item.get("street")),
                ("house", item.get("house")),
                ("flat", item.get("flat")),
                ("qc", item.get("qc")),
                ("geo_lat", item.get("geo_lat")),
                ("geo_lon", item.get("geo_lon")),
                ("fias_id", item.get("fias_id")),
            ]
            parts = [f"{k}: {v}" for k, v in fields if v not in (None, "")]
            lines.append(f"[{i + 1}] {addresses[i]}\n  " + "\n  ".join(parts))

        return "\n\n".join(lines)
    except httpx.HTTPStatusError as e:
        return f"Ошибка Dadata API: {e.response.status_code} {e.response.text}"
    except Exception as e:
        return f"Ошибка: {e}"


async def clean_name(names: list[str]) -> str:
    if not names:
        return "Ошибка: список имён пуст"
    if len(names) > 50:
        return "Ошибка: максимум 50 имён за один запрос"
    if not DADATA_API_KEY or not DADATA_SECRET_KEY:
        return "Ошибка: не заданы DADATA_API_KEY или DADATA_SECRET_KEY"

    try:
        results = await _call_cleaner("NAME", names)

        lines = []
        for i, item in enumerate(results):
            fields = [
                ("result", item.get("result")),
                ("surname", item.get("surname")),
                ("name", item.get("name")),
                ("patronymic", item.get("patronymic")),
                ("gender", item.get("gender")),
                ("qc", item.get("qc")),
            ]
            parts = [f"{k}: {v}" for k, v in fields if v not in (None, "")]
            lines.append(f"[{i + 1}] {names[i]}\n  " + "\n  ".join(parts))

        return "\n\n".join(lines)
    except httpx.HTTPStatusError as e:
        return f"Ошибка Dadata API: {e.response.status_code} {e.response.text}"
    except Exception as e:
        return f"Ошибка: {e}"


async def clean_phone(phones: list[str]) -> str:
    if not phones:
        return "Ошибка: список телефонов пуст"
    if len(phones) > 50:
        return "Ошибка: максимум 50 телефонов за один запрос"
    if not DADATA_API_KEY or not DADATA_SECRET_KEY:
        return "Ошибка: не заданы DADATA_API_KEY или DADATA_SECRET_KEY"

    try:
        results = await _call_cleaner("PHONE", phones)

        lines = []
        for i, item in enumerate(results):
            fields = [
                ("phone", item.get("phone")),
                ("type", item.get("type")),
                ("provider", item.get("provider")),
                ("country", item.get("country")),
                ("region", item.get("region")),
                ("city", item.get("city")),
                ("qc", item.get("qc")),
            ]
            parts = [f"{k}: {v}" for k, v in fields if v not in (None, "")]
            lines.append(f"[{i + 1}] {phones[i]}\n  " + "\n  ".join(parts))

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
        "name": "clean_address",
        "description": (
            "Стандартизирует и парсит российские адреса через Dadata API. "
            "Возвращает нормализованный адрес, почтовый индекс, регион, город, улицу, дом, квартиру, координаты."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "addresses": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Список адресов (1–50 строк)",
                    "minItems": 1,
                    "maxItems": 50,
                },
            },
            "required": ["addresses"],
        },
    },
    {
        "name": "clean_name",
        "description": (
            "Стандартизирует и парсит ФИО через Dadata API. "
            "Возвращает нормализованное ФИО, отдельно фамилию, имя, отчество, пол и код качества."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "names": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Список ФИО (1–50 строк)",
                    "minItems": 1,
                    "maxItems": 50,
                },
            },
            "required": ["names"],
        },
    },
    {
        "name": "clean_phone",
        "description": (
            "Стандартизирует и парсит российские телефонные номера через Dadata API. "
            "Возвращает нормализованный номер, тип, оператора, страну, регион, город и код качества."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "phones": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Список телефонных номеров (1–50 строк)",
                    "minItems": 1,
                    "maxItems": 50,
                },
            },
            "required": ["phones"],
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
                    "description": "Количество результатов (1–20, по умолчанию 5)",
                    "minimum": 1,
                    "maximum": 20,
                    "default": 5,
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
    if req.name == "clean_address":
        result = await clean_address(**req.arguments)
    elif req.name == "clean_name":
        result = await clean_name(**req.arguments)
    elif req.name == "clean_phone":
        result = await clean_phone(**req.arguments)
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
