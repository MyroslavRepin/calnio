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
- `parsers/` — raw third-party payloads into domain schemas, one class per topic: `notion.py` (`NotionParser`), `caldav.py` (`ICalParser`, both directions of the iCal format). Held by the repo as `self.parser`.
- `repo/` — data access, filenames never repeat the folder: `caldav.py` (`CalDavAccountRepo` for calendars, `CalDavEventRepo` for events in one calendar), `notion.py` (`NotionPageRepo`, read-only, no create/update/delete, keep it that way), `user.py` (`UserRepo(db: Session)`, `get_or_create_user_oauth` = login and registration in one), `notion_connection.py` (grant rows plus `revoke()`), `caldav_credential.py`, `sync_settings.py`. A repo's client is built in `__init__`, so constructing one authenticates. **Caller owns the transaction and the commit**, except `services/sync.py`, which commits per event deliberately.
- `services/` — flows composing multiple repos: `sync.py` only. Auth is thin enough to live in the route; add a service only when a flow really composes repos with logic.
- `api/` — route handlers, one literal path per decorator: `oauth.py` (`/auth/*`, since Google's registered redirect URI depends on it), `apple_calendar.py` (`/api/v1/me/apple-calendar*`, per-user iCloud credentials), `notion.py` (`/auth/oauth/notion/*` + `/api/v1/me/notion*`), `sync.py` (`/api/v1/me/sync`, the per-user switch), `account.py` (`DELETE /api/v1/me`, a hard delete: the `users` row goes, children cascade, the Notion grant is revoked, a queued one-off sync job is cancelled, auth cookies are cleared; **iCloud is deliberately untouched**, pushed events are the user's data and stay, same as an Apple Calendar disconnect. Body must echo the signed-in email). New API routers take the `/api/v1` prefix so they don't collide with the SPA served at `/` in prod.
- `deps/` — FastAPI dependencies and the plumbing routers share: `db.py` (`get_session`), `auth.py` (`get_current_user` reads the access cookie and returns the `User` row, plus `set_auth_cookies` / `clear_auth_cookies`), `notion.py` (`get_connection`, `get_notion_repo`, `notion_errors`, `date_property_names`), `caldav.py` (`get_credential`, `icloud_errors`, `icloud_credentials`), `sync.py` (`get_sync_settings`, `is_eligible`, `sync_status`).

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
- Raw payload parsing lives in `backend/parsers/`, one class per topic. See "Repo layer" below.
- PostgreSQL is the only store — no JSON files, no local-file shortcuts.
- Timestamps: ORM rows use db-managed `row_created_at`/`row_updated_at`; domain timestamps are timezone-aware UTC.

## Code style

Binding rules. Existing code that breaks them is wrong and gets rewritten, not copied.

**Comments**

1. One-line docstring per function, saying WHAT it does. Never a paragraph, never a WHY essay, never a multi-line docstring unless a real trap needs recording.
2. Inline comments only where the logic is genuinely unclear. Not to restate a line.
3. **No em dashes anywhere.** Use a comma, a colon, or a full stop.

**Layout, one thing per folder**

4. Pydantic request/response models live in `backend/schemas/<feature>.py`, grouped per feature. Never defined inside a router.
5. FastAPI dependencies live in `backend/deps/<feature>.py`. Chain them, so a route receives the finished object (`repo: NotionPageRepo`), not a row plus a factory call.
6. Routers never import from other routers. Anything two routers share moves to `deps/`.
7. Filenames do not repeat their folder. `repo/notion_connection.py`, not `repo/notion_connection_repo.py`. Classes keep the role suffix: `NotionConnectionRepo`.
8. Network calls belong in `repo/`. Nothing in `api/` opens a connection to a third party.
9. Use a dedicated client library, never raw HTTP by hand. Notion goes through `notion-client`, iCloud through `caldav`, OAuth including token revocation through `authlib`.
10. No service layer for a flow with one caller. Logic stays in the handler until a second caller appears.

**Routes**

