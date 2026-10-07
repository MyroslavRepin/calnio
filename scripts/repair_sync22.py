"""One-off repair of sync 22 (user 25) after the Oct 6 trash. Dry run unless APPLY=1.

Runs inside the production container, so Calnio's own code decrypts the grants
and nothing leaves it. Prints ids and counts only, never a token or a title.
"""

import os
import sys
from collections import Counter
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
from backend.repo.notion import NotionPageRepo, paginate
from backend.services.sync import remember
from sqlalchemy import select

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

    # Every trashed page of the data source, grouped by when it was trashed.
    raw = paginate(lambda cursor: notion.client.data_sources.query(
        data_source_id=mapping.data_source_id, in_trash=True, start_cursor=cursor))
    trashed = [parser.parse_page(item) for item in raw if item.get("in_trash")]
    print(f"trashed pages in the data source: {len(trashed)}")
    by_minute = Counter(page.updated_at.strftime("%m-%d %H:%M") for page in trashed if page.updated_at)
    for minute, count in sorted(by_minute.items()):
        print(f"  trashed at {minute} UTC: {count}")
    batch = [page for page in trashed if page.updated_at and BATCH_START <= page.updated_at < BATCH_END]
    print(f"pages to restore (01:53 batch): {len(batch)}")

    # What the calendar really holds now, read with a tokenless report.
    calendar = CalDavEventRepo(caldav_url=settings.caldav_url, username=credential.icloud_email,
                               password=decrypt(credential.password_encrypted), calendar_url=mapping.calendar_url or "")
    events = calendar.changes(None, set()).events
    print(f"events in the calendar: {len(events)}")

    rows = list(db.scalars(select(SyncedEvent).where(SyncedEvent.mapping_id == MAPPING_ID)))
    rows_by_path = {href_path(row.caldav_href): row for row in rows}
    print(f"link rows now: {len(rows)}")

    # Pair every event with its original page: by uid when Calnio made it,
    # by title and start day when the user made it in Apple Calendar.
    batch_by_id = {page.id: page for page in batch}
    plan = []
    used = set()
    for event in events:
        page = batch_by_id.get(event.uid)
        how = "uid"
        if page is None:
            how = "title+day"
            candidates = []
            for candidate in batch:
                date = parser.parse_date(candidate.properties, due)
                if date is not None and candidate.title == event.title and date.start.date() == event.start.date():
                    candidates.append(candidate)
            if len(candidates) != 1:
                stop(f"event {event.uid} matches {len(candidates)} trashed pages by title and day")
            page = candidates[0]
        if page.id in used:
            stop(f"page {page.id} would be linked twice")
        used.add(page.id)
        row = rows_by_path.get(href_path(event.href or ""))
        plan.append((event, page, how, row))

    unmatched = [page.id for page in batch if page.id not in used]
    repoint = [item for item in plan if item[3] is not None]
    insert = [item for item in plan if item[3] is None]
    duplicates = [item[3].notion_page_id for item in repoint if item[3].notion_page_id != item[1].id]
    print(f"matched by uid: {sum(1 for item in plan if item[2] == 'uid')}, by title+day: {sum(1 for item in plan if item[2] == 'title+day')}")
    print(f"rows to repoint: {len(repoint)}, rows to insert: {len(insert)}, duplicate pages to trash: {len(duplicates)}")
    print(f"batch pages with no event (restored, Calnio will create their event): {len(unmatched)}")
    if len(rows) != len(repoint):
        stop("some existing link rows point at events not in the calendar listing")

    if not APPLY:
        print("DRY RUN: nothing changed")
        sys.exit(0)

    mapping.enabled = False
    db.commit()
    print("sync 22 paused")
    for page in batch:
        notion.client.pages.update(page_id=page.id, in_trash=False)
    print(f"restored {len(batch)} pages")
    for event, page, how, row in plan:
        if row is None:
            row = SyncedEvent(mapping_id=MAPPING_ID, user_id=USER_ID, notion_page_id=page.id,
                              caldav_href=event.href or "", caldav_uid=event.uid)
            db.add(row)
        row.notion_page_id = page.id
        remember(row, event)
    db.commit()
    print(f"link rows now: {len(list(db.scalars(select(SyncedEvent).where(SyncedEvent.mapping_id == MAPPING_ID))))}")
    for page_id in duplicates:
        notion.trash_page(page_id)
    print(f"trashed {len(duplicates)} duplicate pages")
    mapping.enabled = True
    db.commit()
    print("sync 22 resumed")
