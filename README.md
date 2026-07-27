# VitaMind AI 🥗🤖

> An AI-powered nutrition and lifestyle companion that remembers your habits over time and gives contextual, practical, budget-conscious recommendations — through Telegram and WhatsApp.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-async-teal)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Table of Contents

- [Overview](#overview)
- [Motivation & Problem Statement](#motivation--problem-statement)
- [Key Features](#key-features)
- [Architecture Overview](#architecture-overview)
- [Technology Stack](#technology-stack)
- [Project Modules](#project-modules)
- [System Flow](#system-flow)
- [Request Lifecycle](#request-lifecycle)
- [Memory Architecture](#memory-architecture)
- [Recommendation Engine](#recommendation-engine)
- [Reminder & Notification System](#reminder--notification-system)
- [Database Design](#database-design)
- [API Overview](#api-overview)
- [Folder Structure](#folder-structure)
- [Installation Guide](#installation-guide)
- [Environment Variables](#environment-variables)
- [Running the Backend](#running-the-backend)
- [Connecting Telegram](#connecting-telegram)
- [Connecting WhatsApp](#connecting-whatsapp)
- [Security Considerations](#security-considerations)
- [Performance & Scalability](#performance--scalability)
- [Error Handling Strategy](#error-handling-strategy)
- [Future Scope](#future-scope)
- [Screenshots](#screenshots)
- [Resume Highlights](#resume-highlights)
- [Learning Outcomes](#learning-outcomes)
- [Contributing](#contributing)
- [License](#license)

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

```mermaid
flowchart TD
    A[Telegram / WhatsApp] -->|Webhook| B[FastAPI API Layer]
    B --> C[Service Layer]
    C --> D[Repository Layer]
    D --> E[(MySQL)]
    C --> F[RAG Service]
    F --> G[(Vector DB - Knowledge Base)]
    C --> H[Gemini Client]
    I[APScheduler] --> C
    C --> J[Notification Service]
    J --> K[Telegram Sender]
    J --> L[WhatsApp Sender]
```

The design follows a layered architecture: routers are thin, services hold logic, repositories own all DB access, and the LLM/RAG layers are isolated behind their own service boundary so they can be swapped or mocked independently.

## Technology Stack

| Layer | Technology |
|---|---|
| Backend framework | FastAPI (async) |
| LLM | Google Gemini API |
| Structured memory | MySQL |
| Knowledge retrieval | ChromaDB (vector store) |
| Scheduler | APScheduler |
| Messaging | Telegram Bot API, WhatsApp Business API |
| Validation | Pydantic |
| Migrations | Alembic |
| Testing | pytest, pytest-asyncio, unittest.mock |

## Project Modules

- **Ingestion** — meal/exercise/sleep/water/weight logging, including Gemini Vision for meal photos
- **Memory** — structured (MySQL) + knowledge (vector DB) memory, described below
- **Recommendation Engine** — the core pipeline combining user state + retrieved knowledge
- **Scheduler & Reminders** — proactive check-ins
- **Notifications** — unified send layer across Telegram/WhatsApp
- **Dashboard & Reports** — daily/weekly aggregation

## System Flow

```mermaid
sequenceDiagram
    participant U as User
    participant T as Telegram/WhatsApp
    participant F as FastAPI
    participant S as Service Layer
    participant D as MySQL
    participant V as Vector DB
    participant G as Gemini

    U->>T: "I had oats and milk for breakfast"
    T->>F: Webhook POST
    F->>S: log_meal()
    S->>D: INSERT meal
    D-->>S: OK
    S-->>F: confirmation
    F-->>T: "Logged! 320 kcal, 12g protein"
    T-->>U: reply

    U->>T: "What should I eat for dinner?"
    T->>F: Webhook POST
    F->>S: get_recommendation()
    S->>D: fetch today's logs
    S->>V: retrieve relevant knowledge chunks
    S->>G: generate(prompt with logs + knowledge)
    G-->>S: recommendation + reasoning
    S-->>F: response
    F-->>T: reply
    T-->>U: personalized dinner suggestion
```

## Request Lifecycle

A meal-photo upload, end to end:

1. User sends a photo to the Telegram bot.
2. Telegram delivers it to the FastAPI webhook.
3. The API layer downloads the image and hands it to the service layer.
4. Gemini Vision extracts food items and estimates macros.
5. The service layer stores the meal via the repository layer.
6. A short confirmation with macros is sent back immediately.
7. The scheduler later uses this row when computing reminders and the daily dashboard — no separate sync step needed, since everything reads from the same MySQL tables.

## Memory Architecture

VitaMind AI deliberately separates two kinds of memory:

| Type | Storage | Contains |
|---|---|---|
| **Structured memory** | MySQL | Meals, exercise, sleep, water, weight, goals, preferences, reminders, raw chat log |
| **Distilled memory** | MySQL (`user_facts`) | Allergies, recurring patterns, favorite/disliked foods — extracted periodically from chat, not searched semantically |
| **Knowledge memory** | Vector DB (ChromaDB) | Chunked, embedded transcripts from trusted nutrition education sources, retrieved by semantic similarity |

Structured and distilled memory answer "what does this user do." Knowledge memory answers "what's the expert-backed guidance." The recommendation engine combines both — user state is never inferred from vector search, and expert knowledge is never guessed from user logs.

## Recommendation Engine

```mermaid
flowchart LR
    A[User question] --> B[Fetch today's logs - MySQL]
    B --> C[Analyze deficits/excesses]
    C --> D[Retrieve relevant knowledge chunks - Vector DB]
    D --> E[Build prompt: state + knowledge + preferences]
    E --> F[Gemini generation]
    F --> G[Response + reasoning]
```

The pipeline is a plain, linear Python function — deliberately not a multi-agent graph, since there's no branching decision logic that would justify one. Each step is independently unit-testable.

## Reminder & Notification System

APScheduler runs in-process and checks state against MySQL on a fixed schedule (e.g., water check every 2 hours, meal check at fixed windows, weekly report on Sundays). Both the scheduler and the API call a single shared `NotificationService`, which is the only component allowed to actually send a message — this prevents duplicated, drifting send logic across the codebase.

## Database Design

Core tables: `users`, `preferences`, `meals`, `exercise_logs`, `sleep_logs`, `water_logs`, `weight_logs`, `goals`, `reminders`, `chat_history`, `user_facts`, `nutrition_reports`. All log tables carry a composite `(user_id, logged_at)` index, since every real query is "this user's data in a date range." Full DDL lives in `database/schema.sql`.

## API Overview

```
POST /meals              GET  /dashboard
POST /exercise           GET  /reports/weekly
POST /water               GET  /recommendation
POST /sleep               POST /chat
POST /weight              POST /reminders
GET  /goals                POST /webhook/telegram
POST /goals                POST /webhook/whatsapp
```

## Folder Structure

```
app/
├── api/            # thin FastAPI routers
├── services/        # business logic
├── repositories/     # all DB access
├── models/           # SQLAlchemy ORM models
├── schemas/           # Pydantic request/response contracts
├── memory/
│   ├── structured/
│   └── knowledge/
├── llm/               # Gemini client, prompt builder
├── prompts/            # prompt templates as files
├── scheduler/           # APScheduler jobs
├── notifications/
│   ├── telegram/
│   └── whatsapp/
├── database/             # engine, session, Alembic migrations
├── middleware/            # auth, logging, error handling
├── config/                # settings via pydantic-settings
├── utils/
└── main.py
tests/
scripts/                    # e.g. knowledge base indexing
```

## Installation Guide

```bash
git clone https://github.com/<your-username>/vitamind-ai.git
cd vitamind-ai
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # fill in your keys
alembic upgrade head
```

## Environment Variables

```
DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/vitamind
GEMINI_API_KEY=
TELEGRAM_BOT_TOKEN=
WHATSAPP_API_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
VECTOR_DB_PATH=./chroma_store
ENV=development
LOG_LEVEL=INFO
```

## Running the Backend

```bash
uvicorn app.main:app --reload --port 8000
python -m app.scheduler.runner   # separate process for scheduled jobs
```

## Connecting Telegram

1. Create a bot via [@BotFather](https://t.me/BotFather), get the token.
2. Set the webhook: `curl -F "url=https://<your-domain>/webhook/telegram" https://api.telegram.org/bot<TOKEN>/setWebhook`
3. Message the bot to confirm the webhook fires.

## Connecting WhatsApp

1. Register a WhatsApp Business API app via Meta for Developers.
2. Configure the webhook callback URL and verify token.
3. Point it at `/webhook/whatsapp`.

## Security Considerations

- Webhook endpoints verify Telegram/WhatsApp signing secrets before processing.
- No API keys or tokens in source — all via environment variables, `.env` gitignored.
- Input validation on every endpoint via Pydantic — no raw payload trust.
- Parameterized queries only (SQLAlchemy) — no string-built SQL.

## Performance & Scalability

- All I/O-bound routes are `async` — DB, Gemini, and messaging calls don't block the event loop.
- Composite indexes on every log table for the (user_id, date-range) access pattern.
- Repository pattern keeps MySQL swappable and mockable without touching services.
- Deliberately **not** using Celery/Redis or a managed vector DB at this stage — see architecture doc for the reasoning; noted here as a known scaling path, not a current gap.

## Error Handling Strategy

- Centralized exception handlers in `middleware/` translate internal exceptions into consistent API error responses.
- Gemini/network calls wrapped with retries + timeouts; failures degrade to a graceful "try again" message rather than a raw 500.
- All external-call failures logged with context (user_id, endpoint, payload hash) for debugging.

## Future Scope

Wearable/Google Fit integration, barcode food scanning, recipe generation, voice interface, multilingual support, weekly AI-coach summaries — all designed to plug in via the existing repository/service boundaries without refactoring the core.

## Screenshots

`![Dashboard](docs/screenshots/dashboard.png)` *(placeholder)*

## Demo

`![Demo](docs/demo.gif)` *(placeholder)*

## Resume Highlights

- Designed and built a layered backend (API/service/repository) with async FastAPI and MySQL
- Implemented a RAG pipeline (chunking, embeddings, vector retrieval) grounding LLM output in a curated knowledge base
- Built a proactive notification system using APScheduler decoupled from the API layer
- Made and documented explicit architecture trade-offs (e.g., rejecting LangGraph and Celery as premature for the scale of the project)

## Learning Outcomes

Clean architecture and separation of concerns, prompt engineering for grounded generation, RAG pipeline design, async Python, scheduled background jobs, multi-channel bot integration.

## Contributing

This is currently a personal portfolio project; issues and suggestions are welcome via GitHub Issues. PRs should follow the branch naming `feature/<name>`, `fix/<name>`, and include tests for new logic.

## License

MIT