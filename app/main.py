"""
Application entrypoint.

Wires together everything built so far: logging, DB table creation,
exception handlers, middleware, the scheduler, the vector store, and all
v1 routers (CRUD + meals/conversation/reminders + Telegram/WhatsApp
webhooks). Uses FastAPI's lifespan context manager to run startup/shutdown
logic around the app's serving lifetime.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

from app.api.v1 import conversation, health, meals, reminders, reports, users
from app.api.webhooks import telegram
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.db.init_db import init_db
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.rate_limit_middleware import RateLimitMiddleware
from app.scheduler.scheduler import start_scheduler, stop_scheduler
from app.vectorstore.store import get_retriever

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    init_db()

    try:
        # Loads the persisted FAISS index if one exists, or builds and
        # saves one on the spot if this is a fresh clone -- warming it here
        # means the first real user request never pays the index-build
        # cost. Wrapped in try/except because recommendations are a
        # best-effort feature: a missing knowledge base or a failed model
        # download should not prevent the rest of the app (meal logging,
        # reminders, everything else) from starting.
        get_retriever()
    except Exception:
        logger.exception(
            "Vector store unavailable at startup -- recommendations will be skipped until "
            "scripts/build_faiss_index.py has been run successfully."
        )

    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

register_exception_handlers(app)

# Middleware order matters: Starlette runs middleware in reverse of add
# order for the request path, so rate limiting (added last) runs first,
# rejecting over-limit requests before they're even logged as "handled" —
# only requests that pass the rate limit get a full logged entry.
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

app.include_router(health.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(meals.router, prefix="/api/v1")
app.include_router(conversation.router, prefix="/api/v1")
app.include_router(reminders.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(telegram.router , prefix="/api/v1")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )
