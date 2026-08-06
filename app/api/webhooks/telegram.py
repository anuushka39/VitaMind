"""
Telegram webhook entrypoint.

Meal-photo replies now come straight from MealService.analyze_and_log_meal
-- the webhook no longer builds any reply text itself, bullet-point or
otherwise, it just sends whatever conversational string comes back.

Text messages get one new branch: if the user is explicitly asking for
calories/protein/macros/a nutrition breakdown, look up their most recent
meal and answer with the deterministic numeric breakdown (the ONLY place
raw numbers are shown) instead of the generic acknowledgement.
"""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from app.services.reminder_service import ReminderService
from app.integrations.gemini_client import gemini_client
from app.api.deps import get_db
from app.db.session import SessionLocal
from app.integrations.telegram_client import telegram_client
from app.models.conversation import MessageRole, MessageType
from app.models.user import Platform
from app.services.conversation_service import ConversationService
from app.services.meal_service import MealService
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Simple, deterministic keyword check -- this is a backend project, not an
# NLU project, so a keyword match is the right amount of engineering for
# "did the user ask for numbers." A false positive/negative here just means
# falling back to the generic conversational reply, which is a fine
# default either way.
NUTRITION_KEYWORDS = (
    "calorie", "calories", "protein", "carb", "carbs", "carbohydrate",
    "macro", "macros", "nutrition breakdown", "nutritional breakdown", "fat content",
)


@router.post("/telegram")
async def telegram_webhook(
    update: dict, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    message = update.get("message")
    if not message:
        # Telegram sends update types this bot doesn't handle yet (edited
        # messages, callback queries, etc.) — ack with 200 and ignore, since
        # returning an error would make Telegram retry a message we were
        # never going to process anyway.
        return {"ok": True}

    chat_id = str(message["chat"]["id"])
    first_name = message.get("from", {}).get("first_name")

    user_service = UserService(db)
    user = user_service.get_or_create_by_platform(Platform.telegram, chat_id, first_name)

    conversation_service = ConversationService(db)

    if "photo" in message:
        # Telegram sends multiple resolutions; the last entry is the largest.
        file_id = message["photo"][-1]["file_id"]
        conversation_service.log_message(
            user.id, MessageRole.user, "[meal photo]", MessageType.image
        )
        background_tasks.add_task(_handle_meal_photo, user.id, chat_id, file_id)
        return {"ok": True}

    text = message.get("text", "")
    conversation_service.log_message(user.id, MessageRole.user, text, MessageType.text)
    background_tasks.add_task(_handle_text_reply, user.id, chat_id, text)
    return {"ok": True}


async def _handle_meal_photo(user_id: int, chat_id: str, file_id: str) -> None:
    """
    Runs after the webhook has already responded to Telegram — by this
    point the request-scoped `db` session from Depends(get_db) has already
    been closed, so this opens its own short-lived session rather than
    reusing (or worse, silently reusing a closed) one.
    """
    db = SessionLocal()
    try:
        image_bytes = await telegram_client.download_file(file_id)
        meal_service = MealService(db)
        _meal, reply = await meal_service.analyze_and_log_meal(user_id, image_bytes)
    except Exception:
        logger.exception("Meal photo handling failed for user %s", user_id)
        reply = "Sorry, I couldn't analyze that photo. Could you try sending it again?"
    finally:
        db.close()

    await telegram_client.send_message(chat_id, reply)


async def _handle_text_reply(user_id: int, chat_id: str, text: str) -> None:
    db = SessionLocal()
    try:
        reminder_service = ReminderService(db)
        pending = reminder_service.get_latest_pending_sleep_reminder(user_id)

        if pending and text.lower().strip() in {
            "yes",
            "y",
            "yes sleeping",
            "sleeping",
            "i'm in bed",
            "im in bed",
        }:
            reminder_service.confirm(pending.id)

            await telegram_client.send_message(
                chat_id,
                "Sweet dreams, babe 🌙...i'll be here tomorrow to keep you healthy and slightly annoyed😴"
            )
            return

    finally:
        db.close()


    # 2. Nutrition breakdown
    """
    If the text is explicitly asking for numbers, answer with the last
    logged meal's deterministic breakdown. Otherwise, keep V2's simple
    acknowledgement -- a full context-aware conversational loop is out of
    scope here (see meal_service.COMPOSE_REPLY_PROMPT for where the
    conversational tone actually lives: the meal-logged reply itself).
    """
    if any(keyword in text.lower() for keyword in NUTRITION_KEYWORDS):
        db = SessionLocal()
        try:
            meal_service = MealService(db)
            recent = meal_service.get_history(user_id, limit=1)
            reply = (
                meal_service.get_nutrition_breakdown_text(recent[0])
                if recent
                else "You haven't logged a meal yet — send me a photo and I'll break it down!"
            )
        finally:
            db.close()

        await telegram_client.send_message(chat_id, reply)
        return
    
        # 3. Normal Gemini chat
    reply = await gemini_client.generate_text(
            f"""
        You are VitaMind.
        Reply to this user message naturally.
        If they ask about food,
        answer briefly.
        If they ask a nutrition question,
        answer it.
        If they ask something unrelated,
        politely steer them back to nutrition.
        Maximum 3 short sentences.
        User:
        {text}
        """
        )
    await telegram_client.send_message(chat_id, reply)