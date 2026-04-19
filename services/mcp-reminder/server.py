from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Annotated

from fastmcp import FastMCP, Context
from pydantic import Field
from starlette.responses import JSONResponse

from channels import channel_registry
from database import init_db
from models import Notification
import repository
from scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app):
    await init_db()
    start_scheduler()

    yield

    stop_scheduler()


mcp = FastMCP(name="MCP Reminder Server", lifespan=lifespan)


@mcp.resource("notifications://channels")
async def available_channels() -> dict:
    return {
        "channels": [
            {
                "name": ch.name,
                "description": ch.description,
                "available": True,
            }
            for ch in channel_registry.values()
        ]
    }


@mcp.tool(
    description=(
        "Создаёт одноразовое уведомление. "
        "Перед созданием прочитай ресурс `notifications://channels`, чтобы узнать доступные каналы"
    ),
)
async def create_one_shoot_notification(
    text: Annotated[str, Field(description="Текст уведомления")],
    scheduled_at: Annotated[str, Field(description="ISO datetime для уведомления")],
    ctx: Context,
    channel: Annotated[str, Field(description="Имя канала")] = "webhook",
):
    if channel not in channel_registry:
        raise ValueError(f"Канал '{channel}' не найден. Доступные: {list(channel_registry.keys())}")

    notification = Notification(
        id=str(uuid.uuid4()),
        text=text,
        channel=channel,
        next_run_at=datetime.fromisoformat(scheduled_at).astimezone(timezone.utc),
        status="pending",
        created_at=datetime.now(timezone.utc).isoformat(),
        is_periodic=False,
    )
    await repository.create(notification)
    await ctx.info(f"Created notification {notification.id}")


@mcp.tool(
    description=(
        "Создаёт периодическое уведомление. "
        "Перед созданием прочитай ресурс `notifications://channels`, чтобы узнать доступные каналы"
    ),
)
async def create_periodic_notification(
    text: Annotated[str, Field(description="Текст уведомления")],
    interval_seconds: Annotated[int, Field(description="Интервал в секундах")],
    ctx: Context,
    channel: Annotated[str, Field(description="Имя канала (например: webhook)")] = "webhook",
):
    if channel not in channel_registry:
        raise ValueError(f"Канал '{channel}' не найден. Доступные: {list(channel_registry.keys())}")
    if not interval_seconds or interval_seconds <= 0:
        raise ValueError("interval_seconds должен быть положительным числом")

    now = datetime.now(timezone.utc)
    notification = Notification(
        id=str(uuid.uuid4()),
        text=text,
        channel=channel,
        is_periodic=True,
        interval_seconds=interval_seconds,
        next_run_at=now,
        status="pending",
        created_at=now.isoformat(),
    )
    await repository.create(notification)
    await ctx.info(f"Created notification {notification.id}")


@mcp.tool(description="Возвращает список уведомлений на отправку")
async def list_pending_notifications() -> list[dict]:
    items = await repository.list_notifications("pending")
    return [n.model_dump() for n in items]


@mcp.tool(description="Возвращает список отправленных уведомлений")
async def list_sent_notifications() -> list[dict]:
    items = await repository.list_notifications("sent")
    return [n.model_dump() for n in items]



@mcp.tool(description="Отменяет уведомление по ID")
async def delete_notification(
    notification_id: Annotated[str, Field(description="ID уведомления")],
):
    ok = await repository.cancel(notification_id)
    if not ok:
        raise ValueError(f"Уведомление {notification_id} не найдено")


@mcp.tool(description="Возвращает полную запись уведомления по ID")
async def get_notification_status(
    notification_id: Annotated[str, Field(description="ID уведомления")],
) -> dict:
    notification = await repository.get_by_id(notification_id)
    if notification is None:
        raise ValueError(f"Уведомление {notification_id} не найдено")
    return notification.model_dump()


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "ok", "service": "mcp-reminder"})
