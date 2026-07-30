"""
Centralized exception handling.

Why this file exists:
    Without this, an unhandled exception anywhere in the app produces
    FastAPI's default 500 response — which, depending on config, can leak
    a full stack trace to the client. This file registers handlers so
    every error the client sees has a consistent shape, and every error is
    logged server-side with full detail regardless of what the client sees.

    This is also the single place that maps internal exception types to
    HTTP status codes, so that mapping doesn't get duplicated (and drift)
    across every route.

V2 additions: NotFoundError is now actually used (user/meal/etc. lookups),
and ConflictError covers uniqueness violations (e.g. duplicate email).
"""

import json

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.utils.logger import get_logger

logger = get_logger(__name__)


class AppError(Exception):
    status_code = status.HTTP_400_BAD_REQUEST
    message = "Something went wrong."

    def __init__(self, message: str | None = None):
        self.message = message or self.message
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    message = "Resource not found."


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    message = "Resource already exists."


class DatabaseError(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    message = "A database error occurred. Please try again shortly."


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "unknown")
        logger.warning(
            "handled app error request_id=%s type=%s message=%s",
            request_id, type(exc).__name__, exc.message,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": type(exc).__name__, "message": exc.message, "request_id": request_id},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "unknown")
        # exc.errors() can embed the raw exception instance in an error's
        # "ctx" dict when a custom @model_validator/@field_validator raises
        # ValueError (Pydantic v2 does this so you get the original object,
        # not just its message) — that's not JSON-serializable, so it has to
        # be coerced to a string before it can go in a response body.
        safe_errors = json.loads(json.dumps(exc.errors(), default=str))
        logger.warning("validation error request_id=%s errors=%s", request_id, safe_errors)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "ValidationError", "message": "Invalid request data.",
                     "details": safe_errors, "request_id": request_id},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "unknown")
        logger.error(
            "unhandled exception request_id=%s type=%s error=%s",
            request_id, type(exc).__name__, exc, exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "InternalServerError", "message": "An unexpected error occurred.",
                     "request_id": request_id},
        )
