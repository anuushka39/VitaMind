"""
Request logging middleware.

Why this file exists:
    Without this, debugging a production issue means grepping logs with no
    way to tie "request came in" to "request finished" to "this specific
    exception happened" — especially once multiple requests are in flight
    concurrently (which they will be, since everything's async). This
    middleware assigns a short request_id to every request and logs entry
    + exit + duration, so every log line in between can be correlated by
    that id.

Which files use this:
    Registered once in app/main.py via app.add_middleware(...).
"""

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.utils.logger import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = uuid.uuid4().hex[:12]
        request.state.request_id = request_id

        start = time.perf_counter()
        logger.info(
            "request started request_id=%s method=%s path=%s",
            request_id, request.method, request.url.path,
        )

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "request finished request_id=%s status=%s duration_ms=%.1f",
            request_id, response.status_code, duration_ms,
        )
        response.headers["X-Request-ID"] = request_id
        return response
