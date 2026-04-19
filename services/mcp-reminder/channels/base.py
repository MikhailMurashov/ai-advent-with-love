from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models import Notification


class NotificationChannel(ABC):
    name: str
    description: str

    @abstractmethod
    async def send(self, notification: "Notification") -> bool: ...
