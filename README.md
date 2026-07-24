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
- `notion_page_id` — str, unique, index (mapping key)
- `caldav_href` — str (address in iCloud, for update/delete)
- `caldav_uid` — str (iCal uid, = notion id for now)
- `etag` — str, nullable (detect external CalDAV changes)
- `notion_last_edited` — datetime(tz), nullable (LWW change detection)
- `row_created_at` / `row_updated_at` — datetime(tz), db-managed

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

### Frontend integration
- **Dev:** Vue on Vite `:5173`, API on `:8080`. Login start = top-level nav (no CORS). Callback redirects back to `:5173` with JWT. API calls need CORS.
- **Prod:** Vue built to `/dist`, served by FastAPI via `StaticFiles(html=True)` — same origin, no CORS. Google `redirect_uri` becomes the prod domain callback.
