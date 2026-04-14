"""Chainlit data layer backed by the API service."""
from __future__ import annotations

import os
from typing import TYPE_CHECKING, Optional

import chainlit as cl
import chainlit.data as cl_data
from chainlit.types import (
    PageInfo,
    PaginatedResponse,
    Pagination,
    ThreadDict,
    ThreadFilter,
)

from api_client import APIClient

if TYPE_CHECKING:
    pass

API_URL = os.environ.get("API_URL", "http://api:8000")


class APIDataLayer(cl_data.BaseDataLayer):
    def __init__(self) -> None:
        self._client = APIClient(base_url=API_URL)

    # ------------------------------------------------------------------ users

    async def get_user(self, identifier: str) -> Optional[cl.PersistedUser]:
        try:
            data = await self._client.get_or_create_user(identifier)
            return cl.PersistedUser(
                id=data["id"],
                identifier=data["username"],
                createdAt=data["created_at"],
            )
        except Exception:
            return None

    async def create_user(self, user: cl.User) -> Optional[cl.PersistedUser]:
        try:
            data = await self._client.get_or_create_user(user.identifier)
            return cl.PersistedUser(
                id=data["id"],
                identifier=data["username"],
                createdAt=data["created_at"],
            )
        except Exception:
            return None

    # ----------------------------------------------------------------- threads

    async def list_threads(
        self, pagination: Pagination, filters: ThreadFilter
    ) -> PaginatedResponse[ThreadDict]:
        sessions: list[dict] = []
        if filters.userId:
            try:
                sessions = await self._client.get_sessions(filters.userId)
            except Exception:
                pass
        threads = [_session_to_thread(s) for s in sessions]
        return PaginatedResponse(
            pageInfo=PageInfo(hasNextPage=False, startCursor=None, endCursor=None),
            data=threads,
        )

    async def get_thread(self, thread_id: str) -> Optional[ThreadDict]:
        try:
            s = await self._client.get_session(thread_id)
            return _session_to_thread(s) if s else None
        except Exception:
            return None

    async def get_thread_author(self, thread_id: str) -> str:
        return "guest"

    async def update_thread(
        self,
        thread_id: str,
        name: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[dict] = None,
        tags: Optional[list[str]] = None,
    ) -> None:
        pass

    async def delete_thread(self, thread_id: str) -> None:
        try:
            await self._client.delete_session(thread_id)
        except Exception:
            pass

    # ------------------------------------------------------------------- steps

    async def create_step(self, step_dict: dict) -> None:
        pass

    async def update_step(self, step_dict: dict) -> None:
        pass

    async def delete_step(self, step_id: str) -> None:
        pass

    # ---------------------------------------------------------------- elements

    async def get_element(self, thread_id: str, element_id: str) -> Optional[dict]:
        return None

    async def create_element(self, element: dict) -> None:
        pass

    async def delete_element(
        self, element_id: str, thread_id: Optional[str] = None
    ) -> None:
        pass

    # ---------------------------------------------------------------- feedback

    async def upsert_feedback(self, feedback) -> str:  # type: ignore[override]
        return ""

    async def delete_feedback(self, feedback_id: str) -> bool:
        return True

    async def build_debug_url(self) -> str:
        return ""

    async def close(self) -> None:
        pass

    async def get_favorite_steps(self, user_id: str) -> list:
        return []


def _session_to_thread(s: dict) -> ThreadDict:
    return ThreadDict(
        id=s["id"],
        createdAt=s["created_at"],
        name=s["title"],
        userId=s["user_id"],
        userIdentifier="guest",
        tags=None,
        metadata={},
        steps=[],
        elements=None,
    )


@cl.data_layer
def get_data_layer() -> APIDataLayer:
    return APIDataLayer()
