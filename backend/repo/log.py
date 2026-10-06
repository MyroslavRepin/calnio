from pathlib import Path

from backend.core.logging import PROBLEMS_FILE
from backend.parsers.log import LogParser
from backend.schemas.admin import AdminLogEntry, AdminLogGroup, AdminProblems

# How much of the end of the file is read: thousands of records, and still
# quick enough to read on every page load.
TAIL_BYTES = 4 * 1024 * 1024

# How many single entries the answer carries. Groups count all of them.
ENTRY_LIMIT = 500


class LogRepo:
    """The newest warnings and errors loguru wrote to problems.json."""

    def __init__(self, path: Path = PROBLEMS_FILE) -> None:
        self.path = path
        self.parser = LogParser()

    def entries(self) -> list[AdminLogEntry]:
        """Every record in the tail of the file, newest first."""
        if not self.path.is_file():
            return []

        with self.path.open("rb") as file:
            size = file.seek(0, 2)
            file.seek(max(0, size - TAIL_BYTES))
            text = file.read().decode("utf-8", errors="replace")

        lines = text.splitlines()
        if size > TAIL_BYTES:
            # The read started mid-record, so its first line is a fragment.
            lines = lines[1:]

        answer: list[AdminLogEntry] = []
        for line in reversed(lines):
            entry = self.parser.parse_entry(line)
            if entry is not None:
                answer.append(entry)
        return answer

    def problems(self) -> AdminProblems:
        """The newest entries, plus every entry grouped by where it was written."""
        entries = self.entries()

        groups: dict[tuple[str, str], AdminLogGroup] = {}
        for entry in entries:
            key = (entry.level, entry.location)
            group = groups.get(key)
            if group is None:
                # Entries arrive newest first, so the first one seen is the
                # message the group shows.
                groups[key] = AdminLogGroup(
                    level=entry.level,
                    location=entry.location,
                    error_type=entry.error_type,
                    message=entry.message,
                    count=1,
                    last_time=entry.time,
                )
            else:
                group.count += 1

        ordered = sorted(groups.values(), key=lambda group: group.count, reverse=True)
        return AdminProblems(entries=entries[:ENTRY_LIMIT], groups=ordered)
