"""
Weekly nutrition report aggregation, including the categorical
healthy/moderate/unhealthy counts that replaced the old numeric
avg_healthy_score.

Meals are inserted directly via db_session (bypassing the upload API) so
each test can control meal_time and health_status precisely.
"""

from datetime import timedelta

from app.core.timeutils import utcnow
from app.models.meal import HealthStatus, Meal


def _add_meal(db_session, user_id, days_ago, calories, protein, carbs, fat, health_status):
    meal = Meal(
        user_id=user_id,
        detected_food="test meal",
        calories=calories,
        protein_g=protein,
        carbs_g=carbs,
        fat_g=fat,
        health_status=health_status,
        reason="test reason",
        meal_time=utcnow() - timedelta(days=days_ago),
    )
    db_session.add(meal)
    db_session.commit()
    return meal


def test_weekly_report_averages_and_health_status_counts(client, make_user, db_session):
    user = make_user()
    _add_meal(db_session, user.id, days_ago=0, calories=500, protein=30, carbs=40, fat=15, health_status=HealthStatus.healthy)
    _add_meal(db_session, user.id, days_ago=2, calories=700, protein=20, carbs=60, fat=25, health_status=HealthStatus.moderate)
    _add_meal(db_session, user.id, days_ago=4, calories=600, protein=8, carbs=40, fat=38, health_status=HealthStatus.unhealthy)

    response = client.get(f"/api/v1/reports/weekly/{user.id}")
    assert response.status_code == 200
    body = response.json()

    assert body["total_meals"] == 3
    assert body["avg_calories"] == round((500 + 700 + 600) / 3, 1)
    assert body["healthy_meals"] == 1
    assert body["moderate_meals"] == 1
    assert body["unhealthy_meals"] == 1
    assert body["healthy_meal_pct"] == round(1 / 3 * 100, 1)
    # 3 distinct days out of a 7-day window
    assert body["meal_consistency_pct"] == round(3 / 7 * 100, 1)


def test_weekly_report_excludes_meals_outside_window(client, make_user, db_session):
    user = make_user()
    _add_meal(db_session, user.id, days_ago=1, calories=500, protein=30, carbs=40, fat=15, health_status=HealthStatus.healthy)
    _add_meal(db_session, user.id, days_ago=10, calories=999, protein=1, carbs=99, fat=99, health_status=HealthStatus.unhealthy)

    response = client.get(f"/api/v1/reports/weekly/{user.id}")
    assert response.status_code == 200
    body = response.json()

    assert body["total_meals"] == 1
    assert body["avg_calories"] == 500
    assert body["healthy_meals"] == 1
    assert body["unhealthy_meals"] == 0


def test_weekly_report_empty_for_user_with_no_meals(client, make_user):
    user = make_user()
    response = client.get(f"/api/v1/reports/weekly/{user.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["total_meals"] == 0
    assert body["healthy_meal_pct"] is None
    assert body["meal_consistency_pct"] == 0