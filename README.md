## Known errors
- CalDav events may be duplicated with same UID
- Sometimes `error: reason, No reason` happens

## Sync model (MVP: Notion -> Apple Calendar, one-way)

- **Source of truth: Notion.** Recompute events from Notion every run.
- **Mapping key: Notion page id == iCal `uid`.** Set at create time, same id in both systems.
- **`synced_events` table = link index `notion_page_id -> caldav_href`.** Only rows Calnio owns. Foreign Apple Calendar events (no row) are never touched.
- No full event mirror in DB — the old `caldav_events` mirror is replaced by this lean link table.

### `synced_events` columns
- `id` — int PK
- `user_id` — int FK -> `users.id` (cascade), index; unique together with `notion_page_id`
- `notion_page_id` — str, index (mapping key, unique *per user*)
- `caldav_href` — str (address in iCloud, for update/delete)
- `caldav_uid` — str (iCal uid, = notion id for now)
- `etag` — str, nullable (detect external CalDAV changes)
- `notion_last_edited` — datetime(tz), nullable (LWW change detection)
- `row_created_at` / `row_updated_at` — datetime(tz), db-managed

## Per-user sync (done)

Sync runs on each user's own stored connections, not on `.env`. One switch per
user, off until they turn it on.

### Model — `sync_settings` (1 per user)
- `enabled` — bool, default **false**. Nothing is written to anybody's calendar
  until they ask.
- `due_date_property` — the Notion date column to read. No default: guessing
  "Due Date" would let a user see a successful run that created nothing.
  Cleared automatically when they switch to a different database.
- `last_run_at` / `last_status` — `ok` | `error` | `auth_error`. No counts and
  no history table.

### Engine — `services/sync.py`
- `sync_user(user_id)` — one user's reconcile loop, own session, never raises.
  Uses the `calendar_url` stored at setup, so it skips iCloud's slow
  calendar-home discovery.
- `run_all_users()` — the scheduled job. One interval job, `max_instances=1`,
  users synced sequentially, each isolated by its own try/except.
- Eligible = `enabled` AND `due_date_property` AND `data_source_id` AND
  `calendar_url`.
- **Failure policy:** Notion 401/403 or CalDAV `AuthorizationError` →
  `enabled=false`, status `auth_error`. Anything else (network, 502, timeout) →
  status `error`, retried next tick. Re-sending a rejected app-specific
  password every interval is how an Apple ID gets locked.
- `sync_notion_to_caldav` (the old single-user loop) is kept for reference and
  never scheduled. It cannot run any more: `synced_events.user_id` is required
  and it has no user to attribute rows to. `reset_all()` still works and is
  still `.env`-based.

### API (`backend/api/sync.py`, prefix `/api/v1`)
- `GET /me/sync` — `{enabled, eligible, due_date_property, last_run_at, last_status}`.
  Also the poll target while a queued run finishes.
- `PUT /me/sync` — `{enabled?, due_date_property?}`. Turning it on queues a
  one-off job (id `sync-user-<id>`, so a double click cannot stack two runs);
  the request never waits for iCloud. A due-date name is validated against the
  live Notion schema.
- `GET /me/notion/date-properties` — the picker's options (lives with the
  Notion router because it is a schema read).

### Config
`SCHEDULER_ENABLED` (renamed from `ACTIVE_SYNC`) is the global off-switch: no
interval job and no on-demand runs, so an instance pointed at the real database
never writes to a user's calendar.

### Frontend
`composables/useSync.js`; Settings holds the switch + due-date picker, Overview
reports status read-only. After turning it on the client polls `GET /me/sync`
every 3s (≤60s) until `last_run_at` moves.

### Known gaps (deliberate)
- No per-run counts and no run history — Overview's "Pages", "With a due date"
  and "Events synced" rows are still `—`.
- No manual "sync now" button; a run is only triggered by the interval or by
  turning the switch on.
- Turning sync off leaves existing events and link rows alone. There is no
  per-user "remove my synced events" action.
- Sequential loop: N users cost N × (Notion + iCloud) round trips per tick.

## Roadmap

### Phase 1 — replace mirror with link table
1. New model `models/synced_event.py` -> `SyncedEvent` (table `synced_events`, columns above).
2. Delete old `models/caldav_event.py` ORM (`CalDavEventORM` mirror).
3. Alembic migration: drop `caldav_events`, create `synced_events`.

### Phase 2 — reconcile loop in `services/sync.py`
1. Pull Notion pages -> map to events (skip archived, skip no Due Date).
2. Load `synced_events` into `by_page_id = {notion_page_id: row}`.
3. For each Notion event:
   - no row -> `caldav.create`, insert row (`page_id`, `href`, `uid`, `last_edited`).
   - row + `page.last_edited > row.notion_last_edited` -> `caldav.update` by `href`, bump row.
   - else -> skip (unchanged).
