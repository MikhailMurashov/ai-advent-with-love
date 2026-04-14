from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import get_session_repo, get_user_repo
from app.interfaces.repositories import ISessionRepository, IUserRepository, SessionInfo, User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{username}", response_model=None)
async def get_or_create_user(
    username: str,
    user_repo: Annotated[IUserRepository, Depends(get_user_repo)],
) -> User:
    return await user_repo.get_or_create(username)


@router.get("/{user_id}/sessions", response_model=None)
async def list_sessions(
    user_id: str,
    session_repo: Annotated[ISessionRepository, Depends(get_session_repo)],
) -> list[SessionInfo]:
    return await session_repo.list_by_user(user_id)
