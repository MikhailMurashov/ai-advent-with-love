from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import async_session_factory, create_tables
from app.db.repositories import SQLiteMCPServerRepository
from app.dependencies import get_mcp_client
from app.routers import chat, mcp_servers, notifications, sessions, users

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="LLM API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(sessions.router)
app.include_router(chat.router)
app.include_router(mcp_servers.router)
app.include_router(notifications.router)


@app.on_event("startup")
async def startup() -> None:
    await create_tables()

    async with async_session_factory() as db:
        repo = SQLiteMCPServerRepository(db)
        enabled = await repo.list_enabled()

    mcp_client = get_mcp_client()
    await mcp_client.load_servers_from_db(enabled)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
