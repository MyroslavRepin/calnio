"""One-off repair of sync 22 (user 25) after the Oct 6 trash. Dry run unless APPLY=1.

Runs inside the production container, so Calnio's own code decrypts the grants
and nothing leaves it. Prints ids and counts only, never a token or a title.
"""

import os
import sys
from datetime import datetime, timezone

from backend.core.config import settings
from backend.core.crypto import decrypt
from backend.deps.db import SessionLocal
from backend.models.caldav_credential import CaldavCredential
from backend.models.notion_connection import NotionConnection
from backend.models.sync_mapping import SyncMapping
from backend.models.synced_event import SyncedEvent
from backend.models.user import User  # noqa: F401, so the mappers resolve
from backend.repo.caldav import CalDavEventRepo, href_path
from backend.repo.notion import NotionPageRepo
from backend.services.sync import remember
from notion_client.errors import APIResponseError
from sqlalchemy import select
import re

NOTION_ID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

MAPPING_ID = 22
USER_ID = 25
# The run that trashed everything: 79bbb616, 01:53:54 to 01:54:15 UTC.
BATCH_START = datetime(2026, 10, 6, 1, 53, tzinfo=timezone.utc)
BATCH_END = datetime(2026, 10, 6, 1, 55, tzinfo=timezone.utc)
APPLY = os.environ.get("APPLY") == "1"


def stop(message):
    print(f"STOP: {message}")
    sys.exit(1)


with SessionLocal() as db:
    mapping = db.get(SyncMapping, MAPPING_ID)
    if mapping is None or mapping.user_id != USER_ID:
        stop("mapping 22 does not belong to user 25")
    connection = db.scalars(select(NotionConnection).where(NotionConnection.user_id == USER_ID)).one()
    credential = db.scalars(select(CaldavCredential).where(CaldavCredential.user_id == USER_ID)).one()
    notion = NotionPageRepo(decrypt(connection.access_token_encrypted))
    parser = notion.parser
    due = mapping.due_date_property

    # What the calendar really holds now, read with a tokenless report.
    calendar = CalDavEventRepo(caldav_url=settings.caldav_url, username=credential.icloud_email,
                               password=decrypt(credential.password_encrypted), calendar_url=mapping.calendar_url or "")
    events = calendar.changes(None, set()).events
    print(f"events in the calendar: {len(events)}")

    rows = list(db.scalars(select(SyncedEvent).where(SyncedEvent.mapping_id == MAPPING_ID)))
    rows_by_path = {href_path(row.caldav_href): row for row in rows}
    print(f"link rows now: {len(rows)}")

    def is_original(raw):
        """Whether a raw page is a sync 22 page trashed by the 01:53 run, or one this script already restored."""
        if raw.get("parent", {}).get("data_source_id") != mapping.data_source_id:
            return False
        if raw.get("in_trash") is not True:
            return True
        edited = parser.parse_timestamp(raw.get("last_edited_time"))
        return edited is not None and BATCH_START <= edited < BATCH_END

    def retrieve(page_id):
        """A page by id, trashed or not, None when Notion has no such page."""
        try:
            return notion.client.pages.retrieve(page_id=page_id)
        except APIResponseError as exc:
            if exc.code in ("object_not_found", "validation_error"):
                return None
            raise

    # Calnio made these events from the pages, so an event's uid is its page id.
    # Events the user made in Apple Calendar have no such page and keep the row
    # today's import gave them.
    plan = []
    kept = []
    missing = []
    for event in events:
        row = rows_by_path.get(href_path(event.href or ""))
        raw = retrieve(event.uid) if NOTION_ID.match(event.uid) else None
        if raw is None or not is_original(raw):
            if row is not None:
                kept.append(event.uid)
            else:
                missing.append(event.uid)
            continue
        if row is not None and row.notion_page_id != raw["id"]:
            stop(f"event {event.uid} is linked to another page")
        plan.append((event, raw, row))

    to_restore = [raw["id"] for event, raw, row in plan if raw.get("in_trash") is True]
    to_insert = [event.uid for event, raw, row in plan if row is None]
    print(f"originals matched by uid: {len(plan)} (still in trash: {len(to_restore)}, rows to insert: {len(to_insert)})")
    print(f"events kept on today's import: {len(kept)}")
    print(f"events with no row and no original: {len(missing)}")
    if len(rows) != len(kept) + sum(1 for item in plan if item[2] is not None):
        stop("some link rows point at events not in the calendar listing")
    expected = os.environ.get("EXPECT")
    if expected is not None:
        want_plan, want_kept = (int(part) for part in expected.split(","))
        if (len(plan), len(kept), len(missing)) != (want_plan, want_kept, 0):
            stop(f"expected {want_plan} originals, {want_kept} kept, 0 missing")

    if not APPLY:
        print("DRY RUN: nothing changed")
        sys.exit(0)
    if expected is None:
        stop("APPLY needs EXPECT")

    was_enabled = mapping.enabled
    mapping.enabled = False
    db.commit()
    print("sync 22 paused")
    for page_id in to_restore:
        notion.client.pages.update(page_id=page_id, in_trash=False)
    print(f"restored {len(to_restore)} pages")
    for event, raw, row in plan:
        if row is None:
            row = SyncedEvent(mapping_id=MAPPING_ID, user_id=USER_ID, notion_page_id=raw["id"],
                              caldav_href=event.href or "", caldav_uid=event.uid)
            db.add(row)
            remember(row, event)
    db.commit()
    print(f"link rows now: {len(list(db.scalars(select(SyncedEvent).where(SyncedEvent.mapping_id == MAPPING_ID))))}")
    mapping.enabled = was_enabled
    db.commit()
    print(f"sync 22 resumed (enabled={was_enabled})")