11. Full literal path in every decorator: `@router.get("/api/v1/me/notion/databases")`. No path constants, no f-strings, no router prefixes.
12. `response_model=` on the decorator declares the contract. No return annotation on handlers.
13. Routes with no payload return 204 and no body.
14. Take an injected `response: Response` to set cookies. Construct a response object only for redirects, or when cookies must survive an error branch.
15. All handlers are `async def`, uniformly.

**Code**

16. Row to schema conversion is `model_validate` with `model_config = ConfigDict(from_attributes=True)`. No hand-written mapper functions in the API layer.
17. Full words, verb first. No `rv`, no `_bounce`. Names carry no abbreviations.
18. Prefer the shorter shape. Two helpers beat four wrappers; a literal beats a constant used once.
19. Singletons for stateless services live at the bottom of their `core/` module, same shape as `settings`: `jwt_service = JWTService(settings.jwt_secret)`. Nobody constructs a second one.
20. Logging in `api/`: warnings and errors on every failure branch, `info` only for events that happen once per user and cannot be undone (connect, disconnect, delete).
21. **No leading underscore anywhere in `backend/`.** Not on methods, not on module functions, not on attributes. Layout communicates scope, naming does not.

**Repo layer**

22. Every repo is a class, and its client is built in `__init__`. No `connect()` step, no `assert self.client is not None` guards, no `Client | None` attributes.
23. One class per resource, not per remote system: `CalDavAccountRepo` owns calendars, `CalDavEventRepo` owns events inside one calendar. A constructor argument that only half the methods use means the class should be two.
24. Repos log almost nothing: a count after a bulk read, a warning before a destructive bulk write. Never a line before and after the same call. The caller owns the narrative.
25. Raw payload parsing lives in `backend/parsers/<topic>.py` as a class with instance methods, held by the repo as `self.parser`. Verb-first method names: `parse_page`, `parse_database`, `parse_event`, `render_event`. Pagination and other transport concerns stay in the repo.
26. Repos raise `RuntimeError` on a failed lookup. A custom exception class waits until something needs to catch that specific failure and act on it.
27. A repo returns a bare row unless a caller genuinely branches on extra information. `(row, created)` exists only where a route answers 201 versus 200.

## Config

