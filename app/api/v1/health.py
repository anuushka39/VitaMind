"""
Health check endpoint.

Deliberately simple: no auth, no DB dependency to keep it a true liveness
check (it should answer even if MySQL is briefly unreachable, so it can be
used as a Render/uptime health probe without false negatives).
"""

from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
