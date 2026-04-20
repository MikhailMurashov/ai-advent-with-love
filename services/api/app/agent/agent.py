from __future__ import annotations

import json
import logging
import time
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

from app.agent.memory import Invariants, LongTermMemory, Personalization, WorkingMemory
from app.agent.mcp_client import MCPClient
from app.agent.strategies import BaseStrategy, SlidingWindowSummaryStrategy
from app.interfaces.llm import ChatEvent, ILLMClient
from app.interfaces.repositories import IMemoryRepository, ISessionRepository, Message

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Agent:
    def __init__(
        self,
        llm: ILLMClient,
        strategy: BaseStrategy,
        memory_repo: IMemoryRepository,
        session_repo: ISessionRepository,
        mcp_client: MCPClient,
    ) -> None:
        self._llm = llm
        self._strategy = strategy
        self._memory_repo = memory_repo
        self._session_repo = session_repo
        self._mcp_client = mcp_client

    def _build_full_system_prompt(
        self,
        base_system_prompt: str,
        working: WorkingMemory,
        long_term: LongTermMemory,
        personalization: Personalization,
        invariants: Invariants,
    ) -> str:
        parts: list[str] = [f"Текущее время: {_now()}"]

        inv = invariants.to_context_string()
        if inv:
            parts.append(inv)

        pers = personalization.to_context_string()
        if pers:
            parts.append(f"## Персонализация\n{pers}")

        if base_system_prompt:
            parts.append(base_system_prompt)

        lt = long_term.to_context_string()
        if lt:
            parts.append(f"## Долгосрочная память\n{lt}")

        wm = working.to_context_string()
        if wm:
            parts.append(f"## Рабочая память сессии\n{wm}")

        return "\n\n".join(parts)

    async def _do_summarize(self, session_id: str, model: str, **params) -> None:
        if not isinstance(self._strategy, SlidingWindowSummaryStrategy):
            return
        if not self._strategy.should_summarize():
            return

        new_msgs = self._strategy.get_summary_context()
        if not new_msgs:
            return

        convo_text = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in new_msgs
        )
        current_summary = self._strategy.summary
        if current_summary:
            prompt = (
                f"Обнови саммари беседы, добавив новые сообщения.\n\n"
                f"Текущий саммари:\n{current_summary}\n\n"
                f"Новые сообщения:\n{convo_text}\n\n"
                f"Дай очень краткий обновлённый саммари, сохранив только самые важные факты."
            )
        else:
            prompt = (
                f"Очень кратко изложи суть следующей беседы, "
                f"сохранив только самые ключевые факты:\n\n{convo_text}"
            )

        try:
            summary_text = ""
            async for event in self._llm.stream_chat(
                messages=[{"role": "user", "content": prompt}],
                tools=[],
                model=model,
                **params,
            ):
                if event.type == "token":
                    summary_text += event.content
            self._strategy.apply_summary(summary_text)
        except Exception as e:
            logger.warning("agent: summarization failed: %s", e)

    async def stream_chat(
        self,
        session_id: str,
        user_id: str,
        content: str,
        params: dict,
    ) -> AsyncGenerator[ChatEvent, None]:
        model = params.get("model", "")
        session_info = await self._session_repo.get(session_id)
        if session_info is None:
            yield ChatEvent(type="error", message=f"Session {session_id} not found")
            return

        if not model:
            model = session_info.model_key

        # Load memory
        working = WorkingMemory()
        working.load(await self._memory_repo.get_working(session_id))

        long_term = LongTermMemory()
        long_term.load(await self._memory_repo.get_long_term(user_id))

        personalization = Personalization()
        personalization.load(await self._memory_repo.get_personalization(user_id))

        invariants = Invariants()
        invariants.load(await self._memory_repo.get_invariants(user_id))

        full_system_prompt = self._build_full_system_prompt(
            session_info.system_prompt,
            working,
            long_term,
            personalization,
            invariants,
        )

        # Restore history from DB into strategy
        messages_db = await self._session_repo.get_messages(session_id)
        self._strategy._history = []
        for msg in messages_db:
            if msg.role == "assistant":
                entry: dict = {"role": "assistant", "content": msg.content}
                if msg.tool_calls:
                    try:
                        entry["tool_calls"] = json.loads(msg.tool_calls)
                    except json.JSONDecodeError:
                        pass
                self._strategy._history.append(entry)
            elif msg.role == "tool":
                # tool_calls field stores {"id": "...", "name": "..."} (new) or just id (legacy)
                tool_call_id = ""
                tool_name = ""
                if msg.tool_calls:
                    try:
                        meta = json.loads(msg.tool_calls)
                        if isinstance(meta, dict):
                            tool_call_id = meta.get("id", "")
                            tool_name = meta.get("name", "")
                        else:
                            tool_call_id = msg.tool_calls
                    except (json.JSONDecodeError, TypeError):
                        tool_call_id = msg.tool_calls
                entry: dict = {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": msg.content,
                }
                if tool_name:
                    entry["name"] = tool_name
                self._strategy._history.append(entry)
            elif msg.role == "user":
                self._strategy._history.append({"role": "user", "content": msg.content})

        # Save user message
        user_msg = Message(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="user",
            content=content,
            tool_calls=None,
            tokens_prompt=None,
            tokens_completion=None,
            elapsed_s=None,
            created_at=_now(),
        )
        await self._session_repo.save_message(user_msg)
        self._strategy.add_message("user", content)

        # Build messages for LLM
        if isinstance(self._strategy, SlidingWindowSummaryStrategy):
            llm_messages = self._strategy.build_messages(full_system_prompt)
        else:
            llm_messages = []
            if full_system_prompt:
                llm_messages.append({"role": "system", "content": full_system_prompt})
            llm_messages.extend(self._strategy.get_context())

        tools = self._mcp_client.get_tools_schema()
        logger.info("tools available (%d):", len(tools))
        for _t in tools:
            _fn = _t["function"]
            _params = list((_fn.get("parameters") or {}).get("properties", {}).keys())
            logger.info("  %s — %s  [params: %s]", _fn["name"], _fn["description"], _params)

        # Tool calling loop
        t0 = time.time()
        total_prompt_tokens = 0
        total_completion_tokens = 0
        assistant_content = ""
        iteration = 0

        while True:
            iteration += 1
            pending_tool_calls: list[dict] = []
            current_content = ""
            buffered_token_events: list[ChatEvent] = []

            async for event in self._llm.stream_chat(
                messages=llm_messages,
                tools=tools,
                model=model,
                **{k: v for k, v in params.items() if k != "model"},
            ):
                if event.type == "token":
                    current_content += event.content
                    buffered_token_events.append(event)
                elif event.type == "tool_call":
                    pending_tool_calls.append(
                        {
                            "id": event.tool_call_id,
                            "name": event.name,
                            "args": event.args,
                        }
                    )
                elif event.type == "done":
                    total_prompt_tokens += event.stats.get("prompt_tokens", 0)
                    total_completion_tokens += event.stats.get("completion_tokens", 0)
                elif event.type == "error":
                    yield event
                    return

            if pending_tool_calls:
                for tc in pending_tool_calls:
                    logger.info(
                        "agent[iter=%d]: tool_call %r args=%s",
                        iteration, tc["name"], json.dumps(tc["args"], ensure_ascii=False),
                    )

            if not pending_tool_calls:
                logger.info(
                    "agent[iter=%d]: final response len=%d chars",
                    iteration, len(current_content),
                )
                # No tool calls: stream the buffered tokens and finish
                for te in buffered_token_events:
                    yield te
                assistant_content = current_content
                break

            # Build tool_calls list for assistant message
            tool_calls_list = [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": json.dumps(tc["args"]),
                    },
                }
                for tc in pending_tool_calls
            ]

            # Save assistant message with tool_calls to DB
            await self._session_repo.save_message(
                Message(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    role="assistant",
                    content=current_content or None,
                    tool_calls=json.dumps(tool_calls_list, ensure_ascii=False),
                    tokens_prompt=None,
                    tokens_completion=None,
                    elapsed_s=None,
                    created_at=_now(),
                )
            )

            # Execute tool calls and yield a single tool_step per call (input + output together)
            tool_results: list[dict] = []
            for tc in pending_tool_calls:
                result = await self._mcp_client.call_tool(tc["name"], tc["args"])
                tool_results.append(
                    {
                        "tool_call_id": tc["id"],
                        "name": tc["name"],
                        "result": result,
                    }
                )
                # Save tool result to DB; encode both id and name for later restore
                await self._session_repo.save_message(
                    Message(
                        id=str(uuid.uuid4()),
                        session_id=session_id,
                        role="tool",
                        content=result,
                        tool_calls=json.dumps({"id": tc["id"], "name": tc["name"]}),
                        tokens_prompt=None,
                        tokens_completion=None,
                        elapsed_s=None,
                        created_at=_now(),
                    )
                )
                yield ChatEvent(
                    type="tool_step",
                    name=tc["name"],
                    args=tc["args"],
                    tool_call_id=tc["id"],
                    content=result,
                )

            # Add assistant turn with tool_calls to llm_messages
            llm_messages.append(
                {
                    "role": "assistant",
                    "content": current_content or None,
                    "tool_calls": tool_calls_list,
                }
            )
            # Add tool results to llm_messages
            for tr in tool_results:
                llm_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tr["tool_call_id"],
                        "name": tr["name"],
                        "content": tr["result"],
                    }
                )

        elapsed_s = time.time() - t0

        # Save final assistant message (no tool_calls — those were saved per-pass)
        asst_msg = Message(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="assistant",
            content=assistant_content,
            tool_calls=None,
            tokens_prompt=total_prompt_tokens or None,
            tokens_completion=total_completion_tokens or None,
            elapsed_s=elapsed_s,
            created_at=_now(),
        )
        await self._session_repo.save_message(asst_msg)
        await self._session_repo.update_timestamp(session_id)

        self._strategy.add_message("assistant", assistant_content)

        # Summarize if needed
        await self._do_summarize(session_id, model)

        yield ChatEvent(
            type="done",
            stats={
                "prompt_tokens": total_prompt_tokens,
                "completion_tokens": total_completion_tokens,
                "elapsed_s": elapsed_s,
            },
        )