4. **Reconcile deletes:** for each row whose `notion_page_id` not in current Notion ids -> `caldav.delete` by `href`, remove row.

### Phase 3 — cleanup
1. Move import-time `discover_calendar_url()` / `connect()` out of module scope into a setup fn.
2. Move hardcoded `tasks_data_source_id` into config/`.env`.

## Auth (Google OAuth login)

Login via Google. **No separate registration** — first login creates the user (get-or-create), later logins fetch them. One flow does both.

### Model
- `users` — app identity: `id, email (unique), name, picture, timestamps`.
- `oauth_accounts` — provider link, N per user: `user_id (FK), provider, provider_account_id (= Google sub), access_token?, refresh_token?, expires_at?`. Unique `(provider, provider_account_id)`. Lookup key on login = `sub`, never email.

### Flow
`GET /auth/oauth/google/login` (start → 302 to Google) → Google consent → `GET /auth/oauth/google/callback` (verify `state`, exchange `code` for token) → get-or-create user → issue our JWT → redirect to frontend `#token=`.

### Done
1. `authlib` + `SessionMiddleware` (holds OAuth `state`, CSRF).
2. `core/oauth.py` — Google registered via discovery url.
3. `api/oauth.py` — `login` + `callback` (callback returns JSON for now).
4. `models/user.py`, `models/oauth_account.py` + Alembic migration `673af4d22aca` (applied).

5. `core/security.py` — `JWTService` (PyJWT, HS256): access + refresh pair, rotation on refresh.
6. `api/oauth.py` — `/auth/refresh`, `/auth/logout`, `/auth/me`. Both tokens in httpOnly cookies (**not** `Authorization: Bearer` — JS never holds a token). Refresh cookie scoped to path `/auth`.
7. `deps/auth.py` — `get_current_user` dependency: reads the access cookie, decodes, loads the `User` row, else 401. `/auth/me` uses it.
8. `CORSMiddleware` with `allow_credentials` + explicit origin (a wildcard is rejected when credentials are sent).

### Todo
1. `services/auth.py` — only if the flow grows past one repo call; it hasn't yet.

## Apple Calendar connection (per-user iCloud credentials)

Each user connects their own iCloud account with an app-specific password. The `.env` `ICLOUD_EMAIL` / `APP_SPECIFIC_PASSWORD` remain the **single-user dev path** the scheduler still runs on — per-user sync is a later phase.

### Model
`caldav_credentials` — one row per user (unique `user_id`): `icloud_email`, `password_encrypted` (Fernet), `calendar_url` (NULL until the user picks one), `last_verified_at`. A row only exists if iCloud accepted the credential, so "row exists" == "credentials worked".

### API (`backend/api/apple_calendar.py`, prefix `/api/v1`)
| Method | Path | |
|---|---|---|
| `PUT` | `/me/apple-calendar` | verify against iCloud → encrypt → upsert. `201` new / `200` replace. Returns status + the calendar list (saves the wizard a round trip). |
| `GET` | `/me/apple-calendar` | status only, never the password. `404` if not connected. |
| `DELETE` | `/me/apple-calendar` | forgets the credential; leaves iCloud events and calendars alone. `204`. |
| `GET` | `/me/apple-calendar/calendars` | list the account's calendars. |
| `POST` | `/me/apple-calendar/calendars` | create one (default name `Calnio`). `201`. |
| `PUT` | `/me/apple-calendar/calendar` | select a calendar; rejects a URL the account doesn't own. |

### Rules
- **`401` means our auth only, never iCloud's.** The frontend's `apiFetch` auto-refreshes and retries on 401 — returning it for a bad iCloud password would resubmit that password to Apple and risk locking the Apple ID. iCloud rejection is `400`; iCloud unreachable is `502`.
- The plaintext password never appears in a response body (not even masked), a log line, or an exception message. Raw CalDAV exception text is logged, never forwarded.
- `/me` only — no `{user_id}` in any path, so IDOR is unrepresentable.
- `CREDENTIALS_ENCRYPTION_KEY` (Fernet) is required at boot. **Back it up with the database** — losing it makes every stored credential unreadable and forces all users to reconnect.

### Known gaps (deliberate)
- Disconnect orphans events already pushed; cleaning them needs `synced_events.user_id`, which doesn't exist yet.
- `calendar_url` on the credential row is a placeholder for a real Notion-DB→calendar mapping table.
- `reset_all()` / `delete_all()` are unscoped and would destroy foreign events in a user-picked calendar. No callers today (REPL-only) — fix before anything can trigger them.
- Route handlers hold the logic inline; extract to `services/apple_calendar.py` when the per-user sync loop needs to share the decrypt path.

