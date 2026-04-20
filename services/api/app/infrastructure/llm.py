from __future__ import annotations

import json
import logging
import uuid
from collections.abc import AsyncGenerator

import litellm
from litellm.llms.gigachat.chat.transformation import GigaChatConfig

from app.interfaces.llm import ChatEvent

logger = logging.getLogger(__name__)


def _patch_gigachat_transform() -> None:
    """
    Patch litellm's GigaChat transformer to:
    1. Preserve 'name' in role='function' messages (required by GigaChat API).
    2. Pass through 'few_shot_examples' and 'return_parameters' in functions array.

    litellm universally removes the 'name' field from all messages, but GigaChat
    requires it in function-result messages to identify which function returned the result.
    """
    original = GigaChatConfig._transform_messages

    def patched(self, messages):  # type: ignore[override]
        # Collect tool_call_id → name mapping before transformation strips names
        tc_name: dict[str, str] = {}
        for msg in messages:
            if msg.get("role") == "tool":
                tid = msg.get("tool_call_id", "")
                name = msg.get("name", "")
                if tid and name:
                    tc_name[tid] = name

        transformed = original(self, messages)

        for t_msg, o_msg in zip(transformed, messages):
            if t_msg.get("role") == "function":
                tid = o_msg.get("tool_call_id", "")
                name = tc_name.get(tid) or o_msg.get("name", "")
                if name:
                    t_msg["name"] = name
                # Remove tool_call_id — GigaChat doesn't use it
                t_msg.pop("tool_call_id", None)

        return transformed

    GigaChatConfig._transform_messages = patched  # type: ignore[method-assign]


_patch_gigachat_transform()


def _gigachat_functions(tools: list[dict]) -> list[dict]:
    """
    Convert OpenAI-style tools to GigaChat functions format,
    preserving GigaChat-specific extra fields (few_shot_examples, return_parameters).
    litellm's built-in conversion drops these fields.
    """
    fns = []
    for tool in tools:
        if tool.get("type") != "function":
            continue
        func = tool["function"]
        fn: dict = {
            "name": func.get("name", ""),
            "description": func.get("description", ""),
            "parameters": func.get("parameters", {}),
        }
        for extra in ("few_shot_examples", "return_parameters"):
            if extra in func:
                fn[extra] = func[extra]
        fns.append(fn)
    return fns


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
            if is_gigachat:
                # Pass as 'functions' to bypass litellm's conversion and keep extra fields
                call_kwargs["functions"] = _gigachat_functions(tools)
            else:
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
