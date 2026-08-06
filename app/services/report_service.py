"""
Weekly nutrition report — pure SQL/Python aggregation over the meals table.

Previously reported avg_healthy_score (a numeric average of the old
heuristic). Since Meal now stores a categorical health_status instead of a
number, the report reports per-category counts and a healthy_meal_pct
instead — an average of a category doesn't mean anything, but counts and a
percentage do.
"""

from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.timeutils import utcnow
from app.models.meal import HealthStatus, Meal


class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def weekly_report(self, user_id: int, as_of=None) -> dict:
        as_of = as_of or utcnow()
        window_start = as_of - timedelta(days=7)

        meals = (
            self.db.query(Meal)
            .filter(
                Meal.user_id == user_id,
                Meal.meal_time >= window_start,
                Meal.meal_time <= as_of,
            )
            .all()
        )

        if not meals:
            return {
                "user_id": user_id,
                "window_start": window_start,
                "window_end": as_of,
                "total_meals": 0,
                "avg_calories": 0,
                "avg_protein_g": 0,
                "avg_carbs_g": 0,
                "avg_fat_g": 0,
                "healthy_meals": 0,
                "moderate_meals": 0,
                "unhealthy_meals": 0,
                "healthy_meal_pct": None,
                "meal_consistency_pct": 0,
            }

        total = len(meals)
        avg_calories = sum(m.calories for m in meals) / total
        avg_protein = sum(m.protein_g for m in meals) / total
        avg_carbs = sum(m.carbs_g for m in meals) / total
        avg_fat = sum(m.fat_g for m in meals) / total

        healthy_count = sum(1 for m in meals if m.health_status == HealthStatus.healthy)
        moderate_count = sum(1 for m in meals if m.health_status == HealthStatus.moderate)
        unhealthy_count = sum(1 for m in meals if m.health_status == HealthStatus.unhealthy)

        # Consistency = fraction of the 7-day window with at least one
        # logged meal. Simple and explainable, not a "streak" gamification
        # metric that would need its own persisted state.
        distinct_days = len({m.meal_time.date() for m in meals})
        meal_consistency_pct = round(distinct_days / 7 * 100, 1)

        return {
            "user_id": user_id,
            "window_start": window_start,
            "window_end": as_of,
            "total_meals": total,
            "avg_calories": round(avg_calories, 1),
            "avg_protein_g": round(avg_protein, 1),
            "avg_carbs_g": round(avg_carbs, 1),
            "avg_fat_g": round(avg_fat, 1),
            "healthy_meals": healthy_count,
            "moderate_meals": moderate_count,
            "unhealthy_meals": unhealthy_count,
            "healthy_meal_pct": round(healthy_count / total * 100, 1),
            "meal_consistency_pct": meal_consistency_pct,
        }