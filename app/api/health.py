"""
Health check router.

Why this file exists:
    A "the process is running" health check is nearly useless in production
    — the process can be up while its DB connection is dead. This endpoint
    checks both, which is what you actually want a load balancer / uptime
    monitor / deployment pipeline to verify before routing traffic.

Which files it calls:
    app/database/session.py -> check_db_connection()

Which files call it:
    Registered in app/main.py. Not called by any other internal module.
"""

from fastapi import APIRouter

from app.config.settings import settings
from app.database.session import check_db_connection

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict:
    db_ok = check_db_connection()

    return {
        "status": "ok" if db_ok else "degraded",
        "app": settings.app_name,
        "env": settings.env,
        "database": "connected" if db_ok else "unreachable",
    }
