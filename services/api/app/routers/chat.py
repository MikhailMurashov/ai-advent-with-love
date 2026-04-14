from __future__ import annotations

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.agent.agent import Agent
from app.agent.mcp_client import MCPClient
from app.agent.strategies import make_strategy
from app.db.database import async_session_factory
from app.db.repositories import (
    SQLiteMemoryRepository,
    SQLiteSessionRepository,
    SQLiteUserRepository,
)
from app.dependencies import get_mcp_client
from app.infrastructure.llm import LiteLLMClient

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


@router.websocket("/ws/chat/{session_id}")
async def websocket_chat(
    websocket: WebSocket,
    session_id: str,
) -> None:
    await websocket.accept()
    username: str = websocket.query_params.get("username", "")

    try:
        async with async_session_factory() as db:
            user_repo = SQLiteUserRepository(db)
            session_repo = SQLiteSessionRepository(db)
            memory_repo = SQLiteMemoryRepository(db)

            # Resolve user
            if not username:
                await websocket.send_text(
                    json.dumps({"type": "error", "message": "username required"})
                )
                await websocket.close()
                return

            user = await user_repo.get_or_create(username)
            session_info = await session_repo.get(session_id)
            if session_info is None:
                await websocket.send_text(
                    json.dumps({"type": "error", "message": f"session {session_id} not found"})
                )
                await websocket.close()
                return

            mcp_client: MCPClient = get_mcp_client()
            llm = LiteLLMClient()
            strategy = make_strategy(session_info.strategy_type)
            agent = Agent(
                llm=llm,
                strategy=strategy,
                memory_repo=memory_repo,
                session_repo=session_repo,
                mcp_client=mcp_client,
            )

            while True:
                try:
                    raw = await websocket.receive_text()
                except WebSocketDisconnect:
                    break

                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    await websocket.send_text(
                        json.dumps({"type": "error", "message": "invalid JSON"})
                    )
                    continue

                content: str = data.get("content", "")
                params: dict = data.get("params", {})

                if not content:
                    continue

                try:
                    async for event in agent.stream_chat(
                        session_id=session_id,
                        user_id=user.id,
                        content=content,
                        params=params,
                    ):
                        payload: dict = {"type": event.type}
                        if event.content:
                            payload["content"] = event.content
                        if event.name:
                            payload["name"] = event.name
                        if event.args:
                            payload["args"] = event.args
                        if event.tool_call_id:
                            payload["tool_call_id"] = event.tool_call_id
                        if event.stats:
                            payload["stats"] = event.stats
                        if event.message:
                            payload["message"] = event.message
                        await websocket.send_text(json.dumps(payload, ensure_ascii=False))
                except Exception as e:
                    logger.exception("chat: unhandled error in stream_chat")
                    await websocket.send_text(
                        json.dumps({"type": "error", "message": str(e)})
                    )

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.exception("chat: websocket handler error")
        try:
            await websocket.send_text(
                json.dumps({"type": "error", "message": str(e)})
            )
        except Exception:
            pass
