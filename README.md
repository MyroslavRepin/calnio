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
