from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from channels.base import NotificationChannel

if TYPE_CHECKING:
    from models import Notification

logger = logging.getLogger(__name__)


class WebhookChannel(NotificationChannel):
    name = "webhook"
    description = "Отправка POST-запроса на произвольный URL"

    async def send(self, notification: "Notification") -> bool:
        logger.info(f"[stub] Would send via webhook: {notification.id}")
        return True
