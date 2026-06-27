# CLAUDE.md

Guidance for Claude Code working in this repo. Durable context — not a task list or changelog.

## Project

- **Calnio** — syncs Notion with Apple Calendar.
- Notion holds tasks/events; Apple Calendar is where people actually look. Calnio pushes Notion dates into Apple Calendar automatically.
- End goal: full two-way sync.
- MVP (current, only thing in scope): one-way sync, **Notion → Apple Calendar**.

## Scope

IN scope now:
- Read pages from Notion.
- Write events to Apple Calendar via CalDAV.
- Track sync state.

OUT of scope now (do not build):
- Two-way sync.
- Any write back to Notion — **Notion is a READ-ONLY source in the MVP**.
- Calendar → Notion propagation.

## Stack

- Python 3.11+ (pyproject pins `requires-python >=3.14`), pydantic v2, FastAPI, Vue.js, PostgreSQL.
- Package manager: **uv** (not pip).
- Integrations: `notion-client`, `caldav` 3.x, `icalendar`, `loguru`.
- Settings via `pydantic-settings`.

## Architecture

Current code (`backend/`). Only `core/`, `deps/`, `repo/` exist — no `api/` or `services/` yet; `deps/caldav.py` is empty.

- `core/config.py` — `Settings(BaseSettings)` from `.env`: `icloud_email`, `app_specific_password`, `notion_token`. Exports singleton `settings`.
- `repo/models/` — pydantic v2 models, one per file, re-exported from `models/__init__.py`:
  - `CalDavEvent` — `uid, title, start, end, all_day, calendar, href, created_at, updated_at`.
  - `NotionPage` (read-only projection) — `id, title, parent_id, parent_type, properties (raw dict), url, archived, created_at, updated_at`.
  - `NotionDatabase` (read-only projection) — `id, title, properties (raw schema), url, created_at, updated_at`.
- `repo/caldav_repo.py` — `CalDavEventRepo(caldav_url, username, password, calendar_url)`. Write side.
  - `connect()`, `get_range(start, end) -> list[CalDavEvent]`, `create(event) -> CalDavEvent`, `update(event) -> CalDavEvent`, `delete(event) -> None`.
  - Module-level helpers: `_to_ical`, `_from_caldav`, `_as_datetime`.
- `repo/notion_repo.py` — `NotionPageRepo(token)`. Read-only source.
  - `connect()`, `client` (property, asserts connected), `get_page(page_id) -> NotionPage`, `get_database(data_source_id) -> NotionDatabase`, `query_database(data_source_id, *, filter=None, sorts=None) -> list[NotionPage]`, `list_databases() -> list[NotionDatabase]` (via `search`). All read-only; no create/update/delete.
  - **API 2025-09-03 (notion-client 3.1.0):** databases are containers of *data sources*; pages + schema live on the data source. So `get_database`/`query_database` hit `client.data_sources.retrieve`/`.query` and take a `data_source_id`; `list_databases` searches with filter value `"data_source"`. `databases.query` no longer exists. See `[[notion-data-source-api-split]]`.
  - Module-level helpers: `_join_rich_text`, `_extract_title`, `_extract_parent_id`, `_parse_ts`, `_from_notion`, `_from_notion_database`, `_paginate` (drains `start_cursor`/`has_more`).
- `main.py` — current entry/demo: `discover_calendar_url()`, `week_range()`, `main()` prints this week's iCloud events. (FastAPI `app` referenced in run command not yet present.)

## Data & sync state

- **PostgreSQL is the only store.** No JSON files, no local-file shortcuts.
- `synced_events` table (`uid, href, etag`) is the source of truth for sync state — avoids constantly re-reading iCloud.
- Not yet implemented in code; build it in Postgres when adding persistence.

## iCloud CalDAV quirks

- Requires `features="icloud"` and app-specific-password auth.
- Server-side search is unreliable → use client-side fallback filtering.
- Cache the calendar home URL per user after first discovery; do not re-discover each run.

## Conventions & principles

- **Simplicity is rule #1.** No premature abstraction, no extra layers/classes, no scope creep. Answer the actual need, nothing more.
- Conversion logic lives as private methods/module functions inside the repo modules — **no separate mapper classes**.
- Notion parsing rules (real shapes): title = property whose `type == "title"` (key is the column name, not literally `"title"`); `parent_id` from `parent[parent["type"]]`, coerced to `None` when value is the workspace bool; timestamps parsed to aware UTC.

## Run

- Install deps: `uv sync`
- Add dep: `uv add <package>` (dev: `uv add --dev <package>`)
- Dev server: `uv run uvicorn main:app --reload` (once FastAPI `app` exists)
- Current demo script: `uv run python main.py`

## Config

`.env`: `ICLOUD_EMAIL`, `APP_SPECIFIC_PASSWORD`, `NOTION_TOKEN`.
