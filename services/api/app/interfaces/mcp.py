from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class ToolSchema:
    name: str
    description: str
    parameters: dict
    few_shot_examples: list | None = None
    return_parameters: dict | None = None


@runtime_checkable
class IMCPTransport(Protocol):
    async def list_tools(self) -> list[ToolSchema]:
        ...

    async def call_tool(self, name: str, args: dict) -> str:
        ...
