from __future__ import annotations

import aiosqlite

DB_PATH = "/app/data/notifications.sqlite"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS notifications (
    id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    channel TEXT NOT NULL,
    is_periodic INTEGER NOT NULL DEFAULT 0,
    interval_seconds INTEGER,
    scheduled_at TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL
)
"""


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_TABLE_SQL)
        await db.commit()


def get_db_path() -> str:
    return DB_PATH
