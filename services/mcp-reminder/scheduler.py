from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from channels import channel_registry
import repository

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def dispatch() -> None:
    due = await repository.get_due_notifications()
    for notification in due:
        channel = channel_registry.get(notification.channel)
        if channel is None:
            logger.warning("Channel '%s' not found for notification %s", notification.channel, notification.id)
            continue
        try:
            success = await channel.send(notification)
        except Exception:
            logger.exception("Failed to send notification %s", notification.id)
            continue
        if success:
            if notification.is_periodic:
                next_run = datetime.now(timezone.utc) + timedelta(seconds=notification.interval_seconds)
                await repository.reschedule(notification.id, next_run)
            else:
                await repository.mark_as_sent(notification.id)


def start_scheduler() -> None:
    scheduler.add_job(dispatch, trigger=IntervalTrigger(seconds=10))
    scheduler.start()

def stop_scheduler() -> None:
    scheduler.shutdown()

