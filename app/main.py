"""
Application entrypoint.

Why this file exists:
    This is the only file that assembles the app — creates the FastAPI
    instance, registers middleware, exception handlers, and routers. It
    intentionally contains no business logic; if you find yourself writing
    an `if` statement here beyond wiring, it belongs in a service instead.

V2 change: registers the tracking routers (users, preferences, meals,
exercise, water, sleep, weight, goals, dashboard). Version bumped to 0.2.0.

Run with:
    uvicorn app.main:app --reload --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import dashboard, exercise, goals, health, meals, preferences, sleep, users, water, weight
from app.config.settings import settings
from app.database.session import engine
from app.middleware.error_handlers import register_exception_handlers
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s in %s mode", settings.app_name, settings.env)
    yield
    logger.info("Shutting down %s, disposing DB engine", settings.app_name)
    engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.2.0",
        description="AI-powered nutrition and lifestyle assistant.",
        lifespan=lifespan,
    )

    app.add_middleware(RequestLoggingMiddleware)
    register_exception_handlers(app)

    app.include_router(health.router)
    app.include_router(users.router)
    app.include_router(preferences.router)
    app.include_router(meals.router)
    app.include_router(exercise.router)
    app.include_router(water.router)
    app.include_router(sleep.router)
    app.include_router(weight.router)
    app.include_router(goals.router)
    app.include_router(dashboard.router)

    return app


app = create_app()
