"""
Dashboard response contract.

Shape is fixed to match the JSON structure specified for this endpoint,
since it's the contract Version 4's Telegram/WhatsApp bots (and eventually
a web/mobile frontend) will consume — changing this shape later is a
breaking change for every consumer, so it's worth getting right now
rather than letting it drift from whatever was convenient internally.
"""

from pydantic import BaseModel


class DashboardUser(BaseModel):
    id: int
    name: str


class DashboardToday(BaseModel):
    calories: float
    water_ml: int
    exercise_minutes: int
    sleep_hours: float | None
    weight: float | None


class DashboardGoals(BaseModel):
    daily_calories: float | None
    daily_water_ml: float | None


class DashboardResponse(BaseModel):
    user: DashboardUser
    today: DashboardToday
    goals: DashboardGoals
