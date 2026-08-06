"""
APScheduler wiring.

AsyncIOScheduler (not the plain BackgroundScheduler) because our job
functions are async — this lets APScheduler schedule coroutines directly on
FastAPI's own event loop instead of spinning up separate OS threads.

start_scheduler()/stop_scheduler() are called from main.py's lifespan
context — one process, one scheduler instance, no external broker.
"""

import logging
import uuid
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from app.scheduler import jobs

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def start_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.add_job(jobs.send_morning_message, "cron", hour=6, minute=0, id="morning_message", replace_existing=True)
    scheduler.add_job(jobs.send_water_reminder, "interval", hours=2, minutes=30, id="water_reminder", replace_existing=True)
    scheduler.add_job(jobs.send_lunch_reminder, "cron", hour=15, minute=0, id="lunch_reminder", replace_existing=True)
    scheduler.add_job(jobs.send_coffee_reminder, "cron", hour=17, minute=0, id="coffee_reminder", replace_existing=True)
    scheduler.add_job(jobs.send_dinner_reminder, "cron", hour=19, minute=0, id="dinner_reminder", replace_existing=True)
    scheduler.add_job(jobs.send_sleep_reminder, "cron", hour=22, minute=0, id="sleep_reminder", replace_existing=True)

    scheduler.start()
    logger.info("Scheduler started with %d jobs.", len(scheduler.get_jobs()))


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")

def schedule_sleep_check(reminder_id: int, run_in_minutes: int) -> None:
    """
    One-off follow-up job for the sleep-confirmation retry loop. Uses a
    DateTrigger (fires exactly once at a computed timestamp), not an
    interval trigger — an interval trigger would keep firing forever on its
    own schedule, whereas here check_sleep_status() itself decides whether
    to call this function again, turning a single one-shot job into a
    bounded, explicitly-controlled retry chain.
    """
    run_at = datetime.now() + timedelta(minutes=run_in_minutes)
    scheduler.add_job(
        jobs.check_sleep_status,
        trigger=DateTrigger(run_date=run_at),
        args=[reminder_id],
        id=f"sleep_check_{reminder_id}_{uuid.uuid4().hex[:8]}",
        max_instances=1,
    )
