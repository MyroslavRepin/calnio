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

### Todo
1. `core/security.py` — `JWTManager` class (PyJWT, HS256): `create(user_id)`, `decode(token)`. Singleton `jwt_manager`.
2. `repo/user_repo.py` — `get_user_by_oauth(db, provider, sub)`, `create_user_with_oauth(db, ...)`. Plain functions taking `Session`.
3. `services/auth.py` — `login_with_google(db, userinfo)` = get-or-create (registration + login in one).
4. `api/oauth.py` callback — call service, issue JWT, `RedirectResponse` to frontend (restore `FRONTEND_URL`).
5. `deps/auth.py` — `get_current_user(token)` dependency: decode JWT, load user, else 401. Protects API routes.
6. Restore `CORSMiddleware` once Vue calls the API with `Authorization: Bearer`.

### Frontend integration
- **Dev:** Vue on Vite `:5173`, API on `:8080`. Login start = top-level nav (no CORS). Callback redirects back to `:5173` with JWT. API calls need CORS.
- **Prod:** Vue built to `/dist`, served by FastAPI via `StaticFiles(html=True)` — same origin, no CORS. Google `redirect_uri` becomes the prod domain callback.
