"""
Custom exception types + global exception handlers.

Why this exists: without it, every route would need its own try/except to
turn a "not found" or "bad input" situation into a proper HTTP response, and
unhandled errors would leak raw Python tracebacks to the client. Centralizing
this means every error the API returns has the same predictable JSON shape:

    { "error": "UserNotFoundError", "message": "..." }
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Base class for all expected/handled application errors."""

    status_code = status.HTTP_400_BAD_REQUEST
    message = "An application error occurred."

    def __init__(self, message: str | None = None):
        self.message = message or self.message
        super().__init__(self.message)


class NotFoundError(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    message = "Resource not found."


class UserNotFoundError(NotFoundError):
    message = "User not found."


class DuplicateUserError(AppException):
    status_code = status.HTTP_409_CONFLICT
    message = "A user with this platform_user_id already exists."


def register_exception_handlers(app: FastAPI) -> None:
    """
    Wires the handlers into the FastAPI app. Called once from main.py.
    Keeping registration in one function (instead of decorators scattered
    across files) makes it obvious, in one place, exactly which error types
    the API formally handles.
    """

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.warning("Handled error: %s - %s", exc.__class__.__name__, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.__class__.__name__, "message": exc.message},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # Last-resort catch-all: logs the full traceback server-side but
        # never leaks internals to the client.
        logger.exception("Unhandled exception on %s %s", request.method, request.url)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "message": "Something went wrong. Please try again later.",
            },
        )
