"""
Meal service — orchestrates Gemini Vision analysis, health classification,
FAISS-backed tips, and the final conversational reply. Deliberately keeps
all of that in one place (one file, one class) rather than spreading
"decide if we need tips" / "phrase the reply" logic across the webhook
handlers — the webhooks now just call analyze_and_log_meal() and send
whatever reply string comes back.

Pipeline:
  photo -> Gemini Vision (food + macros + health_status + reason)
        -> persist meal
        -> healthy:   no retrieval
           moderate:  retrieve 1 small tip
           unhealthy: retrieve up to 3 alternatives
        -> Gemini rewrites (meal + status + reason + tips) into ONE natural,
           non-robotic reply
        -> (meal, reply) returned to the caller
"""

import logging

from sqlalchemy.orm import Session

from app.integrations.gemini_client import gemini_client
from app.models.meal import HealthStatus, Meal
from app.repositories.meal_repo import MealRepository
from app.services.recommendation_service import recommendation_service

logger = logging.getLogger(__name__)

MODERATE_TIP_COUNT = 1
UNHEALTHY_TIP_COUNT = 3

COMPOSE_REPLY_PROMPT = """You are a warm, encouraging nutrition coach chatting \
one-on-one with someone who just logged a meal by photo in a nutrition app. \
Write a short, natural, conversational reply (2-4 sentences) confirming the \
meal was logged.

Meal: {detected_food}
Health assessment: {health_status}
Why: {reason}
{tips_section}
Rules:
- Sound like a supportive friend texting back, not a report. No bullet \
points, no headers, and do NOT mention specific calorie/protein/carb/fat \
numbers -- describe nutrition only in plain qualitative terms (e.g. "fiber-\
rich", "deep-fried", "well balanced").
- If the assessment is "healthy", keep it short and encouraging.
- If "moderate" or "unhealthy", naturally weave in ONE gentle, specific \
suggestion drawn from the tips above (if any) -- don't lecture, don't list \
multiple options.
- 2-4 sentences total, plain conversational text only.
"""


class MealService:
    def __init__(self, db: Session):
        self.repo = MealRepository(db)

    async def analyze_and_log_meal(self, user_id: int, image_bytes: bytes) -> tuple[Meal, str]:
        """Returns (meal, reply) — reply is always a non-empty, ready-to-send
        conversational string (falls back to a plain sentence if the
        Gemini phrasing call fails; a failed reply-composition step should
        never lose the fact that the meal itself was successfully logged)."""
        result = await gemini_client.analyze_meal_image(image_bytes)

        health_status = self._safe_health_status(result.get("health_status"))
        reason = result.get("reason", "")

        meal = Meal(
            user_id=user_id,
            detected_food=result["detected_food"],
            calories=result["calories"],
            protein_g=result["protein_g"],
            carbs_g=result["carbs_g"],
            fat_g=result["fat_g"],
            health_status=health_status,
            reason=reason,
        )
        meal = self.repo.create(meal)

        tips = self._retrieve_tips_for(health_status, result["detected_food"])
        reply = await self._compose_reply(meal, tips)

        return meal, reply

    def get_history(self, user_id: int, limit: int = 50) -> list[Meal]:
        return self.repo.list_by_user(user_id, limit)

    def get_nutrition_breakdown_text(self, meal: Meal) -> str:
        """
        Deterministic, non-LLM formatted numbers -- used ONLY when a user
        explicitly asks for calories/protein/macros (see the webhook text
        handlers). Every other reply stays qualitative/conversational per
        the compose_reply rules above; this is the one place raw numbers
        are shown, and only on request.
        """
        return (
            f"Here's the breakdown for {meal.detected_food}:\n"
            f"Calories: {meal.calories:.0f} kcal\n"
            f"Protein: {meal.protein_g:.0f} g\n"
            f"Carbs: {meal.carbs_g:.0f} g\n"
            f"Fat: {meal.fat_g:.0f} g"
        )

    @staticmethod
    def _safe_health_status(value: str | None) -> HealthStatus:
        try:
            return HealthStatus(value)
        except ValueError:
            logger.warning("Gemini returned an unrecognized health_status %r, defaulting to moderate.", value)
            return HealthStatus.moderate

    @staticmethod
    def _retrieve_tips_for(health_status: HealthStatus, detected_food: str) -> list[str]:
        if health_status == HealthStatus.moderate:
            return recommendation_service.retrieve_tips(detected_food, k=MODERATE_TIP_COUNT)
        if health_status == HealthStatus.unhealthy:
            return recommendation_service.retrieve_tips(detected_food, k=UNHEALTHY_TIP_COUNT)
        return []  # healthy meals never trigger FAISS retrieval

    async def _compose_reply(self, meal: Meal, tips: list[str]) -> str:
        tips_section = ""
        if tips:
            tips_section = "Relevant tips:\n" + "\n".join(f"- {t}" for t in tips) + "\n"

        prompt = COMPOSE_REPLY_PROMPT.format(
            detected_food=meal.detected_food,
            health_status=meal.health_status.value,
            reason=meal.reason or "",
            tips_section=tips_section,
        )
        try:
            return await gemini_client.generate_text(prompt)
        except Exception:
            logger.exception("Reply composition failed, falling back to a plain confirmation.")
            fallback = f"Your {meal.detected_food} has been logged."
            if meal.health_status != HealthStatus.healthy and tips:
                fallback += f" Tip: {tips[0]}"
            return fallback