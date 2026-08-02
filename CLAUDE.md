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
- Frontend dev server: `cd frontend && npm run dev` (Vite on 5173, cross-origin to the API on 8080 — that setup works, leave it alone)
- Docker: `docker compose up --build` — **production only**, serves on 8080. Reads `.env.prod` (not `.env`), builds the Vue app in a `node:22-slim` stage, one uvicorn worker, no `--reload`. Migrations are **not** run by the container.
- Type check: pyright (config in `pyrightconfig.json`, venv-aware)
- No tests and no linter configured yet.

## Architecture

FastAPI app in `main.py`: lifespan starts an APScheduler `BackgroundScheduler` that runs `run_all_users` every `SYNCING_INTERVAL_MINUTES` (and once at startup) when `SCHEDULER_ENABLED`; the scheduler itself always starts, because turning a user's sync on queues a one-off job through it. **Because of that scheduler the app runs on exactly one uvicorn worker** — a second worker is a second scheduler and doubles every user's sync. `SessionMiddleware` holds the OAuth `state` cookie; mounts the `oauth`, `apple_calendar`, `notion` and `sync` routers.

**Serving the SPA** (bottom of `main.py`, after every router): if `frontend/dist` exists — it only does inside the Docker image — `StaticFiles` is mounted on `/assets` and a catch-all `GET /{spa_path:path}` returns `index.html` with `Cache-Control: no-cache`. The Vue router uses history mode, so deep links must be answered by the server with the app itself. Paths starting `api/` or `auth/` raise 404 from that handler so a mistyped endpoint never returns HTML. In dev the directory is absent, the block is skipped, and the app is a bare API exactly as before.

**Everything DB is synchronous** — `create_engine` + `sessionmaker` (`core/db.py`), sync `Session` everywhere, psycopg3 driver. Routes are `async def` only because authlib requires `await`; don't introduce `AsyncSession` — that decision was made deliberately (scheduler thread + blocking CalDAV/Notion IO gain nothing from async).

Layers under `backend/` (import modules directly — **no `__init__.py` anywhere**, e.g. `from backend.schemas.notion_page import NotionPage`):

- `core/` — stateless infra, no DB access: `config.py` (`Settings` from `.env`, singleton `settings`), `db.py` (engine + `SessionLocal`), `base.py` (ORM `Base`), `oauth.py` (authlib Google client), `security.py` (`JWTService`, PyJWT HS256, access + refresh tokens), `crypto.py` (Fernet `encrypt`/`decrypt` — **the only module importing Fernet**), `scheduler.py`, `logging.py` (loguru).
- `models/` — SQLAlchemy ORM, one per file: `user.py`, `sync_settings.py` (1 per user: the sync switch, the chosen Notion date column, last run + status), `oauth_account.py` (N per user, unique `(provider, provider_account_id)`, lookup by Google `sub` never email), `caldav_credential.py` (1 per user, iCloud password Fernet-encrypted), `synced_event.py`.
- `schemas/` — pydantic v2 domain models: `caldav_event.py`, `notion_page.py`, `notion_database.py` (both read-only projections of raw Notion payloads), `synced_event.py`.
- `repo/` — data access. `caldav_repo.py` (`CalDavEventRepo`, write side, plus `get_calendar_url`), `notion_repo.py` (`NotionPageRepo`, read-only — no create/update/delete, keep it that way), `user_repo.py` (`UserRepo(db: Session)`, `get_or_create_user_oauth` = login and registration in one). Repos take a `Session`/credentials in the constructor; **caller owns the transaction and the commit** (exception: `sync.py` commits per event deliberately — see below).
- `services/` — flows composing multiple repos: `sync.py` only. Auth is thin enough to live in the route; add a service only when a flow really composes repos with logic.
- `api/` — route handlers: `oauth.py` (`/auth/*`, no prefix — Google's registered redirect URI depends on it), `apple_calendar.py` (`/api/v1/me/apple-calendar*`, per-user iCloud credentials; logic inline in the routes by decision, extract to a service when sync needs to share it), `notion.py` (`/auth/oauth/notion/*` + `/api/v1/me/notion*`; `notion_errors` / `notion_repo_for` / `date_property_names` are shared with the sync router), `sync.py` (`/api/v1/me/sync`, the per-user switch), `account.py` (`DELETE /api/v1/me` — hard delete: the `users` row goes, children cascade, the Notion grant is revoked, a queued one-off sync job is cancelled, auth cookies are cleared; **iCloud is deliberately untouched** — pushed events are the user's data and stay, same as an Apple Calendar disconnect. Body must echo the signed-in email). New API routers get the `/api/v1` prefix so they don't collide with the SPA served at `/` in prod.
- `deps/` — FastAPI dependencies: `db.py` (`get_session`), `auth.py` (`get_current_user` — reads the access cookie, returns the `User` row; every protected route uses it).

