# VitaMind 

> An AI-powered nutrition and lifestyle companion that remembers your habits over time and gives contextual, practical, budget-conscious recommendations — through Telegram and WhatsApp.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-async-teal)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange)
![License](https://img.shields.io/badge/license-MIT-green)

---

---

## Overview

VitaMind AI is a conversational nutrition assistant that behaves like a long-term health companion rather than a stateless chatbot. It logs meals, exercise, sleep, water, and weight; remembers preferences and allergies; and generates recommendations that account for the user's *entire day so far* — not just the question they just asked.

The assistant is accessed through Telegram and WhatsApp, so there's no app to install — logging a meal is as easy as sending a message.

## Motivation & Problem Statement

Most nutrition-tracking apps fail for one of three reasons:

1. **They're stateless.** Every question is answered in isolation, with no memory of what you already ate today or your history.
2. **They're generic.** Recommendations assume access to imported superfoods, protein powders, or ingredients that don't reflect an average household's pantry.
3. **They require manual data entry through a dedicated app**, which most people abandon within two weeks.

**VitaMind AI addresses each of these directly**: persistent structured memory across days and weeks, recommendations grounded in practical, commonly available ingredients, and a chat-first interface on platforms people already have open.

## Key Features

- 🍽️ Natural-language meal, water, sleep, exercise, and weight logging
- 🧠 Persistent memory across days/weeks/months — structured logs, not "the LLM remembers"
- 📊 Daily health dashboard: what's logged, what's missing, running nutrition balance
- 🎯 Context-aware recommendations that account for the full day, not just the last message
- 📚 Recommendations grounded in retrieved expert nutrition knowledge (RAG), not just LLM priors
- ⏰ Smart reminders (water, meals, exercise) via APScheduler
- 📈 Weekly nutrition reports
- 💬 Telegram and WhatsApp native — zero-install access
- 🇮🇳 Tuned for practical, affordable, Indian-household ingredients — not aspirational superfoods

## Architecture Overview

                        ┌─────────────────────────┐
                        │   Telegram / WhatsApp    │
                        │   (user sends message/   │
                        │    image)                │
                        └────────────┬─────────────┘
                                     │ webhook
                                     ▼
                        ┌─────────────────────────┐
                        │        FastAPI App        │
                        │  ┌───────────────────┐   │
                        │  │  Middleware layer  │   │  (logging, rate limit, correlation ID)
                        │  └─────────┬─────────┘   │
                        │            ▼              │
                        │  ┌───────────────────┐   │
                        │  │   API Routers      │   │  (meals, conversation, reminders, reports)
                        │  └─────────┬─────────┘   │
                        │            ▼              │
                        │  ┌───────────────────┐   │
                        │  │  Service Layer     │◄──┼── Gemini Vision / Gemini Text (async HTTP)
                        │  └─────────┬─────────┘   │
                        │            ▼              │
                        │  ┌───────────────────┐   │
                        │  │ Repository Layer   │   │
                        │  └─────────┬─────────┘   │
                        └────────────┼──────────────┘
                                     ▼
                        ┌─────────────────────────┐
                        │        MySQL DB           │  (users, meals, conversation, reminders)
                        └─────────────────────────┘

              ┌─────────────────────┐      ┌──────────────────────┐
              │   APScheduler        │      │   FAISS Vector Store  │
              │  (in-process jobs:   │      │  (nutrition knowledge  │
              │  reminders, reports) │      │   embeddings, cosine   │
              │                      │      │   similarity search)   │
              └──────────┬───────────┘      └───────────┬───────────┘
                         │ triggers                       │ queried by
                         ▼                                 ▼
              Telegram/WhatsApp send             recommendation_service.py

```
vitamind/
├── app/
│   ├── main.py                     # FastAPI app factory, router registration, startup/shutdown events
│   ├── core/
│   │   ├── config.py                # Pydantic Settings — loads .env
│   │   ├── logging.py               # Logging config (structured, rotating file + console)
│   │   ├── exceptions.py            # Custom exception classes + global exception handlers
│   │   └── security.py              # Rate limiting, API key/auth dependency (if needed)
│   │
│   ├── db/
│   │   ├── base.py                  # SQLAlchemy declarative Base
│   │   ├── session.py               # Engine + SessionLocal + get_db dependency
│   │   └── init_db.py               # Table creation / Alembic hook (V1: create_all, V4: Alembic)
│   │
│   ├── models/                      # SQLAlchemy ORM models (1 file per table group)
│   │   ├── user.py
│   │   ├── conversation.py
│   │   ├── meal.py
│   │   └── reminder.py
│   │
│   ├── schemas/                     # Pydantic request/response schemas
│   │   ├── user.py
│   │   ├── conversation.py
│   │   ├── meal.py
│   │   └── reminder.py
│   │
│   ├── repositories/                # Pure DB access, no business logic
│   │   ├── user_repo.py
│   │   ├── meal_repo.py
│   │   └── conversation_repo.py
│   │
│   ├── services/                    # Business logic — orchestrates repos + external APIs
│   │   ├── meal_service.py          # Gemini Vision call + calorie estimation + persistence
│   │   ├── conversation_service.py  # Memory read/write, context assembly
│   │   ├── reminder_service.py      # Reminder scheduling logic
│   │   ├── report_service.py        # Weekly nutrition report generation
│   │   └── recommendation_service.py# FAISS retrieval + Gemini suggestion
│   │
│   ├── api/
│   │   ├── deps.py                  # Shared FastAPI dependencies (get_db, get_current_user, etc.)
│   │   └── v1/
│   │       ├── health.py
│   │       ├── users.py
│   │       ├── meals.py
│   │       ├── conversation.py
│   │       ├── reminders.py
│   │       └── reports.py
│   │
│   ├── integrations/                # Thin clients for external services — swappable, testable
│   │   ├── gemini_client.py
│   │   ├── telegram_client.py
│   │   ├── whatsapp_client.py
│   │   └── llm_alt_client.py        # second free LLM for comparison
│   │
│   ├── scheduler/
│   │   ├── scheduler.py             # APScheduler instance + startup registration
│   │   └── jobs.py                  # Job functions (morning msg, water, meal reminders, sleep loop)
│   │
│   ├── vectorstore/
│   │   ├── embedder.py              # Sentence-Transformers wrapper
│   │   ├── faiss_index.py           # Build/load/query FAISS index
│   │   └── knowledge_loader.py      # Ingests FitTuber content / recipes / tips into the index
│   │
│   └── middleware/
│       ├── logging_middleware.py    # Request/response timing + correlation ID
│       └── rate_limit_middleware.py
│
├── data/
│   └── knowledge_base/              # Raw text files for FAISS ingestion
│
├── tests/
│   ├── test_meals.py
│   ├── test_conversation.py
│   └── test_reminders.py
│
├── .env.example
├── requirements.txt
├── Dockerfile                       # optional, for Render
├── .github/workflows/ci.yml
└── README.md

## Request Flow (example: meal image upload)

1. User sends photo → Telegram/WhatsApp webhook hits /api/v1/meals/upload
2. Middleware: logs request, assigns correlation ID, checks rate limit
3. Router (meals.py): validates request via Pydantic schema, calls meal_service.analyze_meal()
4. meal_service:
     a. downloads/decodes image
     b. calls gemini_client.analyze_image() (async) → food items + estimated macros
     c. calls conversation_service to fetch user context (allergies, goals) for personalization
     d. calls meal_repo.save_meal() to persist result
     e. if meal looks unhealthy → calls recommendation_service (FAISS lookup)
5. Router returns structured JSON response (also used to compose the chat reply)
6. Background task (FastAPI BackgroundTasks): sends the formatted reply back via Telegram/WhatsApp client
   — this is what "asynchronous inference workflow reducing latency" means: the HTTP response to
   the webhook returns fast; the actual outbound message send happens as a background task.
```
## Database Schema (MySQL)
```
users
──────────────────────────────
id              BIGINT PK
platform        ENUM('telegram','whatsapp')
platform_user_id VARCHAR(64) UNIQUE   -- chat_id / phone number
name            VARCHAR(100) NULL
goals           JSON NULL             -- {"target":"weight_loss","calories":1800}
allergies       JSON NULL             -- ["peanuts","gluten"]
created_at      DATETIME
updated_at      DATETIME

conversation_messages
──────────────────────────────
id              BIGINT PK
user_id         BIGINT FK -> users.id
role            ENUM('user','assistant')
message_text    TEXT
message_type    ENUM('text','image','system')
created_at      DATETIME
-- indexed on (user_id, created_at) for fast recent-history reads

meals
──────────────────────────────
id              BIGINT PK
user_id         BIGINT FK -> users.id
image_url       VARCHAR(255) NULL
detected_food   VARCHAR(255)
calories        FLOAT
protein_g       FLOAT
carbs_g         FLOAT
fat_g           FLOAT
healthy_score   FLOAT NULL
meal_time       DATETIME
created_at      DATETIME
-- indexed on (user_id, meal_time) for weekly report queries

reminders
──────────────────────────────
id              BIGINT PK
user_id         BIGINT FK -> users.id
reminder_type   ENUM('water','lunch','dinner','sleep','coffee','morning')
scheduled_time  DATETIME
status          ENUM('pending','sent','confirmed','snoozed')
retry_count     INT DEFAULT 0
created_at      DATETIME

```
## Setup

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env              # then edit DB_* values to match your MySQL
```

Create the database (the app creates tables, but not the database itself):

```sql
CREATE DATABASE vitamind_db;
```

## Run

```bash
uvicorn app.main:app --reload
```

Visit `http://127.0.0.1:8000/docs` for interactive Swagger docs.

## Verify it's working

```bash
curl http://127.0.0.1:8000/api/v1/health

curl -X POST http://127.0.0.1:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"platform": "telegram", "platform_user_id": "12345", "name": "Anu"}'

curl http://127.0.0.1:8000/api/v1/users/1
```

Restart the app and re-run the GET — the user should still be there,
confirming data is persisted in MySQL, not held in memory.

## Project layout

```
app/
  core/        settings, logging, exception handling
  db/          engine, session, table creation
  models/      SQLAlchemy ORM models
  schemas/     Pydantic request/response schemas
  repositories/  raw DB queries
  services/    business logic
  api/v1/      route handlers
```

See `docs/`for the full architecture and roadmap.

---


### Additional setup

Fill in the new `.env` values:
```
GEMINI_API_KEY=...
TELEGRAM_BOT_TOKEN=...
WHATSAPP_TOKEN=...
WHATSAPP_PHONE_NUMBER_ID=...
WHATSAPP_VERIFY_TOKEN=...      # any string you choose, used in the Meta webhook setup
```

**Telegram**: after starting the app and exposing it publicly (e.g. via
`ngrok http 8000` for local testing), register the webhook:
```bash
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<your-public-url>/webhooks/telegram"
```

**WhatsApp**: in the Meta App dashboard, set the webhook callback URL to
`https://<your-public-url>/webhooks/whatsapp` and the verify token to match
`WHATSAPP_VERIFY_TOKEN`. Meta will call the `GET` endpoint once to confirm
before your `POST` handler ever receives real messages.

### Verify it is working

- Message your Telegram bot with plain text → check `GET /api/v1/conversation/{user_id}` shows it, and the bot replies.
- Send a meal photo → check `GET /api/v1/meals/{user_id}` shows the logged entry with calories/macros.
- Create a reminder via `POST /api/v1/reminders`, confirm it via `POST /api/v1/reminders/{id}/confirm`, and confirm `status` flips to `confirmed`.
- Hit any endpoint more than `RATE_LIMIT_PER_MINUTE` times in a minute → expect a `429`.
- Check `logs/vitamind.log` for request lines with correlation IDs after making a few calls.

### Known scope limits (intentional, not bugs)

- Rate limiting is in-process (per-instance), not shared across multiple app instances — fine for a single Render service, would need a shared store (e.g. Redis) to scale horizontally.
- The scheduler broadcasts fixed reminder times to every registered user; per-user scheduling preferences aren't implemented in V2.
- Text replies from the bot are simple acknowledgements, not full context-aware conversation — that's deferred to V3 once retrieval exists to ground richer replies.

---
# Progress as follows: 

## Version 1 (Backend Foundation)

Clean FastAPI + MySQL backend: config, logging, DB session management,
dependency injection, global exception handling, and full CRUD on `User`.
No AI, scheduling, or messaging integrations yet — those arrive in V2.

## Version 2 — Core VitaMind Backend

Adds: meal image analysis (Gemini Vision), conversation memory, reminder
scheduling (APScheduler, including the sleep-confirmation retry loop),
Telegram + WhatsApp webhook integration, request logging middleware, and
rate limiting.

## Version 3 — AI Intelligence Layer

Adds: FAISS-backed nutrition knowledge retrieval, a grounded healthy-alternative
recommendation hook on unhealthy meals, weekly nutrition reports, and a
simple concurrent comparison between Gemini and a second free-tier LLM.

### Build the FAISS index (one-time, or whenever `data/knowledge_base/*.txt` changes)

```bash
python scripts/build_faiss_index.py
```

This downloads the `all-MiniLM-L6-v2` sentence-transformers model on first
run (needs internet access) and writes `data/faiss_index.bin` +
`data/faiss_metadata.json`. The app reads these files at request time; it
does **not** rebuild the index automatically on startup.

### Additional setup

```
GROQ_API_KEY=...          # only needed to run scripts/compare_llms.py
GROQ_MODEL=llama-3.1-8b-instant
```

### Verify V3 is working

- Log a meal with clearly unhealthy macros (e.g. via `/api/v1/meals/upload` or a real photo) → response includes a non-null `recommendation`, and you can trace it back to a line in `data/knowledge_base/*.txt`.
- `GET /api/v1/reports/weekly/{user_id}` after a few logged meals → totals/averages should match a manual calculation from the raw rows.
- `python scripts/compare_llms.py` → prints latency + response text for Gemini and the alternate LLM side by side, run concurrently via `asyncio.gather`.

### Known scope limits (intentional, not bugs)

- `healthy_score` is a simple, explainable heuristic (protein reward, calorie/fat penalty), explicitly not an ML model — see the comment in `meal_service.py` for the exact thresholds and why they're placeholders.
- The knowledge base is a handful of original, hand-written nutrition tips (not scraped/reproduced from any copyrighted source) — enough to demonstrate the retrieval pattern, not a production-scale corpus.
- `scripts/compare_llms.py` is a manual comparison script, not automated benchmarking infrastructure, per the project's explicit scope constraint.

---

## Running the test suite

```bash
pip install -r requirements.txt
pytest tests/ -v
```

Tests run against an in-memory SQLite database (swapped in via fixtures in
`tests/conftest.py`) and mock every external call (Gemini, Telegram,
WhatsApp) — no live credentials or network access needed to run them.
33 tests cover CRUD, conversation memory, meal upload + the V3
recommendation hook, reminders (including the not-found path), both
webhook types (including user auto-creation and the background-task meal
pipeline), rate limiting, the weekly report's date-window aggregation, and
the FAISS index + RecommendationService in isolation (via dependency
injection, so no real embedding model download is required to test them).
