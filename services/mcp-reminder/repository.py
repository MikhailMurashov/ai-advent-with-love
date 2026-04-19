from __future__ import annotations

from datetime import datetime, timezone

import aiosqlite
from models import Notification
from database import get_db_path

COLUMNS = "id, text, channel, is_periodic, interval_seconds, next_run_at, status, created_at"


def _row_to_notification(row: aiosqlite.Row) -> Notification:
    return Notification(
        id=row[0],
        text=row[1],
        channel=row[2],
        is_periodic=bool(row[3]),
        interval_seconds=row[4],
        next_run_at=row[5],
        status=row[6],
        created_at=row[7],
    )


async def create(notification: Notification) -> Notification:
    async with aiosqlite.connect(get_db_path()) as db:
        await db.execute(
            """
            INSERT INTO notifications
                (id, text, channel, is_periodic, interval_seconds, next_run_at, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                notification.id,
                notification.text,
                notification.channel,
                int(notification.is_periodic),
                notification.interval_seconds,
                notification.next_run_at.isoformat() if notification.next_run_at else None,
                notification.status,
                notification.created_at,
            ),
        )
        await db.commit()
    return notification


async def list_notifications(status: str | None = None) -> list[Notification]:
    async with aiosqlite.connect(get_db_path()) as db:
        if status is not None:
            cursor = await db.execute(
                f"SELECT {COLUMNS} FROM notifications WHERE status = ? ORDER BY created_at DESC",
                (status,),
            )
        else:
            cursor = await db.execute(
                f"SELECT {COLUMNS} FROM notifications ORDER BY created_at DESC"
            )
        rows = await cursor.fetchall()
    return [_row_to_notification(r) for r in rows]


async def get_by_id(notification_id: str) -> Notification | None:
    async with aiosqlite.connect(get_db_path()) as db:
        cursor = await db.execute(
            f"SELECT {COLUMNS} FROM notifications WHERE id = ?",
            (notification_id,),
        )
        row = await cursor.fetchone()
    if row is None:
        return None
    return _row_to_notification(row)


async def cancel(notification_id: str) -> bool:
    async with aiosqlite.connect(get_db_path()) as db:
        cursor = await db.execute(
            "UPDATE notifications SET status = 'cancelled' WHERE id = ?",
            (notification_id,),
        )
        await db.commit()
        return cursor.rowcount > 0


async def mark_as_sent(notification_id: str) -> None:
    async with aiosqlite.connect(get_db_path()) as db:
        await db.execute(
            "UPDATE notifications SET status = 'sent' WHERE id = ?",
            (notification_id,),
        )
        await db.commit()


async def get_due_notifications() -> list[Notification]:
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(get_db_path()) as db:
        cursor = await db.execute(
            f"SELECT {COLUMNS} FROM notifications WHERE status = 'pending' AND next_run_at <= ?",
            (now,),
        )
        rows = await cursor.fetchall()
    return [_row_to_notification(r) for r in rows]


async def reschedule(notification_id: str, next_run_at: datetime) -> None:
    async with aiosqlite.connect(get_db_path()) as db:
        await db.execute(
            "UPDATE notifications SET next_run_at = ? WHERE id = ?",
            (next_run_at.isoformat(), notification_id),
        )
        await db.commit()
