from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies import get_session_repo
from app.interfaces.repositories import ISessionRepository, SessionInfo

router = APIRouter(prefix="/sessions", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    user_id: str
    model_key: str
    strategy_type: str = "sliding_window_summary"
    system_prompt: str = ""
    title: str = "Новая сессия"
    id: str | None = None


@router.get("/{session_id}", response_model=None)
async def get_session(
    session_id: str,
    session_repo: Annotated[ISessionRepository, Depends(get_session_repo)],
) -> SessionInfo:
    session = await session_repo.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("", response_model=None, status_code=201)
async def create_session(
    body: CreateSessionRequest,
    session_repo: Annotated[ISessionRepository, Depends(get_session_repo)],
) -> SessionInfo:
    return await session_repo.create(
        user_id=body.user_id,
        model_key=body.model_key,
        strategy_type=body.strategy_type,
        system_prompt=body.system_prompt,
        title=body.title,
        session_id=body.id,
    )


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    session_repo: Annotated[ISessionRepository, Depends(get_session_repo)],
) -> None:
    session = await session_repo.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    await session_repo.delete(session_id)
