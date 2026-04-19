from __future__ import annotations

import aiosqlite
from models import Notification
from database import get_db_path


def _row_to_notification(row: aiosqlite.Row) -> Notification:
    return Notification(
        id=row[0],
        text=row[1],
        channel=row[2],
        is_periodic=bool(row[3]),
        interval_seconds=row[4],
        scheduled_at=row[5],
        status=row[6],
        created_at=row[7],
    )


async def create(notification: Notification) -> Notification:
    async with aiosqlite.connect(get_db_path()) as db:
        await db.execute(
            """
            INSERT INTO notifications
                (id, text, channel, is_periodic, interval_seconds, scheduled_at, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                notification.id,
                notification.text,
                notification.channel,
                int(notification.is_periodic),
                notification.interval_seconds,
                notification.scheduled_at,
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
                "SELECT id, text, channel, is_periodic, interval_seconds, scheduled_at, status, created_at "
                "FROM notifications WHERE status = ? ORDER BY created_at DESC",
                (status,),
            )
        else:
            cursor = await db.execute(
                "SELECT id, text, channel, is_periodic, interval_seconds, scheduled_at, status, created_at "
                "FROM notifications ORDER BY created_at DESC"
            )
        rows = await cursor.fetchall()
    return [_row_to_notification(r) for r in rows]


async def get_by_id(notification_id: str) -> Notification | None:
    async with aiosqlite.connect(get_db_path()) as db:
        cursor = await db.execute(
            "SELECT id, text, channel, is_periodic, interval_seconds, scheduled_at, status, created_at "
            "FROM notifications WHERE id = ?",
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
