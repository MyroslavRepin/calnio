# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

- **Calnio** — syncs Notion with Apple Calendar. Notion holds tasks; Apple Calendar is where people look. Calnio pushes Notion due dates into Apple Calendar via CalDAV on a schedule.
- MVP (only thing in scope): **one-way sync, Notion → Apple Calendar**. Notion is a READ-ONLY source — no write back to Notion, no Calendar → Notion propagation, no two-way sync. Do not build those.
- Second track in progress: Google OAuth login (see README "Auth" section for flow + todo list).

## Commands

- Install deps: `uv sync` (package manager is **uv**, not pip)
- Add dep: `uv add <package>` (dev: `uv add --dev <package>`)
- Dev server: `uv run uvicorn main:app --reload --port 8080`
- Migrations: `uv run alembic upgrade head`; new one: `uv run alembic revision --autogenerate -m "..."` (autogenerate works — `alembic/env.py` imports all models and uses `Base.metadata`; a new model must be imported there or autogenerate won't see it)
- Docker: `docker compose up --build` (serves on 8080)
- Type check: pyright (config in `pyrightconfig.json`, venv-aware)
- No tests and no linter configured yet.

## Architecture

FastAPI app in `main.py`: lifespan starts an APScheduler `BackgroundScheduler` that runs `sync_notion_to_caldav` every `SYNCING_INTERVAL_MINUTES` (and once at startup); `SessionMiddleware` holds the OAuth `state` cookie; mounts `backend/api/oauth.py` router.

**Everything DB is synchronous** — `create_engine` + `sessionmaker` (`core/db.py`), sync `Session` everywhere, psycopg3 driver. Routes are `async def` only because authlib requires `await`; don't introduce `AsyncSession` — that decision was made deliberately (scheduler thread + blocking CalDAV/Notion IO gain nothing from async).

Layers under `backend/` (import modules directly — **no `__init__.py` anywhere**, e.g. `from backend.schemas.notion_page import NotionPage`):

- `core/` — stateless infra, no DB access: `config.py` (`Settings` from `.env`, singleton `settings`), `db.py` (engine + `SessionLocal`), `base.py` (ORM `Base`), `oauth.py` (authlib Google client), `security.py` (`JWTService`, PyJWT HS256, access + refresh tokens), `scheduler.py`, `logging.py` (loguru).
- `models/` — SQLAlchemy ORM, one per file: `user.py`, `oauth_account.py` (N per user, unique `(provider, provider_account_id)`, lookup by Google `sub` never email), `synced_event.py`.
- `schemas/` — pydantic v2 domain models: `caldav_event.py`, `notion_page.py`, `notion_database.py` (both read-only projections of raw Notion payloads), `synced_event.py`.
- `repo/` — data access. `caldav_repo.py` (`CalDavEventRepo`, write side, plus `get_calendar_url`), `notion_repo.py` (`NotionPageRepo`, read-only — no create/update/delete, keep it that way), `user_repo.py` (`UserRepo(db: Session)`, `get_or_create_user_oauth` = login and registration in one). Repos take a `Session`/credentials in the constructor; **caller owns the transaction and the commit** (exception: `sync.py` commits per event deliberately — see below).
- `services/` — flows composing multiple repos: `sync.py` only. Auth is thin enough to live in the route; add a service only when a flow really composes repos with logic.
- `api/` — route handlers: `oauth.py` (`/auth/oauth/google/login` + `/callback`).
- `deps/` — FastAPI dependencies: `db.py` (`get_session`).

### Sync model (core of the app)

- Source of truth: Notion; events recomputed from Notion every run. Mapping key: Notion page id == iCal `uid`.
- `synced_events` table is a **link index** (`notion_page_id -> caldav_href`), not an event mirror. Only rows Calnio owns; foreign Apple Calendar events (no row) are never touched.
- `services/sync.py` reconcile loop: query Notion data source → map pages to events (skip archived / no Due Date) → create/update in CalDAV per diff against `synced_events` → delete CalDAV events whose Notion page disappeared. **Commits per event on purpose** — a failure mid-batch must not orphan CalDAV events (uncommitted row → next run re-creates → iCloud 412 duplicate).
- Change detection: compare title directly, then last-edited timestamp LWW — Notion's `last_edited_time` is minute-rounded, so a pure timestamp check misses same-minute edits.
- `reset_all()` in `sync.py` wipes every CalDAV event + all `synced_events` rows — destructive, never call casually.

## Notion API (2025-09-03, notion-client 3.x)

Databases are containers of *data sources*; pages and schema live on the data source. `databases.query` no longer exists — `NotionPageRepo.get_database`/`query_database` hit `client.data_sources.retrieve`/`.query` with a `data_source_id`; `list_databases` searches with filter value `"data_source"`.

Notion parsing rules (real payload shapes): title = the property whose `type == "title"` (key is the column name, not literally `"title"`); `parent_id` from `parent[parent["type"]]`, `None` when the value is the workspace bool; timestamps parsed to aware UTC.

## iCloud CalDAV quirks

- Needs `features="icloud"` and app-specific-password auth.
- Server-side search unreliable → client-side fallback filtering.
- Calendar home URL discovery is slow; the target calendar (named "Calnio") is resolved via `get_calendar_url` at sync start.
- Known issue: events occasionally duplicate with the same UID (see README "Known errors").

## Conventions

- **Simplicity is rule #1.** No premature abstraction, no extra layers, no scope creep.
- Conversion logic = private module functions inside the repo modules (`_page_to_event`, `_from_notion`, …) — no separate mapper classes.
- PostgreSQL is the only store — no JSON files, no local-file shortcuts.
- Timestamps: ORM rows use db-managed `row_created_at`/`row_updated_at`; domain timestamps are timezone-aware UTC.

## Config

`.env` (all required by `Settings`): `ICLOUD_EMAIL`, `APP_SPECIFIC_PASSWORD`, `NOTION_TOKEN`, `DB_URL` (postgresql+psycopg://), `CALDAV_URL`, `TASKS_DATA_SOURCE`, `SYNCING_INTERVAL_MINUTES`, `EVENT_DUE_DATE_FIELD_NAME`, `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, `GOOGLE_OAUTH_REDIRECT_URI`, `SESSION_SECRET`.

`.env.example` is stale (lists only the first three keys).

## README.md

README holds the working plan: sync model detail, roadmap phases, auth flow + todo checklist, frontend integration plan (Vue/Vite dev on :5173, prod served by FastAPI `StaticFiles`). Check it before starting auth or frontend work — it tracks what's done vs todo.
