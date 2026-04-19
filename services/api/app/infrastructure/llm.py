from __future__ import annotations

import json
import logging
import uuid
from collections.abc import AsyncGenerator

import litellm

from app.interfaces.llm import ChatEvent

logger = logging.getLogger(__name__)


class LiteLLMClient:
    """Async streaming LLM client using litellm."""

    async def stream_chat(
        self,
        messages: list[dict],
        tools: list[dict],
        **params,
    ) -> AsyncGenerator[ChatEvent, None]:
        model: str = params.pop("model", "")
        is_gigachat = model.startswith("gigachat/")

        call_kwargs: dict = {
            "model": model,
            "messages": messages,
            "stream": True,
            **params,
        }
        if tools:
            call_kwargs["tools"] = tools
        if is_gigachat:
            call_kwargs["ssl_verify"] = False
            call_kwargs.pop("api_key", None)
        if "timeout" not in call_kwargs:
            call_kwargs["timeout"] = 60

        try:
            logger.info(f"call_kwargs {call_kwargs}")
            response = await litellm.acompletion(**call_kwargs)
        except Exception as e:
            logger.error("llm: completion failed: %s", e)
            yield ChatEvent(type="error", message=str(e))
            return

        full_content = ""
        tool_calls_accumulator: dict[int, dict] = {}
        prompt_tokens = 0
        completion_tokens = 0

        async for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta is None:
                continue

            # Token streaming
            if delta.content:
                full_content += delta.content
                yield ChatEvent(type="token", content=delta.content)

            # Tool call streaming
            if delta.tool_calls:
                for tc_chunk in delta.tool_calls:
                    idx = tc_chunk.index
                    if idx not in tool_calls_accumulator:
                        tool_calls_accumulator[idx] = {
                            "id": tc_chunk.id or str(uuid.uuid4()),
                            "name": "",
                            "args_str": "",
                        }
                    acc = tool_calls_accumulator[idx]
                    if tc_chunk.id:
                        acc["id"] = tc_chunk.id
                    if tc_chunk.function:
                        if tc_chunk.function.name:
                            acc["name"] += tc_chunk.function.name
                        if tc_chunk.function.arguments:
                            acc["args_str"] += tc_chunk.function.arguments

            # Usage stats (last chunk)
            if hasattr(chunk, "usage") and chunk.usage:
                prompt_tokens = chunk.usage.prompt_tokens or 0
                completion_tokens = chunk.usage.completion_tokens or 0

        # Emit tool_call events
        for acc in tool_calls_accumulator.values():
            try:
                args = json.loads(acc["args_str"]) if acc["args_str"] else {}
            except json.JSONDecodeError:
                args = {"raw": acc["args_str"]}
            yield ChatEvent(
                type="tool_call",
                name=acc["name"],
                args=args,
                tool_call_id=acc["id"],
            )

        yield ChatEvent(
            type="done",
            stats={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
            },
        )
