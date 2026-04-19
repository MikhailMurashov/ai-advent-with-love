from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.connection_manager import manager

router = APIRouter(prefix="/webhook", tags=["webhook"])


class NotifyRequest(BaseModel):
    text: str


@router.post("/notify")
async def notify(body: NotifyRequest) -> dict:
    sent = await manager.send_notification(body.text)
    if not sent:
        raise HTTPException(status_code=404, detail="no active connections")
    return {"ok": True}