`.env` (all required by `Settings`): `ICLOUD_EMAIL`, `APP_SPECIFIC_PASSWORD`, `NOTION_TOKEN`, `DB_URL` (postgresql+psycopg://), `CALDAV_URL`, `TASKS_DATA_SOURCE`, `SYNCING_INTERVAL_MINUTES`, `SCHEDULER_ENABLED`, `EVENT_DUE_DATE_FIELD_NAME`, `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, `GOOGLE_OAUTH_REDIRECT_URI`, `SESSION_SECRET`, `JWT_SECRET`, `CREDENTIALS_ENCRYPTION_KEY`.

`ICLOUD_EMAIL` / `APP_SPECIFIC_PASSWORD` are the **single-user dev path** the scheduler still runs on; real users' credentials live per-row in `caldav_credentials`.

`.env` is the **dev** file; `.env.prod` (gitignored, loaded by `docker-compose.yml`) is production and differs in three keys: `FRONTEND_URL` + both OAuth redirect URIs point at the tunnel hostname, and `COOKIE_SAMESITE=lax` because prod is one origin. Neither file enters the image — see `.dockerignore`, which also excludes `frontend/.env` so the dev `VITE_API_URL` cannot be baked into the prod bundle.

`.env.example` and `.env.prod.example` are current — keep them that way when adding a setting.

## README.md

README holds the working plan: sync model detail, roadmap phases, auth flow + todo checklist, frontend integration plan (Vue/Vite dev on :5173, prod served by FastAPI `StaticFiles`). Check it before starting auth or frontend work — it tracks what's done vs todo.

# Calnio Frontend

Vue 3 with `<script setup>`, Vite, vue-router. Two dependencies total: `vue` and `vue-router`. No Tailwind, no state library, no UI kit, no icon set. The design systems below describe how it looks; this section describes how the code is arranged.

## How it works, read this before changing anything

**Two looks, one app, nothing shared.** The landing page at `/` and every signed-in page share no token, no class and no component. Landing rules live under `.landing-ui`, app rules under `.app-ui`, and the wrapper class on the page root decides which system applies. That is why `.btn` legitimately means two different buttons. Landing is about a quarter of the code and changes rarely; the app is the part that gets worked on.

**A composable is one shared box of data, not a layer.** In `composables/useNotion.js` the `reactive({...})` sits at the top level of the file, outside the exported function. JavaScript runs a module's top level once no matter how many components import it, so there is exactly one `state` object in the whole app, and every `useNotion()` call hands back that same object. Put it inside the function and each caller gets its own copy, which is what breaks things: `ConnectionsView` draws the status pill from `notion.connection` while `NotionStatus` sets that same object to `null` on disconnect, and the pill updates only because both point at one object.

```js
const { state, connect } = useNotion()   // the shared box
state.connection                          // read it in the template
await connect()                           // change it, every screen sees the change
```

`state` is handed out through `readonly()`. Components never assign to it, they call an action.

**Auth, start to finish.** `main.js` mounts the app, `App.vue` calls `bootstrap()` once. `bootstrap()` strips `?auth_error=` off the URL, then calls `fetchMe()`, which goes through `apiFetch`. `apiFetch` adds `credentials: 'include'`, so the browser attaches its cookies. Both tokens live in httpOnly cookies: the JavaScript never holds a token and never stores one. On a 401, `apiFetch` calls `refresh()` once and retries; `refresh` keeps a single in-flight promise so ten parallel 401s cause one refresh. The result is `state.user` plus `state.ready`, and `state.ready` is the one flag that stops the whole app flickering before auth is known. Login is a real `window.location.href` navigation, not a fetch, because the browser has to follow redirects to Google and back.

**Who loads data.** The shell (`DashboardLayout`, `WelcomeView`) loads the cheap facts every page needs, through `loadWhenSignedIn`. A component loads the slow lists itself, on demand, when the user asks: the iCloud calendar listing and the Notion database listing are slow third-party calls and must not run on page load. Those are the only two cases.

## Rules

Binding. Existing code that breaks them is wrong and gets rewritten, not copied.

**Layout**

1. `views/` holds one file per route, `components/` holds pieces. Both split into `landing/` and `app/`, and a file in one half never imports from the other.
2. Filenames say what the thing is. A view ends in `View`, a layout in `Layout`, everything else is a plain noun. No `The` prefix.
3. Styles live in `styles/`: `tokens.css` (variables and the page reset), `layout.css` (the three arrangement classes), `base.css` (page-level type, headers, status text), `components.css` (card, label, button, form, list, datarows, wizard), `landing.css` (everything under `.landing-ui`). `main.js` imports them in that order, because each reads from the ones before it.

**Styles**

4. **There are three ways to arrange anything, and they are named.** `column` puts children one under the other, `row` puts them side by side and wraps, `grid` makes columns that reflow. They live unscoped in `layout.css`, they are the only unscoped classes in the project, and they carry no colour and no type. Never write `display: flex` in a component to get one of these three again.
5. The gap is always different, so it comes from the element: `<div class="column hero">` plus `.hero { --gap: 24px; }`. A `grid` also sets `--col`, the narrowest a column may get before one drops to the next line.
6. A local class carries only what is unique to that one place. If it declares more than two or three properties, look for the shared class it should be sitting on instead.
7. A rule that appears in two components belongs in `components.css`. A rule used once stays in that component's `<style scoped>`.
8. Components read variables, never raw values. A hex, a font size or a gap written in a component is a bug: it means a token is missing. The only literals left are one-off geometry, like a progress bar's height or a toggle track's width.
9. Apart from the three layout classes, every shared class name is defined once, under `.app-ui` or under `.landing-ui`. Never unscoped, and never the same name in both.
10. **A class names the thing, not where it sits or what shape it is.** `inner`, `bar`, `side`, `right`, `head`, `sub`, `off`, `spaced`, `cell`, `mark` and `line` are banned: they force you to read the markup to learn what they mean. `progressfill`, `syncoffnote`, `checkmark`, `stephead`, `newcalendar` do not. Short, lowercase, no BEM, no utility classes.
11. Never leave two rules for one class at equal specificity in different files. `.landing-ui .links` in `landing.css` and a scoped `.links` in a component tie, and which wins then depends on file order.

**Components**

12. A component exists when its markup repeats, or when it is a self-contained area with its own state, its own load and its own styles. Not for tidiness, and not to shorten a file.
13. A component never receives a prop it does not use itself.
14. All components are `<script setup>`. No Options API anywhere.
15. A component reports a failure upward when the page owns the error display. It shows the error itself only when the message belongs inside that component's own box.

**Data**

16. Every network call goes through a composable in `composables/`. Nothing in a component calls `fetch` directly.
17. A composable exists when more than one screen reads the same data. Its state is created at module level so all screens share one copy.
18. Composables return `{ state, ...actions }`. State is `readonly`, actions return `{}` on success or `{ error }` on failure, and the caller decides what to show. `send()` in `useAuth.js` is the one place a request is made, and it never throws.
19. A shell loads cheap shared data through `loadWhenSignedIn`. A component loads a slow third-party list on demand. Nothing else triggers a load.
20. New dependencies need to be asked for first.

**How the JavaScript is written**

The frontend is written to be read by someone learning it, not to be short. Verbose and obvious beats clever and dense, every time.

21. **No destructuring.** Call the composable, keep the result, then pull one name per line. `const notionResult = useNotion()`, then `const state = notionResult.state`. Renaming in a destructure (`const { state: notion }`) hides where a name came from.
22. **`function` everywhere, no arrows.** `computed(function () { ... })`, `list.find(function (calendar) { ... })`. A callback gets a named parameter, never `c` or `e`.
23. **Branches are written out.** No ternaries in script, no `||` or `??` chains standing in for a fallback, no `switch`. An `if` per case, each returning. Where a value has a fallback, give the fallback its own `if`.
24. **A comment above every block**, saying what that block is for in plain words. This is the one place where more comments are wanted, and it does not contradict rule 26: the comment names the block's job, it does not restate a line.
25. Anything that needs a fallback for display gets its own `computed`, so the template stays free of `||` and `?:`. `{{ workspaceName }}`, not `{{ notion.connection.workspace_name || '—' }}`. The template is allowed one ternary for a class or a button label, nothing more.

**Comments**

26. Beyond rule 24's block comments, a comment survives only if it records a trap that would otherwise be hit again, like why the router has no auth guard. A comment that restates the line under it gets deleted.
27. No em dashes anywhere.

# Calnio Landing — Design System

**Scope: the landing page only** (`/`, `views/LandingPage.vue` and the components it imports, tokens in `frontend/src/styles/global.css`). Every signed-in page follows the separate app design system at the bottom of this file. The two never share a token.

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

# Calnio App Design System

**Scope: everything except the landing page**, `/dashboard`, `/dashboard/connections`, `/dashboard/settings`, `/welcome`, `/me`, and every component they import. Source of truth: `frontend/src/styles/app.css`. If this document and that file disagree, the file wins.

The app is not the landing page and must not look like it: no atmosphere circles, no mono eyebrows, no 104px display type, no `.surface` panels. The landing page sells; the app reports state and takes instructions. It should read like a settings screen a bank could ship.

**Rules that hold everywhere here**

1. Every rule lives under `.app-ui` and nothing else. The shell (`DashboardLayout`, `WelcomeView`) puts that class on its root, so `global.css` and `app.css` cannot collide.
2. **Components read tokens, never raw values.** A hex, a px gap or a font size written in a component's scoped block is a bug: it means a token is missing from `app.css`. The only literals left in components are one-off geometry (progress bar height, toggle track).
3. **No motion.** No `transition`, no `@keyframes`. Hover changes colour, state changes colour, a toggle knob simply sits at the other end.
4. **No icons, no emoji, no images** other than the user's Google avatar. A tick in the setup checklist is the character `✓`.
5. Shared primitives live in `app.css`, component-specific layout stays in the component's scoped block. If a rule appears in two components, it belongs in `app.css`.
6. No em dashes, in copy or comments.

## 1. Foundations

### Fonts

| Token | Value | Use |
|---|---|---|
| `--app-font` | `-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif` | everything |
| `--app-font-mono` | `ui-monospace, SFMono-Regular, 'SF Mono', Menlo, monospace` | `<code>` chips only |

No IBM Plex Mono, no web fonts, no `<link>` to Google Fonts. The app loads zero font files.

**Five sizes, no more.** Anything that does not fit one is being designed, not styled.

| Token | Size | Use |
|---|---|---|
| `--app-text-meta` | 12px | labels/pills, footnotes (`.note`), counts, code chips |
| `--app-text-body` | 14px | the default: copy, controls, table rows, nav, card headings |
| `--app-text-head` | 16px | wordmark, step headings |
| `--app-text-title` | 20px | a section title inside a page |
| `--app-text-page` | 24px | the one `h1` per page (`.title`) |

Weights: `--app-weight-normal` 400 (copy, `dt`), `--app-weight-medium` 500 (values, button labels), `--app-weight-bold` 600 (headings, active nav). Nothing is 700.

Line height: `--app-lh-tight` 1.25 for headings, `--app-lh-body` 1.5 for everything else. Running copy is capped at `--app-measure` (72ch).

### Gaps

One 4px scale. `--app-space-1` 4 · `-2` 8 · `-3` 12 · `-4` 16 · `-5` 24 · `-6` 32 · `-7` 48 · `-8` 64.

Four of them have named jobs, so intent survives a refactor. Use the named token when the job matches:

| Token | Value | Job |
|---|---|---|
| `--app-gap-inline` | 8px | buttons side by side, label next to a name |
| `--app-gap-stack` | 12px | items inside one block |
| `--app-gap-block` | 16px | card to card, card padding (`--app-pad-card`) |
| `--app-gap-section` | 24px | page header to content, sidebar to content |

Card header padding is `--app-pad-card-head` (12px/16px). Page padding is `--app-pad-page` = `clamp(16px, 4vw, 32px)`.

Layout widths: `--app-width-page` 1280px (dashboard shell) · `--app-width-narrow` 800px (welcome, profile) · `--app-width-panel` 480px (centred signed-out card) · `--app-width-field` 440px (input) · `--app-width-list` 560px (picklist) · `--app-sidebar` 200px.

Sizes: `--app-control-height` 32px (buttons, inputs) · `--app-row-height` 40px (clickable list row) · `--app-marker` 20px (step numeral, pill height, toggle knob) · `--app-avatar` 24px · `--app-avatar-lg` 48px.

Radii: `--app-radius` 6px (cards, buttons, inputs, lists) · `--app-radius-sm` 4px (code chip, toggle knob) · `--app-radius-pill` 999px (labels, avatars). Nothing is bigger than 6px except a pill.

**No breakpoints.** Columns reflow with `flex-wrap` and a `min()` basis, same discipline as the landing page.

### Colours

| Token | Value | Use |
|---|---|---|
| `--app-fg` | `#1f2328` | headings, values, anything you must read |
| `--app-fg-muted` | `#59636e` | labels, body copy, `dt`, secondary rows |
| `--app-fg-subtle` | `#818b98` | disabled, placeholder, unmet checklist item |
| `--app-fg-on-emphasis` | `#fff` | text on a filled button |
| `--app-canvas` | `#fff` | page and card background |
| `--app-canvas-subtle` | `#f6f8fa` | card headers, hover, neutral fills |
| `--app-border` | `#d1d9e0` | card, input, list outlines |
| `--app-border-subtle` | `#e4e8ec` | dividers inside a card |
| `--app-border-emphasis` | `rgba(31,35,40,0.15)` | edge of a filled button |

Four roles, each with a text colour, a tint and a line, so a state can be a word, a pill or a whole panel without inventing a colour:

| Role | Text | Tint | Line | Means |
|---|---|---|---|---|
| accent | `#0969da` | `#ddf4ff` | `rgba(9,105,218,0.4)` | links, focus, "syncing now" |
| success | `#1a7f37` | `#dafbe1` | `rgba(31,136,61,0.4)` | connected, done, sync on |
| attention | `#9a6700` | `#fff8c5` | `rgba(154,103,0,0.4)` | half-configured, needs a decision |
| danger | `#d1242f` | `#ffebe9` | `rgba(255,129,130,0.5)` | failed, destructive |

Buttons carry their own tokens: `--app-btn-bg` `#f6f8fa` / `--app-btn-bg-hover` `#eef1f4` (neutral), `--app-btn-primary` `#1f883d` / `--app-btn-primary-hover` `#1a7f37` (the one affirmative fill), `--app-btn-danger-hover` `#a40e26`.

Rules: the green button is a role of its own, not `success` reused. A saturated fill appears only on a button, a toggle track or a progress fill. Everything else states its role with text on a tint. Focus is `--app-focus-ring` on inputs and a 2px accent outline elsewhere.

## 2. Components (all in `app.css`)

- **`.card`**: the only container: white, 1px `--app-border`, 6px radius, no shadow. `.card-head` (subtle background, hairline under it, `h2` at 14px/600, one action or one `.label` on the right) plus `.card-body` (16px padding). Consecutive cards space themselves; a card never contains another card.
- **`.label`**: the state pill. 20px tall, `--app-radius-pill`, 12px/500, one tone class: `neutral` `accent` `success` `attention` `danger`. Colour repeats what the text already says, it never carries the meaning alone.
- **`.btn`**: one shape, three tones. Bare `.btn` is green and commits (max one per view), `.btn.plain` is grey and is the default for everything else, `.btn.danger` is red and destroys. 32px tall, 14px/500, 6px radius. Disabled is `opacity: 0.6`.
- **`.actions`**: a wrapping row of buttons, `--app-gap-inline`. Buttons wrap rather than shrink.
- **`.field`**: stacked label (14px/600) over an input (32px, 6px radius, focus ring). Max `--app-width-field`.
- **`.picklist`**: bordered list box for a short set of radio choices, 40px rows, hover on `--app-canvas-subtle`. Max `--app-width-list`.
- **`.datarows`**: `dl` of term/value pairs: `dt` muted 400, `dd` ink 500, hairline between rows, none after the last. This is how the app states a stored fact.
- **`.page-head`**: the `h1` (`.title`) and its one `.lead` paragraph, 24px of space under it. Every app page starts with one.
- **`.note`**: 12px muted small print. **`.error`**: 14px on the danger tint with a danger line, 6px radius. **`.loading`**: 14px muted, the single word while data is in flight.
- **`code`**: mono 12px on `--app-canvas-subtle` with a subtle border, 4px radius.

Layout pieces that stay local to their component: `AppHeader` (wordmark, avatar, sign out), the sidebar menu in `DashboardLayout` (36px rows, active = subtle fill + 600 weight, **no coloured bar**), the welcome progress bar, the settings toggle, the setup step numeral.

## 3. Page anatomy

Shell: `AppHeader` (hairline bottom) → `.shell` (max `--app-width-page`, `--app-gap-section` between sidebar and content) → sidebar (Overview / Connections / Settings, then Account → Profile) → content, a `.page-head` followed by cards. `/me` renders inside this shell as an absolute child route, so the sidebar stays visible. `/welcome` is the only page outside it: sticky bar with a progress fill, one narrow column.

## 4. Banned

Landing tokens (`--ink`, `--body`, `--hairline`, `--font-mono`, `--accent`) · the atmosphere layer and grain · `.surface`, `.eyebrow`, `.link-mono`, `.pill` · mono uppercase labels · letter-spacing on anything but the wordmark · icons, emoji, status dots, arrow glyphs · shadows · gradients · nested cards · a second green button on one view · colour as the only carrier of a state · any `transition`.
