from __future__ import annotations

from dataclasses import dataclass, field
from typing import AsyncGenerator, Protocol, runtime_checkable


@dataclass
class ChatEvent:
    type: str  # "token" | "tool_call" | "tool_result" | "tool_step" | "done" | "error"
    content: str = ""
    name: str = ""
    args: dict = field(default_factory=dict)
    tool_call_id: str = ""
    stats: dict = field(default_factory=dict)
    message: str = ""


@runtime_checkable
class ILLMClient(Protocol):
    async def stream_chat(
        self,
        messages: list[dict],
        tools: list[dict],
        **params,
    ) -> AsyncGenerator[ChatEvent, None]:
        ...
