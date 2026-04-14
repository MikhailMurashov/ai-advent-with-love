from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.agent import Agent
from app.agent.mcp_client import MCPClient
from app.agent.strategies import make_strategy
from app.db.database import get_session
from app.db.repositories import (
    SQLiteMemoryRepository,
    SQLiteSessionRepository,
    SQLiteUserRepository,
)
from app.infrastructure.llm import LiteLLMClient
from app.interfaces.repositories import IMemoryRepository, ISessionRepository, IUserRepository

# Singleton MCP client — initialised during startup
_mcp_client: MCPClient = MCPClient()


def get_mcp_client() -> MCPClient:
    return _mcp_client


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_session():
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db_session)]


async def get_user_repo(db: DbSession) -> IUserRepository:
    return SQLiteUserRepository(db)


async def get_session_repo(db: DbSession) -> ISessionRepository:
    return SQLiteSessionRepository(db)


async def get_memory_repo(db: DbSession) -> IMemoryRepository:
    return SQLiteMemoryRepository(db)


async def get_agent(
    session_repo: Annotated[ISessionRepository, Depends(get_session_repo)],
    memory_repo: Annotated[IMemoryRepository, Depends(get_memory_repo)],
    mcp_client: Annotated[MCPClient, Depends(get_mcp_client)],
) -> Agent:
    llm = LiteLLMClient()
    # Strategy type is determined per-request from session info; default here
    strategy = make_strategy("sliding_window_summary")
    return Agent(
        llm=llm,
        strategy=strategy,
        memory_repo=memory_repo,
        session_repo=session_repo,
        mcp_client=mcp_client,
    )