## Notion connection (per-user OAuth)

Each user authorizes Calnio against their own Notion workspace and picks the
database Calnio should read. The `.env` `NOTION_TOKEN` / `TASKS_DATA_SOURCE`
remain the **single-user dev path** the scheduler still runs on — per-user sync
is a later phase, so connecting today records the link and nothing more.

Needs a **public** integration at notion.so/my-integrations (separate from the
internal one `NOTION_TOKEN` belongs to), with the callback registered as
`NOTION_OAUTH_REDIRECT_URI`.

### Model
`notion_connections` — one row per user (unique `user_id`, `ON DELETE CASCADE`):
`access_token_encrypted` (Fernet), `bot_id`, `workspace_id`, `workspace_name`,
`workspace_icon`, `data_source_id` + `data_source_name` (NULL until the user
picks one), `last_verified_at`. Row exists == the grant worked;
`data_source_id` set == fully configured.

Deliberately **not** `oauth_accounts`: that table answers "who is this user" (a
login identity keyed by Google `sub`, N per user). This answers "what does this
user connect to" — a resource grant, 1 per user, with workspace metadata that
has no column there.

Under API 2025-09-03 the stored id is a **data source** id, not a database id —
that is what `data_sources.query` takes, and what `list_databases()` already
returns.

### API (`backend/api/notion.py`, no router prefix)
| Method | Path | |
|---|---|---|
| `GET` | `/auth/oauth/notion/login` | returns `{"authorize_url": …}` as JSON, does not redirect |
| `GET` | `/auth/oauth/notion/callback` | exchange → encrypt → upsert → 302 to `/dashboard/connections` |
| `GET` | `/api/v1/me/notion` | status only, never the token. `404` if not connected. |
| `DELETE` | `/api/v1/me/notion` | best-effort revoke at Notion, then forget the row. `204`. |
| `GET` | `/api/v1/me/notion/databases` | the data sources shared with us; legitimately empty. |
| `PUT` | `/api/v1/me/notion/database` | select one; verified with a single `retrieve`. |

Two path families in one file on purpose: the OAuth dance belongs beside
Google's, the resource routes belong under `/api/v1`, and one feature belongs in
one file.

### Rules
- **`/auth/oauth/notion/login` returns JSON instead of a 302.** The access token
  lives 5 minutes and this route needs it; a plain link would 401 for anyone who
  left the dashboard open, with no `apiFetch` in the loop to refresh silently.
  The frontend fetches the URL through `apiFetch`, then navigates — so the
  callback seconds later still has a valid cookie.
- **`SessionMiddleware` must not use Starlette's `SameSite=Lax` default.** The
  login call above is a cross-origin XHR in dev, and the OAuth `state` cookie set
  on that response is only usable cross-site as `SameSite=None; Secure`. It now
  follows `COOKIE_SAMESITE` / `COOKIE_SECURE`. Google's flow never hit this — its
  state cookie is set during a top-level navigation.
- **`401` means our auth only, never Notion's** — same reasoning as iCloud.
  Notion 401/403/404 → `400`; rate limits, 5xx and network failures → `502`.
- The callback authenticates by calling `get_current_user` by hand rather than as
  a dependency: its 401 is a JSON body, and a browser navigation has to end on a
  page. It bounces to `/dashboard/connections?notion_error=session` instead.
- Disconnect revokes at Notion **best effort** — a Notion outage must never trap a
  user in a connection they asked to end. This differs from the iCloud
  disconnect, which leaves Apple alone: events there are the user's data, whereas
  the Notion grant is ours.

### Known gaps (deliberate)
- No `refresh_token` / `expires_at` columns. Notion access tokens do not expire;
  token rotation is opt-in per integration and is not enabled. Enabling it later
  is a migration.
- Nothing reads the selected data source yet — `services/sync.py` is untouched
  and still runs on `NOTION_TOKEN` + `TASKS_DATA_SOURCE`.
- The due-date property is still the global `EVENT_DUE_DATE_FIELD_NAME`; per-user
  property mapping is the next phase.
- Route handlers hold the logic inline, like `apple_calendar.py`. `_repo()` is the
  single decrypt path — lift it to `services/notion.py` when per-user sync needs
  it.

### Frontend integration
- **Dev:** Vue on Vite `:5173`, API on `:8080`. Login start = top-level nav (no CORS). Callback redirects back to `:5173` with JWT. API calls need CORS.
- **Prod:** Vue built to `/dist`, served by FastAPI via `StaticFiles(html=True)` — same origin, no CORS. Google `redirect_uri` becomes the prod domain callback.
