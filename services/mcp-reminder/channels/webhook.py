from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

import httpx

from channels.base import NotificationChannel

if TYPE_CHECKING:
    from models import Notification

logger = logging.getLogger(__name__)

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "http://api:8000/webhook/notify")


class WebhookChannel(NotificationChannel):
    name = "webhook"
    description = "Отправка POST-запроса на произвольный URL"

    async def send(self, notification: "Notification") -> bool:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    WEBHOOK_URL,
                    json={"text": notification.text},
                    timeout=5,
                )
                response.raise_for_status()
                return True
        except Exception as exc:
            logger.warning(f"Webhook send failed for notification {notification.id}: {exc}")
            return False
