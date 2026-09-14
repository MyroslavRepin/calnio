# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

- **Calnio** — syncs Notion with Apple Calendar. Notion holds tasks; Apple Calendar is where people look. Calnio pushes Notion due dates into Apple Calendar via CalDAV on a schedule.
- MVP (only thing in scope): **one-way sync, Notion → Apple Calendar**. Notion is a READ-ONLY source — no write back to Notion, no Calendar → Notion propagation, no two-way sync. Do not build those.
- A user has **N syncs**. One sync = one Notion data source + its date column + one Apple calendar + its own switch. The two grants (Notion OAuth token, iCloud app-specific password) stay one per user; only the targets multiply.
- Second track in progress: Google OAuth login (see README "Auth" section for flow + todo list).

## Commands

- Install deps: `uv sync` (package manager is **uv**, not pip)
- Add dep: `uv add <package>` (dev: `uv add --dev <package>`)
- Dev server: `uv run uvicorn main:app --reload --port 8080`
- Migrations: `uv run alembic upgrade head`; new one: `uv run alembic revision --autogenerate -m "..."` (autogenerate works — `alembic/env.py` imports all models and uses `Base.metadata`; a new model must be imported there or autogenerate won't see it)
- Frontend dev server: `cd frontend && npm run dev` (Vite on 5173, cross-origin to the API on 8080 — that setup works, leave it alone)
- Docker: `docker compose up --build` — **production only**, serves on 8082 via `network_mode: host` (the container reaches a self-hosted Postgres on the same machine through `localhost`, and the port number itself dodges a collision with another service already on that host's 8080). Reads `.env.prod` (not `.env`), builds the Vue app in a `node:22-slim` stage, one uvicorn worker, no `--reload`. Migrations are **not** run by the container.
- Type check: pyright (config in `pyrightconfig.json`, venv-aware)
- No tests and no linter configured yet.

## Architecture

FastAPI app in `main.py`: lifespan starts an APScheduler `BackgroundScheduler` that runs `run_all_users` every `SYNCING_INTERVAL_MINUTES` (and once at startup) when `SCHEDULER_ENABLED`; the scheduler itself always starts, because turning a user's sync on queues a one-off job through it. **Because of that scheduler the app runs on exactly one uvicorn worker** — a second worker is a second scheduler and doubles every user's sync. `SessionMiddleware` holds the OAuth `state` cookie; mounts the `oauth`, `apple_calendar`, `notion`, `sync`, `mapping` and `account` routers.

**Serving the SPA** (bottom of `main.py`, after every router): if `frontend/dist` exists — it only does inside the Docker image — `StaticFiles` is mounted on `/assets` and a catch-all `GET /{spa_path:path}` returns `index.html` with `Cache-Control: no-cache`. The Vue router uses history mode, so deep links must be answered by the server with the app itself. Paths starting `api/` or `auth/` raise 404 from that handler so a mistyped endpoint never returns HTML. In dev the directory is absent, the block is skipped, and the app is a bare API exactly as before.

**Everything DB is synchronous** — `create_engine` + `sessionmaker` (`core/db.py`), sync `Session` everywhere, psycopg3 driver. Routes are `async def` only because authlib requires `await`; don't introduce `AsyncSession` — that decision was made deliberately (scheduler thread + blocking CalDAV/Notion IO gain nothing from async).

Layers under `backend/` (import modules directly — **no `__init__.py` anywhere**, e.g. `from backend.schemas.notion_page import NotionPage`):

- `core/` — stateless infra, no DB access: `config.py` (`Settings` from `.env`, singleton `settings`), `db.py` (engine + `SessionLocal`), `base.py` (ORM `Base`), `oauth.py` (authlib Google client), `security.py` (`JWTService`, PyJWT HS256, access + refresh tokens), `crypto.py` (Fernet `encrypt`/`decrypt` — **the only module importing Fernet**), `scheduler.py`, `logging.py` (loguru).
- `models/` — SQLAlchemy ORM, one per file: `user.py`, `sync_mapping.py` (**N per user**, unique `(user_id, data_source_id)`: the data source, its date column, its calendar, its switch, its last run + status), `sync_settings.py` (1 per user: the master switch, last tick + status; its `due_date_property` is vestigial), `oauth_account.py` (N per user, unique `(provider, provider_account_id)`, lookup by Google `sub` never email), `caldav_credential.py` (1 per user, iCloud password Fernet-encrypted; its `calendar_url`/`calendar_name` are vestigial), `notion_connection.py` (1 per user, the grant; its `data_source_id`/`data_source_name` are vestigial), `synced_event.py` (scoped by `mapping_id`).
- Five columns are **vestigial**: `notion_connections.data_source_id` + `data_source_name`, `caldav_credentials.calendar_url` + `calendar_name`, `sync_settings.due_date_property`. Migration `b7c1e4d2f8a3` copied them into `sync_mappings` and left them in place so a downgrade restores working old code. Nothing reads or writes them. A follow-up release drops them.
- `schemas/` — pydantic v2 domain models: `caldav_event.py`, `notion_page.py`, `notion_database.py` (both read-only projections of raw Notion payloads), `synced_event.py`, `sync_mapping.py` (`MappingStatus`, built by hand rather than `model_validate` because `eligible` is not a column; `CreateMappingRequest` carries a **list** of data source ids; `UpdateMappingRequest`).
- `parsers/` — raw third-party payloads into domain schemas, one class per topic: `notion.py` (`NotionParser`), `caldav.py` (`ICalParser`, both directions of the iCal format). Held by the repo as `self.parser`.
- `repo/` — data access, filenames never repeat the folder: `caldav.py` (`CalDavAccountRepo` for calendars, `CalDavEventRepo` for events in one calendar), `notion.py` (`NotionPageRepo`, read-only, no create/update/delete, keep it that way), `user.py` (`UserRepo(db: Session)`, `get_or_create_user_oauth` = login and registration in one), `notion_connection.py` (grant rows plus `revoke()`), `caldav_credential.py`, `sync_settings.py`, `sync_mapping.py` (`SyncMappingRepo`, every read scoped by `user_id` so another account's id reads as missing). A repo's client is built in `__init__`, so constructing one authenticates. **Caller owns the transaction and the commit**, except `services/sync.py`, which commits per event deliberately.
- `services/` — flows composing multiple repos: `sync.py` only. Auth is thin enough to live in the route; add a service only when a flow really composes repos with logic.
- `api/` — route handlers, one literal path per decorator: `oauth.py` (`/auth/*`, since Google's registered redirect URI depends on it), `apple_calendar.py` (`/api/v1/me/apple-calendar*`, per-user iCloud credentials), `notion.py` (`/auth/oauth/notion/*` + `/api/v1/me/notion*`), `sync.py` (`/api/v1/me/sync`, the per-user master switch), `mapping.py` (`/api/v1/me/syncs*`, the N syncs: list, create, configure, delete, per-sync date-properties), `account.py` (`DELETE /api/v1/me`, a hard delete: the `users` row goes, children cascade, the Notion grant is revoked, a queued one-off sync job is cancelled, auth cookies are cleared; **iCloud is deliberately untouched**, pushed events are the user's data and stay, same as an Apple Calendar disconnect. Body must echo the signed-in email). New API routers take the `/api/v1` prefix so they don't collide with the SPA served at `/` in prod.
- `deps/` — FastAPI dependencies and the plumbing routers share: `db.py` (`get_session`), `auth.py` (`get_current_user` reads the access cookie and returns the `User` row, plus `set_auth_cookies` / `clear_auth_cookies`), `notion.py` (`get_connection`, `get_notion_repo`, `notion_errors`), `caldav.py` (`get_credential`, `icloud_errors`, `icloud_credentials`), `sync.py` (`get_sync_settings`, `has_eligible_mapping`, `sync_status`, `queue_run`), `mapping.py` (`get_mapping` scoped to the signed-in user, `date_property_names`, `pick_date_property`, `calendar_name_for`, `mapping_eligible`, `mapping_status`). `queue_run` lives in `deps/` rather than `api/sync.py` because two routers queue a run, and routers never import from routers.

### Sync model (core of the app)

- Source of truth: Notion; events recomputed from Notion every run. Mapping key: Notion page id == iCal `uid`.
- `synced_events` is a **link index** (`(mapping_id, notion_page_id) -> caldav_href`), not an event mirror. Only rows Calnio owns; foreign Apple Calendar events (no row) are never touched.
- **Every query in the loop is scoped by `mapping_id`, not `user_id`.** This is the one correctness trap in the file. The delete pass treats "every row for this mapping" as "everything this data source accounts for", so scoping it by user would make one sync's run delete another sync's events and the CalDAV events behind them.
- Two syncs may share a calendar. Page ids are unique across a workspace, so two data sources writing into one calendar cannot collide on `uid`, and the mapping-scoped delete pass keeps them apart.
- `services/sync.py` reconcile loop, per mapping: query the data source → map pages to events (skip archived / no date in that mapping's column) → create/update in CalDAV per diff against `synced_events` → delete CalDAV events whose Notion page disappeared. **Commits per event on purpose** — a failure mid-batch must not orphan CalDAV events (uncommitted row → next run re-creates → iCloud 412 duplicate).
- **Grain:** `sync_mapping(db, mapping, notion, credential)` runs one mapping and returns its status. `sync_user(user_id)` loads the grant, the credential and the master switch once, builds **one** `NotionPageRepo` for the user, then loops their eligible mappings. `run_all_users()` is the scheduled job and syncs every eligible user sequentially. The scheduling grain is still the user: job id `sync-user-{id}`.
- **Failure grain:** an auth failure (Notion 401/403, CalDAV `AuthorizationError`) is the *user's* problem, because the grant and the credential are shared. It breaks the loop, disables the master switch, and stamps `auth_error` on both the user and the mapping that raised. Anything else, an unshared database included, is *that mapping's* problem: it records `error` and the other mappings still run. The user's `last_status` summarises the tick.
- A mapping runs only when **both** switches are on: `sync_settings.enabled` (master) and `sync_mappings.enabled` (per sync).
- **Setup is one action.** `POST /api/v1/me/syncs` takes a list of data source ids and, for each: infers the date column (`pick_date_property` — one column wins outright, several fall back to a name like Due/Deadline/Date, otherwise None and the sync stays off), reuses or creates a calendar named after the database, enables the sync, and flips the master switch on. This replaced a five-decision wizard that only 3 of 8 users finished. Every inferred value stays editable on the sync's card.
- Deleting a mapping **deletes the CalDAV events it created**, unlike an Apple Calendar disconnect which leaves them. A disconnect keeps the link rows so a reconnect reconciles; deleting the mapping destroys them, so leftover events would be unreachable forever and re-adding the database would answer 412 on every page.
- Change detection: compare title directly, then last-edited timestamp LWW — Notion's `last_edited_time` is minute-rounded, so a pure timestamp check misses same-minute edits.
- `reset_all()` in `sync.py` wipes every CalDAV event + all `synced_events` rows — destructive, never call casually. It runs on the `.env` credentials, not a user's.

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

README is user-facing only: what Calnio does, setup, how to run dev and prod. No roadmap, no architecture detail, no per-feature notes — those live here in CLAUDE.md.

## CHANGELOG.md

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), categories `Added` / `Changed` / `Fixed` / `Removed`, one short line per entry, no em dashes.

- Entries are written **only at version bump time**, not per commit. Look at what changed since the last version bump (`git log`) and summarize it then — don't touch `[Unreleased]` on unrelated commits.
- The version-bump commit renames `[Unreleased]` to `[X.Y.Z] - YYYY-MM-DD` and adds a fresh empty `[Unreleased]` (all four category headers, no bullets) above it, in the same commit that bumps `pyproject.toml` / `frontend/package.json` / `uv.lock`.
- Skip empty categories in a cut version section (don't print `### Fixed` with nothing under it) — the empty scaffold under `[Unreleased]` is the only place all four always appear.

# Calnio Frontend

Vue 3 with `<script setup>`, Vite, vue-router. Two dependencies total: `vue` and `vue-router`. No Tailwind, no state library, no UI kit, no icon set. The design systems below describe how it looks; this section describes how the code is arranged.

## How it works, read this before changing anything

**One look, one system.** The landing page at `/` and every signed-in page share the same tokens, the same `.card`, the same `.btn`. Everything is scoped under `.app-ui`, which every page root carries. The second design system (`.landing-ui`, `styles/landing.css`, the blue atmosphere circles) has been deleted, along with the only web font the project loaded.

**A composable is one shared box of data, not a layer.** In `composables/useNotion.js` the `reactive({...})` sits at the top level of the file, outside the exported function. JavaScript runs a module's top level once no matter how many components import it, so there is exactly one `state` object in the whole app, and every `useNotion()` call hands back that same object. Put it inside the function and each caller gets its own copy, which is what breaks things: `ConnectionsView` draws the status pill from `notion.connection` while `NotionStatus` sets that same object to `null` on disconnect, and the pill updates only because both point at one object.

```js
const { state, connect } = useNotion()   // the shared box
state.connection                          // read it in the template
await connect()                           // change it, every screen sees the change
```

`state` is handed out through `readonly()`. Components never assign to it, they call an action.

**Auth, start to finish.** `main.js` mounts the app, `App.vue` calls `bootstrap()` once. `bootstrap()` strips `?auth_error=` off the URL, then calls `fetchMe()`, which goes through `apiFetch`. `apiFetch` adds `credentials: 'include'`, so the browser attaches its cookies. Both tokens live in httpOnly cookies: the JavaScript never holds a token and never stores one. On a 401, `apiFetch` calls `refresh()` once and retries; `refresh` keeps a single in-flight promise so ten parallel 401s cause one refresh. The result is `state.user` plus `state.ready`, and `state.ready` is the one flag that stops the whole app flickering before auth is known. Login is a real `window.location.href` navigation, not a fetch, because the browser has to follow redirects to Google and back.

**Who loads data.** The shell (`DashboardLayout`, `WelcomeView`) loads the cheap facts every page needs, through `loadWhenSignedIn`: the two connections, the master switch, and the mapping list. A component loads the slow lists itself, on demand: the iCloud calendar listing and the Notion database listing are third-party calls and must not run on page load. `MappingAdd` is the one component that fetches on mount, because listing databases is the only reason that card exists.

**Composables.** `useAuth` (holds `apiFetch`, `send`, `loadWhenSignedIn`), `useNotion` and `useAppleCalendar` (one grant each, no targets), `useSync` (the master switch; exports `watchRun` and `reloadSync` because `useMappings` needs both), `useMappings` (the N syncs, plus `dateProperties` keyed by mapping id), `useSetup` (three stages, derived).

## Rules

Binding. Existing code that breaks them is wrong and gets rewritten, not copied.

**Layout**

1. `views/` holds one file per route, `components/` holds pieces. Both split into `landing/` and `app/`, and a file in one half never imports from the other. They share the stylesheet, not code.
2. Filenames say what the thing is. A view ends in `View`, a layout in `Layout`, everything else is a plain noun. No `The` prefix.
3. Styles live in `styles/`: `tokens.css` (variables on `:root, .app-ui`, plus the page reset), `layout.css` (the three arrangement classes), `base.css` (page-level type, headers, status text), `components.css` (card, label, button, form, list, datarows, wizard, switch). `main.js` imports them in that order, because each reads from the ones before it. There is no fifth file.

**Styles**

4. **There are three ways to arrange anything, and they are named.** `column` puts children one under the other, `row` puts them side by side and wraps, `grid` makes columns that reflow. They live unscoped in `layout.css`, they are the only unscoped classes in the project, and they carry no colour and no type. Never write `display: flex` in a component to get one of these three again.
5. The gap is always different, so it comes from the element: `<div class="column hero">` plus `.hero { --gap: 24px; }`. A `grid` also sets `--col`, the narrowest a column may get before one drops to the next line.
6. A local class carries only what is unique to that one place. If it declares more than two or three properties, look for the shared class it should be sitting on instead.
7. A rule that appears in two components belongs in `components.css`. A rule used once stays in that component's `<style scoped>`.
8. Components read variables, never raw values. A hex, a font size or a gap written in a component is a bug: it means a token is missing. The only literals left are one-off geometry, like a progress bar's height or a toggle track's width.
9. Apart from the three layout classes, every shared class name is defined once, under `.app-ui`. Never unscoped.
10. **A class names the thing, not where it sits or what shape it is.** `inner`, `bar`, `side`, `right`, `head`, `sub`, `off`, `spaced`, `cell`, `mark` and `line` are banned: they force you to read the markup to learn what they mean. `progressfill`, `syncoffnote`, `checkmark`, `stephead`, `newcalendar` do not. Short, lowercase, no BEM, no utility classes.
11. Never leave two rules for one class at equal specificity in different files. A shared `.links` in `components.css` and a scoped `.links` in a component tie, and which wins then depends on file order.

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

# Calnio Landing

The landing page has **no design system of its own any more.** It was a separate
one (atmosphere circles, IBM Plex Mono, 104px display type, `.landing-ui`) and it
is gone: `styles/landing.css`, `AtmosphereField.vue`, `ChipBand.vue`,
`BetaStrip.vue` and `FeatureGrid.vue` are deleted, and the page renders under
`.app-ui` with the app's tokens and the app's `.card` / `.btn` / `.label` /
`.picklist` primitives. Tokens live once, on `:root, .app-ui`, so the page ground
outside a component can read them too. The app loads zero font files.

What is left under `components/landing/`: `LandingNav`, `HeroSection`,
`HowItWorks`, `GetStarted`, `LandingFooter`, `GoogleButton`. They follow the app
design system below, with one documented exception: `--app-text-display`
(`clamp(28px, 5vw, 40px)`), used by the hero headline and nowhere else, because
a 24px headline reads as an unfinished page.

**Product truth (never contradict in copy):** Calnio syncs **one way only, for
now** (Notion → Apple Calendar). A user picks **several databases**, and each one
gets **its own Apple calendar**. Ticking a database is the whole setup: the date
column is inferred and the calendar is created. It is **hosted** — nothing to
install, no server to run. It is **free while in beta** because the developer
self-hosts it. It is **not open source** — never mention GitHub, MIT, Docker,
pip, or a CLI install.

**Voice:** plain, honest, quietly confident. First person singular when the
developer speaks ("I host Calnio myself"). No hype, no "revolutionize", no
exclamation marks, no marketing superlatives. Sentences short. Say the limitation
out loud instead of hiding it.

# Calnio App Design System

**Scope: every page, the landing page included.** `/`, `/dashboard`, `/dashboard/syncs`, `/dashboard/connections`, `/dashboard/settings`, `/welcome`, `/me`. Source of truth: `frontend/src/styles/tokens.css`, `base.css`, `components.css`, `layout.css`. If this document and those files disagree, the files win.

It should read like a settings screen a bank could ship: the marketing page reports what the product does in the same voice the app reports state.

**Rules that hold everywhere here**

1. Every rule lives under `.app-ui` and nothing else, apart from the three layout classes. Every page root carries that class: `DashboardLayout`, `WelcomeView` and `LandingView`.
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

**Five sizes, no more, plus one.** Anything that does not fit is being designed, not styled. The sixth exists only for the landing hero.

| Token | Size | Use |
|---|---|---|
| `--app-text-meta` | 12px | labels/pills, footnotes (`.note`), counts, code chips |
| `--app-text-body` | 14px | the default: copy, controls, table rows, nav, card headings |
| `--app-text-head` | 16px | wordmark, step headings |
| `--app-text-title` | 20px | a section title inside a page |
| `--app-text-page` | 24px | the one `h1` per page (`.title`) |
| `--app-text-display` | `clamp(28px, 5vw, 40px)` | the landing hero headline, and nothing else |

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

## 2. Components (all in `components.css`)

- **`.card`**: the only container: white, 1px `--app-border`, 6px radius, no shadow. `.card-head` (subtle background, hairline under it, `h2` at 14px/600, one action or one `.label` on the right) plus `.card-body` (16px padding). Consecutive cards space themselves; a card never contains another card.
- **`.label`**: the state pill. 20px tall, `--app-radius-pill`, 12px/500, one tone class: `neutral` `accent` `success` `attention` `danger`. Colour repeats what the text already says, it never carries the meaning alone.
- **`.btn`**: one shape, three tones. Bare `.btn` is green and commits (max one per view), `.btn.plain` is grey and is the default for everything else, `.btn.danger` is red and destroys. 32px tall, 14px/500, 6px radius. Disabled is `opacity: 0.6`.
- **`.actions`**: a wrapping row of buttons, `--app-gap-inline`. Buttons wrap rather than shrink.
- **`.field`**: stacked label (14px/600) over an input (32px, 6px radius, focus ring). Max `--app-width-field`.
- **`.picklist`**: bordered list box for a short set of radio choices, 40px rows, hover on `--app-canvas-subtle`. Max `--app-width-list`.
- **`.datarows`**: `dl` of term/value pairs: `dt` muted 400, `dd` ink 500, hairline between rows, none after the last. This is how the app states a stored fact.
- **`.switch`** (+ `.track`, `.knob`, `.switchlabel`): the on/off control. Used by the master switch in Settings and by every sync's own switch, which is why it lives here rather than scoped in a component. 48x28 track, the knob simply sits at the other end, no transition.
- **`.page-head`**: the `h1` (`.title`) and its one `.lead` paragraph, 24px of space under it. Every app page starts with one.
- **`.note`**: 12px muted small print. **`.error`**: 14px on the danger tint with a danger line, 6px radius. **`.loading`**: 14px muted, the single word while data is in flight.
- **`code`**: mono 12px on `--app-canvas-subtle` with a subtle border, 4px radius.

Layout pieces that stay local to their component: `AppHeader` (wordmark, avatar, sign out), the sidebar menu in `DashboardLayout` (36px rows, active = subtle fill + 600 weight, **no coloured bar**), the welcome progress bar, the settings toggle, the setup step numeral.

## 3. Page anatomy

Shell: `AppHeader` (hairline bottom) → `.shell` (max `--app-width-page`, `--app-gap-section` between sidebar and content) → sidebar (Overview / **Syncs** / Connections / Settings, then Account → Profile) → content, a `.page-head` followed by cards. `/me` renders inside this shell as an absolute child route, so the sidebar stays visible. `/welcome` sits outside it: sticky bar with a progress fill, one narrow column, three steps. `/` sits outside it too: `LandingNav`, a centred `main`, `LandingFooter`.

**Who owns what:** Connections owns the two *grants* only (Notion workspace, iCloud account) and has no target pickers. Syncs owns the N mappings: one `MappingCard` each plus `MappingAdd`. Settings owns the master switch. Overview summarises.

## 4. Banned

The retired landing tokens (`--ink`, `--body`, `--hairline`, `--font-mono`, `--font-ui`, `--maxw`, `--pad`, `--sec-top`) and the `.landing-ui` scope · the atmosphere layer and grain · `.surface`, `.eyebrow`, `.link-mono`, `.pill`, `.wrap` · web fonts of any kind · mono uppercase labels · letter-spacing on anything but the wordmark and the hero · icons, emoji, status dots, arrow glyphs · shadows · gradients · **nested cards** (`MappingCard` and `MappingAdd` are cards, so nothing wraps them in one) · a second green button on one view · colour as the only carrier of a state · any `transition`.
