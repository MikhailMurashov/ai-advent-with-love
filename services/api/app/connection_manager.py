from __future__ import annotations

import json
import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    def register(self, ws: WebSocket) -> None:
        self._connections.append(ws)
        logger.info("connection_manager: registered ws, total=%d", len(self._connections))

    def unregister(self, ws: WebSocket) -> None:
        try:
            self._connections.remove(ws)
        except ValueError:
            pass
        logger.info("connection_manager: unregistered ws, total=%d", len(self._connections))

    async def send_notification(self, text: str) -> bool:
        """Send notification to the first active connection. Returns False if none."""
        if not self._connections:
            return False
        ws = self._connections[0]
        try:
            await ws.send_text(json.dumps({"type": "notification", "content": text}, ensure_ascii=False))
            return True
        except Exception:
            logger.exception("connection_manager: failed to send notification, removing connection")
            self.unregister(ws)
            return False


manager = ConnectionManager()
