"""
Scheduled job functions.

Jobs run outside any HTTP request, so each one opens and closes its own DB
session (there's no request-scoped Depends(get_db) to borrow) — same
pattern as the webhook background tasks, for the same reason.

Fixed daily jobs (send_morning_message, send_water_reminder, etc.) fan out
to every user with an active reminder subscription. V2 keeps "who gets
reminders" simple: every registered user. Per-user opt-in/scheduling
preferences are a reasonable V3+ extension, not needed to prove the pattern.
"""

import logging
from datetime import datetime

from app.db.session import SessionLocal
from app.integrations.gemini_client import gemini_client
from app.integrations.telegram_client import telegram_client
# from app.integrations.whatsapp_client import whatsapp_client
from app.models.reminder import Reminder, ReminderStatus, ReminderType
from app.models.user import Platform, User
from app.repositories.reminder_repo import ReminderRepository

logger = logging.getLogger(__name__)

SLEEP_RETRY_INTERVAL_MINUTES = 1
SLEEP_RETRY_MAX_ATTEMPTS = 6  # caps the retry loop at 3 hours of nagging

REMINDER_SYSTEM_PROMPT = """
You are VitaMind, an AI nutrition companion.
Your personality:
- Talk like a caring best friend.
- Be playful and teasing, like a close best friend.
- You may lightly flirt only when it feels natural.
- Never become romantic.
- Never become creepy.
- Never guilt-trip the user.
- Never repeat the same joke twice.
- Vary your tone every time.
- Sometimes be funny.
- Sometimes be wholesome.
- Sometimes be chaotic.
- Sometimes be sarcastic.
- Sometimes be cute.
- Sound like Duolingo, Zomato, Blinkit and Swiggy notifications.
- Slightly flirty, playful and witty.
- Sound like Zomato, Swiggy, Duolingo or Blinkit notifications.
- Never sound like a hospital or a robotic reminder.
- Keep messages under 2 short sentences.
- Never use bullet points.
- Never use quotation marks.
- Never repeat wording from previous reminders.
- Every reminder should feel fresh and unique.
- Use emojis naturally.
- Do NOT mention you are an AI.
- Do NOT sound like a doctor.
- Do NOT use formal English.
- Occasionally tease the user in a cute way.
- Encourage healthy habits without sounding preachy.
- Mention the user's name sometimes, but not always.
- Never mention calories unless the reminder is about a meal.
- Never mention nutrition facts unless asked.
- Don't over-explain.
- Write exactly ONE notification.
- No greetings like "Hello".
- Never say "As an AI".
-Never use hashtags.
-Never use markdown.
-Output only the notification text.
"""

async def _send_to_platform(platform: Platform, platform_user_id: str, text: str) -> None:
    if platform == Platform.telegram:
        await telegram_client.send_message(platform_user_id, text)
    # elif platform == Platform.whatsapp:
    #     await whatsapp_client.send_message(platform_user_id, text)


async def _send_to_user(user: User, text: str) -> None:
    """Convenience wrapper for the fixed-schedule broadcasts, which don't
    need to survive a commit/close boundary the way the sleep loop does."""
    await _send_to_platform(user.platform, user.platform_user_id, text)


async def _broadcast(text_fn) -> None:
    """
    text_fn(user) -> str | Awaitable[str]. Iterates every user and sends
    them a per-user-generated message. Kept as a plain loop, not a task
    queue — the user count this project deals with doesn't justify one.
    """
    db = SessionLocal()
    try:
        users = db.query(User).all()
    finally:
        db.close()

    for user in users:
        try:
            text = await text_fn(user)
            await _send_to_user(user, text)
        except Exception:
            logger.exception("Failed to send scheduled message to user %s", user.id)


async def send_morning_message() -> None:
    async def text_for(user: User) -> str:
        try:
            return await _generate_reminder(
            user=user,
            reminder_type="Morning Greeting",
            instruction="""
Wish the user a good morning.

Requirements:
- Wish them a wonderful morning.
- Encourage them to eat a healthy breakfast.
- Ask them to log their first meal today.
- Be playful, wholesome and energetic.
- Sound like a caring best friend.
- Feel like a Zomato, Blinkit or Duolingo notification.
- Maximum 2 short sentences.
- Use at most one emoji.
""",
            fallback="Good morning! 🌞 Hope today treats you kindly. Don't forget to log your first meal today!"
        )
        except Exception:
            return "Good morning! 🌞 Hope today treats you kindly. Don't forget to log your first meal today!"

    await _broadcast(text_for)


async def send_water_reminder() -> None:

    async def text_for(user: User) -> str:
        try:
            return await _generate_reminder(
                user=user,
                reminder_type="Water Reminder",
                instruction="""
Remind the user to drink water.
Be playful.
Sound like Zomato or Duolingo.
""",
            fallback="Hydration check! 💧 Your water bottle misses you."
        )
        except Exception:
            return "Hydration check! 💧 Your water bottle misses you."

    await _broadcast(text_for)


async def send_lunch_reminder() -> None:
    async def text_for(user: User) -> str:
        try:
            return await _generate_reminder(
                user=user,
                reminder_type="Lunch Reminder",
                instruction="""
Tell them it's lunch time.
Ask them to send a meal photo afterwards.
Sound fun.
Be playful.
Sound like Zomato or Duolingo.
""",
            fallback="Lunch time! 🍛 Don't forget to log your meal."
        )
        except Exception:
            return "Lunch time! 🍛 Don't forget to log your meal."

    await _broadcast(text_for)


