from __future__ import annotations

import logging

import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.database import create_tables
from app.dependencies import get_mcp_client
from app.routers import chat, sessions, users

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


@app.on_event("startup")
async def startup() -> None:
    await create_tables()

    mcp_client = get_mcp_client()
    try:
        with open(settings.mcp_config_path) as f:
            config = yaml.safe_load(f)
        await mcp_client.load_servers(config or {})
    except FileNotFoundError:
        logging.warning("main: mcp_config.yaml not found, MCP tools unavailable")
    except Exception as e:
        logging.warning("main: failed to load MCP config: %s", e)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
