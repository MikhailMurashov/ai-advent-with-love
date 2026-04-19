"""MCP Dadata server — address/name/phone cleaning and party suggestions via Dadata API."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Annotated

import httpx
from fastmcp import FastMCP, Context
from pydantic import Field
from starlette.responses import JSONResponse

mcp = FastMCP(name="MCP Dadata Server")

DADATA_SUGGEST_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/party"
DADATA_SUGGEST_ADDRESS_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/address"

DADATA_API_KEY = os.environ.get("DADATA_API_KEY", "")
DADATA_SECRET_KEY = os.environ.get("DADATA_SECRET_KEY", "")


@dataclass
class AddressGeo:
    geo_lat: str | None
    geo_lon: str | None


@dataclass
class AddressSuggestion:
    address: str
    postal_code: str | None
    region: str | None
    city: str | None
    street: str | None
    house: str | None
    geo_lat: str | None
    geo_lon: str | None
    fias_id: str | None


@dataclass
class PartySuggestion:
    name: str
    inn: str | None
    ogrn: str | None
    kpp: str | None
    opf: str | None
    status: str | None
    address: str | None
    management: str | None


@mcp.tool(
    description="Ищет координаты адреса по любой части: регион, город, улица, дом",
    annotations={"readOnlyHint": True, "openWorldHint": True},
)
async def get_address_geo(
    query: Annotated[str, Field(description="Адрес")],
    ctx: Context,
) -> AddressGeo | None:
    await ctx.info(f"get_address_geo for {query}")

    if not DADATA_API_KEY:
        raise ValueError("Не задан DADATA_API_KEY")

    headers = {
        "Authorization": f"Token {DADATA_API_KEY}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            DADATA_SUGGEST_ADDRESS_URL,
            headers=headers,
            json={"query": query, "count": 1},
        )
        resp.raise_for_status()
        data = resp.json()

    suggestions = data.get("suggestions", [])
    if not suggestions:
        return None

    suggest = suggestions[0]
    return AddressGeo(
        geo_lat=suggest.get("data", {}).get("geo_lat"),
        geo_lon=suggest.get("data", {}).get("geo_lon"),
    )


@mcp.tool(
    description="Ищет адреса по любой части: регион, город, улица, дом",
    annotations={"readOnlyHint": True, "openWorldHint": True},
)
async def suggest_address(
    query: Annotated[str, Field(description="Часть адреса")],
    ctx: Context,
    count: Annotated[int, Field(description="Кол-во результатов", ge=1, le=20)] = 1,
) -> list[AddressSuggestion]:
    await ctx.info(f"suggest_address for {query}")

    if not DADATA_API_KEY:
        raise ValueError("Не задан DADATA_API_KEY")

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
    return [
        AddressSuggestion(
            address=s.get("value", ""),
            postal_code=s.get("data", {}).get("postal_code"),
            region=s.get("data", {}).get("region"),
            city=s.get("data", {}).get("city") or s.get("data", {}).get("settlement"),
            street=s.get("data", {}).get("street"),
            house=s.get("data", {}).get("house"),
            geo_lat=s.get("data", {}).get("geo_lat"),
            geo_lon=s.get("data", {}).get("geo_lon"),
            fias_id=s.get("data", {}).get("fias_id"),
        )
        for s in suggestions
    ]


@mcp.tool(
    description="Поиск компаний и ИП по ИНН, ОГРН или названию",
    annotations={"readOnlyHint": True, "openWorldHint": True},
)
async def suggest_party(
    query: Annotated[str, Field(description="ИНН, ОГРН или название")],
    count: Annotated[int, Field(description="Кол-во результатов", ge=1, le=20)] = 5,
) -> list[PartySuggestion]:
    if not DADATA_API_KEY:
        raise ValueError("Не задан DADATA_API_KEY")

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
    return [
        PartySuggestion(
            name=s.get("value", ""),
            inn=s.get("data", {}).get("inn"),
            ogrn=s.get("data", {}).get("ogrn"),
            kpp=s.get("data", {}).get("kpp"),
            opf=(s.get("data", {}).get("opf") or {}).get("short"),
            status=(s.get("data", {}).get("state") or {}).get("status"),
            address=(s.get("data", {}).get("address") or {}).get("value"),
            management=(
                f"{m.get('name', '')} ({m.get('post', '')})"
                if (m := s.get("data", {}).get("management") or {}) and m.get("name")
                else None
            ),
        )
        for s in suggestions
    ]


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "ok", "service": "mcp-server"})