async def send_coffee_reminder() -> None:

    async def text_for(user: User) -> str:
        return await _generate_reminder(
            user=user,
            reminder_type="Coffee Reminder",
            instruction="""
Remind them about coffee, milk or snacks.
Keep it cute.
""",
            fallback="Coffee break? ☕ Don't forget to log your snack too."
        )
    await _broadcast(text_for)

async def send_dinner_reminder() -> None:

    async def text_for(user: User) -> str:
        return await _generate_reminder(
            user=user,
            reminder_type="Dinner Reminder",
            instruction="""
Tell them to enjoy dinner.
Ask for a meal photo afterwards.
""",
            fallback="Dinner time! 🍽️ Can't wait to see today's dinner."
        )
        

    await _broadcast(text_for)


async def _generate_reminder(
    user: User,
    reminder_type: str,
    instruction: str,
    fallback: str,
) -> str:
    try:
        prompt = f"""
{REMINDER_SYSTEM_PROMPT}

Reminder Type:
{reminder_type}

User Name:
{user.name or "friend"}

Write ONE notification.

Task:
{instruction}
"""

        return await gemini_client.generate_text(prompt)

    except Exception:
        return fallback


async def send_sleep_reminder() -> None:
    """
    Creates a `reminders` row per user (status=sent) and schedules the first
    follow-up check. The scheduler.py module wires the actual one-off job —
    this function only creates the DB record and sends the first message.

    Important detail: we pull (platform, platform_user_id) into plain tuples
    up front, rather than holding onto the SQLAlchemy `User` objects across
    the loop. repo.create() commits after every insert, and SQLAlchemy
    expires an object's loaded attributes on commit by default — so reading
    user.platform after a later commit (or after db.close()) would trigger
    a lazy-reload against an already-closed session and raise
    DetachedInstanceError. Capturing plain values sidesteps that entirely.
    """
    from app.scheduler.scheduler import schedule_sleep_check  # local import avoids a circular import

    db = SessionLocal()
    try:
        users = [(u.id, u.platform, u.platform_user_id) for u in db.query(User).all()]
        repo = ReminderRepository(db)
        reminder_targets = []
        for user_id, platform, platform_user_id in users:
            reminder = repo.create(
                Reminder(
                    user_id=user_id,
                    reminder_type=ReminderType.sleep,
                    scheduled_time=datetime.utcnow(),
                    status=ReminderStatus.sent,
                )
            )
            reminder_targets.append((reminder.id, platform, platform_user_id))
    finally:
        db.close()

    for reminder_id, platform, platform_user_id in reminder_targets:

        temp_user = User(name=None)

        text = await _generate_reminder(
            user=temp_user,
            reminder_type="Sleep Reminder",
            instruction="""
Tell the user it's bedtime.

Requirements:
- Ask them to reply ONLY with "yes" once they're actually in bed.
- Sound like a caring best friend.
- Be playful and wholesome.
- Feel like a Zomato, Swiggy or Duolingo notification.
- Maximum 2 short sentences.
- Use at most one emoji.
""",
        fallback="Hey sleepyhead 😴 Reply 'yes' once you're tucked into bed."
    )
    await _send_to_platform(platform, platform_user_id, text)
    schedule_sleep_check(reminder_id,run_in_minutes=SLEEP_RETRY_INTERVAL_MINUTES,)


async def check_sleep_status(reminder_id: int) -> None:
    """
    The retry loop: if the reminder is still not confirmed, resend and
    reschedule itself. Stops once confirmed, or after
    SLEEP_RETRY_MAX_ATTEMPTS — an unconfirmed reminder should not nag
    forever if the user is simply not responding.

    Same detachment pitfall as send_sleep_reminder(): platform and
    platform_user_id are captured into local variables before
    update_status() commits, not read off the ORM object afterward.
    """
    from app.scheduler.scheduler import schedule_sleep_check  # local import avoids a circular import

    db = SessionLocal()
    try:
        repo = ReminderRepository(db)
        reminder = repo.get_by_id(reminder_id)
        if reminder is None or reminder.status == ReminderStatus.confirmed:
            return

        if reminder.retry_count >= SLEEP_RETRY_MAX_ATTEMPTS:
            logger.info("Sleep reminder %s hit max retries, giving up.", reminder_id)
            return

        user = db.get(User, reminder.user_id)
        if user is None:
            return
        platform, platform_user_id = user.platform, user.platform_user_id

        repo.update_status(reminder, ReminderStatus.snoozed, bump_retry=True)
    finally:
        db.close()

    try:
        text = await _generate_reminder(
        user=user,
        reminder_type="Sleep Follow-up",
        instruction="""
    The user still hasn't replied.

    Write one playful follow-up reminder.

    Requirements:
- Ask them to reply ONLY with "yes" once they're in bed.
- Don't sound annoyed.
- Sound like a clingy best friend.
- Be cute and funny.
- Don't guilt-trip the user.
- Maximum 2 short sentences.
- Use at most one emoji.
""",
        fallback="Still awake? 👀 Reply 'yes' once you're finally in bed."
    )
    except Exception:
        text = "Still awake? 👀 Reply 'yes' once you're finally in bed."
    await _send_to_platform(platform, platform_user_id, text)

    schedule_sleep_check(
        reminder_id,
        run_in_minutes=SLEEP_RETRY_INTERVAL_MINUTES,
    )