"""
Rate limiting middleware.

Fixed-window counter per client IP, kept in an in-process dict — no Redis.
This is an explicit scope decision, not an oversight: it's correct for a
single-instance deployment (which is what this project targets, per Render
deployment on one dyno/service) but would under-count correctly if the app
ever ran as multiple processes/instances, since each instance would keep its
own counters. That trade-off, and "how would you fix it for multiple
instances" (shared store, e.g. Redis INCR + TTL), is the exact follow-up
question this design invites in an interview — which is the point.
"""

import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings

WINDOW_SECONDS = 60

# Module-level (not instance-level) so tests can import and clear it
# directly between test cases -- the FastAPI `app` object, and therefore
# this middleware instance, is created once and reused for the whole test
# session, so without an explicit reset, hit counts would leak across
# unrelated tests that happen to share a client IP.
_hits: dict[str, list[float]] = defaultdict(list)


def reset_rate_limit_state() -> None:
    _hits.clear()


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        window_start = now - WINDOW_SECONDS
        recent_hits = [t for t in _hits[client_ip] if t > window_start]

        if len(recent_hits) >= settings.RATE_LIMIT_PER_MINUTE:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "RateLimitExceeded",
                    "message": "Too many requests. Please slow down.",
                },
            )

        recent_hits.append(now)
        _hits[client_ip] = recent_hits

        return await call_next(request)
