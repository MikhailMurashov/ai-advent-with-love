"""Chainlit UI for the LLM agent."""
from __future__ import annotations

import os

import chainlit as cl

import data_layer  # noqa: F401 — registers @cl.data_layer

from api_client import APIClient

API_URL = os.environ.get("API_URL", "http://api:8000")
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "gigachat/GigaChat-2-Pro")


def _make_client() -> APIClient:
    return APIClient(base_url=API_URL)


@cl.header_auth_callback
def header_auth_callback(headers: dict) -> cl.User:  # noqa: ARG001
    """No login page — everyone is 'guest'."""
    return cl.User(identifier="guest")


@cl.on_chat_start
async def on_chat_start() -> None:
    username = "guest"
    thread_id: str = cl.context.session.thread_id

    client = _make_client()

    try:
        user_data = await client.get_or_create_user(username)
        user_id: str = user_data["id"]
    except Exception as e:
        await cl.Message(content=f"Ошибка подключения к API: {e}").send()
        return

    cl.user_session.set("user_id", user_id)
    cl.user_session.set("username", username)
    cl.user_session.set("client", client)

    _models = [
        "gigachat/GigaChat-2",
        "gigachat/GigaChat-2-Pro",
        "gigachat/GigaChat-2-Max",
    ]
    _model_index = _models.index(DEFAULT_MODEL) if DEFAULT_MODEL in _models else 0

    settings = await cl.ChatSettings(
        [
            cl.input_widget.Select(
                id="model",
                label="Модель",
                values=_models,
                initial_index=_model_index,
            ),
            cl.input_widget.Select(
                id="strategy",
                label="Стратегия",
                values=["sliding_window_summary", "branching"],
                initial_index=0,
            ),
            cl.input_widget.Slider(
                id="temperature",
                label="Температура",
                initial=0.7,
                min=0.0,
                max=2.0,
                step=0.1,
            ),
            cl.input_widget.TextInput(
                id="system_prompt",
                label="System prompt",
                initial="Ты полезный ИИ-ассистент.",
            ),
        ]
    ).send()

    cl.user_session.set("settings", settings)
    cl.user_session.set("thread_id", thread_id)
    # session_id будет создан при первом сообщении


@cl.on_chat_resume
async def on_chat_resume(thread: cl.types.ThreadDict) -> None:
    """Restore state when user resumes a thread from the sidebar."""
    client = _make_client()
    username = "guest"

    try:
        user_data = await client.get_or_create_user(username)
        user_id: str = user_data["id"]
    except Exception as e:
        await cl.Message(content=f"Ошибка подключения к API: {e}").send()
        return

    cl.user_session.set("user_id", user_id)
    cl.user_session.set("username", username)
    cl.user_session.set("client", client)
    cl.user_session.set("session_id", thread["id"])
    cl.user_session.set("settings", {})


@cl.on_settings_update
async def on_settings_update(settings: dict) -> None:
    cl.user_session.set("settings", settings)


@cl.on_message
async def on_message(message: cl.Message) -> None:
    client: APIClient = cl.user_session.get("client")
    session_id: str | None = cl.user_session.get("session_id")
    username: str = cl.user_session.get("username", "guest")
    settings: dict = cl.user_session.get("settings") or {}

    if not session_id:
        # Создаём сессию при первом сообщении
        thread_id: str = cl.user_session.get("thread_id")
        user_id: str = cl.user_session.get("user_id")
        try:
            session = await client.create_session(
                user_id=user_id,
                model_key=settings.get("model", DEFAULT_MODEL),
                strategy_type=settings.get("strategy", "sliding_window_summary"),
                system_prompt=settings.get("system_prompt", ""),
                title=message.content[:60],
                session_id=thread_id,
            )
            session_id = session["id"]
            cl.user_session.set("session_id", session_id)
        except Exception as e:
            await cl.Message(content=f"Ошибка создания сессии: {e}").send()
            return

    params: dict = {}
    model = settings.get("model", DEFAULT_MODEL)
    if model:
        params["model"] = model
    temperature = settings.get("temperature")
    if temperature is not None:
        params["temperature"] = float(temperature)

    response_msg = cl.Message(content="")
    await response_msg.send()

    try:
        async for event in client.stream_chat(
            session_id=session_id,
            username=username,
            content=message.content,
            params=params,
        ):
            if event.type == "token":
                await response_msg.stream_token(event.content)
            elif event.type == "tool_call":
                await cl.Message(
                    content=f"🔧 Вызов инструмента: **{event.name}**\n```json\n{event.args}\n```",
                    author="tool",
                ).send()
            elif event.type == "tool_result":
                await cl.Message(
                    content=f"✅ Результат **{event.name}**:\n{event.content}",
                    author="tool",
                ).send()
            elif event.type == "error":
                await cl.Message(content=f"Ошибка: {event.message}").send()
                break
            elif event.type == "done":
                await response_msg.update()
    except Exception as e:
        await cl.Message(content=f"Ошибка соединения: {e}").send()
