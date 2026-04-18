from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class User:
    id: str
    username: str
    created_at: str


@dataclass
class SessionInfo:
    id: str
    user_id: str
    title: str
    strategy_type: str
    model_key: str
    system_prompt: str
    created_at: str
    updated_at: str


@dataclass
class Message:
    id: str
    session_id: str
    role: str
    content: str
    tool_calls: str | None
    tokens_prompt: int | None
    tokens_completion: int | None
    elapsed_s: float | None
    created_at: str


@runtime_checkable
class IUserRepository(Protocol):
    async def get_or_create(self, username: str) -> User:
        ...


@runtime_checkable
class ISessionRepository(Protocol):
    async def get(self, session_id: str) -> SessionInfo | None:
        ...

    async def create(
        self,
        user_id: str,
        model_key: str,
        strategy_type: str = "sliding_window_summary",
        system_prompt: str = "",
        title: str = "Новая сессия",
        session_id: str | None = None,
    ) -> SessionInfo:
        ...

    async def list_by_user(self, user_id: str) -> list[SessionInfo]:
        ...

    async def delete(self, session_id: str) -> None:
        ...

    async def save_message(self, msg: Message) -> None:
        ...

    async def get_messages(self, session_id: str) -> list[Message]:
        ...

    async def update_timestamp(self, session_id: str) -> None:
        ...


@runtime_checkable
class IMemoryRepository(Protocol):
    async def get_working(self, session_id: str) -> dict[str, str]:
        ...

    async def set_working(self, session_id: str, key: str, value: str) -> None:
        ...

    async def get_long_term(self, user_id: str) -> dict[str, str]:
        ...

    async def set_long_term(self, user_id: str, key: str, value: str) -> None:
        ...

    async def get_personalization(self, user_id: str) -> str:
        ...

    async def set_personalization(self, user_id: str, content: str) -> None:
        ...

    async def get_invariants(self, user_id: str) -> list[str]:
        ...

    async def set_invariants(self, user_id: str, rules: list[str]) -> None:
        ...


@dataclass
class MCPServerInfo:
    id: str
    name: str
    url: str
    description: str
    enabled: bool
    created_at: str


class IMCPServerRepository(Protocol):
    async def list_all(self) -> list[MCPServerInfo]: ...
    async def list_enabled(self) -> list[MCPServerInfo]: ...
    async def get(self, server_id: str) -> MCPServerInfo | None: ...
    async def get_by_name(self, name: str) -> MCPServerInfo | None: ...
    async def create(self, name: str, url: str, description: str = "", enabled: bool = True) -> MCPServerInfo: ...
    async def delete(self, server_id: str) -> None: ...
    async def set_enabled(self, server_id: str, enabled: bool) -> MCPServerInfo | None: ...
