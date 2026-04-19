from __future__ import annotations

from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class Notification(BaseModel):
    id: str
    text: str
    channel: str
    is_periodic: bool
    interval_seconds: int | None = None
    next_run_at: datetime | None = None
    status: Literal["pending", "cancelled", "sent"]
    created_at: str
