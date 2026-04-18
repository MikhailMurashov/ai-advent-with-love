from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.agent.mcp_client import MCPClient
from app.dependencies import DbSession, get_mcp_client
from app.db.repositories import SQLiteMCPServerRepository
from app.interfaces.repositories import IMCPServerRepository

router = APIRouter(prefix="/mcp-servers", tags=["mcp-servers"])


class MCPServerResponse(BaseModel):
    id: str
    name: str
    url: str
    description: str
    enabled: bool
    created_at: str


class CreateMCPServerRequest(BaseModel):
    name: str
    url: str
    description: str = ""
    enabled: bool = True


async def get_mcp_server_repo(db: DbSession) -> IMCPServerRepository:
    return SQLiteMCPServerRepository(db)


MCPServerRepo = Annotated[IMCPServerRepository, Depends(get_mcp_server_repo)]
MCPClientDep = Annotated[MCPClient, Depends(get_mcp_client)]


@router.get("", response_model=list[MCPServerResponse])
async def list_servers(repo: MCPServerRepo) -> list[MCPServerResponse]:
    servers = await repo.list_all()
    return [MCPServerResponse(**s.__dict__) for s in servers]


@router.post("", response_model=MCPServerResponse, status_code=201)
async def create_server(
    body: CreateMCPServerRequest,
    repo: MCPServerRepo,
    mcp_client: MCPClientDep,
) -> MCPServerResponse:
    existing = await repo.get_by_name(body.name)
    if existing:
        raise HTTPException(status_code=409, detail=f"Server with name {body.name!r} already exists")
    server = await repo.create(
        name=body.name, url=body.url, description=body.description, enabled=body.enabled
    )
    if server.enabled:
        await mcp_client.register_server(server.name, server.url)
    return MCPServerResponse(**server.__dict__)


@router.delete("/{server_id}", status_code=204)
async def delete_server(
    server_id: str,
    repo: MCPServerRepo,
    mcp_client: MCPClientDep,
) -> None:
    server = await repo.get(server_id)
    if server is None:
        raise HTTPException(status_code=404, detail="Server not found")
    await mcp_client.unregister_server(server.name)
    await repo.delete(server_id)


@router.patch("/{server_id}/enable", response_model=MCPServerResponse)
async def enable_server(
    server_id: str,
    repo: MCPServerRepo,
    mcp_client: MCPClientDep,
) -> MCPServerResponse:
    server = await repo.get(server_id)
    if server is None:
        raise HTTPException(status_code=404, detail="Server not found")
    updated = await repo.set_enabled(server_id, True)
    if not server.enabled:
        await mcp_client.register_server(updated.name, updated.url)
    return MCPServerResponse(**updated.__dict__)


@router.patch("/{server_id}/disable", response_model=MCPServerResponse)
async def disable_server(
    server_id: str,
    repo: MCPServerRepo,
    mcp_client: MCPClientDep,
) -> MCPServerResponse:
    server = await repo.get(server_id)
    if server is None:
        raise HTTPException(status_code=404, detail="Server not found")
    updated = await repo.set_enabled(server_id, False)
    if server.enabled:
        await mcp_client.unregister_server(server.name)
    return MCPServerResponse(**updated.__dict__)
