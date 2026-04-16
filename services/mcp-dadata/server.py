"""MCP Dadata server — address cleaning via Dadata Cleaner API."""
from __future__ import annotations

import os

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="MCP Dadata Server")

DADATA_CLEAN_URL = "https://cleaner.dadata.ru/api/v1/clean/ADDRESS"

DADATA_API_KEY = os.environ.get("DADATA_API_KEY", "")
DADATA_SECRET_KEY = os.environ.get("DADATA_SECRET_KEY", "")


async def clean_address(addresses: list[str]) -> str:
    if not addresses:
        return "Ошибка: список адресов пуст"
    if len(addresses) > 50:
        return "Ошибка: максимум 50 адресов за один запрос"
    if not DADATA_API_KEY or not DADATA_SECRET_KEY:
        return "Ошибка: не заданы DADATA_API_KEY или DADATA_SECRET_KEY"

    try:
        headers = {
            "Authorization": f"Token {DADATA_API_KEY}",
            "X-Secret": DADATA_SECRET_KEY,
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(DADATA_CLEAN_URL, headers=headers, json=addresses)
            resp.raise_for_status()
            results = resp.json()

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
    }
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
    else:
        result = f"Unknown tool: {req.name}"
    return {"content": [{"type": "text", "text": result}]}


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