### Sync model (core of the app)

- Source of truth: Notion; events recomputed from Notion every run. Mapping key: Notion page id == iCal `uid`.
- `synced_events` table is a **link index** (`(user_id, notion_page_id) -> caldav_href`), not an event mirror. Only rows Calnio owns; foreign Apple Calendar events (no row) are never touched. Every query in the loop is scoped by `user_id`.
- `services/sync.py` reconcile loop: query Notion data source → map pages to events (skip archived / no date in the user's chosen column) → create/update in CalDAV per diff against `synced_events` → delete CalDAV events whose Notion page disappeared. **Commits per event on purpose** — a failure mid-batch must not orphan CalDAV events (uncommitted row → next run re-creates → iCloud 412 duplicate).
- **Per-user:** `sync_user(user_id)` runs one user off their stored Notion grant + iCloud credential + `sync_settings` row; `run_all_users()` is the scheduled job and syncs every eligible user sequentially. Auth failures disable the user (`last_status="auth_error"`); everything else retries next tick. Old `sync_notion_to_caldav` is kept unscheduled and can no longer run (`user_id` is required).
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

`.env` (all required by `Settings`): `ICLOUD_EMAIL`, `APP_SPECIFIC_PASSWORD`, `NOTION_TOKEN`, `DB_URL` (postgresql+psycopg://), `CALDAV_URL`, `TASKS_DATA_SOURCE`, `SYNCING_INTERVAL_MINUTES`, `SCHEDULER_ENABLED`, `EVENT_DUE_DATE_FIELD_NAME`, `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, `GOOGLE_OAUTH_REDIRECT_URI`, `SESSION_SECRET`, `JWT_SECRET`, `CREDENTIALS_ENCRYPTION_KEY`.

`ICLOUD_EMAIL` / `APP_SPECIFIC_PASSWORD` are the **single-user dev path** the scheduler still runs on; real users' credentials live per-row in `caldav_credentials`.

`.env` is the **dev** file; `.env.prod` (gitignored, loaded by `docker-compose.yml`) is production and differs in three keys: `FRONTEND_URL` + both OAuth redirect URIs point at the tunnel hostname, and `COOKIE_SAMESITE=lax` because prod is one origin. Neither file enters the image — see `.dockerignore`, which also excludes `frontend/.env` so the dev `VITE_API_URL` cannot be baked into the prod bundle.

`.env.example` and `.env.prod.example` are current — keep them that way when adding a setting.

## README.md

README holds the working plan: sync model detail, roadmap phases, auth flow + todo checklist, frontend integration plan (Vue/Vite dev on :5173, prod served by FastAPI `StaticFiles`). Check it before starting auth or frontend work — it tracks what's done vs todo.

# Calnio — Design System

Source of truth: `Calnio Landing.dc.html`. Every value below is lifted from that file; if the two disagree, the file wins.

**Product truth (never contradict in copy):** Calnio syncs **one way only, for now** (Notion → Apple Calendar). It is **hosted** — nothing to install, no server to run. It is **free while in beta** because the developer self-hosts it. It is **not open source** — never mention GitHub, MIT, Docker, pip, or a CLI install.

**Voice:** plain, honest, quietly confident. First person singular when the developer speaks ("I host Calnio myself"). No hype, no "revolutionize", no exclamation marks, no marketing superlatives. Sentences short. Say the limitation out loud instead of hiding it.

---

## 1. Foundations

### Color

| Role | Value | Use |
|---|---|---|
| Page background | `#fff` | body + root |
| Ink | `#0a0a0a` | headlines, wordmark, primary buttons, key labels |
| Ink hover | `#262626` | primary button hover only |
| Body copy | `#57554e` | paragraphs on plain white |
| Body copy over atmosphere | `#1d2b38` | paragraphs that sit near/over blue |
| Muted meta | `#8a877e` | mono footnotes on white |
| Muted meta (cool) | `#6b8299` | mono meta inside white cards over blue |
| Nav / footer link | `#3a4a5c` | resting state, hover → `#0a0a0a` |
| Hairline | `#ededea`, `rgba(10,10,10,0.12)` | dividers, footer top border |
| Field / secondary underline | `rgba(10,10,10,0.4)` | text-link underline, input borders |
| Accent (default) | `#0b63f6` | step numerals, atmosphere gradients |
| Accent alternates | `#0a0a0a`, `#2f7d5b`, `#a4670f` | one at a time, via the `accent` prop |
| Selection | bg `#0a0a0a`, text `#fff` | — |

Rules:
- Accent is exposed as `--accent` on the root and consumed as `var(--accent, #0b63f6)`. Never hardcode `#0b63f6` in new components — read the var.
- One accent on screen at a time. Accent is for numerals and the atmosphere, never for body text or buttons.
- Never put ink or body-grey text directly on the saturated part of a blue circle. See §3.

### Type

- **UI / display:** `-apple-system, 'Helvetica Neue', Helvetica, Arial, sans-serif`
- **Mono (labels, meta, numerals):** `'IBM Plex Mono', monospace` — weights 400/500, loaded from Google Fonts in `<helmet>`
- Never Inter, Roboto, Fraunces, or a stylized display face.

| Element | Spec |
|---|---|
| h1 | `clamp(44px,9vw,104px)` / 700 / lh `0.92` / ls `-0.045em` / `text-wrap:balance` |
| h2 | `clamp(32px,6vw,52px)` / 700 / lh `1.02` / ls `-0.04em` |
| h3 (step) | `clamp(19px,4.6vw,21px)` / 600 / ls `-0.01em` |
| h3 (feature) | `17px` / 600 |
| Lead paragraph | `clamp(16px,1.5vw,17px)` / lh `1.55` / max `44–52ch` / `text-wrap:pretty` |
| Body | `15px` (features `14.5px`) / lh `1.6` |
| Mono eyebrow / kicker | `clamp(10.5px,2.6vw,12px)` / uppercase / ls `0.16–0.18em` |
| Mono nav | `12px` / uppercase / ls `0.08em` |
| Mono step numeral | `clamp(30px,6vw,40px)` / 500 / ls `-0.04em` / accent |
| Mono footnote | `12.5px` / lh `1.7` / `#8a877e` |

Line breaks in headlines are authored manually with `<br>` (`Plan it once.<br>See it<br>everywhere.`) — keep them; they set the rhythm.

### Layout & spacing

- Content column `max-width:1180px`, centered, horizontal padding `clamp(20px,5vw,40px)`.
- Section vertical rhythm: `clamp(56px,11vw,120px)` top, `clamp(48px,9vw,96px)` bottom. Hero `clamp(40px,9vw,84px)` top.
- **No breakpoints.** Everything scales with `clamp()` and `min()`; columns reflow with `grid-template-columns: repeat(auto-fit, minmax(<floor>, 1fr))`:
  - two-column text blocks → `minmax(300px, 1fr)`
  - three steps → `minmax(240px, 1fr)`
  - four features / four setup steps → `minmax(220px, 1fr)` / `minmax(200px, 1fr)`
- Always flex/grid + `gap`. Never margin-spaced inline siblings.
- No cards, no boxes, no shadow panels for content. Structure comes from whitespace and the occasional hairline. (Tiles were tried and rejected.)
- Every section: `position:relative; z-index:1` so it stacks above the atmosphere layer (`z-index:0`). Nav is `z-index:2`.

### Mobile / touch

- Every link and button: `display:inline-flex; align-items:center; min-height:44px` (buttons `50px`). Vertical padding on an inline `<a>` does **not** create a hit box — always use inline-flex + min-height.
- `body { overflow-x: hidden }`, `html { -webkit-text-size-adjust: 100% }`, `a { -webkit-tap-highlight-color: rgba(10,10,10,0.06) }`.
- Footer bottom padding: `calc(<pad> + env(safe-area-inset-bottom, 0px))`.
- Atmosphere circles are sized in `min(px, vw)` so they keep proportion on narrow screens.
- Body text never below `14.5px`.

---

## 2. Components

**Primary button**
```html
<a style="display:inline-flex; align-items:center; justify-content:center; text-decoration:none;
  font-size:15px; font-weight:500; color:#fff; background:#0a0a0a;
  padding:16px 24px; min-height:50px; border-radius:8px;" style-hover="background:#262626;">Start syncing</a>
```
No arrow glyph, no lift, no shadow, no transition.

**Secondary link** — mono uppercase `12px`, ls `0.12em`, ink, underline on a nested `<span style="border-bottom:1px solid rgba(10,10,10,0.4); padding-bottom:3px;">` (nested so the 44/50px hit box doesn't drag the rule down).

**Nav** — wordmark `calnio` 700 / `19px` / ls `-0.03em`; links mono `12px` uppercase `#3a4a5c`, the primary one ink with a 1px underline span.

**Mono pill (eyebrow, status line)** — used only where text sits over the atmosphere:
`background:rgba(255,255,255,0.72–0.78); backdrop-filter:blur(8px); padding:7–8px 14–16px; border-radius:999px;` + ink text.

**Event chip** — `background:#fff; padding:13px 18px; border-radius:10px; box-shadow:0 18px 40px -26px rgba(4,32,74,0.85);`, label in UI font, meta in mono `12.5px` `#6b8299`, laid out `display:inline-flex; align-items:baseline; gap:12px`. Flat — no rotation, no tilt.

**Numbered step** — mono numeral in accent, then h3, then body. Column via flex + `gap:12px`. No card, no border.

**Footer** — `border-top:1px solid rgba(10,10,10,0.12)`, `background:rgba(255,255,255,0.72)` + `blur(10px)`, all-mono `12px`, three groups: wordmark / one-line claim / links.

---

## 3. The atmosphere layer (the blue circles)

One page-wide layer, first child of the root, behind everything:

```html
<div style="position:absolute; inset:0; z-index:0; pointer-events:none;"> … </div>
```

It must be **page-wide, never per-section** — a per-section layer produces visible rectangular seams, which is exactly what this replaced. The root carries `position:relative; overflow:hidden` so circles crop against the viewport edge.

**Filled circle recipe** — a radial gradient with a transparent falloff, plus a small blur. The transparent stop is what removes any visible edge:
```css
border-radius: 50%;
background: radial-gradient(circle at 50% 46%,
  #7df3ff 0%, #17a5ff 32%, var(--accent, #0b63f6) 58%,
  rgba(11,99,246,0.14) 76%, rgba(11,99,246,0) 82%);
filter: blur(14px);
```
Cyan core → accent mid → transparent by 82%. Blur `10–20px` (bigger circle, more blur). Never a linear-gradient rectangle, never a white gradient mask to fade a circle out.

**Current placements** (page ≈ 2630px tall at 924px wide):

| # | Position | Size | Character |
|---|---|---|---|
| 1 | `left:-26vw; top:clamp(340px,42vw,540px)` | `min(480px,58vw)` | arc into the hero's lower left |
| 2 | `right:-20vw; top:clamp(600px,72vw,880px)` | `min(420px,50vw)` | arc from the right at the chip band |
| 3 | `left:-6vw; top:clamp(1000px,102vw,1300px)` | `min(200px,28vw)` | small crisp orb, blur `10px` |
| 4 | ring `left:-20vw; top:clamp(1120px,116vw,1480px)` | `min(720px,92vw)` | hairline `1px rgba(11,99,246,0.2)` |
| 5 | `left:50%; bottom:min(-430px,-58vw)` (translateX -50%) | `min(1320px,160vw)` × `min(940px,116vw)` | the big glow under the closing CTA |
| 6 | ring `right:-12vw; bottom:clamp(260px,34vw,420px)` | `min(280px,40vw)` | hairline `1px rgba(10,10,10,0.16)` |

**Grain** — one continuous overlay as the last child of the layer (one for the whole page, so there are no per-section grain seams):
```html
<div style="position:absolute; inset:0; mix-blend-mode:overlay; opacity:0.38;
 background-image:url(data:image/svg+xml,%3Csvg%20xmlns=%27http://www.w3.org/2000/svg%27%3E%3Cfilter%20id=%27g1%27%3E%3CfeTurbulence%20type=%27fractalNoise%27%20baseFrequency=%270.85%27%20numOctaves=%274%27%20stitchTiles=%27stitch%27/%3E%3C/filter%3E%3Crect%20width=%27100%25%27%20height=%27100%25%27%20filter=%27url%28%23g1%29%27/%3E%3C/svg%3E);"></div>
```
`mix-blend-mode: overlay` only. A `multiply` grain layer greys the white page — do not add one.

**Placement discipline (the rule that keeps breaking):** a circle's *saturated band runs to ~76% of its radius*. Any text whose box falls inside that radius is unreadable. So:
1. Circles live in **margins and empty bands** — off-canvas left/right, above the nav, below the last paragraph, in the gap between sections. They enter as arcs, not as full discs.
2. Headlines and body copy stay on clean white.
3. If content must overlap blue, it gets a white surface: an event chip, or a white translucent mono pill with `backdrop-filter:blur(8px)`.
4. Check nav and footer rows explicitly — they are full-width and get hit first.
5. No decorative solid dots floating next to text.

---

## 4. Motion

**There is none.** No `@keyframes`, no drifting circles, no hover lift, no `transition`. Hover changes color only (`background:#262626`, `border-color`, `color:#0a0a0a`). If motion is ever added, it needs a `@media (prefers-reduced-motion: reduce)` escape — but the current direction is deliberately static.

## 5. Banned

Icons of any kind (including arrow glyphs in buttons and status dots) · emoji · hand-drawn SVG imagery · gradient page backgrounds · colored cards with a left-border accent · big radii (max `10px` on chips, `8px` on buttons, `999px` on pills) · heavy drop shadows (only the one chip shadow) · fake app chrome or boxes-as-illustration · rotated/tilted cards · ASCII art · CSS classes or stylesheets for layout (inline styles only; `<helmet><style>` holds only resets, `::selection`, and the font link) · `React.createElement` for layout.

## 6. Component contract (`Calnio Landing.dc.html`)

Props on `<script data-dc-script data-props>`, read as `this.props.x ?? default` in `renderVals()`:

| Prop | Editor | Default | Effect |
|---|---|---|---|
| `accent` | color (`#0b63f6`, `#0a0a0a`, `#2f7d5b`, `#a4670f`) | `#0b63f6` | sets `--accent`: step numerals + circle gradients |
| `showField` | boolean | `true` | toggles the whole atmosphere layer (circles + grain) |
| `showBeta` | boolean | `true` | shows/hides the "free while in beta" line |

Page order: nav → hero → chip band + claim row → beta line → `#how` (3 steps + one-way footnote) → 4 features → `#start` (CTA + 4 setup steps) → footer. Anchors: `#how`, `#start`, both with `scroll-margin-top:24px`.

## 7. Known gaps / next moves

- The chip band is styled text, not proof — real Notion table and Apple Calendar screenshots would carry more weight.
- Nothing addresses failure: a short honest line about failed syncs and retries would build more trust than another feature bullet.
- "No duplicates" and "Smart scheduler" in the feature row restate steps 02 and 03 — worth cutting to two features for more air.
