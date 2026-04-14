from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import httpx
import websockets


@dataclass
class WSEvent:
    type: str
    content: str = ""
    name: str = ""
    args: dict | None = None
    tool_call_id: str = ""
    stats: dict | None = None
    message: str = ""


class APIClient:
    def __init__(self, base_url: str = "http://api:8000") -> None:
        self._base_url = base_url.rstrip("/")
        self._ws_base = self._base_url.replace("http://", "ws://").replace(
            "https://", "wss://"
        )

    async def get_or_create_user(self, username: str) -> dict:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{self._base_url}/users/{username}")
            resp.raise_for_status()
            return resp.json()

    async def get_sessions(self, user_id: str) -> list[dict]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{self._base_url}/users/{user_id}/sessions")
            resp.raise_for_status()
            return resp.json()

    async def get_session(self, session_id: str) -> dict | None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{self._base_url}/sessions/{session_id}")
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()

    async def create_session(
        self,
        user_id: str,
        model_key: str,
        strategy_type: str = "sliding_window_summary",
        system_prompt: str = "",
        title: str = "Новая сессия",
        session_id: str | None = None,
    ) -> dict:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self._base_url}/sessions",
                json={
                    "user_id": user_id,
                    "model_key": model_key,
                    "strategy_type": strategy_type,
                    "system_prompt": system_prompt,
                    "title": title,
                    "id": session_id,
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def delete_session(self, session_id: str) -> None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.delete(f"{self._base_url}/sessions/{session_id}")
            resp.raise_for_status()

    async def stream_chat(
        self,
        session_id: str,
        username: str,
        content: str,
        params: dict | None = None,
    ) -> AsyncGenerator[WSEvent, None]:
        url = f"{self._ws_base}/ws/chat/{session_id}?username={username}"
        async with websockets.connect(url) as ws:
            await ws.send(
                json.dumps(
                    {"content": content, "params": params or {}},
                    ensure_ascii=False,
                )
            )
            async for raw in ws:
                data = json.loads(raw)
                event = WSEvent(
                    type=data.get("type", ""),
                    content=data.get("content", ""),
                    name=data.get("name", ""),
                    args=data.get("args"),
                    tool_call_id=data.get("tool_call_id", ""),
                    stats=data.get("stats"),
                    message=data.get("message", ""),
                )
                yield event
                if event.type in ("done", "error"):
                    break
